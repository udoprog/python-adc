from twisted.protocols.basic import LineReceiver

from ..parser import ADCParser
from ..hashing import ishash, gethash

from .helpers import *

class ADCProtocol(LineReceiver):
    delimiter = '\n'
    
    def __init__(self):
        if self.context is None:
            raise ValueError("you must static field 'context' must be set");
        
        self.__state = None;
        
        # related to hash method
        self.hash_name = None;
        self.hash_method = None;
        self.hash_size = 0;
    
    def setstate(self, state):
        self.__state = state;

    def sendFrame(self, frame):
        sf = str(frame);
        self.log.debug("(cli):", sf);
        self.sendLine(sf);
    
    def connectionMade(self):
        """
        This is the entry for client-client connections.
        """
        if not hasattr(self.factory, 'connectionMade'):
            raise Exception("Factory must have 'connectionMade' method defined");
        
        self.factory.connectionMade(self);
        self.context.runinitial(self);
    
    def connectionLost(self, reason):
        self.log.info("lost connection:", str(reason));
    
    def lineReceived(self, line):
        self.log.debug("(hub):", line);
        
        try:
            frame = ADCParser.parseString(line);
        except Exception, e:
            import traceback
            self.log.error("invalid frame, losing connection:", traceback.format_exc(e));
            self.transport.loseConnection();
            return;
        
        self.frameReceived(frame);
            
    def frameReceived(self, frame):
        if not frame.header:
            return;
        
        if not self.context.hasmethod(self.__state, frame.header.__class__, frame.header.cmd):
            self.log.warn("No such method (not defined by @context):", self.__state,
                repr(frame.header),
                frame.header.cmd);
            return;
        
        try:
            self.context.callmethod(self.__state, frame.header.__class__, frame.header.cmd, self, frame);
        except Exception, e:
            import sys;
            import traceback;
            self.log.error("exception while handling method:", traceback.format_exc(e));
            self.transport.loseConnection();

    def ishash(self, k):
        return ishash(k);

    def hashashmethod(self):
        return self.hash_method is not None;

    def gethashsize(self):
        return self.hash_size;
    
    def gethashname(self):
        return self.hash_name;
    
    def sethashmethod(self, a):
        self.hash_method, self.hash_size = gethash(a);
        self.hash_name = a;
