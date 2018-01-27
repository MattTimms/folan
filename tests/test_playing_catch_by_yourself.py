from __future__ import print_function
import os
import sys
import filecmp
import shutil
import time
import threading

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import folan

arg_dict = {'listen': False, '<ip:port>': '127.0.0.1:50000', '--save_path': 'folan_dest/', '--stayalive': False,
            '--limit': None, 'send': False, 'files': False, '<file_path>': [], 'dir': False, '<dir_path>': None,
            '--help': False}


def write_dummy_file(filename='temp.txt', filesize=1048576):
    """ Creates 1MB temporary file """
    with open(filename, 'wb') as f:
        size = filesize
        f.write(b"\0" * size)


def serv():
    serv_args = arg_dict.copy()
    serv_args['<ip:port>'] = '127.0.0.1:49999'
    serv_args['listen'] = True
    serv_args['--limit'] = 1
    folan.main(serv_args)


def cli():
    write_dummy_file()
    cli_args = arg_dict.copy()
    cli_args['<ip:port>'] = '127.0.0.1:49999'
    cli_args['send'] = True
    cli_args['files'] = True
    cli_args['<file_path>'] = ['temp.txt']
    cli_args['--limit'] = 1
    folan.main(cli_args)


def test_throwing_file_locally():
    server_thread = threading.Thread(target=serv)
    client_thread = threading.Thread(target=cli)
    server_thread.daemon = True
    client_thread.daemon = True
    server_thread.start()
    client_thread.start()
    while server_thread.is_alive():
        pass

    assert filecmp.cmp('temp.txt', 'folan_dest/temp.txt', shallow=False)
    os.remove('temp.txt')
    shutil.rmtree('folan_dest/')
