from merkletree import MerkleTree

import hashing;

class TigerTree(MerkleTree):
  segment = 1024;
  _hash, hashsize = hashing.gethash("TIGR");

def main(app, argv):
    if len(argv) < 1:
        app.err.println("Usage: adc-tthsum <file>");
        return 1;
    
    fn=argv[0];
    
    app.out.println(TigerTree(open(fn, "r")).base32()[:-1], fn);

from . import entrypoint

def entry():
    entrypoint.method = main;
    entrypoint.run();

if __name__ == '__main__':
    entry();
