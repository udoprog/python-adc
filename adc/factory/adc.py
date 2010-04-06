from twisted.internet.protocol import Factory, ClientFactory
from twisted.internet import reactor

from ..parser import ADCParser
from ..protocol import ADCProtocol
from ..parser import Message, CIHHeader
from ..types import *
from ..protocol.logger import *

class ADCFactory(Factory):
    protocol = ADCProtocol
    
    def __init__(self):
        pass;

def print_item(item):
    print item.sev_s, ' '.join(item.msg);

class ADCClientToHub(ClientFactory):
    protocol = ADCProtocol
    
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
    reactor.connectTCP("localhost", 1511, ADCClientToHub());
    reactor.run();
