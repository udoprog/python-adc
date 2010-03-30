This is suppose to be a complete implementation for the Advanced Direct Connect protocol.

The parts marked with a plus (+) have been implemented, the minus parts are TODO:

    + Protocol Parser
    - Client Logic
    - Transport (TCP/UDP/TLS)

===Parser===
The parser probably is not the most effective parser out there, at rundowns on 
a Dual Core 2.6 GhZ computer, I have been able to parse about 10000 small 
frames/s. Which roughly translates to well beyond what is necessary for 
effective communication.

The following is an example usage of the parser:

    from adc import ADCParser
    import sys

    try:
        frame = ADCParser.parseString("FART AAAA +TEST\n");
    except Exception, e:
        print e;
        sys.exit(0);

    print repr(frame.header)        # -> <adc.parser.ADC_FMessageHeader instance at 0xXXXXXXXX>
    print frame.header.command_name # -> ART
    print frame.header.my_sid       # -> AAAA
    print frame.header.features     # -> {'+': ["test"], '-': []}

The distribution contains testing code, after installing, run:

    python -m adc.parser_tests

To run all available tests, type:

    python -m adc.all_tests

Congratulations
