import string

from pyparsing import *

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
    parameter_value       = Combine(OneOrMore(escaped_letter)).setResultsName('parameter_value')
    
    """
    parameter_name        ::= simple_alpha simple_alphanum
    """
    parameter_name        = Combine(Word(simple_alpha, exact=1) + Word(simple_alphanum, exact=1))
    
    """
    positional_parameter  ::= parameter_value
    """
    positional_parameter  = Combine(~parameter_name + parameter_value)
    
    """
    convenience function for positional parameters
    """
    positional_parameters = ZeroOrMore(separator + positional_parameter).setResultsName("positional_parameters")
    
    """
    named_parameter       ::= parameter_name parameter_value?
    """
    named_parameter       = (parameter_name + Optional(parameter_value)).setParseAction(lambda s, l, t: (t[0], t[1]))
    
    """
    convenience function for named_parameters
    """
    named_parameters      = ZeroOrMore(separator + named_parameter).setResultsName('named_parameters')
    
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
                              (separator positional_parameter)* (separator named_parameter)*
    """
    message_body          = (message_header + positional_parameters + named_parameters).setResultsName('message_body');
    
    """
    message               ::= message_body? eol
    """
    message               = Optional(message_body) + StringEnd();

    @classmethod
    def parseString(klass, s):
        return ADC_Message.create(ADCParser.message.parseString(s, parseAll=True));

class ADC_Message:
  def __init__(self, header=None, *params, **named_params):
    self.header = header
    self.params = list(params)
    self.named_params = named_params
  
  @classmethod
  def create(klass, tree_root):
    if "message_body" in tree_root:
        header = ADC_MessageHeader.create(tree_root);
        params = [a for a in tree_root.get('positional_parameters', [])];
        named_params = tree_root.get('named_parameters', {});
        return ADC_Message(header, *params, **dict(list(named_params)));
    else:
        return ADC_Message();
    
  def __repr__(self):
    return "<ADC_Message header=" + repr(self.header) + " params=" + repr(self.params) + " named_params=" + repr(self.named_params) + ">"

  def __str__(self):
    if self.header is None:
        return "";
    
    return ADCParser.SEPARATOR.join([self.header.__str__()] + list(self.params) + [v + e for v,e in self.named_params.items()])

class ADC_MessageHeader:
  def __init__(self, **kw):
    self.type = kw.pop('type', None);
    self.command_name = kw.pop('command_name', None);    
    
    if hasattr(self, 'validates'):
      for v in self.validates:
        if getattr(self, v) is None:
          continue;

        try:
          getattr(ADCParser, v).parseString(getattr(self, v), parseAll=True);
        except Exception, e:
          raise ValueError("argument '" + v + "' is invalid: " + str(e));
    
    if self.type and not self.type in self.types:
      raise ValueError("type '" + self.type + "' not valid for: " + repr(self));
  
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
      return ADC_BMessageHeader().from_tree(tree_root);
    
    if header_type in ADCParser.CIH_HEADER:
      return ADC_CIHMessageHeader().from_tree(tree_root);
    
    if header_type in ADCParser.DE_HEADER:
      return ADC_DEMessageHeader().from_tree(tree_root);
    
    if header_type in ADCParser.F_HEADER:
      return ADC_FMessageHeader().from_tree(tree_root);
    
    if header_type in ADCParser.U_HEADER:
      return ADC_UMessageHeader().from_tree(tree_root);
    
    return None;

class ADC_BMessageHeader(ADC_MessageHeader):
  validates = ['command_name', 'my_sid'];
  types = ADCParser.B_HEADER;
  
  def __init__(self, **kw):
    self.my_sid = kw.pop('my_sid', None);
    ADC_MessageHeader.__init__(self, **kw);
  
  def from_tree(self, tree_root):
    ADC_MessageHeader.from_tree(self, tree_root);
    self.my_sid = tree_root.get("my_sid");
    return self;
  
  def __repr__(self):
    return "<ADC_BMessageHeader type=" + repr(self.type) + " command_name=" + repr(self.command_name) + " my_sid=" + repr(self.my_sid) + ">"

  def __str__(self):
    return ADCParser.SEPARATOR.join([self.type + self.command_name, self.my_sid]);

class ADC_CIHMessageHeader(ADC_MessageHeader):
  validates = ['command_name'];
  types = ADCParser.CIH_HEADER;
  
  def __init__(self, **kw):
    ADC_MessageHeader.__init__(self, **kw);
  
  def __init__(self, tree_root):
    ADC_MessageHeader.from_tree(self, tree_root);
    return self;
  
  def __repr__(self):
    return "<ADC_CIHMessageHeader type=" + repr(self.type) + " command_name=" + repr(self.command_name) + ">"
  
  def __str__(self):
    return self.type + self.command_name;

class ADC_DEMessageHeader(ADC_MessageHeader):
  validates = ['command_name', 'my_sid', 'target_sid']
  types = ADCParser.DE_HEADER;
  
  def __init__(self, **kw):
    self.my_sid = kw.pop('my_sid', None);
    self.target_sid = kw.pop('target_sid', None);
    ADC_MessageHeader.__init__(self, **kw);
  
  def from_tree(self, tree_root):
    ADC_MessageHeader.from_tree(self, tree_root);
    self.my_sid = tree_root.get("my_sid");
    self.target_sid = tree_root.get("target_sid");
    return self;
  
  def __repr__(self):
    return "<ADC_DEMessageHeader type=" + repr(self.type) + " command_name=" + repr(self.command_name) + " my_sid=" + repr(self.my_sid) + " target_sid=" + repr(self.target_sid) + ">"
  
  def __str__(self):
    return ADCParser.SEPARATOR.join([self.type + self.command_name, self.my_sid, self.target_sid]);

class ADC_FMessageHeader(ADC_MessageHeader):
  validates = ['command_name', 'my_sid']
  types = ADCParser.F_HEADER;
  
  def __init__(self, **kw):
    self.my_sid = kw.pop('my_sid', None);
    self.features = kw.pop('features', dict());
    ADC_MessageHeader.__init__(self, **kw);
  
  def from_tree(self, tree_root):
    ADC_MessageHeader.from_tree(self, tree_root);
    self.my_sid = tree_root.get("my_sid");
    self.feature_list = tree_root.get("feature_list");
    
    self.features = dict();
    self.features[ADCParser.FEATURE_ADD] = list();
    self.features[ADCParser.FEATURE_REM] = list();
    
    for t, f in self.feature_list:
        self.features[t].append(f);

    return self;
  
  def __repr__(self):
    return "<ADC_FMessageHeader type=" + repr(self.type) + " command_name=" + repr(self.command_name) + " my_sid=" + repr(self.my_sid) + " features=" + repr(self.features) + ">"
  
  def __str__(self):
    features = reduce(lambda o, (ft, fv): o + [ft + v for v in fv], self.features.items(), [])
    return ADCParser.SEPARATOR.join([self.type + self.command_name, self.my_sid] + features);

class ADC_UMessageHeader(ADC_MessageHeader):
  def __init__(self, **kw):
    ADC_MessageHeader.__init__(self, **kw);
    self.my_cid = kw.pop('my_cid', None);
  
  def from_tree(self, tree_root):
    ADC_MessageHeader.from_tree(self, tree_root);
    self.my_cid = tree_root.get("my_cid");
    return self;
  
  def __repr__(self):
    return "<ADC_FMessageHeader type=" + repr(self.type) + " command_name=" + repr(self.command_name) + " my_cid=" + repr(self.my_cid) + ">"
  
  def __str__(self):
    return ADCParser.SEPARATOR.join([self.type + self.command_name, self.my_cid]);

if __name__ == "__main__":
  import sys
  if len(sys.argv) < 2:
    sys.stderr.write("usage: adc.parser <string>\n");
    sys.exit(1);
  
  sys.stdout.write(repr(ADCParser.parseString(sys.argv[1])) + "\n")
