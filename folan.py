"""Files over LAN.

Send & receives files over local area network.

Usage:
  folan send <file_path>
  folan receive <host>
  folan (-h | --help)

Examples:
  folan send path/to/file.py
  folan send path/to/directory
  folan receive 192.168.0.15-4567

Options:
  -h --help         Shows this screen.

"""

import os
import re
import select
import socket
import sys
import tarfile
import tempfile
from typing import BinaryIO, Optional, Tuple

import psutil

__version__ = '2.0.0'

BUFFER_SIZE = 4096
PATTERN = b"(.+?)\|(\d+)\|(.+)*"


def handle_keyboard_interrupt(func):
    """ Decorator keyboard interrupts. """

    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except KeyboardInterrupt:
            print("User interrupted transfer. Closing...")
            sys.exit(1)

    return wrapper


@handle_keyboard_interrupt
def send(file_path: str, host: Tuple[str, int] = ('', 0)):
    ip, port = host

    # Evaluate file path & pack if directory
    filename = os.path.basename(file_path)
    if os.path.isdir(file_path):
        temp_path = tempfile.NamedTemporaryFile(suffix='.tar.gz').name
        with tarfile.open(temp_path, "w:gz") as tar:
            tar.add(file_path, arcname=os.path.basename(file_path))
        file_path = temp_path
        filename += '.tar.gz'

    # Get file size
    file_size = os.path.getsize(file_path)  # (bytes)
    if file_size == 0:
        print("Cannot send an empty file.")
        sys.exit(1)

    if ip == '':
        # Collect interface IPv4 addresses
        interfaces = {
            name: next(filter(lambda snicaddr: snicaddr.family is socket.AddressFamily.AF_INET, inet_list), None) for
            name, inet_list in psutil.net_if_addrs().items()}
        interfaces = {name: snicaddr.address for name, snicaddr in
                      filter(lambda kv: kv[1] is not None, interfaces.items())}

        # Repeating user prompt for selecting server interface
        while True:
            for i, (name, ipv4) in enumerate(interfaces.items()):
                print(f"{i} {name:<10}: {ipv4}")
            selection = input("Please select interface to bind to... [no./name]: ")

            if selection in interfaces:  # user gives interface's name
                ip = interfaces[selection]
                break
            try:  # user gives number of interface's index
                idx = int(selection)
                ip = list(interfaces.values())[idx]
                break
            except (ValueError, IndexError):
                continue  # input isn't a number or isn't a valid number

    # Create local server
    server = socket.create_server(address=(ip, port),  # all interfaces, any available port
                                  family=socket.AF_INET,
                                  backlog=None,
                                  reuse_port=True)
    server.settimeout(0.1)
    host: Tuple[str, int] = server.getsockname()
    ip, port = host

    # Notify user of next step
    print(f"Ready to send {file_size} bytes of file named {filename}.\n"
          f"On the other computer. please run:\n\n"
          f"folan receive {ip}-{port}")

    # Wait for client connection
    conn: Optional[socket.socket] = None
    while not isinstance(conn, socket.socket):
        try:
            conn, addr = server.accept()
        except socket.timeout:
            # Expect periodic socket timeouts as server waits for client connection.
            continue

    # Send file to client
    try:
        with conn:
            with open(file_path, 'rb') as file_obj:
                # Send file meta first
                conn.send(f'{filename}|{file_size}|'.encode('utf-8'))

                # Send file data
                while buff := file_obj.read(BUFFER_SIZE):
                    # Check for socket closure behaviour
                    r_ready, w_ready, _ = select.select([conn], [conn], [], 0.01)
                    if r_ready:
                        message_in: bytes = conn.recv(BUFFER_SIZE)
                        if message_in == b'':  # Socket closed
                            raise BrokenPipeError

                    # Send bytes to client
                    conn.send(buff)
    except (socket.timeout, BrokenPipeError, KeyboardInterrupt):
        pass
    except ConnectionResetError:
        print("Connection was refused. Closing...")
        sys.exit(1)
    finally:
        print(f"Finished sending {filename} to {addr}")


@handle_keyboard_interrupt
def receive(ip: str, port: int):
    # Connect to host sender
    try:
        client = socket.create_connection(address=(ip, port),
                                          timeout=0.5)
    except ConnectionRefusedError:
        print("Connection was refused. Is sender still running?")
        sys.exit(1)

    file_obj: Optional[BinaryIO] = None
    filename: Optional[str] = None
    file_size: Optional[int] = None  # (bytes)
    try:
        with client:
            while True:
                # Check socket is readable
                r_ready, w_ready, _ = select.select([client], [client], [], 0.01)

                # Read socket
                if r_ready:
                    message_in: bytes = client.recv(BUFFER_SIZE)

                    if message_in == b'':  # Socket closed
                        raise BrokenPipeError
                    elif filename is None:  # On first socket read

                        # Expected start of stream to receive file meta
                        match = re.match(PATTERN, message_in)
                        if match is None:
                            raise ValueError("First packet does not match expected pattern.")
                        else:
                            # Create file object
                            filename = match.group(1).decode('utf-8')
                            if os.path.exists(filename):
                                print(f"{filename} already exists.")
                                sys.exit(1)

                            file_obj = open(filename, 'wb')

                            # Collect additional file meta
                            file_size = int(match.group(2))
                            if match.group(3) is not None:
                                file_obj.write(match.group(3))

                    else:
                        # Write to file object
                        file_obj.write(message_in)

    except (ValueError, socket.timeout, BrokenPipeError, KeyboardInterrupt):
        pass
    finally:
        # Close file objects
        if file_obj is not None:
            file_obj.close()

            # Remove file if incorrect file size - premature connection closure
            if os.path.getsize(filename) != file_size:
                os.remove(filename)
                print(f"Failed to receive {filename}")
            else:
                print(f"File transfer complete & saved to: {filename}")
        else:
            print("Failed to receive file.")


def _entry_point():
    from docopt import docopt
    args = docopt(__doc__)

    if args['send']:
        send(file_path=args['<file_path>'])
    else:
        ip, port = args['<host>'].split('-')
        receive(ip, int(port))


if __name__ == '__main__':
    _entry_point()
