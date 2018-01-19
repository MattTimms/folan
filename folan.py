"""Files over LAN.
Written by Matthew Timms for MonashUAS

Send/Receives files, or polls directory until user kills process.

Usage:
  folan.py listen <ip:port> [--save_path DIR_PATH] [options]
  folan.py send files <ip:port> [options] <file_path>...
  folan.py send dir <ip:port> <dir_path> [options]
  folan.py (-h | --help)

Options:
  -h --help                 Shows this screen.
  -s, --save_path DIR_PATH  Path to saving directory [default: serv_dest/].
  --stdout                  Use stdout.
"""

from __future__ import print_function
import socket
import struct
import os.path

__all__ = ['folan']
__version__ = '1.0.0a2'


class Client(object):
    """ """
    def __init__(self, ip, port, timeout=3, debug=False):
        self.dest = (ip, port)
        self.timeout = timeout
        self.debug = debug
        self.sock = None

    def connect(self):
        self._print_dbg("\n# Trying to Connect...", True)
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(self.timeout)
        try:
            self.sock.connect(self.dest)
        except socket.error as error:
            self._print_dbg("Could not connect: {}\nEnsure end host is running and ip:port are correct".format(error))
            return 0
        self._print_dbg("Connection made")
        return 1

    def close(self):
        self.sock.close()

    def send_file(self, filepath):
        self._print_dbg("\nSending file: {}".format(filepath))
        _, filename = os.path.split(filepath)

        namesize = struct.pack('I', len(filename))
        self.sock.send(namesize)
        self.sock.send(filename.encode())

        filesize = os.path.getsize(filepath)
        self._print_dbg("Filesize is {:.1f} KB...".format(float(filesize)/1024), True)

        sizepack = struct.pack('I', filesize)  # Filesize is packed and sent to server
        self.sock.send(sizepack)

        with open(filepath, 'rb') as f:
            buff = f.read(4096)
            while buff:
                self.sock.send(buff)
                buff = f.read(4096)

        verify = self.sock.recv(13).decode()
        self._print_dbg(verify)
        self._print_dbg("Done Sending")

    def _print_dbg(self, string, newline=False):
        if self.debug:
            if newline:
                print(string, end=' ')
            else:
                print(string)


class Server(object):
    """ """
    def __init__(self, ip, port, timeout=3, debug=False):
        self.dest = (ip, port)
        self.timeout = timeout
        self.debug = debug
        self.sock = None
        self.conn = None

    def connect(self):
        self._print_dbg("\n# Trying to Connect...", True)
        try:
            self.sock = socket.socket()
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind(self.dest)
            self.sock.listen(self.timeout)
        except socket.error as message:
            self._print_dbg("Could not open socket: {}".format(message))
            return 0
        self.sock.settimeout(self.timeout)
        try:
            self.conn, addr = self.sock.accept()
        except socket.timeout:
            return 0
        self.conn.settimeout(self.timeout)
        self._print_dbg("Got connection from {}".format(addr))
        return 1

    def close(self):
        self.conn.close()
        self.sock.close()

    def recv_file(self, save_directory=''):
        namesize = self.conn.recv(struct.calcsize("!I"))
        namesize = struct.unpack('I', namesize)[0]
        filename = self.conn.recv(namesize).decode()
        self._print_dbg("\nReceiving file: {}".format(filename))

        sizepack = self.conn.recv(struct.calcsize('!I'))
        filesize = struct.unpack('I', sizepack)[0]
        self._print_dbg("Filesize is {:.1f} KB...".format(float(filesize)/1024), True)

        filepath = ''.join([save_directory, filename])
        with open(filepath, 'wb') as f:
            while True:
                data = self.conn.recv(4096)
                if len(data) == 0:  # Phantom error
                    f.close()
                    raise ValueError("Socket closure")
                f.write(data)
                if f.tell() == filesize:
                    break
            self.conn.send("File received".encode())
            f.close()
        self._print_dbg("File received")

    def _print_dbg(self, string, newline=False):
        if self.debug:
            if newline:
                print(string, end=' ')
            else:
                print(string)


def main():
    from docopt import docopt
    args = docopt(__doc__)

    ip, port = args['<ip:port>'].split(':')
    port = int(port)

    if args['listen']:
        server = Server(ip, port, debug=args['--stdout'])
        save_directory = args['--save_path']  # TODO allow for current directory
        if save_directory[-1] != '/':
            save_directory += '/'

        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        while not server.connect():
            pass

        while True:
            try:
                server.recv_file(save_directory)
            except KeyboardInterrupt:
                print('KeyboardInterrupt')
                break
            except:
                while not server.connect():
                    pass

    elif args['send']:
        client = Client(ip, port, debug=args['--stdout'])
        while not client.connect():
            pass

        if args['files']:
            i = 0
            file_paths = args['<file_path>']
            file_path = file_paths[i]
            while True:
                if not os.path.exists(file_path):
                    print("Path to file is incorrect: ", file_path)
                    continue
                try:
                    client.send_file(file_path)
                    i += 1
                    if i > len(file_paths):
                        break
                except KeyboardInterrupt:
                    print('KeyboardInterrupt')
                    break
                except:  # Any error will trigger a reconnect, be aware for debugging
                    while not client.connect():
                        pass

        elif args['dir']:
            dir_path = args['<dir_path>']
            if dir_path[-1] != '/':
                dir_path += '/'

            file_history = []
            while True:
                filelist = [''.join([dir_path, f]) for f in os.listdir(dir_path) if os.path.isfile(dir_path + f)]
                new_files = [f for f in filelist if f not in file_history]
                file_history.extend(new_files)

                if new_files:
                    i = 0
                    file_path = new_files[i]
                    while True:
                        if not os.path.exists(file_path):
                            print("Path to file is incorrect: ", file_path)
                            continue
                        try:
                            client.send_file(file_path)
                            i += 1
                            if i > len(new_files):
                                break
                        except KeyboardInterrupt:
                            print('KeyboardInterrupt')
                            break
                        except:  # Any error will trigger a reconnect, be aware for debugging
                            while not client.connect():
                                pass

        client.close()
    print("fin.")


if __name__ == '__main__':
    main()
