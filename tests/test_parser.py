from adc.arguments import *
from adc.parser import *
from adc.message import *

import adc.parser as parser

import unittest

class TestParser(unittest.TestCase):
    def test_command_name(self):
        for s in ["AAA", "Z99", "A00", "ZAA"]:
            self.assertEqual(parser.command_name.parseString(s, parseAll=True)["command_name"], s)
    
    def test_feature_name(self):
        for s in ["AAAA", "Z999", "A000", "ZAAA"]:
            self.assertEqual(parser.feature_name.parseString(s, parseAll=True)[0], s)
    
    def test_features_list(self):
        test_s = list();
        test_s += [(" +AAAA -ZAAA", [[FEATURE_ADD, "AAAA"], [FEATURE_REM, "ZAAA"]])];
        test_s += [(" +A000 -Z999", [[FEATURE_ADD, "A000"], ([FEATURE_REM, "Z999"])])];
        test_s += [(" +A000",       [[FEATURE_ADD, "A000"]])];
        test_s += [(" +A000 -Z999 -F000", [[FEATURE_ADD, "A000"], [FEATURE_REM, "Z999"], [FEATURE_REM, "F000"]])];
        
        for s in test_s:
            i = 0;
            for f in parser.feature_list.parseString(s[0], parseAll=True)["feature_list"][:]:
                self.assertEqual(f[:], s[1][i])
                i += 1;
    
    def test_parameter_value(self):
        pass;
        #for s in [("\\s\\n", " \n"), ("This\\sis\\sa\\stest\\nTest", "This is a test\nTest")]:
        #    self.assertEqual(parser.parameter_value.parseFrame(s[0], parseAll=True)["parameter_value"], s[1])
    
    def test_b_message(self):
        message = Message.parse("BART AAAA");
        
        self.assertTrue(isinstance(message.header, Broadcast));
        self.assertEquals(message.header.cmd, "ART")
        self.assertEquals(message.header.my_sid, "AAAA")
    
    def test_b_w_arguments(self):
        message = Message.parse("BART AAAA TEfoo\\sbar\\sbaz");
        self.assertTrue(isinstance(message.header, Broadcast));
        self.assertEquals(message.header.cmd, "ART")
        self.assertEquals(message.header.my_sid, "AAAA")
        #self.assertEquals(message.params, {'TE': 'foo bar baz'});
    
    def test_f_message(self):
        message = Message.parse("FART AAAA +T000 -T002");
        self.assertTrue(isinstance(message.header, Feature));
        self.assertEquals(message.header.cmd, "ART")
        self.assertEquals(message.header.my_sid, "AAAA")
        self.assertEquals(message.header.add, ["T000"]);
        self.assertEquals(message.header.rem, ["T002"]);
    
    def test_de_message(self):
        message = Message.parse("DART AAAA BBBB");
        self.assertTrue(isinstance(message.header, Direct));
        self.assertEquals(message.header.cmd, "ART")
        self.assertEquals(message.header.my_sid, "AAAA")
        self.assertEquals(message.header.target_sid, "BBBB")
    
    def test_u_message(self):
        message = Message.parse("UART AAAA");
        self.assertTrue(isinstance(message.header, UDP));
        self.assertEqual(message.header.my_cid, "AAAA");

class TestMessages(unittest.TestCase):
    def test_b_message(self):
        self.assertEqual(str(Message(Broadcast(my_sid="AAAA", cmd='ART'))), "BART AAAA")
    
    def test_f_message(self):
        self.assertEqual(str(Message(Feature(my_sid="AAAA", cmd='ART', add="ZLIB"))), "FART AAAA +ZLIB")
    
    def test_argument_message(self):
        self.assertEqual(str(Message(Broadcast(my_sid="AAAA", cmd='ART'), TE="TEST")), "BART AAAA TETEST")
        self.assertEqual(str(Message(Broadcast(my_sid="AAAA", cmd='ART'), TE=encode(Base32("TEST")))), "BART AAAA TEKRCVGVA")
        self.assertEqual(str(Message(Client(cmd='INF'), I4=encode(IP('10.0.0.1', ipversion=4)), I6=encode(IP('::ffff', ipversion=6)), ID=encode(Base32('FOOBARBAZ')), PD=encode(Base32('FOOBAR')))), 
            "CINF I6::ffff I410.0.0.1 PDIZHU6QSBKI IDIZHU6QSBKJBECWQ")

if __name__ == "__main__":
    unittest.main()
