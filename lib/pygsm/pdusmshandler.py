#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import gsmpdu
import traceback
import errors
from smshandler import SmsHandler

MAX_MESSAGES=255

class PduSmsHandler(SmsHandler):
    def __init__(self,modem):
        SmsHandler.__init__(self, modem)
    
    def get_mode_cmd(self):
        return "AT+CMGF=0"

    def send_sms(self, recipient, text):
        pdus = gsmpdu.get_outbound_pdus(text, recipient)
        if len(pdus) > MAX_MESSAGES:
            raise ValueError(
                'Max_message is %d and text requires %d messages' %
                (MAX_MESSAGES, len(pdus))
                )

        for pdu in pdus:
		    self._send_pdu(pdu)
		    
    def _send_pdu(self, pdu):
        # outer try to catch any error and make sure to
        # get the modem out of 'waiting for data' mode
		try:
            # accesing the property causes the pdu_string
			# to be generated, so do once and cache
			pdu_string = pdu.pdu_string

			# try to catch write timeouts
			try:
				# content length is in bytes, so half PDU minus
				# the first blank '00' byte
				result = self.modem.command( 
				'AT+CMGS=%d' % (len(pdu_string)/2 - 1), 
				read_timeout=1
				)

				# if no error is raised within the timeout period,
				# and the text-mode prompt WAS received, send the
				# sms text, wait until it is accepted or rejected
				# (text-mode messages are terminated with ascii char 26
				# "SUBSTITUTE" (ctrl+z)), and return True (message sent)
			except errors.GsmReadTimeoutError, err:
				if err.pending_data[0] == ">":
					self.modem.command(pdu_string, write_term=chr(26))
					return True

					# a timeout was raised, but no prompt nor
					# error was received. i have no idea what
					# is going on, so allow the error to propagate
				else:
					raise

			finally:
				pass

		# for all other errors...
		# (likely CMS or CME from device)
		except Exception:
			traceback.print_exc()
			# whatever went wrong, break out of the
			# message prompt. if this is missed, all
			# subsequent writes will go into the message!
			self.modem.break_out_of_prompt()

			# rule of thumb: pyGSM is meant to be embedded,
			# so DO NOT EVER allow exceptions to propagate
			# (obviously, this sucks. there should be an
			# option, at least, but i'm being cautious)
			return None
