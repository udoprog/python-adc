# case 1: initial of a byte
# case 2: offset

base32string="ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";

def b32encode(s):
    c1 = 0;
    c2 = 0;
    c3 = 0;

    for c in s:
        o = ord(c);
        
        c1 = base32string[o >> 3]
        c2 += (o & 0x07) << 
    
    return c1;

if __name__ == "__main__":
    print b32encode("T");
