import logging

import sys;
import time;

class Logger:
    delimiter = "\n";

    def __init__(self, klass, *prefixes):
        self.stream = sys.stdout;
        self.klass = klass.__name__;
        self.logLevel = logging.DEBUG;
        self.prefixes = prefixes;

    def setPrefixes(self, *prefixes):
        self.prefixes = prefixes;

    def setLogLevel(self, logLevel):
        self.logLevel = logLevel;

    def __encode(self, *msg):
        return ' '.join(str(s).encode("utf-8") for s in msg)

    def onMessageLine(self, s, logLevel):
        self.stream.write(s + self.delimiter);
    
    def msg(self, *msg, **kw):
        logLevel = kw.get("logLevel", logging.INFO);
        if self.logLevel <= logLevel:
            now = time.strftime("%Y-%m-%d %H:%M:%S%z")
            self.onMessageLine(self.__encode(now, "[" + self.klass + "]", "[" + self.__encode(*self.prefixes) + "]", self.__encode(*msg)), logLevel);
    
    def err(self, *msg):
        import traceback;
        import sys

        exc_type, exc_value, exc_traceback = sys.exc_info()

        for file, line, func, method in traceback.extract_tb(exc_traceback):
           self.msg(*["  ", file, "line", line, "in", func], logLevel=logging.ERROR);
           self.msg(*["    ", method], logLevel=logging.ERROR);
        
        self.msg(*[exc_type.__name__ + ":", exc_value], logLevel=logging.ERROR);

        #for line in traceback.format_stack(exc_traceback):
        #    for l in line.split("\n"):
