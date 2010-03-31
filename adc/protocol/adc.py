from twisted.protocols.basic import LineReceiver
from ..parser import ADCParser
from ..parser import Message, CIHHeader

class ADCProtocol(LineReceiver):
    delimiter = '\n'
    PROTOCOL, IDENTIFY, VERIFY, NORMAL, DATA = range(5);
    
    def __init__(self):
        self.state = self.PROTOCOL;

class ADCClientToLocal(ADCProtocol):
    def connectionMade(self):
        """
        This is the entry for client-client connections.
        """
        features = list();

        features.append("ADBASE");
        features.append("ADTIGR");
        
        sup = Message(
            CIHHeader(type='H', command_name='SUP'),
            *features
        );
        
        self.transport.write(str(sup) + "\n") 
        self.transport.loseConnection();
    
    def lineReceived(self, line):
        ADCParser.parseString(line);
        
        try:
            print repr(ADCParser.parseString(line));
        except Exception, e:
            print "invalid frame:", str(e)
    
    def connectionLost(self, c):
        print "connection lost", c

class ADCLocalToClient(ADCProtocol):
    pass;

class ADCClientToHub(ADCProtocol):
    def connectionMade(self):
        """
        This is the entry for client-client connections.
        """
        features = list();

        features.append("ADBASE");
        features.append("ADTIGR");
        
        sup = Message(
            CIHHeader(type='H', command_name='SUP'),
            *features
        );
        
        self.transport.write(str(sup) + "\n") 
        self.transport.loseConnection();
    
    def lineReceived(self, line):
        ADCParser.parseString(line);
        
        try:
            print repr(ADCParser.parseString(line));
        except Exception, e:
            print "invalid frame:", str(e)
    
    def connectionLost(self, c):
        print "connection lost", c

class ADCHubToClient(LineReceiver):
    pass
