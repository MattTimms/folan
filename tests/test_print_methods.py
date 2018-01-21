from __future__ import print_function, division
import os
import time
import sys

# Sending %filename% |=============| remaing / filesize (KB)
# files left |

# Clear Line tests
CLEAR_LINE = '\033[K'

sys.stdout.write('\rWOW')
sys.stdout.write(CLEAR_LINE)
sys.stdout.flush()
sys.stdout.write('\rDONT')
sys.stdout.write('please')
time.sleep(1)
print('')
sys.stdout.write('start\r')
time.sleep(1)
sys.stdout.write(CLEAR_LINE)
sys.stdout.flush()
sys.stdout.write('finish')



# "\n# Trying to Connect... "
#
#
# "Could not connect: {}".format(error)
# "Connection made"
# "\nSending file: {}".format(filepath)
# "\tFilesize is {:.1f} KB...".format(float(filesize) / 1024)
#
# "\tDone Sending"
#
# "Could not open socket: {}".format(message)
# "Got connection from {}".format(addr)
# "\nReceiving file: {}".format(filename)
# "\tFilesize is {:.1f} KB...".format(float(filesize) / 1024)
# "File received"
#
# filename = "temp.txt"
# output = "{}\t|\r".format(filename)


# filename
# filesize
# pass_no
# - push next


class PrintyMcPrintington(object):
    progress_bar_len = 30

    def __init__(self, filename, filesize, socket_buffer_size=4096):
        self.filename = filename
        self.filesize = filesize  # Bytes
        self.socket_buffer_size = socket_buffer_size  # Bytes
        self._progress_ref = filesize / self.progress_bar_len // socket_buffer_size
        self._pkts_moved = 0
        self._print_buffer = ''
        self._print_header = ''.join(['\r', filename, '\t|'])

    @property
    def pkts_moved(self):
        return self._pkts_moved

    @pkts_moved.setter
    def pkts_moved(self, number):
        self._pkts_moved += number
        self.foo() # TODO update display
        pass

    def foo(self):
        sys.stdout.write('\r')
        sys.stdout.write(CLEAR_LINE)
        output = ''.join([self._print_header, self._print_body, self._print_tail])
        sys.stdout.write(output)

    @property
    def _print_body(self):
        progress = int(self.pkts_moved / self._progress_ref)
        return '{}{}'.format('=' * progress, ' ' * (self.progress_bar_len - progress))

    @property
    def _print_tail(self):
        return '|  {0:.2f} /{1:.2f}KB'.format((self.pkts_moved * self.socket_buffer_size / 1024), (self.filesize/1024))


a = PrintyMcPrintington('temp.txt', 1048576)
for i in range(16):
    a.pkts_moved = i
    time.sleep(0.4)
