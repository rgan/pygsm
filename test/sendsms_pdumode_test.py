#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


import unittest
import pygsm
from pygsm import errors

from mockito import *

class SendSmsPduModeTest(unittest.TestCase):
    
    def setUp(self):
        self.mockDevice = Mock()
        self.oklines = []
        self.oklines.append("OK\r\n")
        when(self.mockDevice).read_lines().thenReturn(self.oklines)
        self.gsm = pygsm.GsmModem(device=self.mockDevice, mode="PDU")
        # verify the config commands
        verify(self.mockDevice,times=1).write("ATE0\r")
        verify(self.mockDevice,times=1).write("AT+CMEE=1\r")
        verify(self.mockDevice,times=1).write("AT+WIND=0\r")
        verify(self.mockDevice,times=1).write("AT+CSMS=1\r")
        
        # must see command to set PDU mode
        verify(self.mockDevice,times=1).write("AT+CMGF=0\r")
        
        verify(self.mockDevice, times=1).write("AT+CNMI=2,2,0,0,0\r")
        # verify fetch_stored_messages in boot
        verify(self.mockDevice,times=1).write("AT+CMGL=0\r")
        
    def testSendSmsPduMode(self):
        """Checks that the GsmModem in PDU mode accepts outgoing SMS,
           when the text is within ASCII chars 22 - 126."""
        
        # setup expectation to raise a timeout error with prompt
        err = errors.GsmReadTimeoutError(">")
        when(self.mockDevice).read_lines().thenRaise(err).thenReturn(self.oklines)
        self.gsm.send_sms("1234", "Test Message")
       
        # must see command with size
        verify(self.mockDevice, times=1).write("AT+CMGS=21\r")
        # must see command with text and terminating char
        verify(self.mockDevice, times=1).write("00110004A821430000AA0CD4F29C0E6A96E7F3F0B90C\x1a")
        # allow any number of reads
        verify(self.mockDevice, atleast=1).read_lines()
        verifyNoMoreInteractions(self.mockDevice)
         
    def testSendSmsPduModeError(self):
        """Checks that the GsmModem in PDU mode does not send message if error,
        when the text is within ASCII chars 22 - 126."""

        # setup expectation to raise a non-timeout error with prompt
        when(self.mockDevice).read_lines().thenRaise(Exception("something other than timeout"))
        self.gsm.send_sms("1234", "Test Message")
       
        # must see command with size
        verify(self.mockDevice, times=1).write("AT+CMGS=21\r")
        # must see command to break out of command prompt
        verify(self.mockDevice, times=1).write("\x1b")
        # must NOT see command with text and terminating char
        verify(self.mockDevice, times=0).write("00110004A821430000AA0CD4F29C0E6A96E7F3F0B90C\x1a")
        # allow any number of reads
        verify(self.mockDevice, atleast=1).read_lines()
        verifyNoMoreInteractions(self.mockDevice)