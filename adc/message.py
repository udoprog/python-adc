from . import parser

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

  @classmethod
  def parse(klass, string):
    return klass.create(parser.parseFrame(string));
  
  def __repr__(self):
    return "<Message header=" + repr(self.header) + " params=" + repr(self.params) + ">"

  def __str__(self):
    if self.header is None:
      return "";
    
    return parser.SEPARATOR.join([self.header.__str__()] + self.params)
  
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
    
    if header_type in parser.B_HEADER:
      return Broadcast(tree_root);
    if header_type in parser.CIH_HEADER:
      if header_type == 'C': return Client(tree_root);
      if header_type == 'I': return Info(tree_root);
      if header_type == 'H': return Hub(tree_root);
    if header_type in parser.DE_HEADER:
      if header_type == 'D': return Direct(tree_root);
      if header_type == 'E': return Echo(tree_root);
    if header_type in parser.F_HEADER: return Feature(tree_root);
    if header_type in parser.U_HEADER: return UDP(tree_root);
    return None;

class Broadcast(Header):
  validates = ['cmd', 'my_sid'];
  types = parser.B_HEADER;
  
  def __init__(self, tree_root=None, **kw):
    kw['type'] = 'B';
    
    if tree_root:
        self.my_sid = tree_root.get("my_sid");
    else:
        self.my_sid = kw.pop('my_sid', None);
    
    Header.__init__(self, tree_root, **kw);
  
  def __repr__(self):
    return "<Broadcast cmd=" + repr(self.cmd) + " my_sid=" + repr(self.my_sid) + ">"

  def __str__(self):
    return parser.SEPARATOR.join([self.type + self.cmd, self.my_sid]);

class CIH(Header):
  validates = ['cmd'];
  types = parser.CIH_HEADER;
  
  def __str__(self):
    return self.type + self.cmd;

class Client(CIH):
  types = parser.CIH_HEADER;
  
  def __init__(self, *args, **kw):
    kw['type'] = 'C';
    CIH.__init__(self, *args, **kw);
  
  def __repr__(self):
    return "<Client cmd=" + repr(self.cmd) + ">"

class Info(CIH):
  types = parser.CIH_HEADER;
  
  def __init__(self, *args, **kw):
    kw['type'] = 'I';
    CIH.__init__(self, *args, **kw);
  
  def __repr__(self):
    return "<Info cmd=" + repr(self.cmd) + ">"

class Hub(CIH):
  types = parser.CIH_HEADER;
  
  def __init__(self, *args, **kw):
    kw['type'] = 'H';
    CIH.__init__(self, *args, **kw);
  
  def __repr__(self):
    return "<Hub cmd=" + repr(self.cmd) + ">"

class DE(Header):
  validates = ['cmd', 'my_sid', 'target_sid']
  types = parser.DE_HEADER;
  
  def __init__(self, tree_root=None, **kw):
    if tree_root:
        self.my_sid = tree_root.get("my_sid");
        self.target_sid = tree_root.get("target_sid");
    else:
        self.my_sid = kw.pop('my_sid', None);
        self.target_sid = kw.pop('target_sid', None);
    
    Header.__init__(self, tree_root, **kw);
  
  def __str__(self):
    return parser.SEPARATOR.join([self.type + self.cmd, self.my_sid, self.target_sid]);

class Direct(DE):
  types = parser.DE_HEADER;
  
  def __init__(self, *args, **kw):
    kw['type'] = 'D';
    DE.__init__(self, *args, **kw);
  
  def __repr__(self):
    return "<Direct cmd=" + repr(self.cmd) + " my_sid=" + repr(self.my_sid) + " target_sid=" + repr(self.target_sid) + ">"

class Echo(DE):
  types = parser.DE_HEADER;
  
  def __init__(self, *args, **kw):
    kw['type'] = 'E';
    DE.__init__(self, *args, **kw);
  
  def __repr__(self):
    return "<Echo cmd=" + repr(self.cmd) + " my_sid=" + repr(self.my_sid) + " target_sid=" + repr(self.target_sid) + ">"

class Feature(Header):
  validates = ['cmd', 'my_sid']
  types = parser.F_HEADER;
  
  def __init__(self, tree_root=None, **kw):
    if tree_root:
        self.my_sid = tree_root.get("my_sid");
        self.add = list();
        self.rem = list();
        
        for t, f in tree_root.get("feature_list"):
            if t == parser.FEATURE_ADD:
                self.add.append(f);
            elif t == parser.FEATURE_REM:
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
    return "<Feature cmd=" + repr(self.cmd) + " my_sid=" + repr(self.my_sid) + " features=" + repr(self.features) + ">"
  
  def __str__(self):
    features = [parser.FEATURE_ADD + feat for feat in self.add] + [parser.FEATURE_REM + feat for feat in self.rem];
    return parser.SEPARATOR.join([self.type + self.cmd, self.my_sid] + features);

class UDP(Header):
  validates = ['my_cid', 'type'];
  types = parser.U_HEADER;
  
  def __init__(self, tree_root=None, **kw):
    if tree_root:
        self.my_cid = tree_root.get("my_cid");
    else:
        self.my_cid = kw.pop('my_cid', None);
    
    Header.__init__(self, tree_root, **kw);
  
  def __repr__(self):
    return "<UDP cmd=" + repr(self.cmd) + " my_cid=" + repr(self.my_cid) + ">"
  
  def __str__(self):
    return parser.SEPARATOR.join([self.type + self.cmd, self.my_cid]);

__all__ = [ "Message", "Client", "Info", "Hub", "Direct", "Echo", "Feature", "UDP", "Broadcast"];
