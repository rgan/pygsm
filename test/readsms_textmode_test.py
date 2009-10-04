#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


import unittest
import pygsm
import datetime
from pygsm import errors
from textmode_test_base import TextModeTestBase

from mockito import *

class ReadSmsTextModeTest(TextModeTestBase):
       
    def testShouldReturnStoredMessage(self):
        lines = []
        lines.append("+CMGL: 1,\"status\",\"14153773715\",,\"09/09/11,10:10:10\"")
        lines.append("Yo")
        when(self.mockDevice).read_lines().thenReturn(lines)
        msg = self.gsm.next_message(ping=False)
        self.assertEquals("Yo", msg.text);
        self.assertEquals("14153773715", msg.sender)
        self.assertEquals(datetime.datetime(2009, 9, 11, 10, 10, 10), msg.sent)
        # verify command to fetch_stored_messages
        verify(self.mockDevice,times=2).write("AT+CMGL=\"REC UNREAD\"\r")
        # allow any number of reads
        verify(self.mockDevice, atleast=1).read_lines()
        
        verifyNoMoreInteractions(self.mockDevice)

    def testShouldReturnHexUTF16EncodedStoredMessage(self):
        lines = []
        lines.append("+CMGL: 1,\"status\",\"14153773715\",,\"09/09/11,10:10:10\"")
        lines.append("Yo".encode("utf-16").encode("hex"))
        when(self.mockDevice).read_lines().thenReturn(lines)
        msg = self.gsm.next_message(ping=False)
        self.assertEquals("Yo", msg.text);
        self.assertEquals("14153773715", msg.sender)
        self.assertEquals(datetime.datetime(2009, 9, 11, 10, 10, 10), msg.sent)
        # verify command to fetch_stored_messages
        verify(self.mockDevice,times=2).write("AT+CMGL=\"REC UNREAD\"\r")
        # allow any number of reads
        verify(self.mockDevice, atleast=1).read_lines()
        
        verifyNoMoreInteractions(self.mockDevice)

    def testShouldParseIncomingSms(self):
        lines = []
        lines.append("+CMT: \"14153773715\",,\"09/09/11,10:10:10\"")
        lines.append("Yo")
        ok_lines = []
        ok_lines.append("OK\r\n")
        when(self.mockDevice).read_lines().thenReturn(lines).thenReturn(ok_lines)
        msg = self.gsm.next_message(ping=True,fetch=False)        
        self.assertEquals("Yo", msg.text);
        self.assertEquals("14153773715", msg.sender);
        self.assertEquals(datetime.datetime(2009, 9, 11, 10, 10, 10), msg.sent);
        # verify that ping command AT is issued
        verify(self.mockDevice, times=1).write("AT\r")
        # verify that command is issued for read receipt
        verify(self.mockDevice, times=1).write("AT+CNMA\r")
        # allow any number of reads
        verify(self.mockDevice, atleast=1).read_lines()
        
        verifyNoMoreInteractions(self.mockDevice)
     
    def testShouldParseIncomingSmsWithMangledHeader(self):
        lines = []
        lines.append("+CMT: \"14153773715\",")
        lines.append("Yo")
        ok_lines = []
        ok_lines.append("OK\r\n")
        when(self.mockDevice).read_lines().thenReturn(lines).thenReturn(ok_lines)
        msg = self.gsm.next_message(ping=True,fetch=False) 
        # verify that ping command AT is issued
        verify(self.mockDevice, times=1).write("AT\r")   
        # verify that command is issued for read receipt
        verify(self.mockDevice, times=1).write("AT+CNMA\r")
        self.assertEquals("Yo", msg.text);
        self.assertEquals("", msg.sender);
        self.assertEquals(None, msg.sent);
        # allow any number of reads
        verify(self.mockDevice, atleast=1).read_lines()
        
        verifyNoMoreInteractions(self.mockDevice)
  
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
        msg = self.gsm.next_message(ping=True,fetch=False)
        # verify that ping command AT is issued
        verify(self.mockDevice, times=1).write("AT\r")   
        # verify that command is issued for read receipt
        verify(self.mockDevice, times=2).write("AT+CNMA\r")
        self.assertEquals("firstpartofmultipartsecondpartofmultipart", msg.text);
        self.assertEquals("14153773715", msg.sender);
        self.assertEquals(datetime.datetime(2009, 9, 11, 10, 10, 10), msg.sent);
        # allow any number of reads
        verify(self.mockDevice, atleast=1).read_lines()
        
        verifyNoMoreInteractions(self.mockDevice)