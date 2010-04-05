from twisted.internet.protocol import Factory, ClientFactory
from twisted.internet import reactor

from ..protocol import ServerProtocol
from .. import entrypoint

class ServerFactory(Factory):
    protocol = ServerProtocol
    
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
    
def main(self, argv):
    if len(argv) < 1:
        self.out.println("Usage: adc-server <service-port>");
        return 1;

    try:
        port = int(argv[0]);
    except:
        self.err.println("Bad numeric:", argv[0]);
        return 2;
    
    self.out.println("Starting to listen on tcp port:", port);
    
    try:
        reactor.listenTCP(port, ServerFactory())
        reactor.run()
    except Exception, e:
        self.err.println("Exception Caught:", str(e));
    
    self.out.println("Stopped listening on tcp port:", port);

def entry():
    entrypoint.method = main;
    entrypoint.run();

if __name__ == "__main__":
    entry();
