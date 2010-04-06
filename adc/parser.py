import string

from pyparsing import *

from .types import *

"""
The following module is a parser based on the ADC specification version 1.0:
http://adc.sourceforge.net/ADC.html
"""

class ADCParser:
    """
    A pyparser parsing with all methods encapsulated as static fields in this class.
    """
    ParserElement.setDefaultWhitespaceChars("")
    ParserElement.enablePackrat();
    
    FEATURE_ADD="+"
    FEATURE_REM="-"
    SEPARATOR=" "
    TYPE_SEP=":"
    EOL="\n"
    
    """
    separator             ::= ' '
    """
    separator             = Literal(SEPARATOR).suppress()
    
    """
    eol                   ::= #x0a
    """
    eol                   = Literal(EOL)
    
    """
    simple_alphanum       ::= [A-Z0-9]
    """
    simple_alphanum       = string.uppercase + string.digits
    
    """
    simple_alpha          ::= [A-Z]
    """
    simple_alpha          = string.uppercase

    """
    base32_character      ::= simple_alpha | [2-7]
    """
    base32_character      = simple_alpha + "234567"
    
    """
    escape                ::= '\'
    """
    escape                = "\\"
    
    """
    convenience functions for escaped_letter
    """
    escaped_nl            = Literal(escape + "n").setParseAction(lambda s, l, t: "\n")
    escaped_s             = Literal(escape + "s").setParseAction(lambda s, l, t: " ")
    escaped_bs            = Literal(escape + escape).setParseAction(lambda s, l, t: "\\")
    
    """
    escaped_letter        ::= [^ \#x0a] | escape 's' | escape 'n' | escape escape
    """
    escaped_letter        = (escaped_s | escaped_nl | escaped_bs) | Regex("[^ \n]")

    """
    feature_name          ::= simple_alpha simple_alphanum{3}
    """
    feature_name          = Combine(Word(simple_alpha, exact=1) + Word(simple_alphanum, exact=3))

    """
    encoded_sid           ::= base32_character{4}
    """
    encoded_sid           = Word(base32_character, exact=4)

    """
    my_sid                ::= encoded_sid
    """
    my_sid                = encoded_sid.setResultsName('my_sid');

    """
    encoded_cid           ::= base32_character+
    """
    encoded_cid           = Word(base32_character)

    """
    my_cid                ::= encoded_cid
    """
    my_cid                = encoded_cid.setResultsName('my_cid');
    
    """
    target_sid            ::= encoded_sid
    """
    target_sid            = encoded_sid.setResultsName('target_sid')

    """
    command_name          ::= simple_alpha simple_alphanum simple_alphanum
    """
    command_name          = Combine(Word(simple_alpha, exact=1) + Word(simple_alphanum, exact=2)).setResultsName('command_name')
    
    """
    parameter_value       ::= escaped_letter+
    """
    parameter_value       = Combine(OneOrMore(escaped_letter))
    
    """
    parameter_type        ::= 'INT' | 'STR' | 'B32' | 'IP4' | 'IP6'
    """
    parameter_type        = (Literal(INT) | Literal(STR) | Literal(B32) | Literal(IP4) | Literal(IP6))
    
    """
    parameter_name        ::= simple_alpha simple_alphanum
    """
    parameter_name        = Combine(Word(simple_alpha, exact=1) + Word(simple_alphanum, exact=1))
    
    """
    parameter       ::= parameter_type ':' parameter_name (':' parameter_value)?
    """
    parameter       = parameter_value
    
    """
    convenience function for parameters
    """
    parameters      = ZeroOrMore(separator + parameter).setResultsName('parameters')
    
    """
    convenience function for f_message_header
    """
    feature_list         = OneOrMore(Group(separator + (Literal(FEATURE_ADD) | Literal(FEATURE_REM)) + feature_name)).setResultsName('feature_list')

    """
    b_message_header      ::= 'B' command_name separator my_sid
    """
    B_HEADER = ["B"];
    b_message_header      = Word(B_HEADER, exact=1).setResultsName('type') + command_name + separator + my_sid;
    
    """
    cih_message_header    ::= ('C' | 'I' | 'H') command_name
    """
    CIH_HEADER = ["C", "I", "H"];
    cih_message_header    = (Word(CIH_HEADER, exact=1)).setResultsName('type') + command_name
    
    """
    de_message_header     ::= ('D' | 'E') command_name separator my_sid separator target_sid
    """
    DE_HEADER = ["D", "E"];
    de_message_header     = Word(DE_HEADER, exact = 1).setResultsName('type') + command_name + separator + my_sid + separator + target_sid
    
    """
    f_message_header      ::= 'F' command_name separator my_sid separator (('+'|'-') feature_name)+
    """
    F_HEADER = ["F"];
    f_message_header      = Word(F_HEADER, exact=1).setResultsName('type') + command_name + separator + my_sid + feature_list

    """
    u_message_header      ::= 'U' command_name separator my_cid
    """
    U_HEADER = ["U"];
    u_message_header      = Word(U_HEADER, exact=1).setResultsName('type') + command_name + separator + my_cid
    
    """
    convenience function to match all different message headers.
    """
    message_header        = (b_message_header | cih_message_header | de_message_header | f_message_header | u_message_header).setResultsName('message_header');
    
    """
    message_body          ::= (b_message_header | cih_message_header | de_message_header | f_message_header | u_message_header | message_header)
                              (separator parameter)*
    """
    message_body          = (message_header + parameters).setResultsName('message_body');
    
    """
    message               ::= message_body? eol
    """
    message               = Optional(message_body) + StringEnd();

    @classmethod
    def parseString(klass, s):
        return Message.create(ADCParser.message.parseString(s, parseAll=True));

class Message:
  def __init__(self, header=None, *params, **kw):
    self.header = header
    for k, a in kw.items():
        if type(a) != list:
            kw[k] = [a];
    
    self.params = list(params) + reduce(lambda o, (nk, nv): o + [nk + str(v) for v in nv], kw.items(), [])
  
  @classmethod
  def create(klass, tree_root):
    if "message_body" in tree_root:
        header = Header.create(tree_root);
        params = list(tree_root.get('parameters', []));
        return Message(header, *params);
    else:
        return Message();
  
  def __repr__(self):
    return "<Message header=" + repr(self.header) + " params=" + repr(self.params) + ">"

  def __str__(self):
    if self.header is None:
      return "";
    
    return ADCParser.SEPARATOR.join([self.header.__str__()] + self.params)
  
  def get(self, a_key):
    """
    Decode a value, key from a set of tokens to a specific type, always must return type
    """
    
    if isinstance(a_key, int):
        if a_key < 0 or a_key >= len(self.params):
            raise ValueError("parameter index out of range: " + a_key);
        return self.params[a_key];
    
    return map(lambda s: s[len(a_key):], filter(lambda v: v.startswith(a_key), self.params));
  
  def getfirst(self, a_key):
    l = self.get(a_key);
    if len(l) == 0:
      return None;
    return l[0];
  
  def parameterKeys(self):
    return map(lambda s: s[:2], filter(lambda v: len(v) > 2, self.params));

class Header:
  def __init__(self, tree_root=None, **kw):
    if tree_root:
        self.type = tree_root.get('type', None);
        self.cmd = tree_root.get('command_name', None);
    else:
        self.type = kw.pop('type', None);
        self.cmd = kw.pop('cmd', None);    
    
    if hasattr(self, 'validates'):
      for v in self.validates:
        if getattr(self, v) is None:
          raise ValueError("argument '" + str(v) + "' must not be None");
        
        try:
          val = getattr(self, v);
          assert isinstance(val, basestring), "value must be of type: basestring";
        except Exception, e:
          raise ValueError("argument '" + str(v) + "' is invalid: " + str(e));
    
    if self.type and not self.type in self.types:
      raise ValueError("type " + repr(self.type) + " not valid for: " + repr(self));
  
  @classmethod
  def create(klass, tree_root):
    header_type = tree_root.get("message_header", None);
    
    if header_type is None:
      return None;
    
    header_type = header_type[0];
    
    if header_type in ADCParser.B_HEADER:
      return BHeader(tree_root);
    
    if header_type in ADCParser.CIH_HEADER:
      return CIHHeader(tree_root);
    
    if header_type in ADCParser.DE_HEADER:
      return DEHeader(tree_root);
    
    if header_type in ADCParser.F_HEADER:
      return FHeader(tree_root);
    
    if header_type in ADCParser.U_HEADER:
      return UHeader(tree_root);
    
    return None;

class BHeader(Header):
  validates = ['cmd', 'my_sid'];
  types = ADCParser.B_HEADER;
  
  def __init__(self, tree_root=None, **kw):
    kw['type'] = 'B';
    
    if tree_root:
        self.my_sid = tree_root.get("my_sid");
    else:
        self.my_sid = kw.pop('my_sid', None);
    
    Header.__init__(self, tree_root, **kw);
  
  def __repr__(self):
    return "<BHeader type=" + repr(self.type) + " cmd=" + repr(self.cmd) + " my_sid=" + repr(self.my_sid) + ">"

  def __str__(self):
    return ADCParser.SEPARATOR.join([self.type + self.cmd, self.my_sid]);

class CIHHeader(Header):
  validates = ['cmd'];
  types = ADCParser.CIH_HEADER;
  
  def __repr__(self):
    return "<CIHHeader type=" + repr(self.type) + " cmd=" + repr(self.cmd) + ">"
  
  def __str__(self):
    return self.type + self.cmd;

class CHeader(CIHHeader):
  types = ADCParser.CIH_HEADER;
  
  def __init__(self, **kw):
    kw['type'] = 'C';
    CIHHeader.__init__(self, **kw);

class IHeader(CIHHeader):
  types = ADCParser.CIH_HEADER;
  
  def __init__(self, **kw):
    kw['type'] = 'I';
    CIHHeader.__init__(self, **kw);

class HHeader(CIHHeader):
  types = ADCParser.CIH_HEADER;
  
  def __init__(self, **kw):
    kw['type'] = 'H';
    CIHHeader.__init__(self, **kw);

class DEHeader(Header):
  validates = ['cmd', 'my_sid', 'target_sid']
  types = ADCParser.DE_HEADER;
  
  def __init__(self, tree_root=None, **kw):
    if tree_root:
        self.my_sid = tree_root.get("my_sid");
        self.target_sid = tree_root.get("target_sid");
    else:
        self.my_sid = kw.pop('my_sid', None);
        self.target_sid = kw.pop('target_sid', None);
    
    Header.__init__(self, tree_root, **kw);
  
  def __repr__(self):
    return "<DEHeader type=" + repr(self.type) + " cmd=" + repr(self.cmd) + " my_sid=" + repr(self.my_sid) + " target_sid=" + repr(self.target_sid) + ">"
  
  def __str__(self):
    return ADCParser.SEPARATOR.join([self.type + self.cmd, self.my_sid, self.target_sid]);

class DHeader(DEHeader):
  types = ADCParser.DE_HEADER;
  
  def __init__(self, **kw):
    kw['type'] = 'D';
    DEHeader.__init__(self, **kw);

class EHeader(DEHeader):
  types = ADCParser.DE_HEADER;
  
  def __init__(self, **kw):
    kw['type'] = 'E';
    DEHeader.__init__(self, **kw);

class FHeader(Header):
  validates = ['cmd', 'my_sid']
  types = ADCParser.F_HEADER;
  
  def __init__(self, tree_root=None, **kw):
    if tree_root:
        self.my_sid = tree_root.get("my_sid");
        self.add = list();
        self.rem = list();
        
        for t, f in tree_root.get("feature_list"):
            if t == ADCParser.FEATURE_ADD:
                self.add.append(f);
            elif t == ADCParser.FEATURE_REM:
                self.rem.append(f);
    else:
        kw['type'] = 'F';
        self.my_sid = kw.pop('my_sid', None);
        self.add = kw.pop('add', []);
        self.rem = kw.pop('rem', []);
        
        if type(self.add) != list:
            self.add = [self.add];
        
        if type(self.rem) != list:
            self.rem = [self.rem];
    
    Header.__init__(self, tree_root, **kw);
  
  def __repr__(self):
    return "<FHeader type=" + repr(self.type) + " cmd=" + repr(self.cmd) + " my_sid=" + repr(self.my_sid) + " features=" + repr(self.features) + ">"
  
  def __str__(self):
    features = [ADCParser.FEATURE_ADD + feat for feat in self.add] + [ADCParser.FEATURE_REM + feat for feat in self.rem];
    return ADCParser.SEPARATOR.join([self.type + self.cmd, self.my_sid] + features);

class UHeader(Header):
  validates = ['my_cid', 'type'];
  types = ADCParser.U_HEADER;
  
  def __init__(self, tree_root=None, **kw):
    if tree_root:
        self.my_cid = tree_root.get("my_cid");
    else:
        self.my_cid = kw.pop('my_cid', None);
    
    Header.__init__(self, tree_root, **kw);
  
  def __repr__(self):
    return "<FHeader type=" + repr(self.type) + " cmd=" + repr(self.cmd) + " my_cid=" + repr(self.my_cid) + ">"
  
  def __str__(self):
    return ADCParser.SEPARATOR.join([self.type + self.cmd, self.my_cid]);

if __name__ == "__main__":
  import sys
  if len(sys.argv) < 2:
    sys.stderr.write("usage: adc.parser <string>\n");
    sys.exit(1);
  
  sys.stdout.write(repr(ADCParser.parseString(sys.argv[1])) + "\n")
