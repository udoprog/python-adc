from mhash import MHASH, MHASH_TIGER

__all__ = ['TigerHash'];

class HashMethod:
    size = 0;

    def __init__(self, name):
        self.name = name;
    
    def digest(self, *chunks):
        raise Exception("HashMethod");

class TigerHash:
    size = 24;
    
    @classmethod
    def digest(klass, *chunks):
        h=MHASH(MHASH_TIGER);
        
        for chunk in chunks:
          h.update(chunk);
        
        d = h.digest();
        
        return ''.join([d[i*8:i*8 + 8][::-1] for i in range(klass.size)]);
