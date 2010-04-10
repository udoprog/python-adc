from twisted.protocols.basic import LineReceiver

import base64;
import json;

class ServerProtocol(LineReceiver):
    delimiter = "\n";

    def __init__(self):
        self.messages = list();
    
    def send_message(self, fr, text):
        self.messages.append((fr, text));
    
    def send_object(self, obj):
        p = base64.b64encode(json.dumps(obj));
        self.sendLine(p);

    def connectionMade(self):
        peer = self.transport.getPeer()
        self.factory.connections[(peer.host, peer.port)] = self;
        print "made connection:", self
    
    def connectionLost(self, reason):
        peer = self.transport.getPeer();
        self.factory.connections.pop((peer.host, peer.port));
        print "lost connection:", self, reason
    
    def lineReceived(self, line):
        m = json.loads(base64.b64decode(line));
        
        messages = self.messages;
        self.messages = list();
        try:
            remote = m['remote'];
            args = m.get('args', []);
            kw_u = m.get('kw', {});
            kw = dict();

            for k, v in kw_u.items():
                kw[str(k)] = v;
            
            attr = "remote_" + remote;
            
            if hasattr(self.factory, attr):
                result = getattr(self.factory, attr)(self, *args, **kw);
                messages += self.messages;
                self.messages = list();
                self.send_object({'ok': True, 'error': None, 'result': result, 'messages': messages});
            else:
                raise Exception("no such remote method: " + remote);
        except Exception, e:
            self.send_object({'ok': False, 'error': str(e), 'result': None, 'messages': messages})
