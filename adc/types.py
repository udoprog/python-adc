import base64

__all__ = ['INT', 'IP4', 'IP6', 'B32', 'STR', 'Base32', 'IP'];

from IPy import IP

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

INT = "INT";
IP4 = "IP4";
IP6 = "IP6";
B32 = "B32";
STR = "STR";

def encode(v):
    """
    Encode a value, key to a specific type, always must return string or throw exception.
    """
    if v is None:
        return "";
    
    if type(v) == int:
        print str(v);
    elif isinstance(v, IP):
        if v.version() == 4:
            return str(v)
        elif v.version() == 6:
            return str(v)
    elif isinstance(v, basestring):
        return v;
    elif isinstance(v, Base32):
        enc = base64.b32encode(v.val);
        o = enc.find('=');
        if o == -1:
            o = len(enc);
        return enc[:o];
    
    raise ValueError("cannot encode value: " + repr(v));

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
    sfx = ("=" * (size - len(v)))[:size];
    return Base32(base64.b32decode(v + sfx, size));
  elif t == IP4:
    return IP(v, ipversion=4);
  elif t == IP6:
    return IP(v, ipversion=6);
