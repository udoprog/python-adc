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
    b_message_header      = Word(B_HEADER, exact=1).setResultsName('type') + command_name + separator + my_sid;
    
    """
    cih_message_header    ::= ('C' | 'I' | 'H') command_name
    """
    cih_message_header    = (Word(CIH_HEADER, exact=1)).setResultsName('type') + command_name
    
    """
    de_message_header     ::= ('D' | 'E') command_name separator my_sid separator target_sid
    """
    de_message_header     = Word(DE_HEADER, exact = 1).setResultsName('type') + command_name + separator + my_sid + separator + target_sid
    
    """
    f_message_header      ::= 'F' command_name separator my_sid separator (('+'|'-') feature_name)+
    """
    f_message_header      = Word(F_HEADER, exact=1).setResultsName('type') + command_name + separator + my_sid + feature_list

    """
    u_message_header      ::= 'U' command_name separator my_cid
    """
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

if __name__ == "__main__":
  import sys
  if len(sys.argv) < 2:
    sys.stderr.write("usage: adc.parser <string>\n");
    sys.exit(1);
  
  sys.stdout.write(repr(ADCParser.parseString(sys.argv[1])) + "\n")
