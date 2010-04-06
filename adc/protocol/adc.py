from twisted.protocols.basic import LineReceiver
from ..parser import ADCParser
from ..parser import Message, CIHHeader, BHeader, CHeader, IHeader, HHeader, FHeader
from ..types import *
from ..types import encode, decode
from .logger import Logger

class ADCStatus:
    MESSAGES = {
        '00': "Generic",
        '10': "Generic hub error",
        '11': "Hub full",
        '12': "Hub disabled",
        '20': "Generic login/access error",
        '21': "Nick invalid",
        '22': "Nick taken",
        '23': "Invalid password",
        '24': "CID taken",
        '25': "Access denied, flag \"FC\" is the FOURCC of the offending command. Sent when a user is not allowed to execute a particular command",
        '26': "Registered users only",
        '27': "Invalid PID supplied",
        '30': "Kicks/bans/disconnects generic",
        '31': "Permanently banned",
        '32': "Temporarily banned",
        '40': "Protocol error",
        '41': "Transfer protocol unsupported",
        '42': "Direct connection failed",
        '43': "Required INF field missing/bad",
        '44': "Invalid state",
        '45': "Required feature missing",
        '46': "Invalid IP supplied in INF",
        '47': "No hash support overlap in SUP between client and hub",
        '50': "Client-client / file transfer error",
        '51': "File not available",
        '52': "File part not available",
        '53': "Slots full",
        '54': "No hash support overlap in SUP between clients",
    };

    SUCCESS = 0;
    RECOVERABLE = 1;
    FATAL = 2;
    
    def __init__(self, code, description):
        sev, code = code[0], code[1:];

        if code not in self.MESSAGES:
            raise ValueError("Invalid code: " + code);
        
        self.sev = int(sev);
        self.code = code;
        self.formal = self.MESSAGES.get(code);
        self.description = description;
    
    def success(self):
        return self.sev == self.SUCCESS;
    
    def recoverable(self):
        return self.sev == self.RECOVERABLE;
    
    def fatal(self):
        return not self.success() and not self.recoverable();

    def __str__(self):
        return "[" + self.code + "](" + self.formal + ") " + self.description;

class ADCInfo(dict):
    TYPES = {
        'ID': B32, 'PD': B32, 'I4': IP4, 'I6': IP6, 'U4': INT, 'U6': INT,
        'SS': INT, 'SF': INT, 'VE': STR, 'US': INT, 'DS': INT, 'SL': INT,
        'AS': INT, 'AM': INT, 'EM': STR, 'NI': STR, 'DE': STR, 'HN': INT,
        'HR': INT, 'HO': INT, 'TO': STR, 'CT': INT, 'AW': INT, 'SU': STR,
        'RF': STR,
    };

    def __setitem__(self, k, v):
        if not self.exists(k):
            raise ValueError("invalid info key: " + k);
        dict.__setitem__(self, k, decode(v, self.TYPES[k]));

    def __getitem__(self, k):
        if self.exists(k):
            raise ValueError("invalid info key: " + k);

        if not dict.__hasitem__(self, k):
            return None;

        return dict.__getitem__(self, k);

    def getdecoded(self, k):
        return decode(self.__getitem__(k), self.TYPES[k]);
    
    
    def exists(self, k):
        return k in self.TYPES;

class ADCFeatures(set):
    FEATURES = [
        "TIGR",
        "BASE",
        "GZIP",
        "PING"
    ];
    
    def __contains__(self, k):
        if not self.exists(k):
            raise ValueError("invalid feature: " + k);
        return set.__contains__(self, k);

    def __getitem__(self, k):
        return self.__contains__(k);
    
    def __setitem__(self, k, v):
        if v: self.add(k);
        else: self.remove(k);
    
    def exists(self, k):
        return k in self.FEATURES;
    
    def add(self, k):
        if not self.exists(k):
            raise ValueError("invalid feature: " + k);
        return set.add(self, k);
    
    def remove(self, k):
        if not self.exists(k):
            raise ValueError("invalid feature: " + k);
        return set.remove(self, k);

def parameters(*required_args, **required_kw):
    def wrapper(f):
        def cb(self, frame):
            args = list();
            kw = dict();
            
            for i, t in enumerate(required_args):
                if type(t) == tuple:
                    args.append(decode(frame.get(i), *t));
                else:
                    args.append(decode(frame.get(i), t));
            
            for k, t in required_kw.items():
                kw[k] = [decode(v, t) for v in frame.get(k)];
            
            self.log.debug("entering:", f.func_name, repr(args), repr(kw));
            return f(self, frame, *args, **kw);
        return cb;
    
    return wrapper;

class ADCProtocol(LineReceiver):
    delimiter = '\n'
    
    PROTOCOL="PROTOCOL";
    IDENTIFY="IDENTIFY";
    VERIFY="VERIFY";
    NORMAL="NORMAL";
    DATA="DATA";
    
    def __init__(self):
        self.__state = self.PROTOCOL;
        
        self.messagebuffer = 1000;
        self.messages = list();
        self.features = ADCFeatures();
        self.sid = None;
        self.info = ADCInfo();
        self.log = Logger();
    
    def addmessage(self, message):
        self.messages.append(message);
        
        if len(self.messages) > self.messagebuffer:
            self.messages.pop(0);
    
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
        self.factory.connectionMade(self);
        
        #self.sendFrame(Message(FHeader(cmd='SUP', features={'+': ["TIGR", "BASE", "CUST"]})));
        sup = Message(HHeader(cmd='SUP'), AD=["TIGR", "BASE", "GZIP"]);
        self.sendFrame(sup);
    
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
        
        mname = "adc_" + self.__state + "_" + frame.header.type + frame.header.cmd;
        
        method = getattr(self, mname, None);
        
        if method is None:
            self.log.warn("no such method:", mname);
            return;
        
        try:
            method(frame);
        except Exception, e:
            import sys;
            import traceback;
            self.log.error("exception while handling method:", traceback.format_exc(e));
            self.transport.loseConnection();

    @parameters(AD=STR, RM=STR)
    def adc_PROTOCOL_ISUP(self, frame, AD, RM):
        for a in AD:
            self.features.add(a);
        
        for r in RM:
            self.features.remove(r);
    
    @parameters(STR)
    def adc_PROTOCOL_ISID(self, frame, sid):
        if self.sid is not None:
            self.log.error("Sid has already been set, closing connection");
            self.transport.loseConnection();
        
        self.sid = sid;
        self.setstate(self.IDENTIFY);

    @parameters(STR, STR)
    def adc_IDENTIFY_ISTA(self, frame, code, description):
        error = ADCStatus(code, description);
        
        if error.fatal():
            self.log.error("Fatal from hub:", str(error));
            self.transport.loseConnection();

        elif error.success():
            self.log.info("Status from hub:", str(error));
        
        elif error.recoverable():
            self.log.warn("Recoverable from hub:", str(error));
        
        self.addmessage(description);
    
    def adc_IDENTIFY_IINF(self, frame):
        self.UPDATE_IINF(frame);
        
        if self.sid is None:
            self.log.error("Sid has not been set, closing connection");
            self.transport.loseConnection();
        
        self.sendFrame(Message(BHeader(cmd='INF', my_sid=encode(self.sid)), PD=["TEST"], CD=["TEST"]));
    
    def adc_NORMAL_IINF(self, frame):
        self.UPDATE_IINF(frame);

    def UPDATE_IINF(self, frame):
        for k in frame.parameterKeys():
            self.info[k] = frame.getfirst(k);
        
        self.log.debug("updated info:", repr(self.info));
