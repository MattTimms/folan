from __future__ import print_function
import os
import sys
import filecmp
import time
import threading

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import folan


def serv():
    server = folan.Server('127.0.0.1', 40002, debug=True)
    while not server.connect():
        pass

    while True:
        try:
            server.recv_file('_')
            break
        except:
            while not server.connect():
                pass


def cli():
    client = folan.Client('127.0.0.1', 40002, debug=True)
    while not client.connect():
        pass

    file_path = 'temp.txt'
    with open(file_path, 'wb') as f:  # Create 1MB temp file
        size = 1048576
        f.write(b"\0" * size)

    while True:
        try:
            client.send_file(file_path)
            break
        except:
            while not client.connect():
                pass


def test_throwing_file_locally():
    server_thread = threading.Thread(target=serv)
    client_thread = threading.Thread(target=cli)
    server_thread.start()
    time.sleep(1)
    client_thread.start()
    while server_thread.is_alive():
        pass

    assert filecmp.cmp('temp.txt', '_temp.txt', shallow=False)
    os.remove('temp.txt')
    os.remove('_temp.txt')


if __name__ == "__main__":
    test_throwing_file_locally()
    print('\nfin.')
