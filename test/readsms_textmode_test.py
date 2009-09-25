#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


import unittest
import pygsm
import datetime
from pygsm import errors

from mockito import *

class ReadSmsTextModeTest(unittest.TestCase):
    
    def setUp(self):
        self.mockDevice = Mock()
        lines = []
        lines.append("OK\r\n")
        when(self.mockDevice).read_lines().thenReturn(lines)
        self.gsm = pygsm.GsmModem(device=self.mockDevice, mode="TEXT")
    
    def testShouldReturnStoredMessage(self):
        lines = []
        lines.append("+CMGL: 1,\"status\",\"14153773715\",,\"09/09/11,10:10:10\"")
        # it does not matter what this is since we mock the parsing
        lines.append("Yo")
        when(self.mockDevice).read_lines().thenReturn(lines)
        pdu = self.gsm.next_message()
        self.assertEquals("Yo", pdu.text);
        self.assertEquals("14153773715", pdu.sender)
        self.assertEquals(datetime.datetime(2009, 9, 11, 10, 10, 10), pdu.sent)

    def testShouldParseIncomingSms(self):
        lines = []
        lines.append("+CMT: \"14153773715\",,\"09/09/11,10:10:10\"")
        lines.append("Yo")
        ok_lines = []
        ok_lines.append("OK\r\n")
        when(self.mockDevice).read_lines().thenReturn(lines).thenReturn(ok_lines)
        # sms messages can be returned with any command
        self.gsm.command("ATE0")
        # verify that command is issued for read receipt
        verify(self.mockDevice, times=1).write("AT+CNMA\r")
        pdu = self.gsm.incoming_queue.pop(0)
        self.assertEquals("Yo", pdu.text);
        self.assertEquals("14153773715", pdu.sender);
        self.assertEquals(datetime.datetime(2009, 9, 11, 10, 10, 10), pdu.sent);
     
    def testShouldParseIncomingSmsWithMangledHeader(self):
        lines = []
        lines.append("+CMT: \"14153773715\",")
        lines.append("Yo")
        ok_lines = []
        ok_lines.append("OK\r\n")
        when(self.mockDevice).read_lines().thenReturn(lines).thenReturn(ok_lines)
        # sms messages can be returned with any command
        self.gsm.command("ATE0")
        # verify that command is issued for read receipt
        verify(self.mockDevice, times=1).write("AT+CNMA\r")
        pdu = self.gsm.incoming_queue.pop(0)
        self.assertEquals("Yo", pdu.text);
        self.assertEquals("", pdu.sender);
        self.assertEquals(None, pdu.sent);
  
    def testShouldParseIncomingMultipartSms(self):
        lines = []
        header = "+CMT: \"14153773715\",,\"09/09/11,10:10:10\""
         # first part of multi-part msg
        lines.append(header)
        lines.append(chr(130) + "@" + "ignorfirstpartofmultipart")
         # second part of multi-part msg
        lines.append(header)
        lines.append(chr(130) + "@" + "345" + chr(173) + "7secondpartofmultipart")
        ok_lines = []
        ok_lines.append("OK\r\n")
        when(self.mockDevice).read_lines().thenReturn(lines).thenReturn(ok_lines)
        # sms messages can be returned with any command
        self.gsm.command("ATE0")
        # verify that command is issued for read receipt
        verify(self.mockDevice, times=2).write("AT+CNMA\r")
        pdu = self.gsm.incoming_queue.pop(0)
        self.assertEquals("firstpartofmultipartsecondpartofmultipart", pdu.text);
        self.assertEquals("14153773715", pdu.sender);
        self.assertEquals(datetime.datetime(2009, 9, 11, 10, 10, 10), pdu.sent);