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
    
    """
    separator             ::= ' '
    """
    separator             = Literal(" ").suppress()
    
    """
    eol                   ::= #x0a
    """
    eol                   = "\x0a"

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
    positional_parameter  = parameter_value

    """
    convenience function for positional parameters
    """
    positional_parameters = ZeroOrMore(separator + positional_parameter).setResultsName("positional_parameters")
    
    """
    named_parameter       ::= parameter_name parameter_value?
    """
    named_parameter       = parameter_name + Optional(parameter_value)
    
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
        return ADC_Message(ADCParser.message.parseString(s, parseAll=True));

class ADC_Message:
  def __init__(self, tree_root = None):
    self.header = None;
    self.params = list();
    self.named_params = dict();
    
    if not tree_root:
        return;
    
    if "message_body" not in tree_root:
        return;
    
    self.header = ADC_MessageHeader.create(tree_root);
    self.params = [a for a in tree_root.get('positional_parameters', [])];
    self.named_params = tree_root.get('named_parameters', []);
    
  def __str__(self):
    return "<ADC_Message header=" + str(self.header) + " params=" + repr(self.params) + " named_params=" + repr(self.named_params) + ">"

class ADC_MessageHeader:
  def __init__(self, tree_root):
    self.type = tree_root.get('type', None);
    self.command_name = tree_root.get('command_name', None);
  
  @classmethod
  def create(klass, tree_root):
    type = tree_root.get("message_header")[0];
    
    if type in ADCParser.B_HEADER:
      return ADC_BMessageHeader(tree_root);
    
    if type in ADCParser.CIH_HEADER:
      return ADC_CIHMessageHeader(tree_root);
    
    if type in ADCParser.DE_HEADER:
      return ADC_DEMessageHeader(tree_root);
    
    if type in ADCParser.F_HEADER:
      return ADC_FMessageHeader(tree_root);
    
    if type in ADCParser.U_HEADER:
      return ADC_UMessageHeader(tree_root);
    
    return None;

class ADC_BMessageHeader(ADC_MessageHeader):
  def __init__(self, tree_root):
    ADC_MessageHeader.__init__(self, tree_root);
    self.my_sid = tree_root.get("my_sid");

  def __str__(self):
    return "<ADC_BMessageHeader type=" + repr(self.type) + " command_name=" + repr(self.command_name) + " my_sid=" + repr(self.my_sid) + ">"

class ADC_CIHMessageHeader(ADC_MessageHeader):
  def __init__(self, tree_root):
    ADC_MessageHeader.__init__(self, tree_root);
  
  def __str__(self):
    return "<ADC_CIHMessageHeader type=" + repr(self.type) + " command_name=" + repr(self.command_name) + ">"

class ADC_DEMessageHeader(ADC_MessageHeader):
  def __init__(self, tree_root):
    ADC_MessageHeader.__init__(self, tree_root);
    self.my_sid = tree_root.get("my_sid");
    self.target_sid = tree_root.get("target_sid");
  
  def __str__(self):
    return "<ADC_DEMessageHeader type=" + repr(self.type) + " command_name=" + repr(self.command_name) + " my_sid=" + repr(self.my_sid) + " target_sid=" + repr(self.target_sid) + ">"

class ADC_FMessageHeader(ADC_MessageHeader):
  def __init__(self, tree_root):
    ADC_MessageHeader.__init__(self, tree_root);
    self.my_sid = tree_root.get("my_sid");
    self.feature_list = tree_root.get("feature_list");
    
    self.features = dict();
    self.features[ADCParser.FEATURE_ADD] = list();
    self.features[ADCParser.FEATURE_REM] = list();
    
    for t, f in self.feature_list:
        self.features[t].append(f);
  
  def __str__(self):
    return "<ADC_FMessageHeader type=" + repr(self.type) + " command_name=" + repr(self.command_name) + " my_sid=" + repr(self.my_sid) + " features=" + repr(self.features) + ">"

class ADC_UMessageHeader(ADC_MessageHeader):
  def __init__(self, tree_root):
    ADC_MessageHeader.__init__(self, tree_root);
    self.my_cid = tree_root.get("my_cid");
  
  def __str__(self):
    return "<ADC_FMessageHeader type=" + repr(self.type) + " command_name=" + repr(self.command_name) + " my_cid=" + repr(self.my_cid) + ">"

if __name__ == "__main__":
  import sys
  if len(sys.argv) < 2:
    sys.stderr.write("usage: adc.parser <string>");
    sys.exit(1);
  
  sys.stdout.write(str(ADCParser.parseString(sys.argv[1])) + "\n")
