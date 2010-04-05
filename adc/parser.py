import string

from pyparsing import *
from adctypes import *

"""
The following module is a parser based on the ADC specification version 1.0:
http://adc.sourceforge.net/ADC.html
"""

import base64

def encode_type(k, v):
    """
    Encode a value, key to a specific type, always must return string or throw exception.
    """
    
    if type(v) == int:
        print k, str(v);
    elif isinstance(v, IP):
        if v.version() == 4:
            return k, str(v)
        elif v.version() == 6:
            return k, str(v)
    elif isinstance(v, basestring):
        return k, v;
    elif isinstance(v, Base32):
        enc = base64.b32encode(v.val);
        o = enc.find('=');
        if o == -1:
            o = len(enc);
        return k, enc[:o];
    
    raise ValueError("cannot encode value: " + repr(v));

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
    
    TYPE_INT = "INT";
    TYPE_IP4 = "IP4";
    TYPE_IP6 = "IP6";
    TYPE_B32 = "B32";
    TYPE_STR = "STR";
    
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
    parameter_type        = (Literal(TYPE_INT) | Literal(TYPE_STR) | Literal(TYPE_B32) | Literal(TYPE_IP4) | Literal(TYPE_IP6))
    
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
  def __init__(self, header=None, *params, **named_params):
    self.header = header
    self.params = list(params) + [''.join(encode_type(k, v)) for k, v in named_params.items()]
  
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
  
  def decode(self, a_key, a_type, *args):
    """
    Decode a value, key from a set of tokens to a specific type, always must return type
    """
    
    if isinstance(a_key, int):
        a_val = self.params[a_key];
    else:
        a_val = filter(lambda v: v.startswith(a_key), self.params);
        
        if len(a_val) == 0:
          return None;
        
        a_val = a_val[0][len(a_key):];
    
    if a_type == ADCParser.TYPE_STR:
      return a_val;
    elif a_type == ADCParser.TYPE_INT:
      return int(a_val);
    elif a_type == ADCParser.TYPE_B32:
      if len(args) <= 0:
        raise ValueError("decoding of type TYPE_B32 requires extra argument: <size>");
      
      size = args[0];
      a_val += ("=" * (size - len(a_val)));
      return Base32(base64.b32decode(a_val)[:size], size);
    elif a_type == ADCParser.TYPE_IP4:
      return IP(a_val, ipversion=4);
    elif a_type == ADCParser.TYPE_IP6:
      return IP(a_val, ipversion=6);
    
    return None;

class Header:
  def __init__(self, **kw):
    self.type = kw.pop('type', None);
    self.command_name = kw.pop('command_name', None);    
    
    if hasattr(self, 'validates'):
      for v in self.validates:
        if getattr(self, v) is None:
          continue;
        
        try:
          val = getattr(self, v);
          assert isinstance(val, basestring), "value must be of type: basestring";
          getattr(ADCParser, v).parseString(val, parseAll=True);
        except Exception, e:
          raise ValueError("argument '" + str(v) + "' is invalid: " + str(e));
    
    if self.type and not self.type in self.types:
      raise ValueError("type " + repr(self.type) + " not valid for: " + repr(self));
  
  def from_tree(self, tree_root):
    self.type = tree_root.get('type', None);
    self.command_name = tree_root.get('command_name', None);
  
  @classmethod
  def create(klass, tree_root):
    header_type = tree_root.get("message_header", None);
    
    if header_type is None:
      return None;
    
    header_type = header_type[0];
    
    if header_type in ADCParser.B_HEADER:
      return BHeader().from_tree(tree_root);
    
    if header_type in ADCParser.CIH_HEADER:
      return CIHHeader().from_tree(tree_root);
    
    if header_type in ADCParser.DE_HEADER:
      return DEHeader().from_tree(tree_root);
    
    if header_type in ADCParser.F_HEADER:
      return FHeader().from_tree(tree_root);
    
    if header_type in ADCParser.U_HEADER:
      return UHeader().from_tree(tree_root);
    
    return None;

class BHeader(Header):
  validates = ['command_name', 'my_sid'];
  types = ADCParser.B_HEADER;
  
  def __init__(self, **kw):
    self.my_sid = kw.pop('my_sid', None);
    Header.__init__(self, **kw);
  
  def from_tree(self, tree_root):
    Header.from_tree(self, tree_root);
    self.my_sid = tree_root.get("my_sid");
    return self;
  
  def __repr__(self):
    return "<BHeader type=" + repr(self.type) + " command_name=" + repr(self.command_name) + " my_sid=" + repr(self.my_sid) + ">"

  def __str__(self):
    return ADCParser.SEPARATOR.join([self.type + self.command_name, self.my_sid]);

class CIHHeader(Header):
  validates = ['command_name'];
  types = ADCParser.CIH_HEADER;
  
  def __init__(self, **kw):
    Header.__init__(self, **kw);
  
  def from_tree(self, tree_root):
    Header.from_tree(self, tree_root);
    return self;
  
  def __repr__(self):
    return "<CIHHeader type=" + repr(self.type) + " command_name=" + repr(self.command_name) + ">"
  
  def __str__(self):
    return self.type + self.command_name;

class DEHeader(Header):
  validates = ['command_name', 'my_sid', 'target_sid']
  types = ADCParser.DE_HEADER;
  
  def __init__(self, **kw):
    self.my_sid = kw.pop('my_sid', None);
    self.target_sid = kw.pop('target_sid', None);
    Header.__init__(self, **kw);
  
  def from_tree(self, tree_root):
    Header.from_tree(self, tree_root);
    self.my_sid = tree_root.get("my_sid");
    self.target_sid = tree_root.get("target_sid");
    return self;
  
  def __repr__(self):
    return "<DEHeader type=" + repr(self.type) + " command_name=" + repr(self.command_name) + " my_sid=" + repr(self.my_sid) + " target_sid=" + repr(self.target_sid) + ">"
  
  def __str__(self):
    return ADCParser.SEPARATOR.join([self.type + self.command_name, self.my_sid, self.target_sid]);

class FHeader(Header):
  validates = ['command_name', 'my_sid']
  types = ADCParser.F_HEADER;
  
  def __init__(self, **kw):
    self.my_sid = kw.pop('my_sid', None);
    self.features = kw.pop('features', dict());
    Header.__init__(self, **kw);
  
  def from_tree(self, tree_root):
    Header.from_tree(self, tree_root);
    self.my_sid = tree_root.get("my_sid");
    self.feature_list = tree_root.get("feature_list");
    
    self.features = dict();
    self.features[ADCParser.FEATURE_ADD] = list();
    self.features[ADCParser.FEATURE_REM] = list();
    
    for t, f in self.feature_list:
        self.features[t].append(f);

    return self;
  
  def __repr__(self):
    return "<FHeader type=" + repr(self.type) + " command_name=" + repr(self.command_name) + " my_sid=" + repr(self.my_sid) + " features=" + repr(self.features) + ">"
  
  def __str__(self):
    features = reduce(lambda o, (ft, fv): o + [ft + v for v in fv], self.features.items(), [])
    return ADCParser.SEPARATOR.join([self.type + self.command_name, self.my_sid] + features);

class UHeader(Header):
  def __init__(self, **kw):
    Header.__init__(self, **kw);
    self.my_cid = kw.pop('my_cid', None);
  
  def from_tree(self, tree_root):
    Header.from_tree(self, tree_root);
    self.my_cid = tree_root.get("my_cid");
    return self;
  
  def __repr__(self):
    return "<FHeader type=" + repr(self.type) + " command_name=" + repr(self.command_name) + " my_cid=" + repr(self.my_cid) + ">"
  
  def __str__(self):
    return ADCParser.SEPARATOR.join([self.type + self.command_name, self.my_cid]);

if __name__ == "__main__":
  import sys
  if len(sys.argv) < 2:
    sys.stderr.write("usage: adc.parser <string>\n");
    sys.exit(1);
  
  sys.stdout.write(repr(ADCParser.parseString(sys.argv[1])) + "\n")
