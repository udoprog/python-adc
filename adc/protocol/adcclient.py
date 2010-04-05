from twisted.protocols.basic import LineReceiver

from ..parser import ADCParser, Message

class ADCBaseProtocol(LineReceiver):
    delimiter = '\n';

    FROM_HUB="F"
    TO_HUB="T"
    CLIENT_CLIENT_TCP="C"
    CLIENT_CLIENT_UDP="U"
    
    PROTOCOL="PROTOCOL";
    IDENTIFY="IDENTIFY";
    VERIFY="VERIFY";
    NORMAL="NORMAL";
    DATA="DATA";
    
    def connectionMade(self):
        self.factory.connect(self);
    
    def connectionLost(self):
        self.factory.disconnect(self);
    
    def lineReceived(self, line):
        try:
            m = ADCParser.parseString(line);
        except:
            self.transport.loseConnection();
        
        method = m.header.type + m.header.command_name + "_" + self.stage;

        if not hasattr(self.factory, method):
            # not supported
            self.transport.loseConnection();
        
        getattr(self.factory, method)(self, m);

class ADCHubToLocalProtocol(LineReceiver):
    def __init__(self):
        self.context = self.FROM_HUB;
        self.state = self.PROTOCOL;

class ADCLocalToHubProtocol(LineReceiver):
    def __init__(self):
        self.context = self.TO_HUB;
        self.state = self.PROTOCOL;

class ADCLocalToClientProtocol(LineReceiver):
    def __init__(self):
        self.context = self.CLIENT_TO_CLIENT_TCP;
        self.state = self.PROTOCOL;

class ADCClientToLocalProtocol(LineReceiver):
    def __init__(self):
        self.context = self.CLIENT_TO_CLIENT_TCP;
        self.state = self.PROTOCOL;
