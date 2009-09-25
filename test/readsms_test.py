#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


import unittest
import pygsm
from pygsm import errors

from mockito import *

class ReadSmsTest(unittest.TestCase):
    
    def setUp(self):
        self.mockDevice = Mock()
        lines = []
        lines.append("OK\r\n")
        when(self.mockDevice).read_lines().thenReturn(lines)
        self.gsm = pygsm.GsmModem(device=self.mockDevice, mode="PDU")
    
    def testShouldParseIncomingSms(self):
        lines = []
        lines.append("+CMT:")
        lines.append("07912180958729F6040B814151733717F500009070102230438A02D937")
        ok_lines = []
        ok_lines.append("OK\r\n")
        when(self.mockDevice).read_lines().thenReturn(lines).thenReturn(ok_lines)
        self.gsm.command("ATE0") # sms messages can be returned with any command
        pdu = self.gsm.incoming_queue.pop(0)
        self.assertEquals("Yo", pdu.text);
        self.assertEquals("14153773715", pdu.sender);
           
    def testShouldReturnEmptyIfNoStoredMessages(self):
        lines = []
        lines.append("+CMGL:")
        when(self.mockDevice).read_lines().thenReturn(lines)
        self.assertEquals(None, self.gsm.next_message());
        
    def testShouldReturnStoredMessage(self):
        lines = []
        lines.append("+CMGL:")
        # it does not matter what this is since we mock the parsing
        lines.append("07912180958729F6040B814151733717F500009070102230438A02D937")
        when(self.mockDevice).read_lines().thenReturn(lines)
        pdu = self.gsm.next_message()
        self.assertEquals("Yo", pdu.text);
        self.assertEquals("14153773715", pdu.sender);

    def xtestShouldReturnStoredMessageForCsmPdu(self): #currently failing the process csm returns NONE
        lines = []
        lines.append("+CMGL:")
        # it does not matter what this is since we mock the parsing
        lines.append("07912180958729F6400B814151733717F500009070208044148AA0050003160201986FF719C47EBBCF20F6DB7D06B1DFEE3388FD769F41ECB7FB0C62BFDD6710FBED3E83D8ECB73B0D62BFDD67109BFD76A741613719C47EBBCF20F6DB7D06BCF61BC466BF41ECF719C47EBBCF20F6D")
        when(self.mockDevice).read_lines().thenReturn(lines)
        pdu = self.gsm.next_message()
        self.assertEquals("Yo", pdu.text);
        self.assertEquals("14153773715", pdu.sender);