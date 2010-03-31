from twisted.internet.protocol import Factory, ClientFactory


from ..parser import ADCParser
from ..protocol import ADCProtocol, ServiceProtocol

class ADCFactory(Factory):
    protocol = ADCProtocol
    
    def __init__(self):
        pass;

class ADCClientFactory(ClientFactory):
    protocol = ADCProtocol

    def clientConnectionLost(self, connector, reason):
        pass;
    
    def clientConnectionFailed(self, connector, reason):
        pass;
    
    def startedConnecting(self, connector):
        print repr(connector);
