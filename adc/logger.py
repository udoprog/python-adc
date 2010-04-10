import datetime;
import collections;

logitem = collections.namedtuple('logitem', 'time sev sev_s msg');

DEBUG=8;
INFO=6;
WARN=4;
ERROR=2;
NONE=0;

SEV_NAMES = {
    DEBUG: "DEBUG",
    INFO: "INFO",
    WARN: "WARN",
    ERROR: "ERROR",
    NONE: "NONE",
};

class ChildLogger:
    """
    A Childlogger is a reference copy to a specific logger, but has a specific prefix added to the list of messages.
    """
    def __init__(self, prefix, parent):
        self.prefix = prefix;
        self.parent = parent;
    
    def setseverity(self, sev):
        self.parent.setseverity(sev);
    
    def setcb(self, sev, cb):
        self.parent.setcb(sev, cb);
    
    def info(self, *m):
        m = [self.prefix] + list(m);
        self.parent.info(*m);
    
    def debug(self, *m):
        m = [self.prefix] + list(m);
        self.parent.debug(*m);
    
    def warn(self, *m):
        m = [self.prefix] + list(m);
        self.parent.warn(*m);
    
    def error(self, *m):
        m = [self.prefix] + list(m);
        self.parent.error(*m);

class Logger:
    def __init__(self, limit=1000, sev=INFO, prefix=None):
        self.sev = INFO;
        self.limit = limit;
        self.messages = list();
        self.callbacks = dict();
        self.prefix = prefix;
    
    def setseverity(self, sev):
        if sev not in SEV_NAMES:
            raise ValueError("Not a valid severity: " + str(sev));
        self.sev = sev;
    
    def __addmessage(self, sev, *m):
        if sev not in SEV_NAMES:
            return;

        if self.sev < sev:
            return;
        
        self.messages.append(logitem(datetime.datetime.now(), sev, SEV_NAMES[sev], m));
        
        if len(self.messages) > self.limit:
            self.messages.pop(0);
        
        for cb_sev, cb in self.callbacks.items():
            if sev <= cb_sev:
                cb(self.messages[-1]);
    
    def lastm(self, count=1):
        return self.messages[-count];
    
    def info(self, *m):
        self.__addmessage(INFO, *m);
    
    def debug(self, *m):
        self.__addmessage(DEBUG, *m);
    
    def warn(self, *m):
        self.__addmessage(WARN, *m);

    def error(self, *m):
        self.__addmessage(ERROR, *m);
    
    def setcb(self, sev, cb):
        self.callbacks[sev] = cb;
    
    def prefixLog(self, prefix):
        return ChildLogger(prefix, self);

__all__ = ['DEBUG', 'INFO', 'WARN', 'ERROR', 'NONE', 'Logger'];
