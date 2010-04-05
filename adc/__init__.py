from parser import ADCParser

from printer import Printer;

class entrypoint:
    out = None;
    err = None;

    @classmethod
    def method(klass, argv):
        klass.err.println("no entrypoint method defined");
        return 250;
    
    @classmethod
    def run(klass):
        import sys;
        klass.out = Printer(stream=sys.stdout);
        klass.err = Printer(stream=sys.stdout);
        klass.method(klass(), sys.argv[1:]);
