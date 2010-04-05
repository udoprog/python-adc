#!/usr/bin/python

from mhash import MHASH, MHASH_TIGER

from merkletree import MerkleTree

from . import entrypoint

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

def main(app, argv):
    if len(argv) < 1:
        app.err.println("Usage: adc-tthsum <file>");
        return 1;
    
    fn=argv[0];
    
    app.out.println(TigerTree(open(fn, "r")).base32()[:-1], fn);

def entry():
    entrypoint.method = main;
    entrypoint.run();

if __name__ == '__main__':
    entry();
