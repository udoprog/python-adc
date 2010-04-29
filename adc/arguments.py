import base64

from IPy import IP

class List:
    """
    A simple type helpers which speicifies that a set of parameters are expected as a list.
    """
    def __init__(self, type):
        self.type = type;

INT = "INT";
IP4 = "IP4";
IP6 = "IP6";
B32 = "B32";
STR = "STR";

class Base32:
    """
    A read only type to indicate that the containing message should be encoded using Base32
    """
    def __init__(self, val, size=None):
        self._val = val;
        self._size = size;
    
    val = property(lambda self: self._val);
    size = property(lambda self: self._size);
    
    def __str__(self):
        return self.val;
    
    def __repr__(self):
        return "<Base32 val=" + repr(self.val) + ">"

def encode(v):
    """
    Encode a value, key to a specific type, always must return string or throw exception.
    """
    if v is None:
        return "";
    
    if type(v) in [int, long, float]:
        return str(v);
    elif isinstance(v, IP):
        if v.version() == 4:
            return str(v)
        elif v.version() == 6:
            return str(v)
    elif isinstance(v, basestring):
        return v.replace(' ', "\\s").replace('\n', "\\n");
    elif isinstance(v, Base32):
        enc = base64.b32encode(v.val);
        o = enc.find('=');
        if o == -1:
            o = len(enc);
        return enc[:o];
    
    raise ValueError("cannot encode value: " + str(type(v)) + " " + repr(v));

def decode(v, t, *args):
  if v is None:
    return None;

  if t == STR:
    return v;
  elif t == INT:
    return int(v);
  elif t == B32:
    if len(args) <= 0:
      raise ValueError("decoding of type B32 requires extra argument: <size>");
    
    size = args[0];
    
    mod = size % 5;
    
    if mod == 0:
        need = 0;
    else:
        need = (size + (5 - mod)) / 5 * 8 - len(v);
    
    return Base32(base64.b32decode(v + "=" * need, size));
  elif t == IP4:
    return IP(v, ipversion=4);
  elif t == IP6:
    return IP(v, ipversion=6);
