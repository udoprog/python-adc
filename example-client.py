from twisted.internet.protocol import Factory, ClientFactory
from twisted.internet import reactor

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

    def __init__(self):
        ADCProtocol.__init__(self);
        
        self.features = ADCFeatures();
        self.sid = None;
        self.cid = None;
        self.pid = None;
        self.hubinfo = ADCInfo(None);
        self.log = Logger();
        
        self.users = dict();
        self.users_by_sid = dict();
    
    def sendInfo(self, **kw):
        kw.update(dict(NI=encode(self.factory.nickname), SS=encode(self.factory.sharesize)));
        self.sendFrame(Message(Broadcast(cmd='INF', my_sid=encode(self.sid)), **kw));
    
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
    
    #@context(context, Context.NORMAL, 'IINF')
    #def adc_normal_iinf(self, frame):
    #    self.any_iinf(frame);
    
    @context(Context.NORMAL, Broadcast, 'INF')
    @parameters(NI=STR)
    def any_binf(self, frame, NI):
        if NI in self.users:
            nick_info = self.users[NI];
        else:
            nick_info = self.users[NI] = ADCInfo(frame.header.my_sid);
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
        
        self.log.info("Got message:", "<" + user_info["NI"] + ">", message);

def print_item(item):
    print item.sev_s, ' '.join(item.msg);

class ADCClientToHub(ClientFactory):
    protocol = ADCClientToHubProtocol
    
    def __init__(self, **kw):
        self.nickname = kw.get("nickname", "");
        self.sharesize = kw.get("sharesize", "");
    
    def connectionMade(self, proto):
        proto.log.setseverity(DEBUG);
        proto.log.setcb(DEBUG, print_item);
        print "connection made", proto;
    
    def clientConnectionLost(self, connector, reason):
        print "connection lost", connector;
        print connector;
    
    def clientConnectionFailed(self, connector, reason):
        print "connection failed", connector;

def entry():
    reactor.connectTCP("localhost", 1511, ADCClientToHub(nickname="udoprog", sharesize=1024**5));
    reactor.run();

if __name__ == "__main__":
    entry();
