"""Files over LAN.
Written by Matthew Timms for MonashUAS

Send/Receives files, or polls directory until user kills process.

Usage:
  folan.py listen <ip:port> [--save_path DIR_PATH] [options]
  folan.py send files <ip:port> [options] <file_path>...
  folan.py send dir <ip:port> <dir_path> [options]
  folan.py (-h | --help)

Example:
  folan.py listen 196.168.0.13:40000 -s . --limit=10
  folan.py send dir 10.100.192.15:5555 imgs/ --stayalive --limit=10

Options:
  -h --help                 Shows this screen.
  --stayalive               Continues to poll directory and send new files
  -r, --recursive           Sends directories recursively
  --limit LEN_FILES         Limits number of files to receive before closing
  -s, --save_path DIR_PATH  Path to saving directory [default: folan_dest/].
"""

from __future__ import print_function
import socket
import struct
import os
import time
import threading

__all__ = ['folan']
__version__ = '1.1.6'


class Client(object):
    def __init__(self, ip, port, timeout=3, debug=False):
        self.dest = (ip, port)
        self.timeout = timeout
        self.debug = debug
        self.sock = None
        self.buffer_size = 4096
        self.files_sent_len = 0
        self.printer = None
        self.trim_root = None

    def connect(self):
        """ Returns 1 if successfully connects with target host else 0 after timeout """
        if self.printer is not None and self.printer.finish_time is None:
            self.printer.release_violently()
        self._print_dbg("\r# Trying to Connect... ", end='')
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow address reuse
        self.sock.settimeout(self.timeout)
        try:
            self.sock.connect(self.dest)
        except socket.error as error:
            self._print_dbg("Could not connect: {}".format(error), end=' ')
            return 0
        self._print_dbg("Connection made")
        return 1

    def close(self):
        self.sock.close()

    def allow_relative_filenames(self, root):
        """Tells send_file() to send the relative filepath with root trimmed off."""
        self.trim_root = root

    def send_file(self, filepath):
        self.printer = PrintyMcPrintington.current_file(filepath)
        if self.trim_root is None:
            _, filename = os.path.split(filepath)
        else:
            filename = filepath.replace(self.trim_root, '')

        filename_size = struct.pack('I', len(filename))
        self.sock.send(filename_size)  # Length of next expected pkt sent
        self.sock.send(filename.encode())

        filesize = os.path.getsize(filepath)
        sizepack = struct.pack('I', filesize)
        self.sock.send(sizepack)

        with open(filepath, 'rb') as f:
            buff = f.read(self.buffer_size)
            while buff:
                self.sock.send(buff)
                buff = f.read(self.buffer_size)
                self.printer.pkts_moved += 1

        self.sock.recv(13).decode()  # TODO
        self.printer.release_gracefully()
        self.files_sent_len += 1

    def _print_dbg(self, *args, **kwargs):
        if self.debug:
            print(*args, **kwargs)


class Server(object):
    def __init__(self, ip, port, timeout=3, debug=False):
        self.dest = (ip, port)
        self.timeout = timeout
        self.debug = debug
        self.sock = None
        self.conn = None
        self.buffer_size = 4096
        self.files_recv_len = 0
        self.printer = None

    def connect(self):
        """ Returns 1 if successfully connects with target host else 0 after timeout """
        if self.printer is not None and self.printer.finish_time is None:
            self.printer.release_violently()
        self._print_dbg("\r# Trying to Connect... ", end='')
        try:
            self.sock = socket.socket()
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind(self.dest)
            self.sock.listen(self.timeout)
        except socket.error as message:
            self._print_dbg("Could not open socket: {}".format(message), end=' ')
            return 0
        self.sock.settimeout(self.timeout)
        try:
            self.conn, addr = self.sock.accept()
        except socket.timeout:
            return 0
        self._print_dbg("Got connection from {}".format(addr))
        return 1

    def close(self):
        self.conn.close()
        self.sock.close()

    def recv_file(self, save_directory=''):
        """ Receives file and writes into save_directory """
        filename_size = self.conn.recv(struct.calcsize("!I"))
        if len(filename_size) == 0:
            raise socket.error("Socket closure")
        filename_size = struct.unpack('I', filename_size)[0]
        filename = self.conn.recv(filename_size).decode()

        sizepack = self.conn.recv(struct.calcsize('!I'))
        filesize = struct.unpack('I', sizepack)[0]
        self.printer = PrintyMcPrintington(filename, filesize)

        path, filename = os.path.split(filename)
        if path:
            if not os.path.exists(save_directory + path):
                os.makedirs(save_directory + path)
        filepath = ''.join([save_directory, path, '/', filename])
        with open(filepath, 'wb') as f:
            if filesize:
                while True:
                    data = self.conn.recv(self.buffer_size)
                    if len(data) == 0:
                        raise socket.error("Socket closure")
                    self.printer.pkts_moved += 1
                    f.write(data)
                    if f.tell() == filesize:
                        break
        self.conn.send("File received".encode())
        self.files_recv_len += 1
        self.printer.release_gracefully()

    def _print_dbg(self, *args, **kwargs):
        if self.debug:
            print(*args, **kwargs)


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
        self._print_thread = threading.Thread(target=self.print_thread)
        self._print_thread.daemon = True
        self._print_thread.start()

    def print_thread(self):
        while self.stayalive:
            if self.progress_ref == 0:
                progress = 0
            else:
                progress = int(self.pkts_moved / self.progress_ref)
            output = '\r%s\t|%s%s| %i/%iKB  elapse:%is' % (
                self.filename, '=' * progress, ' ' * (self.progress_bar_len - progress),
                self.pkts_moved * self.socket_buffer_size / 1024, self.filesize, time.time() - self.start_time)
            print(output, end='')
            time.sleep(0.1)

    @classmethod
    def current_file(cls, filepath):
        _, filename = os.path.split(filepath)
        filesize = os.path.getsize(filepath)
        return PrintyMcPrintington(filepath, filesize)

    def release_gracefully(self):
        self.stayalive = False
        self.finish_time = time.time()
        elapse_time = self.finish_time - self.start_time
        if self._print_thread is not None:
            self._print_thread.join()
        output = '\r%s\t|%s| size:%iKB  elapse:%is  rate:%.1f KB/s' % (
            self.filename, '=' * self.progress_bar_len, self.filesize, elapse_time, self.filesize / elapse_time)
        print(output)

    def release_violently(self):
        self.stayalive = False
        self.finish_time = time.time()
        if self._print_thread is not None:
            self._print_thread.join()
        progress = int(self.pkts_moved / self.progress_ref)
        output = '\r%s\t|%sX%s| Connection broken!' % (
            self.filename, '=' * progress, ' ' * (self.progress_bar_len - progress - 1),)
        print(output)

    def print_decorator(self, some_function):
        def wrapper(*args, **kwargs):
            if self.allow_printing:
                some_function(*args, **kwargs)
        return wrapper


def main(args):
    if not isinstance(args, dict):
        raise TypeError("args expected as dictionary")
    if '--debug' not in args.keys():
        args['--debug'] = True

    ip, port = args['<ip:port>'].split(':')
    if ip == '\'\'':  # docopt's response to '' input
        ip = ''  # default interface
    port = int(port)

    if args['listen']:
        server = Server(ip, port, debug=args['--debug'])

        save_directory = args['--save_path']
        if save_directory[-1] != '/':
            save_directory += '/'
        if args['--limit'] is not None:
            file_limit = int(args['--limit'])
        else:
            file_limit = 0

        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        while not server.connect():
            pass

        while True:
            if server.files_recv_len == file_limit and file_limit > 0:
                break

            try:
                server.recv_file(save_directory)
            except KeyboardInterrupt:
                print('KeyboardInterrupt')
                break
            except socket.error:
                while not server.connect():  # reconnect
                    pass
        server.close()

    elif args['send']:
        client = Client(ip, port, debug=args['--debug')
        while not client.connect():
            print('Ensure end host is running and target ip:port are correct.')
            time.sleep(0.5)
            pass

        if args['files']:
            file_paths = args['<file_path>']
            file_path = file_paths[client.files_sent_len]
            while True:
                if not os.path.exists(file_path):
                    print("Path to file is incorrect: ", file_path)
                    file_paths.pop(client.files_sent_len)

                if client.files_sent_len == len(file_paths):
                    break
                file_path = file_paths[client.files_sent_len]

                try:
                    client.send_file(file_path)
                except KeyboardInterrupt:
                    print('KeyboardInterrupt')
                    break
                except socket.error:  # Any error will trigger a reconnect, be aware for debugging
                    while not client.connect():
                        pass

        elif args['dir']:
            dir_path = args['<dir_path>']
            if dir_path[-1] != '/':
                dir_path += '/'
            if args['--limit'] is not None:
                file_limit = int(args['--limit'])
            else:
                file_limit = 0
            stayalive = args['--stayalive']

            if args['--recursive']:
                client.allow_relative_filenames(dir_path)

            file_history = []
            while True:
                filelist = []
                for root, directories, filenames in os.walk(dir_path):
                    filepaths = [os.path.join(root, filename) for filename in filenames]
                    filelist.extend([filepath for filepath in filepaths if os.path.isfile(filepath)])
                    if not args['--recursive']:
                        break
                new_files = [f for f in filelist if f not in file_history]
                file_history.extend(new_files)

                if new_files:
                    len_newfiles_sent = 0
                    file_path = new_files[len_newfiles_sent]
                    while True:
                        if not os.path.exists(file_path):
                            print("Path to file is incorrect: ", file_path)
                            new_files.pop(client.files_sent_len)

                        if len_newfiles_sent == len(new_files):
                            break
                        elif client.files_sent_len >= file_limit and file_limit:
                            break
                        file_path = new_files[len_newfiles_sent]

                        try:
                            client.send_file(file_path)
                            len_newfiles_sent += 1
                        except KeyboardInterrupt:
                            print('KeyboardInterrupt')
                            break
                        except socket.error:
                            while not client.connect():
                                pass
                if client.files_sent_len >= file_limit and file_limit:
                    break
                elif not stayalive:
                    break

        client.close()
    print("fin.")


if __name__ == '__main__':
    from docopt import docopt
    args = docopt(__doc__)
    main(args)
