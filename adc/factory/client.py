from twisted.internet.protocol import ClientFactory
from twisted.internet import reactor

import sys
import readline

from ..protocol import ClientProtocol
from ..printer import Printer
from .. import entrypoint

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
    protocol = ClientProtocol
    
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

def main(app, argv):
    if len(argv) < 2:
        app.err.println("Usage: adc.factory <service-host> <service-port>");
        return 1;
    
    host = argv[0];
    
    try:
        port = int(argv[1]);
    except:
        app.err.println("Bad numeric:", argv[1]);
        return 2;
    
    readline.parse_and_bind('tab: complete');
    reactor.connectTCP(host, port, RemoteClientFactory())
    reactor.run()

def entry():
    entrypoint.method = main;
    entrypoint.run();

if __name__ == '__main__':
    entry();
