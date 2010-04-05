from parser import *
from adctypes import *

import unittest

class TestParser(unittest.TestCase):
    def test_command_name(self):
        for s in ["AAA", "Z99", "A00", "ZAA"]:
            self.assertEqual(ADCParser.command_name.parseString(s, parseAll=True)["command_name"], s)
    
    def test_feature_name(self):
        for s in ["AAAA", "Z999", "A000", "ZAAA"]:
            self.assertEqual(ADCParser.feature_name.parseString(s, parseAll=True)[0], s)
    
    def test_features_list(self):
        test_s = list();
        test_s += [(" +AAAA -ZAAA", [[ADCParser.FEATURE_ADD, "AAAA"], [ADCParser.FEATURE_REM, "ZAAA"]])];
        test_s += [(" +A000 -Z999", [[ADCParser.FEATURE_ADD, "A000"], ([ADCParser.FEATURE_REM, "Z999"])])];
        test_s += [(" +A000",       [[ADCParser.FEATURE_ADD, "A000"]])];
        test_s += [(" +A000 -Z999 -F000", [[ADCParser.FEATURE_ADD, "A000"], [ADCParser.FEATURE_REM, "Z999"], [ADCParser.FEATURE_REM, "F000"]])];
        
        for s in test_s:
            i = 0;
            for f in ADCParser.feature_list.parseString(s[0], parseAll=True)["feature_list"][:]:
                self.assertEqual(f[:], s[1][i])
                i += 1;
    
    def test_parameter_value(self):
        pass;
        #for s in [("\\s\\n", " \n"), ("This\\sis\\sa\\stest\\nTest", "This is a test\nTest")]:
        #    self.assertEqual(ADCParser.parameter_value.parseString(s[0], parseAll=True)["parameter_value"], s[1])
    
    def test_b_message(self):
        message = ADCParser.parseString("BART AAAA");
        
        self.assertTrue(isinstance(message.header, BHeader));
        self.assertEquals(message.header.command_name, "ART")
        self.assertEquals(message.header.my_sid, "AAAA")
    
    def test_b_w_arguments(self):
        message = ADCParser.parseString("BART AAAA TEfoo\\sbar\\sbaz");
        self.assertTrue(isinstance(message.header, BHeader));
        self.assertEquals(message.header.command_name, "ART")
        self.assertEquals(message.header.my_sid, "AAAA")
        #self.assertEquals(message.params, {'TE': 'foo bar baz'});
    
    def test_f_message(self):
        message = ADCParser.parseString("FART AAAA +T000 -T002");
        self.assertTrue(isinstance(message.header, FHeader));
        self.assertEquals(message.header.command_name, "ART")
        self.assertEquals(message.header.my_sid, "AAAA")
        self.assertEquals(message.header.features, {"+": ["T000"], "-": ["T002"]})
    
    def test_de_message(self):
        message = ADCParser.parseString("DART AAAA BBBB");
        self.assertTrue(isinstance(message.header, DEHeader));
        self.assertEquals(message.header.command_name, "ART")
        self.assertEquals(message.header.my_sid, "AAAA")
        self.assertEquals(message.header.target_sid, "BBBB")
    
    def test_u_message(self):
        message = ADCParser.parseString("UART AAAA");
        self.assertTrue(isinstance(message.header, UHeader));
        self.assertEqual(message.header.my_cid, "AAAA");

class TestMessages(unittest.TestCase):
    def test_b_message(self):
        self.assertEqual(str(Message(header=BHeader(my_sid="AAAA", type='B', command_name='ART'))), "BART AAAA")
    
    def test_f_message(self):
        self.assertEqual(str(Message(header=FHeader(my_sid="AAAA", type='F', command_name='ART', features={'+': ["ZLIB"]}))), "FART AAAA +ZLIB")
    
    def test_argument_message(self):
        self.assertEqual(str(Message(header=BHeader(my_sid="AAAA", type='B', command_name='ART'), TE="TEST")), "BART AAAA TETEST")
        self.assertEqual(str(Message(header=BHeader(my_sid="AAAA", type='B', command_name='ART'), TE=Base32("TEST"))), "BART AAAA TEKRCVGVA")
        self.assertEqual(str(Message(header=CIHHeader(type='C', command_name='INF'), I4=IP('10.0.0.1', ipversion=4), I6=IP('::ffff', ipversion=6), ID=Base32('FOOBARBAZ'), PD=Base32('FOOBAR'))), 
            "CINF I6::ffff I410.0.0.1 PDIZHU6QSBKI IDIZHU6QSBKJBECWQ")

if __name__ == "__main__":
    unittest.main()
