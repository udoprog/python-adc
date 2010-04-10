from twisted.internet.protocol import Factory, ClientFactory
from twisted.internet import reactor

from ..protocol import ServerProtocol
from .. import entrypoint
from ..adc.twisted.client import ADCApplication, HubDescription, HubUser
from ..logger import *

import urlparse;

ADC_SCHEME="adc"
ADCS_SCHEME="adcs"

urlparse.uses_netloc.append(ADC_SCHEME)
urlparse.uses_netloc.append(ADCS_SCHEME)

class ServerFactory(Factory):
    protocol = ServerProtocol
    
    def info_log(self, item):
        print item.sev_s, ' '.join(item.msg);
    
    def __init__(self):
        self.connections = dict();
        self.app = ADCApplication();
        self.app.log.setcb(DEBUG, self.info_log);
    
    def send_global_message(self, sender, text):
        for (host, port), v in self.connections.items():
            v.send_message(host + ":" + str(port), text);
    
    def remote_global(self, conn, *text):
        self.send_global_message(conn, ' '.join(text));
        return "Sent global message"
    
    def remote_list(self, conn):
        if len(self.connections) == 0:
            return "No active connections : ("
        
        return [host + ":" + str(port) for (host, port), v in self.connections.items()];

    def remote_send(self, conn, hub_i, *text):
        for i, hub in enumerate(self.app.hubs):
            if hub_i == i:
                if not hub.connected:
                    raise ValueError("Not connected to hub");

                hub.sendMessage(' '.join([str(m.encode('utf-8')) for m in text]));
                return "Successfully Sent Message";

        raise ValueError("No such hub index: " + str(hub_i));
    
    def remote_connect(self, conn, url, username, **kw):
        up = urlparse.urlparse(url);
        
        user = HubUser(username, **kw);
        hub = HubDescription(up.hostname, int(up.port), user, scheme=up.scheme);
        self.app.addhub(hub);
    
    def remote_disconnect(self, conn, hub_i):
        for i, hub in enumerate(self.app.hubs):
            if hub_i == i:
                self.app.removehub(hub);
                return "Successfully Disconnected";
        
        raise ValueError("No such hub index: " + str(hub_i));
    
    def remote_hubs(self, conn):
        result = list();
        
        if len(self.app.hubs) == 0:
            return result;
        
        for i, hub in enumerate(self.app.hubs):
            result.append((i, hub.host, hub.port, hub.connected));
        
        return result;
    
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
