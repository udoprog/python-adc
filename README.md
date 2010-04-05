This is suppose to be a complete implementation for the Advanced Direct Connect protocol.

The parts marked with a plus (+) have been implemented, the minus parts are TODO:

    + Protocol Parser
    - Client Logic
    - Transport (TCP/UDP/TLS)

Commands
---
The following entry points are availble in this library:

*adc-server*: Experimental adc client (implemented as a server)
*adc-client*: Experimental adc client (to connect to the running client-server)
*adc-tthsum*: A simple wrapper program to check the tth root hash of a file

Parser
---
The parser is based on pyparsing which creates a recursive descent parser.
I aim at keeping the grammar as readable and as close as possible to the
original ADC specification.

The parser is definately not the most effective parser out there, at rundowns on 
a Dual Core 2.6 GhZ computer I have been able to parse about 10000 small 
frames/s. Which in theory might not be effective enough for a populated hub, but
well beyond what is necessary for a client.

The parser only cares about formal grammar as defined in the ADC specification and
is completely uncoupled from context (as is prudent).

The following is an example usage of the parser:

    from adc import ADCParser
    
    try:
        frame = ADCParser.parseString("FART AAAA +TEST");
    except Exception, e:
        print e;

    # handle frame information here

The distribution contains testing code, after installing, run:

    #> python -m adc.parser_tests

To run all available tests, type:

    #> python -m adc.all_tests

If you want to play around with the parser, run:

    #> python -m adc.parser "FART AAAA +ZLIB +BASE"

Note: the command_name 'ART' does not really exist.

CLIENT
---
This package comes with an experimental DC client implemented with a client-server approach.

The idea is that a constant service is running in the background which controls 
the Direct Connect process, and it is administered by connecting to it via one, 
or a set of clients.

To try it out, run the following to start the service:

    #> bin/adc-server <port>

And the following to run the client:

    #> bin/adc-client <host> <port>

The current protocol is just a simple rpc protocol using newlines as delimiters, and by pickling and base64 encoding the following construct:

    frame = {
        'method': "remote_method",
        'argv': ["argument 1"],
        'kw': {'kw1': "value1"}
    };

The result frame has the following format:

    result = {
        'ok': False,
        'error': "Error message describing problem"
        'result': <the return value of the result method>
    }

_A couple of important points to understand before using the client:_

* The Pickle/Base64 approach is very flexible for defining remote protocols, 
but '''extremely''' unsafe. This is an experimental client, DO NOT USE IT 
AGAINST POTENTIALLY UNSAFE CLIENTS, YOUR COMPUTER CAN LITERALLY BE DESTROYED. 
In the future this might be fixed by defining a proper protocol, but in the 
meantime beware, here be dragons.
* There is no authentication, I have no plans to create a multiuser environment 
since I find that unethical against DC common sense. 

ARGUMENT TYPING SUGGESTION FOR ADC 2.0:
---
This is an experimental branch where I've implemented type declaration for each argument passed through the protocol
Try it out by doing the following INF (also see; example-message.py):

    from adc.parser import Message, CIHHeader
    from adc.types import Base32, IP
    
    try:
        print Message(
            CIHHeader(type='C', command_name='INF'),
            I4=IP('10.0.0.1', ipversion=4),
            I6=IP('::ffff', ipversion=6),
            ID=Base32('FOOBARBAZ'),
            PD=Base32('FOOBAR')
        )
    except Exception, e:
        print "bad message parameter: " + str(e)
    
    # -> CINF IP6:I6:::ffff IP4:I4:10.0.0.1 B32:PD:IZHU6QSBKI====== B32:ID:IZHU6QSBKJBECWQ=

ADC Type declarations
---
The following grammar defines the type declaration changes for the ADC protocol:

    separator             ::= ' '
    eol                   ::= #x0a
    simple_alphanum       ::= [A-Z0-9]
    simple_alpha          ::= [A-Z]
    base32_character      ::= simple_alpha | [2-7]
    escape                ::= '\'
    escaped_letter        ::= [^ \#x0a] | escape 's' | escape 'n' | escape escape
    feature_name          ::= simple_alpha simple_alphanum{3}
    encoded_sid           ::= base32_character{4}
    my_sid                ::= encoded_sid
    encoded_cid           ::= base32_character+
    my_cid                ::= encoded_cid
    target_sid            ::= encoded_sid
    command_name          ::= simple_alpha simple_alphanum simple_alphanum
    parameter_value       ::= escaped_letter+
    parameter_type        ::= 'INT' | 'STR' | 'B32' | 'IP4' | 'IP6'
    parameter_name        ::= simple_alpha simple_alphanum
    named_parameter       ::= parameter_type ':' parameter_name (':' parameter_value)?
    b_message_header      ::= 'B' command_name separator my_sid
    cih_message_header    ::= ('C' | 'I' | 'H') command_name
    de_message_header     ::= ('D' | 'E') command_name separator my_sid separator target_sid
    f_message_header      ::= 'F' command_name separator my_sid separator (('+'|'-') feature_name)+
    u_message_header      ::= 'U' command_name separator my_cid
    message_body          ::= (b_message_header | cih_message_header | de_message_header | f_message_header | u_message_header | message_header)
                              (separator positional_parameter)* (separator named_parameter)*
    message               ::= message_body? eol

B32
---
A B32 type message is a base32 encoded string according to [http://tools.ietf.org/html/rfc4648](IETF RFC4648)

INT
---
An INT type message is an integer encoded as a string, matching the following grammar:
    INT                   ::= '1' [0-9]*

STR
---
A string is a raw string taken from the parameter_value, which is encoded as an UTF-8 string

IP4
---
IP4 is a valid IPv4 address

IP6
---
IP6 is a vald IPv6 address
