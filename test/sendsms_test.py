#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


import unittest
import pygsm
from pygsm import errors

from mockito import *

class SendSmsTest(unittest.TestCase):

    def testSendSmsTextMode(self):
        """Checks that the GsmModem in Text mode accepts outgoing SMS,
           when the text is within ASCII chars 22 - 126."""

        # stub DeviceWrapper
        mockDevice = Mock()
        lines = []
        lines.append("OK\r\n")
        when(mockDevice).read_lines().thenReturn(lines)
        
        gsm = pygsm.GsmModem(device=mockDevice, mode="TEXT")
        # must see command to set TEXT mode
        verify(mockDevice,times=1).write("AT+CMGF=1\r")
        
        err = errors.GsmReadTimeoutError(">")
        when(mockDevice).read_lines().thenRaise(err)
        gsm.send_sms("1234", "Test Message")
       
        # must see command with recipient
        verify(mockDevice, times=1).write("AT+CMGS=\"1234\"\r")
        # must see command with text and terminating char
        verify(mockDevice, times=1).write("Test Message\x1a")
     
    def testSendSmsTextModeWithHexUTF16Encoding(self):
        """Checks that the GsmModem in Text mode accepts outgoing SMS,
           when the text has Non-ASCII"""

        # stub DeviceWrapper
        mockDevice = Mock()
        lines = []
        lines.append("OK\r\n")
        when(mockDevice).read_lines().thenReturn(lines)
        
        gsm = pygsm.GsmModem(device=mockDevice, mode="TEXT")
        # must see command to set TEXT mode
        verify(mockDevice,times=1).write("AT+CMGF=1\r")
        
        csmp_response_lines = []
        csmp_response_lines.append("+CSMP:1,2,3,4")
        csmp_response_lines.append("OK")
        err = errors.GsmReadTimeoutError(">")
        when(mockDevice).read_lines().thenReturn(csmp_response_lines).thenReturn(lines).thenReturn(lines).thenRaise(err).thenReturn(lines)
        gsm.send_sms("1234", u'La Pe\xf1a')
        
        verify(mockDevice, times=1).write("AT+CSMP?\r")
        verify(mockDevice, times=1).write("AT+CSCS=\"HEX\"\r")
        verify(mockDevice, times=1).write("AT+CSMP=1,2,3,8\r")
        
        # must see command with recipient
        verify(mockDevice, times=1).write("AT+CMGS=\"1234\"\r")
        # must see command with encoded text and terminating char
        verify(mockDevice, times=1).write("fffe4c006100200050006500f1006100\x1a")
        # command to set mode back 
        verify(mockDevice, times=1).write("AT+CSMP=1,2,3,4\r")
        verify(mockDevice, times=1).write("AT+CSCS=\"GSM\"\r")
           
    def testSendSmsPduMode(self):
        """Checks that the GsmModem in PDU mode accepts outgoing SMS,
           when the text is within ASCII chars 22 - 126."""

        # stub DeviceWrapper
        mockDevice = Mock()
        lines = []
        lines.append("OK\r\n")
        when(mockDevice).read_lines().thenReturn(lines)
        
        gsm = pygsm.GsmModem(device=mockDevice, mode="PDU")
        # must see command to set PDU mode
        verify(mockDevice, times=1).write("AT+CMGF=0\r")
        
        # setup expectation to raise a timeout error with prompt
        err = errors.GsmReadTimeoutError(">")
        when(mockDevice).read_lines().thenRaise(err)
        gsm.send_sms("1234", "Test Message")
       
        # must see command with size
        verify(mockDevice, times=1).write("AT+CMGS=21\r")
        # must see command with text and terminating char
        verify(mockDevice, times=1).write("00110004A821430000AA0CD4F29C0E6A96E7F3F0B90C\x1a")
        
    def testSendSmsPduModeError(self):
        """Checks that the GsmModem in PDU mode does not send message if error,
        when the text is within ASCII chars 22 - 126."""

        # stub DeviceWrapper
        mockDevice = Mock()
        lines = []
        lines.append("OK\r\n")
        when(mockDevice).read_lines().thenReturn(lines)
        
        gsm = pygsm.GsmModem(device=mockDevice, mode="PDU")
        # must see command to set PDU mode
        verify(mockDevice, times=1).write("AT+CMGF=0\r")
        
        # setup expectation to raise a non-timeout error with prompt
        when(mockDevice).read_lines().thenRaise(Exception("something other than timeout"))
        gsm.send_sms("1234", "Test Message")
       
        # must see command with size
        verify(mockDevice, times=1).write("AT+CMGS=21\r")
        # must NOT see command with text and terminating char
        verify(mockDevice, times=0).write("00110004A821430000AA0CD4F29C0E6A96E7F3F0B90C\x1a")