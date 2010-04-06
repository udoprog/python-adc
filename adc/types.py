import base64

from IPy import IP

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

class Message:
  def __init__(self, header=None, *params, **kw):
    self.header = header
    for k, a in kw.items():
        if type(a) != list:
            kw[k] = [a];
    
    self.params = list(params) + reduce(lambda o, (nk, nv): o + [nk + str(v) for v in nv], kw.items(), [])
  
  @classmethod
  def create(klass, tree_root):
    if "message_body" in tree_root:
        header = Header.create(tree_root);
        params = list(tree_root.get('parameters', []));
        return Message(header, *params);
    else:
        return Message();
  
  def __repr__(self):
    return "<Message header=" + repr(self.header) + " params=" + repr(self.params) + ">"

  def __str__(self):
    if self.header is None:
      return "";
    
    return ADCParser.SEPARATOR.join([self.header.__str__()] + self.params)
  
  def get(self, a_key):
    """
    Decode a value, key from a set of tokens to a specific type, always must return type
    """
    
    if isinstance(a_key, int):
        if a_key < 0 or a_key >= len(self.params):
            raise ValueError("parameter index out of range: " + a_key);
        return self.params[a_key];
    
    return map(lambda s: s[len(a_key):], filter(lambda v: v.startswith(a_key), self.params));
  
  def getfirst(self, a_key):
    l = self.get(a_key);
    if len(l) == 0:
      return None;
    return l[0];
  
  def getkeys(self):
    return map(lambda s: s[:2], filter(lambda v: len(v) > 2, self.params));

  def haskey(self, k):
    return k in self.getkeys();

class Header:
  def __init__(self, tree_root=None, **kw):
    if tree_root:
        self.type = tree_root.get('type', None);
        self.cmd = tree_root.get('command_name', None);
    else:
        self.type = kw.pop('type', None);
        self.cmd = kw.pop('cmd', None);    
    
    if hasattr(self, 'validates'):
      for v in self.validates:
        if getattr(self, v) is None:
          raise ValueError("argument '" + str(v) + "' must not be None");
        
        try:
          val = getattr(self, v);
          assert isinstance(val, basestring), "value must be of type: basestring";
        except Exception, e:
          raise ValueError("argument '" + str(v) + "' is invalid: " + str(e));
    
    if self.type and not self.type in self.types:
      raise ValueError("type " + repr(self.type) + " not valid for: " + repr(self));
  
  @classmethod
  def create(klass, tree_root):
    header_type = tree_root.get("message_header", None);
    
    if header_type is None:
      return None;
    
    header_type = header_type[0];
    
    if header_type in ADCParser.B_HEADER:
      return BHeader(tree_root);
    
    if header_type in ADCParser.CIH_HEADER:
      if header_type == 'C':
          return CHeader(tree_root);
      if header_type == 'I':
          return IHeader(tree_root);
      if header_type == 'H':
          return HHeader(tree_root);
    
    if header_type in ADCParser.DE_HEADER:
      if header_type == 'D':
        return DHeader(tree_root);
      if header_type == 'E':
        return EHeader(tree_root);
    
    if header_type in ADCParser.F_HEADER:
      return FHeader(tree_root);
    
    if header_type in ADCParser.U_HEADER:
      return UHeader(tree_root);
    
    return None;

class BHeader(Header):
  validates = ['cmd', 'my_sid'];
  types = ADCParser.B_HEADER;
  
  def __init__(self, tree_root=None, **kw):
    kw['type'] = 'B';
    
    if tree_root:
        self.my_sid = tree_root.get("my_sid");
    else:
        self.my_sid = kw.pop('my_sid', None);
    
    Header.__init__(self, tree_root, **kw);
  
  def __repr__(self):
    return "<BHeader type=" + repr(self.type) + " cmd=" + repr(self.cmd) + " my_sid=" + repr(self.my_sid) + ">"

  def __str__(self):
    return ADCParser.SEPARATOR.join([self.type + self.cmd, self.my_sid]);

class CIHHeader(Header):
  validates = ['cmd'];
  types = ADCParser.CIH_HEADER;
  
  def __repr__(self):
    return "<CIHHeader type=" + repr(self.type) + " cmd=" + repr(self.cmd) + ">"
  
  def __str__(self):
    return self.type + self.cmd;

class CHeader(CIHHeader):
  types = ADCParser.CIH_HEADER;
  
  def __init__(self, *args, **kw):
    kw['type'] = 'C';
    CIHHeader.__init__(self, *args, **kw);

class IHeader(CIHHeader):
  types = ADCParser.CIH_HEADER;
  
  def __init__(self, *args, **kw):
    kw['type'] = 'I';
    CIHHeader.__init__(self, *args, **kw);

class HHeader(CIHHeader):
  types = ADCParser.CIH_HEADER;
  
  def __init__(self, *args, **kw):
    kw['type'] = 'H';
    CIHHeader.__init__(self, *args, **kw);

class DEHeader(Header):
  validates = ['cmd', 'my_sid', 'target_sid']
  types = ADCParser.DE_HEADER;
  
  def __init__(self, tree_root=None, **kw):
    if tree_root:
        self.my_sid = tree_root.get("my_sid");
        self.target_sid = tree_root.get("target_sid");
    else:
        self.my_sid = kw.pop('my_sid', None);
        self.target_sid = kw.pop('target_sid', None);
    
    Header.__init__(self, tree_root, **kw);
  
  def __repr__(self):
    return "<DEHeader type=" + repr(self.type) + " cmd=" + repr(self.cmd) + " my_sid=" + repr(self.my_sid) + " target_sid=" + repr(self.target_sid) + ">"
  
  def __str__(self):
    return ADCParser.SEPARATOR.join([self.type + self.cmd, self.my_sid, self.target_sid]);

class DHeader(DEHeader):
  types = ADCParser.DE_HEADER;
  
  def __init__(self, *args, **kw):
    kw['type'] = 'D';
    DEHeader.__init__(self, *args, **kw);

class EHeader(DEHeader):
  types = ADCParser.DE_HEADER;
  
  def __init__(self, *args, **kw):
    kw['type'] = 'E';
    DEHeader.__init__(self, *args, **kw);

class FHeader(Header):
  validates = ['cmd', 'my_sid']
  types = ADCParser.F_HEADER;
  
  def __init__(self, tree_root=None, **kw):
    if tree_root:
        self.my_sid = tree_root.get("my_sid");
        self.add = list();
        self.rem = list();
        
        for t, f in tree_root.get("feature_list"):
            if t == ADCParser.FEATURE_ADD:
                self.add.append(f);
            elif t == ADCParser.FEATURE_REM:
                self.rem.append(f);
    else:
        kw['type'] = 'F';
        self.my_sid = kw.pop('my_sid', None);
        self.add = kw.pop('add', []);
        self.rem = kw.pop('rem', []);
        
        if type(self.add) != list:
            self.add = [self.add];
        
        if type(self.rem) != list:
            self.rem = [self.rem];
    
    Header.__init__(self, tree_root, **kw);
  
  def __repr__(self):
    return "<FHeader type=" + repr(self.type) + " cmd=" + repr(self.cmd) + " my_sid=" + repr(self.my_sid) + " features=" + repr(self.features) + ">"
  
  def __str__(self):
    features = [ADCParser.FEATURE_ADD + feat for feat in self.add] + [ADCParser.FEATURE_REM + feat for feat in self.rem];
    return ADCParser.SEPARATOR.join([self.type + self.cmd, self.my_sid] + features);

class UHeader(Header):
  validates = ['my_cid', 'type'];
  types = ADCParser.U_HEADER;
  
  def __init__(self, tree_root=None, **kw):
    if tree_root:
        self.my_cid = tree_root.get("my_cid");
    else:
        self.my_cid = kw.pop('my_cid', None);
    
    Header.__init__(self, tree_root, **kw);
  
  def __repr__(self):
    return "<FHeader type=" + repr(self.type) + " cmd=" + repr(self.cmd) + " my_cid=" + repr(self.my_cid) + ">"
  
  def __str__(self):
    return ADCParser.SEPARATOR.join([self.type + self.cmd, self.my_cid]);

