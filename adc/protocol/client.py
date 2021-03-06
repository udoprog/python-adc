from twisted.protocols.basic import LineReceiver

import base64;
import json;

class ClientProtocol(LineReceiver):
    delimiter = "\n"
    
    def send_object(self, remote, *args, **kw):
        self.sendLine(base64.b64encode(json.dumps({'remote': remote, 'args': args, 'kw': kw})));
    
    def connectionMade(self):
        remote, args, kw = self.factory.input(self);
        self.send_object(remote, *args, **kw);
    
    def lineReceived(self, line):
        self.factory.response(json.loads(base64.b64decode(line)));
        remote, args, kw = self.factory.input(self);
        self.send_object(remote, *args, **kw);
