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
