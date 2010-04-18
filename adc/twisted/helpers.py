from ..types import encode, decode
from ..types import *

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
    B32_TYPES = ['ID', 'PD'];
    
    TYPES = {
        'ID': B32, 'PD': B32, 'I4': IP4, 'I6': IP6, 'U4': INT, 'U6': INT,
        'SS': INT, 'SF': INT, 'VE': STR, 'US': INT, 'DS': INT, 'SL': INT,
        'AS': INT, 'AM': INT, 'EM': STR, 'NI': STR, 'DE': STR, 'HN': INT,
        'HR': INT, 'HO': INT, 'TO': STR, 'CT': INT, 'AW': INT, 'SU': STR,
        'RF': STR, 'KP': STR, 'HI': STR, 'OP': STR
    };
    
    def __init__(self, sid, *args, **kw):
        self.sid = sid;
        self.dirtykeys = set();
        dict.__init__(self, *args, **kw);
    
    def __setitem__(self, k, v):
        if self.isdirty(k):
            raise ValueError("key can only be updated once before cleaned: " + k);
        
        if not self.exists(k):
            dict.__setitem__(self, k, decode(v, STR));
            return;
        
        self.dirtykeys.add(k);
        dict.__setitem__(self, k, decode(v, self.TYPES[k]));

    def setitem(self, k, v, *args):
        """
        An explicit setitem method to pass arguments to the underlying encoding procedure.
        """
        if self.isdirty(k):
            raise ValueError("key can only be updated once before cleaned: " + k);
        
        if not self.exists(k):
            dict.__setitem__(self, k, decode(v, STR));
            return;
        
        dv = decode(v, self.TYPES[k], *args);
        
        self.dirtykeys.add(k);
        dict.__setitem__(self, k, dv);
    
    def __getitem__(self, k):
        if not self.exists(k):
            raise ValueError("invalid info key: " + k);

        if not dict.__contains__(self, k):
            return None;

        return dict.__getitem__(self, k);

    def setrawitem(self, k, v):
        if not self.exists(k):
            raise ValueError("invalid info key: " + k);
        
        self.dirtykeys.add(k);
        dict.__setitem__(self, k, v);

    def getdecoded(self, k):
        return decode(self.__getitem__(k), self.TYPES[k]);
    
    def exists(self, k):
        """
        Indicates weither key is an valid INFO key or not.
        """
        return k in self.TYPES;

    def isdirty(self, k):
        """
        Indicates weither key has been recently changed/updated.
        This can be cleaned using #clean
        """
        return k in self.dirtykeys;
    
    def clean(self):
        self.dirtykeys.clear();

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

