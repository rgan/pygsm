#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

class SmsHandler(object):
	
    def __init__(self,modem):
        self.modem = modem

    def send_sms(self, recipient, text):
        raise Exception("Must use one of concrete subclasses:PduSmsHandler or TextSmsHandler")
	
	def get_mode_cmd(self):
	    raise Exception("Must use one of concrete subclasses:PduSmsHandler or TextSmsHandler")