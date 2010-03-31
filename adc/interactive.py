import code

import factory
import parser

banner="""Python-ADC Interactive Console
avaible modules:
    parser - adc.parser
    factory - factory for creating connections
"""

locals={
    'factory': factory,
    'parser': parser,
};

if __name__ == "__main__":
    import rlcompleter, readline
    readline.parse_and_bind('tab: complete')
    code.interact(banner, raw_input, locals);
