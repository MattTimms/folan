from __future__ import print_function, division
import os
import time
import threading


class PrintyMcPrintington(object):
    def __init__(self, filename, filesize, allow_printing=True, progress_bar_len=30, socket_buffer_size=4096):
        self.filename = filename
        self.filesize = filesize / 1024  # Bytes2Kilobytes
        self.progress_bar_len = progress_bar_len
        self.socket_buffer_size = socket_buffer_size  # Bytes
        self.allow_printing = allow_printing
        self.progress_ref = filesize / self.progress_bar_len / socket_buffer_size  # ratio of pkts moved to '=' icons
        self.start_time = time.time()
        self.finish_time = None
        self.stayalive = True
        self.pkts_moved = 0
        self._print_thread = threading.Thread(target=self.print_thread).start()

    def print_thread(self):
        while self.stayalive:
            progress = int(self.pkts_moved / self.progress_ref)
            output = '\r%s\t|%s%s| %.1f /%.1fKB  elapse:%is' % (
                self.filename, '=' * progress, ' ' * (self.progress_bar_len - progress),
                self.pkts_moved * self.socket_buffer_size, self.filesize, time.time() - self.start_time)
            print(output, end='')
            time.sleep(0.1)

    @classmethod
    def current_file(cls, filepath):
        _, filename = os.path.split(filepath)
        filesize = os.path.getsize(filepath)
        return PrintyMcPrintington(filename, filesize)

    def release_gracefully(self):
        self.stayalive = False
        self.finish_time = time.time()
        elapse_time = self.finish_time - self.start_time
        while self._print_thread is not None:
            pass
        output = '\r%s\t|%s| size:%.1fKB  elapse:%is  rate:%.1f KB/s' % (
            self.filename, '=' * self.progress_bar_len, self.filesize, elapse_time, self.filesize / elapse_time)
        print(output)

    def release_violently(self):
        self.stayalive = False
        self.finish_time = time.time()
        while self._print_thread is not None:
            pass
        progress = int(self.pkts_moved / self.progress_ref)
        output = '\r%s\t|%sX%s| Connection broken!' % (
            self.filename, '=' * progress, ' ' * (self.progress_bar_len - progress - 1),)
        print(output)

    def print_decorator(self, some_function):
        def wrapper(*args, **kwargs):
            if self.allow_printing:
                some_function(*args, **kwargs)
        return wrapper


if __name__ == '__main__':
    filename = 'temp.txt'
    filesize = 262994
    printy = PrintyMcPrintington(filename, filesize)
    for i in range(5):
        printy.pkts_moved += 1
        time.sleep(0.5)
    printy.release_gracefully()
    printy = PrintyMcPrintington(filename, filesize)
    for i in range(5):
        printy.pkts_moved += 1
        time.sleep(0.5)
    printy.release_violently()
    printy = PrintyMcPrintington(filename, filesize)
    printy.release_violently()
