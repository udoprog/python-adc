from .protocol import ADCProtocol, ADCContext
from .helpers import ADCStatus
from ..types import *
from ..types import encode, decode
from ..message import *
from ..hashing import TigerHash

from twisted.python import log

import logging
import uuid

class HubUser(object):
  TYPES = {
    'NI': ('nick', "twisteduser", STR),
    'SS': ('sharesize', 0, INT),
    'I4': ('ip4', None, IP4),
    'I6': ('ip6', None, IP4),
  };

  def __init__(self, **kw):
    self.sid = kw.pop("sid", None);
    self.update(**kw);
  
  def update(self, **kw):
    for k, v in self.TYPES.items():
      attr, default, t = v;
      
      if k in kw:
        setattr(self, attr, decode(kw[k], t));
      elif not hasattr(self, attr):
        setattr(self, attr, default);

class HubDescriptor:
    def __init__(self, protocol):
        self.protocol = protocol;
        self.connected = True;
        self.__name = None;
        self.__version = None;
        self.__sid = None;
        self.__peer = None;

    def setName(self, name):
        self.__name = name;

    def getName(self):
        return self.__name;

    def setVersion(self, version):
        self.__version = version;

    def getVersion(self):
        return self.__version;

    def setSid(self, sid):
        self.__sid = sid;

    def getSid(self):
        return self.__sid;

    def setPeer(self, peer):
        self.__peer = peer;

    def getPeer(self):
        return self.__peer;
    
    name = property(getName, setName);
    version = property(getVersion, setVersion);
    sid = property(getSid, setSid);
    peer = property(getPeer, setPeer);
    
    def disconnect(self):
        if self.connected:
            self.protocol.transport.loseConnection();
            self.connected = False;
    
    def sendMessage(self, message):
        if self.connected:
            self.protocol.sendMessage(message);
        else:
            log.msg("Cannot send message to hub, not connected");
    
    def __str__(self):
        if not self.__name:
            return "no hub";
        else:
            return self.__name + ":" + self.__version;

class ADCHubProtocol(ADCProtocol):
    """
    This defines a low level client to hub connection which can be use to define high level clients on top of.
    """
    context = ADCContext("Hub Connection");
    
    supported_features = set(["BASE", "ZLIB", "TIGR"]);
    
    signals = set([
      "hub-identified",
      "get-user",
      "user-info",
      "user-quit",
      "direct-connect",
      "status",
      "message",
      "connection-made",
      "connection-lost",
    ]);
    
    def __init__(self, **kw):
      ADCProtocol.__init__(self, **kw);
      
      self.log.setPrefixes("n/a");
      self.hub = HubDescriptor(self);
      self.hashes = {'TIGR': TigerHash};
      self.hashing = None;
      self.features = set();

      self.pid = None;
      self.cid = None;
      self.peer = None;
      
      self.__users = list();
      self.__users_by_sid = dict();
    
    def sendLogin(self, user):
      if user is None:
        self.log("user is None", logLevel=logging.ERROR);
        self.transport.loseConnection();
        return;

      if not self.hub.sid:
        self.log("Sid is not set", logLevel=logging.ERROR);
        self.transport.loseConnection();
        return;
      
      kw = {
        'NI': encode(user.nick),
        'SS': encode(user.sharesize),
        'ID': encode(Base32(self.cid)),
        'PD': encode(Base32(self.pid)),
      };
      
      self.sendFrame(Message(Broadcast(cmd='INF', my_sid=encode(self.hub.sid)), **kw));

    def connectionMade(self):
      ADCProtocol.connectionMade(self);
      self.emit("connection-made");

    def connectionLost(self, reason):
      ADCProtocol.connectionLost(self, reason);
      self.emit("connection-lost", reason);
    
    def sendMessage(self, msg):
      if self.connected:
        self.sendFrame(Message(Broadcast(cmd='MSG', my_sid=encode(self.hub.sid)), encode(msg)));
    
    @context(context.INITIAL)
    def do_initial(self):
        self.setState(self.context.PROTOCOL);
        self.sendFrame(Message(Hub(cmd='SUP'), AD=self.hashes.keys() + ["BASE"]));
        p = self.transport.getPeer();
        self.log.setPrefixes(p.host+ ":" + str(p.port));

    @context(context.PROTOCOL, Info, 'SUP')
    @context.params(AD=List(STR), RM=List(STR))
    def do_protocol_features(self, frame, AD=[], RM=[]):
        """
        Initial SUP negotiation, the hub informs the client which of the announced features should be used.
        """
        # features to add
        for feature in AD:
            if feature not in self.supported_features:
                log.msg("feature not supported:", feature);
                continue;
            
            if feature in self.hashes.keys():
                self.hashing = self.hashes[feature]();
            else:
                self.features.add(feature);
        
        # features to remove
        for feature in RM:
            self.features.remove(feature);

    @context(context.PROTOCOL, Info, 'SID')
    @context.params(STR)
    def get_session_id(self, frame, sid):
        self.hub.sid = sid;
        
        self.pid = self.hashing.digest(uuid.uuid1().hex);
        self.cid = self.hashing.digest(self.pid);
        log.msg("Private id: " + repr(self.pid), );
        
        self.sendLogin(self.emit("get-user"));
        self.setState(self.context.IDENTIFY);

    @context(context.IDENTIFY, Info, 'INF')
    @context.params(CT=INT, VE=STR, NI=STR, DE=STR)
    def identify_hub(self, frame, CT, VE, NI, DE):
        self.hub.name = NI;
        self.hub.version = VE;
        
        self.peer = self.transport.getPeer();
        
        self.log.setPrefixes(self.peer.host + ":" + str(self.peer.port), self.hub.version);
        
        self.emit("hub-identified", self.hub);
        self.setState(self.context.NORMAL);
    
    @context(context.NORMAL, Info, 'STA')
    @context.params(STR, STR)
    def identify_hub(self, frame, code, message):
        self.emit("status", ADCStatus(code, message));
    
    @context(context.NORMAL, Broadcast, 'INF')
    @context.params(ID=STR, NI=STR, HN=INT, SS=INT, I4=IP4, I6=IP6)
    def identify_user(self, frame, **kw):
        sid = frame.header.my_sid;
        
        if sid in self.__users_by_sid:
          user = self.__users_by_sid[sid];
          user.update(**kw);
        else:
          user = HubUser(sid=sid, **kw)
          self.__users.append(user);
          self.__users_by_sid[user.sid] = user;
        
        self.emit("user-info", user);
    
    @context(context.NORMAL, Broadcast, 'MSG')
    @context.params(STR)
    def hub_message(self, frame, message):
      sid = frame.header.my_sid

      if sid not in self.__users_by_sid:
        self.log.msg("no such user sid: " + sid);
        return;
      
      self.emit("message", self.__users_by_sid[sid], message);

    @context(context.NORMAL, Info, 'QUI')
    @context.params(STR)
    def user_quit(self, frame, sid):
      if sid not in self.__users_by_sid:
        self.log.msg("no such user sid: " + sid);
        return;
      
      user = self.__users_by_sid[sid];
      
      self.emit("user-quit", user);
      self.__users.remove(user)
      self.__users_by_sid.pop(sid);

    @context(context.NORMAL, Direct, 'CTM')
    def user_ctm(self, frame):
      msid = frame.header.my_sid
      tsid = frame.header.target_sid
      
      if not msid in self.__users_by_sid:
        self.log.msg("no such user sid: " + tsid);
        return;

      print frame.header
      
      # the user to connect to
      user = self.__users_by_sid[msid];
      
      self.emit("direct-connect", user);

        #BINF AAAB ID7CE3GLXRIH46VRI3CQESXUAKRVXKXCIF76ODN2A NIudodev SL2 SS0 SF0 HR0 HO0 VEUC\sV:0.83 SUTCP4,UDP4,ADC0,KEY0 US65536 U49086 KPSHA256/3H3DKERANVIDMWRXHDZCCVOEKBSM3LN3UXNPCBWAJK5GMH2IQZLA I4127.0.0.1 HN2
    
#    def sendInfo(self, **kw):
#        kw.update(dict(NI=encode(self.user.nick), SS=encode(self.user.get("sharesize"))));
#        self.sendFrame(Message(Broadcast(cmd='INF', my_sid=encode(self.sid)), **kw));
#    
#    def sendMessage(self, message):
#        self.sendFrame(Message(Broadcast(cmd='MSG', my_sid=encode(self.sid)), encode(message)));
#    
#    
#    @context(Context.PROTOCOL, Info, "SUP")
#    @parameters(AD=STR, RM=STR)
#    def do_isup(self, frame, AD, RM):
#        for a in AD:
#            if a in self.hashes:
#                self.hash = self.hashes[a]();
#                log.msg("Hash method updated: " + a);
#            else:
#                self.features.add(a);
#        
#        for r in RM:
#            self.features.remove(r);
#        
#        if not self.hash:
#            log.err("No hash method specified, closing connection");
#            self.transport.loseConnection();
#        
#        if self.cid:
#            log.err("Cid already set, context is invalid");
#            self.transport.loseConnection();
#        
#        self.pid = self.hash.digest(uuid.uuid1().hex);
#        self.cid = self.hash.digest(self.pid);
#        log.msg("Private id: " + repr(self.pid), );
#    
#    @context(Context.PROTOCOL, Info, 'SID')
#    @parameters(STR)
#    def set_sid(self, frame, sid):
#        if self.sid is not None:
#            log.err("Sid has already been set, closing connection");
#            self.transport.loseConnection();
#        
#        self.sid = sid;
#        self.setstate(Context.IDENTIFY);
#
#    @context(Context.IDENTIFY, Info, 'STA')
#    def identify_ista(self, *args, **kw):
#        """
#        Catch an IDENTIFY ISTA message and send it to a generic handler.
#        """
#        self.any_ista(*args, **kw);
#    
#    @context(Context.NORMAL, Info, 'STA')
#    def normal_ista(self, *args, **kw):
#        """
#        Catch an NORMAL ISTA message and send it to generic handler.
#        """
#        self.any_ista(*args, **kw);
#    
#    @parameters(STR, STR)
#    def any_ista(self, frame, code, description):
#        """
#        Handle ISTA message likewise from any context.
#        """
#        error = ADCStatus(code, description);
#        
#        if error.fatal():
#            log.err("Fatal from hub: " + str(error));
#            self.transport.loseConnection();
#        
#        elif error.success():
#            log.msg("Status from hub: " + str(error));
#        
#        elif error.recoverable():
#            log.msg("Recoverable from hub: " + str(error));
#    
#    def _update_adc_info(self, info, frame):
#        for k in frame.getkeys():
#            if k in ADCInfo.B32_TYPES:
#                info.setitem(k, frame.getfirst(k), self.hash.size);
#            else:
#                info[k] = frame.getfirst(k);
#    
#    @context(Context.IDENTIFY, Info, 'INF')
#    def identify_iinf(self, frame):
#        """
#        This should be the initial INF message sent from the server.
#        
#        During context, perform a login, or close connection if sid has not been set yet.
#        @context IDENTIFY
#        """
#        if self.sid is None:
#            log.err("Sid has not been set, closing connection");
#            self.transport.loseConnection();
#        
#        self._update_adc_info(self.hubinfo, frame);
#        self.hubinfo.clean();
#
#        self.sendInfo(ID=encode(Base32(self.cid)), PD=encode(Base32(self.pid)));
#        self.setstate(Context.NORMAL);
#    
#    #@context(context, Context.NORMAL, 'IINF')
#    #def adc_normal_iinf(self, frame):
#    #    self.any_iinf(frame);
#    
#    @context(Context.NORMAL, Broadcast, 'INF')
#    @parameters(NI=STR)
#    def any_binf(self, frame, NI):
#        if len(NI) == 0:
#            log.msg("Missing argument NI, got frame: " + repr(frame));
#            return;
#        
#        NI = NI[0];
#        
#        if NI in self.users:
#            nick_info = self.users[NI];
#        else:
#            nick_info = ADCInfo(frame.header.my_sid);
#            self.users[NI] = nick_info;
#            self.users_by_sid[nick_info.sid] = nick_info;
#        
#        self._update_adc_info(nick_info, frame);
#        
#        # check that keys are the same, even if they have been updated.
#        nick_info.clean();
#        log.msg("updated info: " + NI + " " + str(nick_info));
#    
#    @context(Context.NORMAL, Broadcast, 'MSG')
#    @parameters(STR)
#    def hub_message(self, frame, message):
#        from_sid = frame.header.my_sid;
#        
#        if not from_sid in self.users_by_sid:
#            log.msg("Got message from unknown user: " + message);
#            return;
#        
#        user_info = self.users_by_sid[from_sid];
#        
#        log.msg("Got message: <" + user_info["NI"] + ">", message.decode('utf-8'));
