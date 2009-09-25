#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import errors
from smshandler import SmsHandler

class TextSmsHandler(SmsHandler):
    
    def __init__(self, modem):
        SmsHandler.__init__(self, modem)
    
    def get_mode_cmd(self):
        return "AT+CMGF=1"
	    
    def send_sms(self, recipient, text):
        """Sends an SMS to _recipient_ containing _text_. Some networks
           will automatically chunk long messages into multiple parts,
           and reassembled them upon delivery, but some will silently
           drop them. At the moment, pyGSM does nothing to avoid this,
           so try to keep _text_ under 160 characters."""

        old_mode = None
        try:
            try:
                # cast the text to a string, to check that
                # it doesn't contain non-ascii characters
                try:
                    text = str(text)

                # uh-oh. unicode ahoy
                except UnicodeEncodeError:

                    # fetch and store the current mode (so we can
                    # restore it later), and override it with UCS2
                    csmp = self.modem.query("AT+CSMP?", "+CSMP:")
                    if csmp is not None:
                        old_mode = csmp.split(",")
                        mode = old_mode[:]
                        mode[3] = "8"

                        # enable hex mode, and set the encoding
                        # to UCS2 for the full character set
                        self.modem.command('AT+CSCS="HEX"')
                        self.modem.command("AT+CSMP=%s" % ",".join(mode))
                        text = text.encode("utf-16").encode("hex")

                # initiate the sms, and give the device a second
                # to raise an error. unfortunately, we can't just
                # wait for the "> " prompt, because some modems
                # will echo it FOLLOWED BY a CMS error
                result = self.modem.command(
                        'AT+CMGS=\"%s\"' % (recipient),
                        read_timeout=1)

            # if no error is raised within the timeout period,
            # and the text-mode prompt WAS received, send the
            # sms text, wait until it is accepted or rejected
            # (text-mode messages are terminated with ascii char 26
            # "SUBSTITUTE" (ctrl+z)), and return True (message sent)
            except errors.GsmReadTimeoutError, err:
                if err.pending_data[0] == ">":
                    self.modem.command(text, write_term=chr(26))
                    return True

                # a timeout was raised, but no prompt nor
                # error was received. i have no idea what
                # is going on, so allow the error to propagate
                else:
                    raise

        # for all other errors...
        # (likely CMS or CME from device)
        except Exception, err:
                
            # whatever went wrong, break out of the
            # message prompt. if this is missed, all
            # subsequent writes will go into the message!
            self.modem.break_out_of_prompt()

            # rule of thumb: pyGSM is meant to be embedded,
            # so DO NOT EVER allow exceptions to propagate
            # (obviously, this sucks. there should be an
            # option, at least, but i'm being cautious)
            return None

        finally:

            # if the mode was overridden above, (if this
            # message contained unicode), switch it back
            if old_mode is not None:
                self.modem.command("AT+CSMP=%s" % ",".join(old_mode))
                self.modem.command('AT+CSCS="GSM"')

	# returns a list of messages
    def parse_stored_messages(self, lines):
	    return [] # TODO

    # returns a single message   
    def parse_incoming_message(self, line):
        return None # TODO
