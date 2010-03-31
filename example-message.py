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
