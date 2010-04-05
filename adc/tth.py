#!/usr/bin/python

from mhash import MHASH, MHASH_TIGER

from merkletree import MerkleTree

class TigerTree(MerkleTree):
  segment = 1024;
  hashsize = 24;
  
  @classmethod
  def _hash(klass, *chunks):
    h=MHASH(MHASH_TIGER);
    for chunk in chunks:
      h.update(chunk);
    
    d = h.digest();
    
    return ''.join([d[i*8:i*8 + 8][::-1] for i in range(24)])[:klass.hashsize];
