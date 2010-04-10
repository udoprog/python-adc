from twisted.internet.protocol import ClientFactory
from twisted.internet import reactor, defer, ssl
from OpenSSL import SSL

import uuid;

from adc.protocol import ADCProtocol

# Context
from adc.protocol.helpers import *
# contants, encode/decode functions
from adc.types import *
# Logger
from adc.logger import *

class ADCClientToHubProtocol(ADCProtocol):
    context = Context("Client to hub connection");
    
    def __init__(self, **kw):
        ADCProtocol.__init__(self);
        
        self.log = None;
        
        self.features = ADCFeatures();
        self.sid = None;
        self.cid = None;
        self.pid = None;
        self.hubinfo = ADCInfo(None);
        
        self.log = kw.get("log");
        self.user = kw.get("user");
        self.hub = kw.get("hub");
        
        self.user.signal("sharesize", self.sendInfo);
        
        self.users = dict();
        self.users_by_sid = dict();
    
    def setapp(self, app):
        self.app = app;
    
    def sendInfo(self, **kw):
        kw.update(dict(NI=encode(self.user.nick), SS=encode(self.user.get("sharesize"))));
        self.sendFrame(Message(Broadcast(cmd='INF', my_sid=encode(self.sid)), **kw));
    
    def sendMessage(self, message):
        self.sendFrame(Message(Broadcast(cmd='MSG', my_sid=encode(self.sid)), encode(message)));
    
    def connectionMade(self):
        ADCProtocol.connectionMade(self);
        self.factory.clientConnectionMade(self, self.transport);
    
    @context(Context.INITIAL)
    def do_initial(self):
        self.setstate(Context.PROTOCOL);
        sup = Message(Hub(cmd='SUP'), AD=["TIGR", "BASE", "GZIP"]);
        self.sendFrame(sup);
    
    @context(Context.PROTOCOL, Info, "SUP")
    @parameters(AD=STR, RM=STR)
    def do_isup(self, frame, AD, RM):
        for a in AD:
            if self.ishash(a) and not self.hashashmethod():
                self.sethashmethod(a);
                self.log.info("Hash method chosen:", a);
            else:
                self.features.add(a);
        
        for r in RM:
            self.features.remove(r);
        
        if not self.hashashmethod():
            self.log.error("No hash method specified, closing connection");
            self.transport.loseConnection();
        
        if self.cid:
            self.log.error("Cid already set, context is invalid");
            self.transport.loseConnection();
        
        self.pid = self.hash_method(uuid.uuid1().hex);
        self.cid = self.hash_method(self.pid);
        self.log.debug("Private id:", repr(self.pid));
    
    @context(Context.PROTOCOL, Info, 'SID')
    @parameters(STR)
    def set_sid(self, frame, sid):
        if self.sid is not None:
            self.log.error("Sid has already been set, closing connection");
            self.transport.loseConnection();
        
        self.sid = sid;
        self.setstate(Context.IDENTIFY);

    @context(Context.IDENTIFY, Info, 'STA')
    def identify_ista(self, *args, **kw):
        """
        Catch an IDENTIFY ISTA message and send it to a generic handler.
        """
        self.any_ista(*args, **kw);
    
    @context(Context.NORMAL, Info, 'STA')
    def normal_ista(self, *args, **kw):
        """
        Catch an NORMAL ISTA message and send it to generic handler.
        """
        self.any_ista(*args, **kw);
    
    @parameters(STR, STR)
    def any_ista(self, frame, code, description):
        """
        Handle ISTA message likewise from any context.
        """
        error = ADCStatus(code, description);
        
        if error.fatal():
            self.log.error("Fatal from hub:", str(error));
            self.transport.loseConnection();

        elif error.success():
            self.log.info("Status from hub:", str(error));
        
        elif error.recoverable():
            self.log.warn("Recoverable from hub:", str(error));
    
    def _update_adc_info(self, info, frame):
        for k in frame.getkeys():
            if k in ADCInfo.B32_TYPES:
                info.setitem(k, frame.getfirst(k), self.gethashsize());
            else:
                info[k] = frame.getfirst(k);
    
    @context(Context.IDENTIFY, Info, 'INF')
    def identify_iinf(self, frame):
        """
        This should be the initial INF message sent from the server.
        
        During context, perform a login, or close connection if sid has not been set yet.
        @context IDENTIFY
        """
        if self.sid is None:
            self.log.error("Sid has not been set, closing connection");
            self.transport.loseConnection();
        
        self._update_adc_info(self.hubinfo, frame);
        self.hubinfo.clean();

        self.sendInfo(ID=encode(Base32(self.cid)), PD=encode(Base32(self.pid)));
        self.setstate(Context.NORMAL);
        self.log.prefix = self.log.prefix + " " + str(self.hubinfo["VE"]) + " (" + self.user.nick + ")";
    
    #@context(context, Context.NORMAL, 'IINF')
    #def adc_normal_iinf(self, frame):
    #    self.any_iinf(frame);
    
    @context(Context.NORMAL, Broadcast, 'INF')
    @parameters(NI=STR)
    def any_binf(self, frame, NI):
        if len(NI) == 0:
            self.log.warn("Missing argument NI, got frame: " + repr(frame));
            return;
        
        NI = NI[0];
        
        if NI in self.users:
            nick_info = self.users[NI];
        else:
            nick_info = ADCInfo(frame.header.my_sid);
            self.users[NI] = nick_info;
            self.users_by_sid[nick_info.sid] = nick_info;
        
        self._update_adc_info(nick_info, frame);
        
        # check that keys are the same, even if they have been updated.
        nick_info.clean();
        self.log.debug("updated info:", NI, str(nick_info));
    
    @context(Context.NORMAL, Broadcast, 'MSG')
    @parameters(STR)
    def hub_message(self, frame, message):
        from_sid = frame.header.my_sid;
        
        if not from_sid in self.users_by_sid:
            self.log.warn("Got message from unknown user: ", message);
            return;
        
        user_info = self.users_by_sid[from_sid];
        
        self.log.info("Got message:", "<" + user_info["NI"] + ">", message.decode('utf-8'));

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

class HubDescription:
    def __init__(self, host, port, user, **kw):
        if not isinstance(host, basestring):
            raise ValueError("'host' has to be a string");
        
        if type(port) != int:
            raise ValueError("'port' has to be an int");
        
        if not isinstance(user, HubUser):
            raise ValueError("'user' is not a HubUser instance");
        
        if host == "":
            raise ValueError("host cannot be empty");
        
        if user == "":
            raise ValueError("user cannot be empty");
        
        self.reconnect = True;
        self.host = host;
        self.port = port;
        self.user = user;
        self.connected = False;
        self.client = None;
        self.scheme = kw.get("scheme", "adc")

        if self.scheme not in ["adc", "adcs"]:
            raise ValueError("scheme is invalid, should be one of 'adc' or 'adcs': " + self.scheme);

    def disconnect(self):
        if self.client:
            self.client.transport.loseConnection();
    
    def sendMessage(self, message):
        if self.client:
            self.client.sendMessage(message);

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
