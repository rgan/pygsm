#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


import unittest
import pygsm
from pygsm import errors

from mockito import *

class ReadSmsPduModeTest(unittest.TestCase):
    
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
        # sms messages can be returned with any command
        self.gsm.command("ATE0") 
        # verify that command is issued for read receipt
        verify(self.mockDevice, times=1).write("AT+CNMA\r")
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
        lines.append("07912180958729F6040B814151733717F500009070102230438A02D937")
        when(self.mockDevice).read_lines().thenReturn(lines)
        pdu = self.gsm.next_message()
        self.assertEquals("Yo", pdu.text);
        self.assertEquals("14153773715", pdu.sender);

    def testShouldHandleMultipartCSMPdus(self):
        lines = []
        lines.append("+CMGL:")
        lines.append("0791448720003023440C91449703529096000050015132532240A00500037A020190E9339A9D3EA3E920FA1B1466B341E472193E079DD3EE73D85DA7EB41E7B41C1407C1CBF43228CC26E3416137390F3AABCFEAB3FAAC3EABCFEAB3FAAC3EABCFEAB3FAAC3EABCFEAB3FADC3EB7CFED73FBDC3EBF5D4416D9457411596457137D87B7E16438194E86BBCF6D16D9055D429548A28BE822BA882E6370196C2A8950E291E822BA88")
        lines.append("0791448720003023440C91449703529096000050015132537240310500037A02025C4417D1D52422894EE5B17824BA8EC423F1483C129BC725315464118FCDE011247C4A8B44")
        when(self.mockDevice).read_lines().thenReturn(lines)
        pdu = self.gsm.next_message()
        self.assertEquals("Highlight to all deeps ginganutz gir q pete aldx andy gjgjgjgjgjgjgjgjgjgjgjgjgjgjgjgmgmgmgmgmgo.D,d.D.D,d.Mhwpmpdpdpdpngm,d.PKPJHD.D.D.D.FAKAMJDPDGD.D.D.D.D.MDHDNJGEGD.GDGDGDGDMGKD!E,DGMAG BORED", pdu.text);
        
    def testShouldNotCreateMessageIfAllPartsOfCsmPduAreNotReceived(self):
        lines = []
        lines.append("+CMGL:")
        lines.append("07912180958729F6400B814151733717F500009070208044148AA0050003160201986FF719C47EBBCF20F6DB7D06B1DFEE3388FD769F41ECB7FB0C62BFDD6710FBED3E83D8ECB73B0D62BFDD67109BFD76A741613719C47EBBCF20F6DB7D06BCF61BC466BF41ECF719C47EBBCF20F6D")
        when(self.mockDevice).read_lines().thenReturn(lines)
        pdu = self.gsm.next_message()
        self.assertEquals(None, pdu)