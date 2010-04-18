from twisted.internet.protocol import ClientFactory
from twisted.internet import reactor, defer, ssl
from OpenSSL import SSL

import uuid;

from adc.protocol import ADCProtocol, ADCContext

# Context
from adc.protocol.helpers import *
# contants, encode/decode functions
from adc.types import *
# Logger
from adc.logger import *

import adc.hashing as hashing;


class ADCClientToHub(ClientFactory):
    protocol = ADCClientToHubProtocol
    
    def __init__(self, hub, deferreds, log):
        self.hub = hub;
        self.log = log;
        self.connect, self.disconnect = deferreds;
    
    def clientConnectionMade(self, client, transport):
        self.hub.client = client;
        self.connect.callback((self.hub, client, transport));
    
    def clientConnectionLost(self, transport, reason):
        self.hub.client = None;
        self.disconnect.callback((self.hub, transport, reason));
    
    def clientConnectionFailed(self, transport, reason):
        self.hub.client = None;
        self.connect.errback((self.hub, transport, reason));
    
    def buildProtocol(self, addr):
        p = ADCClientToHubProtocol(log=self.log.prefixLog(self.hub.host + ":" + str(self.hub.port)), user=self.hub.user, hub=self.hub);
        p.factory = self;
        return p;

class HubUser:
    def __init__(self, nick, **kw):
        self.nick = nick;
        self.sharesize = kw.get("sharesize", 0);
        self.kw = kw;
        
        self._signals = dict();
    
    def get(self, key):
        return self.kw.get(key, None);
    
    def signal(self, key, cb):
        self._signals[key] = cb;
    
    def update(self, key, value):
        if key in self.kw:
            self.kw[key] = value;
        
        if key in self._signals:
            self._signals[key](self);

class ADCApplication:
    def __init__(self, **kw):
        self.statusinterval = kw.get("statusinterval", 10);
        self.reconnectinterval = kw.get("reconnectinterval", 10);
        
        """
        List of client-to-client connections.
        """
        self.ctoc = list();
        
        """
        List of client-to-hub connections.
        """
        self.hubs = list();

        self.log = Logger();
        
    def addhub(self, hub):
        self.hubs.append(hub);
        self.connecthub(hub);
    
    def removehub(self, hub):
        if hub in self.hubs:
            hub.reconnect = False;
            hub.disconnect();
        else:
            pass;
    
    def connecthub(self, hub):
        hubc = defer.Deferred();
        hubc.addCallback(self.hubConnectionMade);
        hubc.addErrback(self.hubConnectionFailed);
        
        hubd = defer.Deferred();
        hubd.addCallback(self.hubConnectionLost);
        hubd.addErrback(self.hubConnectionFailed);
        
        if hub.scheme == "adc":
            reactor.connectTCP(hub.host, hub.port, ADCClientToHub(hub, (hubc, hubd), self.log));
        elif hub.scheme == "adcs":
            ctx = ssl.ClientContextFactory();
            ctx.method = SSL.TLSv1_METHOD;
            reactor.connectSSL(hub.host, hub.port, ADCClientToHub(hub, (hubc, hubd), self.log), ctx);
    
    def hubConnectionMade(self, value):
        hub, proto, transport = value;
        hub.connected = True;
        self.log.info("hub connection made:", hub.host + ":" + str(hub.port));
    
    def hubConnectionLost(self, value):
        hub, transport, reason = value;
        hub.connected = False;
        
        self.log.info("hub connection lost:", hub.host + ":" + str(hub.port));
        
        if hub.reconnect:
            reactor.callLater(self.reconnectinterval, self.connecthub, (hub));
        else:
            self.hubs.remove(hub);
    
    def hubConnectionFailed(self, error):
        hub, transport, reason = error.value;
        
        self.log.info("hub connection failed:", hub.host + ":" + str(hub.port));
        
        if hub.reconnect:
            reactor.callLater(self.reconnectinterval, self.connecthub, (hub));
        else:
            self.hubs.remove(hub);

def entry():
    app = ADCApplication();
    hub = HubDescription("localhost", 1511, HubUser("udoprog2", sharesize=1024**4));
    app.addhub(hub);
    reactor.run();

if __name__ == "__main__":
    entry();
