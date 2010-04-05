import types;
import base64;
import collections;

node = collections.namedtuple("node", "left right hash");

class MerkleTree:
  segment = 1024;
  hashsize = 0;
  
  def __init__(self, data, **kw):
    if type(data) == file:
      self.root = self._hash_fp(data);
    elif type(data) == str:
      self.root = self._hash_text(data);
    else:
      self.root = data;

  @classmethod
  def _hash(klass, *chunks):
    raise Exception("A MerkleTree implementation must implement the _hash class method and set the class fields 'segment' and 'hashsize'");
  
  @classmethod
  def _ih(klass, *chunks):
    return klass._hash("\x01", *chunks);
  
  @classmethod
  def _lh(klass, *chunks):
    return klass._hash("\x00", *chunks);
  
  @classmethod
  def _hash_text(klass, text):
    nodes = list();
    
    for i in range(0, len(text), klass.segment):
      nodes.append(node(None, None, klass._lh(text[i:i+klass.segment])))
    
    return klass._build_tree(nodes);
  
  @classmethod
  def _hash_fp(klass, fp):
    nodes = list();
    
    while True:
      chunk = fp.read(klass.segment)
      
      if not chunk:
        break
      
      nodes.append(node(None, None, klass._lh(chunk)))
    
    return klass._build_tree(nodes);

  @classmethod
  def _build_tree(klass, nodes):
    if len(nodes) == 0:
        return node(None, None, klass._lh(""));
    
    if len(nodes) == 1:
        return nodes[0];
    
    while len(nodes) > 2:
      acc = list();
      
      quanta, mod = divmod(len(nodes), 2);
      
      for i in range(quanta):
        l = nodes[i*2];
        r = nodes[i*2+1];
        acc.append(node(l, r, klass._ih(l.hash, r.hash)));
      
      if mod:
        acc.append(node(nodes[-1], None, nodes[-1].hash));
      
      nodes = acc;
    
    l = nodes[0];
    
    if len(nodes) == 1:
      return node(l, None, klass._ih(l.hash))
    else:
      r = nodes[1];
      return node(l, r, klass._ih(l.hash, r.hash))
  
  def base32(self):
    return base64.b32encode(self.root.hash);
    
  def base16(self):
    return base64.b16encode(self.root.hash);

  def serialize(self):
    result = [];
    queue = [self.root];

    while len(queue) > 0:
      n = queue.pop();
      result.append(n.hash);
      if n.left: queue.insert(0, n.left);
      if n.right: queue.insert(0, n.right);
    
    return ''.join(result);

  @classmethod
  def deserialize(klass, data, depth):
    """
    This is the simplest deserilization i could think of, reversibly calculate each row starting from the lowest.
    """
    
    import math;
    
    if len(data) % klass.hashsize != 0:
      raise ValueError("data is not valid hash data, not a multiple of 24 bytes");
    
    hashes = [data[i*klass.hashsize:i*klass.hashsize+klass.hashsize] for i in range(len(data) / klass.hashsize)]
    
    nodes = list();

    def _calc_segments(depths, ns, depth):
      if ns <= 0: return 0;
      if depth >= len(depths): return ns + 1;
      
      depths[depth] += 1;
      
      ns = _calc_segments(depths, ns - 1, depth + 1);
      ns = _calc_segments(depths, ns - 1, depth + 1);
      
      return ns;

    def calc_segments(ns, depth):
      depths = [0 for x in range(depth)];
      
      depths[0] = 1;
      ns = _calc_segments(depths, ns - 1, 1);
      ns = _calc_segments(depths, ns - 1, 1);
      
      depths.reverse();
      return depths;
    
    for seg in calc_segments(len(hashes), depth):
      acc = list();
      
      for i, h in enumerate(hashes[-seg:]):
        if len(nodes) > i*2:   l = nodes[i*2];
        else:                  l = None;
        if len(nodes) > i*2+1: r = nodes[i*2+1];
        else:                  r = None;
        acc.append(node(l, r, h));
      
      hashes = hashes[:-seg]
      nodes = acc;
    
    return klass(nodes[0]);
  
  def __eq__(self, o):
    def _check(n1, n2):
      if n1 is None and n2 is None: return True;
      if n1 is None: return False;
      if n2 is None: return False;
      return n1.hash == n2.hash and _check(n1.left, n2.left) and _check(n1.right, n2.right);
    
    return _check(self.root, o.root);

  def __ne__(self, o):
    return not self.__eq__(o);
