from mhash import MHASH, MHASH_TIGER

__all__ = ['HASHES', 'gethash', 'ishash'];

@classmethod
def tiger_digest(klass, *chunks):
    h=MHASH(MHASH_TIGER);
    for chunk in chunks:
      h.update(chunk);
    
    d = h.digest();
    
    return ''.join([d[i*8:i*8 + 8][::-1] for i in range(24)])[:klass.hashsize];

"""
A dict specifyong all available hashing methods.
"""
HASHES = {
    'TIGR': (tiger_digest, 24)
};

def gethash(v):
    return HASHES.get(v, (None, 0));

def ishash(v):
    return v in HASHES;
