from twisted.protocols.basic import LineReceiver

import base64, pickle

class RemoteProtocol(LineReceiver):
    delimiter = "\n"
    
    def send_object(self, remote, *args, **kw):
        self.sendLine(base64.b64encode(pickle.dumps({'remote': remote, 'args': args, 'kw': kw})));
    
    def connectionMade(self):
        remote, args, kw = self.factory.input(self);
        self.send_object(remote, *args, **kw);
    
    def lineReceived(self, line):
        self.factory.response(pickle.loads(base64.b64decode(line)));
        remote, args, kw = self.factory.input(self);
        self.send_object(remote, *args, **kw);
