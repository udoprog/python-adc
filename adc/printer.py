from pytermcaps import TermCaps

class Printer(TermCaps):
    def notice(self, *s):
        self._writeall(self.c.bold, self.c.magenta, self._join(s), self.c.sgr0, "\n");
    
    def error(self, *s):
        self._writeall(self.c.bold, self.c.red, self._join(s), self.c.sgr0, "\n");
    
    def message(self, *s):
        self._writeall(self.c.bold, self.c.green, self._join(s), self.c.sgr0, "\n");
    
    def println(self, *s):
        self._writeall(self._join(s), "\n");
