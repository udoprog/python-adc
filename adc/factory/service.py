from twisted.internet.protocol import Factory, ClientFactory
from twisted.internet import reactor

from ..protocol import ServiceProtocol

class ServiceFactory(Factory):
    protocol = ServiceProtocol
    
    def __init__(self):
        self.connections = dict();

    def send_global_message(self, sender, text):
        for (host, port), v in self.connections.items():
            v.send_message(host + ":" + str(port), text);
    
    def remote_global(self, conn, *text):
        self.send_global_message(conn, ' '.join(text));
        return "Sent global message"
    
    def remote_connect(self, conn, host, port=6697):
        return "Connected to: " + host + ":" + str(port);
    
    def remote_list(self, conn):
        if len(self.connections) == 0:
            return "No active connections : ("
        
        return [host + ":" + str(port) for (host, port), v in self.connections.items()];

    def remote_send(self, conn, host, port, *text):
        peer = (host, port)
        
        if peer in self.connections:
            fr_peer = conn.transport.getPeer();
            self.connections[peer].send_message(fr_peer.host + ":" + str(fr_peer.port), ' '.join(text));
            return "send message to peer: " + host + ":" + str(port);
        else:
            return "could not find peer: " + host + ":" + str(port);
    
def main():
    import sys;
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: adc.factory <service-port>\n");
        sys.exit(1);

    try:
        port = int(sys.argv[1]);
    except:
        print "Bad numeric:", sys.argv[1];
        sys.exit(2);
    
    print "Starting to listen on tcp port:", port
    
    try:
        reactor.listenTCP(port, ServiceFactory())
        reactor.run()
    except Exception, e:
        print "Exception Caught:", str(e);
    
    print "Stopped listening on tcp port:", port

if __name__ == "__main__":
    main();
