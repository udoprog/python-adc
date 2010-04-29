from merkletree import MerkleTree

from .hashing import TigerHash

class TigerTree(MerkleTree):
  segment = 1024;
  hashsize = TigerHash.size;
  
  @classmethod
  def _hash(klass, *chunks):
    return TigerHash.digest(*chunks);
