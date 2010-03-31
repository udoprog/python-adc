from twisted.internet.protocol import ClientFactory
from twisted.internet import reactor

import sys
import readline

from ..protocol.remote import RemoteProtocol

from pytermcaps import TermCaps

class Printer(TermCaps):
    def notice(self, *s):
        self._writeall(self.c.bold, self.c.magenta, self._join(s), self.c.sgr0, "\n");
    
    def error(self, *s):
        self._writeall(self.c.bold, self.c.red, self._join(s), self.c.sgr0, "\n");
    
    def message(self, *s):
        self._writeall(self.c.bold, self.c.green, self._join(s), self.c.sgr0, "\n");

def parse_input(s):
    r_i = s.find(' ')
    
    if r_i == -1:
        r_i = len(s);
    
    remote = s[:r_i];
    rest = s[r_i:].strip();
    
    def pretend(*args, **kw):
        return args, kw;
    
    args, kw = eval('pretend(' + rest + ")", {'pretend': pretend});
    return remote, args, kw;

class RemoteClientFactory(ClientFactory):
    protocol = RemoteProtocol
    
    def __init__(self):
        self.printer = Printer();
    
    def input(self, conn):
        while True:
            try:
                remote, args, kw = parse_input(raw_input("#> "));
            except Exception, e:
                print str(e);
                continue;
            
            break;
        
        if remote == "exit":
            conn.transport.loseConnection();
        
        return remote, args, kw;
    
    def response(self, r):
        ok =        r['ok'];
        result =    r['result'];
        error =     r['error'];
        messages =  r['messages'];
        
        if ok:
            if isinstance(result, basestring):
                self.printer.notice(result);
            elif isinstance(result, list):
                for line in result:
                    self.printer.notice(line);
            else:
                print self.printer.notice(repr(result));
        else:
            self.printer.error(error);
        
        for message in messages:
            fr, text = message;
            self.printer.message("Got message from", fr, "-", text);
    
    def clientConnectionFailed(self, connector, reason):
        print 'connection failed:', reason.getErrorMessage()
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print 'connection lost:', reason.getErrorMessage()
        reactor.stop()

def main():
    import sys;
    if len(sys.argv) < 3:
        sys.stderr.write("Usage: adc.factory <service-host> <service-port>\n");
        sys.exit(1);
    
    host = sys.argv[1];
    
    try:
        port = int(sys.argv[2]);
    except:
        print "Bad numeric:", sys.argv[2];
        sys.exit(2);
    
    readline.parse_and_bind('tab: complete');
    reactor.connectTCP(host, port, RemoteClientFactory())
    reactor.run()

if __name__ == '__main__':
    main()
