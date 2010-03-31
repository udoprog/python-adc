from adc.parser import Message, CIHHeader, ADCParser
from adc.types import Base32, IP

m1 = Message(
    CIHHeader(type='C', command_name='INF'),
    I4=IP('10.0.0.1', ipversion=4),
    I6=IP('::ffff', ipversion=6),
    ID=Base32('FOOBARBAZ'),
    PD=Base32('FOOBAR')
)

m2 = ADCParser.parseString(str(m1));

print repr(m2.decode('I4', ADCParser.TYPE_IP4));
print repr(m2.decode('PD', ADCParser.TYPE_B32, 16));
print repr(m2.decode('ID', ADCParser.TYPE_B32, 16));

# -> CINF IP6:I6:::ffff IP4:I4:10.0.0.1 B32:PD:IZHU6QSBKI====== B32:ID:IZHU6QSBKJBECWQ=
