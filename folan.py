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
  --limit LEN_FILES         Limits number of files to receive before closing
  -s, --save_path DIR_PATH  Path to saving directory [default: folan_dest/].
"""

from __future__ import print_function
from tests.test_print_methods import PrintyMcPrintington
import os.path
import socket
import struct
import time


__all__ = ['folan']
__version__ = '1.1.1'


class Client(object):
    def __init__(self, ip, port, timeout=3, debug=False):
        self.dest = (ip, port)
        self.timeout = timeout
        self.debug = debug
        self.sock = None
        self.buffer_size = 4096
        self.len_files_sent = 0
        self.printer = None

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

    def send_file(self, filepath):
        self.printer = PrintyMcPrintington.current_file(filepath)
        _, filename = os.path.split(filepath)
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
        self.len_files_sent += 1

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
        self.len_files_recv = 0
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

        filepath = ''.join([save_directory, filename])
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
        self.len_files_recv += 1
        self.printer.release_gracefully()

    def _print_dbg(self, *args, **kwargs):
        if self.debug:
            print(*args, **kwargs)


def main(args):
    ip, port = args['<ip:port>'].split(':')
    if ip == '\'\'':  # docopt's response to '' input
        ip = ''  # default interface
    port = int(port)

    if args['listen']:
        server = Server(ip, port, debug=True)

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
            if server.len_files_recv == file_limit and file_limit > 0:
                break

            try:
                server.recv_file(save_directory)
            except KeyboardInterrupt:
                print('KeyboardInterrupt')
                break
            except socket.error:
                while not server.connect():  # reconnect
                    pass

    elif args['send']:
        client = Client(ip, port, debug=True)
        while not client.connect():
            print('Ensure end host is running and target ip:port are correct.')
            time.sleep(0.5)
            pass

        if args['files']:
            file_paths = args['<file_path>']
            file_path = file_paths[client.len_files_sent]
            while True:
                if not os.path.exists(file_path):
                    print("Path to file is incorrect: ", file_path)
                    file_paths.pop(client.len_files_sent)

                if client.len_files_sent == len(file_paths):
                    break
                file_path = file_paths[client.len_files_sent]

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

            file_history = []
            while True:
                filelist = [''.join([dir_path, f]) for f in os.listdir(dir_path) if os.path.isfile(dir_path + f)]
                new_files = [f for f in filelist if f not in file_history]
                file_history.extend(new_files)

                if new_files:
                    len_newfiles_sent = 0
                    file_path = new_files[len_newfiles_sent]
                    while True:
                        if not os.path.exists(file_path):
                            print("Path to file is incorrect: ", file_path)
                            new_files.pop(client.len_files_sent)

                        if len_newfiles_sent == len(new_files):
                            break
                        elif client.len_files_sent >= file_limit and file_limit:
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
                if client.len_files_sent >= file_limit and file_limit:
                    break
                elif not stayalive:
                    break

        client.close()
    print("fin.")


if __name__ == '__main__':
    from docopt import docopt
    args = docopt(__doc__)
    main(args)
