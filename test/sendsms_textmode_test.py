#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


import unittest
import pygsm
from pygsm import errors
from textmode_test_base import TextModeTestBase

from mockito import *

class SendSmsTextModeTest(TextModeTestBase):
        
    def testSendSmsTextMode(self):
        """Checks that the GsmModem in Text mode accepts outgoing SMS,
           when the text is within ASCII chars 22 - 126."""        

        err = errors.GsmReadTimeoutError(">")
        when(self.mockDevice).read_lines().thenRaise(err).thenReturn(self.oklines)
        self.gsm.send_sms("1234", "Test Message")

        # must see command with recipient
        verify(self.mockDevice, times=1).write("AT+CMGS=\"1234\"\r")
        # must see command with text and terminating char
        verify(self.mockDevice, times=1).write("Test Message\x1a")
        # allow any number of reads
        verify(self.mockDevice, atleast=1).read_lines()
        
        verifyNoMoreInteractions(self.mockDevice)
     
    def testSendSmsTextModeWithHexUTF16Encoding(self):
        """Checks that the GsmModem in Text mode accepts outgoing SMS,
           when the text has Non-ASCII"""
        
        csmp_response_lines = []
        csmp_response_lines.append("+CSMP:1,2,3,4")
        csmp_response_lines.append("OK")
        err = errors.GsmReadTimeoutError(">")
        when(self.mockDevice).read_lines().thenReturn(csmp_response_lines).thenReturn(self.oklines).thenReturn(self.oklines).thenRaise(err).thenReturn(self.oklines)
        self.gsm.send_sms("1234", u'La Pe\xf1a')
        
        verify(self.mockDevice, times=1).write("AT+CSMP?\r")
        verify(self.mockDevice, times=1).write("AT+CSCS=\"HEX\"\r")
        verify(self.mockDevice, times=1).write("AT+CSMP=1,2,3,8\r")
        
        # must see command with recipient
        verify(self.mockDevice, times=1).write("AT+CMGS=\"1234\"\r")
        # must see command with encoded text and terminating char
        verify(self.mockDevice, times=1).write("fffe4c006100200050006500f1006100\x1a")
        # command to set mode back 
        verify(self.mockDevice, times=1).write("AT+CSMP=1,2,3,4\r")
        verify(self.mockDevice, times=1).write("AT+CSCS=\"GSM\"\r")
        # allow any number of reads
        verify(self.mockDevice, atleast=1).read_lines()
        verifyNoMoreInteractions(self.mockDevice)