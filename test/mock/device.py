#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


import time, re
from pygsm import errors

class MockDevice(object):

    print_traffic = False
    read_interval = 0.1
    mode = "PDU" # or TEXT
    echo = True


    def __init__(self):
        self.buf_read = []
        self.buf_write = []
        self.timeout = None


    def _debug(self, str):
        """If self.print_traffic is True, prints
           _str_ to STDOUT. Otherwise, does nothing."""

        if self.print_traffic:
            print str


    def read(self, size=1):
        """Reads and returns _size_ characters from the read buffer, which
           represents the output of the "serial port" of this "modem". This
           method is a very rough port of Serial.write. If the self.timeout
           attribute is set, this method may time out and return only as many
           characters as possible -- just like a modem."""

        waited = 0
        read = ""

        # keep on reading until we have _size_
        # number of characters/bytes
        while len(read) < size:
            if len(self.buf_read):
                read += self.buf_read.pop(0)

            else:
                # there's no data in the buffer. if we've
                # been waiting longer than self.timeout,
                # just return what we have
                if self.timeout and waited > self.timeout:
                    self._debug("TIMEOUT (%d)" % self.timeout)
                    break

                # otherwise, wait for a short while
                # before trying the buffer again
                time.sleep(self.read_interval)
                waited += self.read_interval

        self._debug("READ (%d): %r" % (size, read))
        return read

    def _read(self, read_timeout=None):
        """Read from the modem (blocking) until _terminator_ is hit,
           (defaults to \r\n, which reads a single "line"), and return."""
        
        buffer = []
        read_term = "\r\n"
        self.timeout = read_timeout
        while(True):
            buf = self.read()
            buffer.append(buf)			
            # if a timeout was hit, raise an exception including the raw data that
            # we've already read (in case the calling func was _expecting_ a timeout
            # (wouldn't it be nice if serial.Serial.read returned None for this?)
            if buf == '':
                raise(errors.GsmReadTimeoutError(buffer))

            # if last n characters of the buffer match the read
            # terminator, return what we've received so far
            if ''.join(buffer[-len(read_term):]) == read_term:
                buf_str = ''.join(buffer)
                print 'Read ' + buf_str
                return buf_str

    def read_lines(self, read_term=None, read_timeout=None):
        """Read from the modem (blocking) one line at a time until a response
           terminator ("OK", "ERROR", or "CMx ERROR...") is hit, then return
           a list containing the lines."""
        buffer = []

        # keep on looping until a command terminator
        # is encountered. these are NOT the same as the
        # "read_term" argument - only OK or ERROR is valid
        while(True):
            buf = self._read(read_timeout)

            buf = buf.strip()
            buffer.append(buf)

            # most commands return OK for success, but there
            # are some exceptions. we're not checking those
            # here (unlike RubyGSM), because they should be
            # handled when they're _expected_
            if buf == "OK":
                return buffer

            # some errors contain useful error codes, so raise a
            # proper error with a description from pygsm/errors.py
            m = re.match(r"^\+(CM[ES]) ERROR: (\d+)$", buf)
            if m is not None:
                type, code = m.groups()
                raise(errors.GsmModemError(type, int(code)))

            # ...some errors are not so useful
            # (at+cmee=1 should enable error codes)
            if buf == "ERROR":
                raise(errors.GsmModemError)

    def write(self, str):
        """Appends _str_ to the write buffer, which represents input to this "modem".
           If _str_ ends with a GSM command terminator (\r), the contents of the write
           buffer are passed on to self._process."""

        self._debug("WRITE: %r" % (str))

        # push each character
        # to the write buffer
        for char in str:
            self.buf_write.append(char)

            # if character echo is currently ON, also
            # push this character back to read buffer
            if self.echo:
                self.buf_read.append(char)

        # if the last character is a terminator, process
        # the current contents of the buffer, and clear it.
        # TODO: this doesn't work if "AT\rAT\rAT\r" if passed.
        if self.buf_write[-1] == "\r":
            self._process("".join(self.buf_write))
            self.buf_write = []

        return True


    def _process(self, cmd):
        """Receives a command, and passes it on to self.process, which should be defined
           by subclasses to respond to the command(s) which their testcase is interested
           in, and return True or False when done. If the call succeeds, this method will
           call self._ok -- otherwise, calls self._error."""

        self._debug("CMD: %r" % (cmd))

        def _respond(out):
            """Given the output from a command-handling function,
               injects a status line into the read buffer, to avoid
               repeating it in every handler."""
            
            # boolean values result in OK or ERROR
            # being injected into the read buffer
            if   out == True:  return self._ok()
            elif out == False: return self._error()

            # for any other return value, leave the
            # read buffer alone (we'll assume that
            # the method has injected its own output)
            else: return None

        # we can probably ignore whitespace,
        # even though a modem never would
        cmd = cmd.strip()
        
        # if this command looks like an AT+SOMETHING=VAL string (which most
        # do), check for an at_something method to handle the command. this
        # is bad, since mock modems should handle as little as possible (and
        # return ERROR for everything else), but some commands are _required_
        # (AT+CMGF=1 # switch to text mode) for anything to work.
        m = re.match(r"^AT\+([A-Z]+)=(.+)$", cmd)
        if m is not None:
            key, val = m.groups()
            method = "at_%s" % key.lower()

            # if the value is wrapped in "quotes", remove
            # them. this is sloppy, but we're only mocking
            val = val.strip('"')

            # call the method, and insert OK or ERROR into the
            # read buffer depending on the True/False output
            if hasattr(self, method):
                out = getattr(self, method)(val)
                return _respond(out)

        # attempt to hand off this
        # command to the subclass
        if hasattr(self, "process"):
            out = self.process(cmd)
            return _respond(out)

        # this modem has no "process" method,
        # or it was called and failed. either
        # way, report an unknown error
        return self._error()


    def at_cmgf(self, mode):
        """Switches this "modem" into PDU mode (0) or TEXT mode (1).
           Returns True for success, or False for unrecognized modes."""

        if mode == "0":
            self.mode = "PDU"
            return True

        elif mode == "1":
            self.mode = "TEXT"
            return True

        else:
            self.mode = None
            return False


    def _output(self, str, delimiters=True):
        """Insert a GSM response into the read buffer, with leading and
           trailing terminators (\r\n). This spews whitespace everywhere,
           but is (curiously) how most modems work."""

        def _delimit():
            self.buf_read.extend(["\r", "\n"])

        # add each letter to the buf_read array,
        # optionally surrounded by the delimiters
        if delimiters: _delimit()
        self.buf_read.extend(str)
        if delimiters: _delimit()

        # what could possibly
        # have gone wrong?
        return True


    def _ok(self):
        """Insert a GSM "OK" string into the read buffer.
           This should be called when a command succeeds."""

        self._output("OK")
        return True


    def _error(self):
        """Insert a GSM "ERROR" string into the read buffer.
           This should be called when a command fails."""
        
        self._output("ERROR")
        return False



class MockSenderDevice(MockDevice):
    """This mock device accepts outgoing SMS (in text mode), and stores them in
       self.sent_messages for later retrieval. This functionality is encapsulated
       here, because it's confusing and ugly."""

    def __init__(self):
        MockDevice.__init__(self)
        self.sent_messages = []
        self.recipient = None
        self.message = None


    def _prompt(self):
        """Outputs the message prompt, which indicates that the device
           is currently accepting the text contents of an SMS."""
        self._output("\r\n>", False)
        return None


    def write(self, str):

        # if we are currently writing a message, and
        # ascii 26 (ctrl+z) was hit, it's time to send!
        if self.recipient:
            if str[-1] == chr(26):
                MockDevice.write(self, str[0:-1])
                self.message.append("".join(self.buf_write))
                self.buf_write = []

                # just store this outgoing message to be checked
                # later on. we're not _really_ sending anything
                self.sent_messages.append({
                    "recipient": self.recipient,
                    "text": "\n".join(self.message)
                })

                # confirm that the message was
                # accepted, and clear the state
                self._output("+CMGS: 1")
                self.recipient = None
                self.message = None
                return self._ok()

        # most of the time, invoke the superclass
        return MockDevice.write(self, str)


    def _process(self, cmd):

        # if we're currently building a message,
        # store this line and prompt for the next
        if self.recipient:
            self.message.append(cmd)
            return self._prompt()

        # otherwise, behave normally
        else: MockDevice._process(self, cmd)    


    def at_cmgs(self, recipient):

        # note the recipient's number (to attach to
        # the message when we're finished), and make
        # a space for the text to be collected
        self.recipient = recipient
        self.message = []

        # start prompting for text
        return self._prompt()
