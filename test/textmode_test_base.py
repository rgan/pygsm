#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


import unittest
import pygsm

from mockito import *

class TextModeTestBase(unittest.TestCase):

    def setUp(self):
        self.mockDevice = Mock()
        self.oklines = []
        self.oklines.append("OK\r\n")
        when(self.mockDevice).read_lines().thenReturn(self.oklines)
        self.gsm = pygsm.GsmModem(device=self.mockDevice, mode="TEXT")
        # verify the config commands
        verify(self.mockDevice,times=1).write("ATE0\r")
        verify(self.mockDevice,times=1).write("AT+CMEE=1\r")
        verify(self.mockDevice,times=1).write("AT+WIND=0\r")
        verify(self.mockDevice,times=1).write("AT+CSMS=1\r")
        
        # must see command to set TEXT mode
        verify(self.mockDevice,times=1).write("AT+CMGF=1\r")
        verify(self.mockDevice, times=1).write("AT+CNMI=2,2,0,0,0\r")
        # verify fetch_stored_messages in boot
        verify(self.mockDevice,times=1).write("AT+CMGL=REC UNREAD\r")