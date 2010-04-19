from twisted.protocols.basic import LineReceiver

import logging

from ..parser import ADCParser
from ..types import *
from ..types import decode
from ..logger import Logger

class ADCProtocol(LineReceiver):
    delimiter = '\n'
    
    def __init__(self, **kw):
        self.log = kw.get("logger", Logger(ADCProtocol, "n/a"));
        
        if self.context is None:
            raise ValueError("the static field 'context' must be set in the ADCProtocol");

        if self.signals is None:
            raise ValueError("the static field 'signals' must be set in the ADCProtocol");
        
        self.prefix = "n/a";
        self.connected = False;
        self.__state = None;
        self.__signalhandlers = dict();
    
    def connect(self, handle, callback):
        if handle not in self.signals:
            raise ValueError("bad signal handle: " + handle);
        
        self.__signalhandlers[handle] = callback;
    
    def emit(self, handle, *args, **kw):
        if handle not in self.signals:
            raise ValueError("bad signal handle: " + handle);
        
        if not self.__signalhandlers.has_key(handle):
            self.log.msg("no registered handles for signal: " + handle, logLevel=logging.WARN);
            return;
        
        return self.__signalhandlers[handle](*args, **kw);
    
    def setState(self, state):
        """
        Set the state of the current connection.
        This will affect how the next state is picked.
        """
        self.log.msg("setState:", state, logLevel=logging.DEBUG);
        self.__state = state;
    
    def sendFrame(self, frame):
        sf = str(frame);
        self.log.msg("sendFrame:", sf, logLevel=logging.DEBUG)
        self.sendLine(sf);
    
    def connectionMade(self):
        """
        This is the entry for client-client connections.
        """
        self.connected = True;
        self.context.runinitial(self);
    
    def connectionLost(self, reason):
        self.connected = False;
        self.log.msg(reason.value);
    
    def lineReceived(self, line):
        """
        Receive a line, and transform it into a frame.
        """
        self.log.msg("lineReceived:", line, logLevel=logging.DEBUG)
        
        try:
            frame = ADCParser.parseString(line);
        except Exception, e:
            import traceback
            self.log.err();
            self.transport.loseConnection();
            return;
        
        if not frame.header:
            return;
        
        if not self.context.hasmethod(self.__state, frame.header.__class__, frame.header.cmd):
            self.log.msg("unhandled: @context(context." + self.__state + ", " + str(frame.header.__class__) + ", '" + frame.header.cmd + "')", logLevel=logging.WARN);
            return;
        
        try:
            self.context.callmethod(self.__state, frame.header.__class__, frame.header.cmd, self, frame);
        except:
            self.log.err();
            self.transport.loseConnection();

class ADCContext:
    INITIAL="INITIAL";
    PROTOCOL="PROTOCOL";
    IDENTIFY="IDENTIFY";
    VERIFY="VERIFY";
    NORMAL="NORMAL";
    DATA="DATA";
    
    VALID_STATES=[PROTOCOL, IDENTIFY, VERIFY, NORMAL, DATA];
    
    def __init__(self, name):
        self.name = name;
        self.states = dict();
        self.initial = list();

    def runinitial(self, kself, *args, **kw):
        for init in self.initial:
            init(kself, *args, **kw);
        
    def addmethod(self, state, header, command, cb):
        if state not in self.VALID_STATES:
            raise ValueError("not a valid state: " + str(state));
        
        if (state, header, command) not in self.states:
            self.states[(state, header, command)] = list();
        
        self.states[(state, header, command)].append(cb);
    
    def addinitialmethod(self, cb):
        self.initial.append(cb);
    
    def hasmethod(self, state, header, command):
        if (state, header, command) in self.states:
            return True;
        
        return False;
    
    def params(self, *required_args, **required_kw):
        """
        bind the helper method params to the wrapper
        """
        
        def wrapper(f):
            def cb(self, frame):
                args = list();
                kw = dict();
                
                for i, t in enumerate(required_args):
                    rval = frame.get(i);
                    if rval is None: raise ValueError("missing required positional argument: " + str(i));
                    if type(t) == tuple: args.append(decode(rval, *t));
                    else: args.append(decode(rval, t));
                
                for k, t in required_kw.items():
                    plist = frame.get(k)

                    if isinstance(t, List):
                        kw[k] = [decode(v, t.type) for v in plist];
                    else:
                        kw[k] = [decode(v, t) for v in plist];
                        
                        if len(kw[k]) > 0:
                            kw[k] = kw[k][0];
                        else:
                            kw[k] = None;
                
                self.log.msg("entering:", f.func_name, repr(args), repr(kw), logLevel=logging.DEBUG);
                try:
                    return f(self, frame, *args, **kw);
                finally:
                    self.log.msg("exiting:", f.func_name, logLevel=logging.DEBUG);
            return cb;
        
        return wrapper;
    
    def callmethod(self, state, header, command, kself, *args, **kw):
        if not self.hasmethod(state, header, command):
            raise ValueError("not a valid method for context '" + self.name + "': " + state + " " + str(header) + " " + command);
        
        for cb in self.states[(state, header, command)]:
            cb(kself, *args, **kw);

    def __call__(self, state, header=None, command=None):
        if state == self.INITIAL:
            def initialwrapper(f):
                def cb(*args, **kw):
                    return f(*args, **kw);
                
                self.addinitialmethod(cb);
                return cb;
            
            return initialwrapper;

        if header is None or command is None:
            raise ValueError("Unless state is INITIAL, 'header' and 'command' must be set");
        
        def wrapper(f):
            def cb(*args, **kw):
                return f(*args, **kw);
        
            self.addmethod(state, header, command, cb);
        
        return wrapper;
