from __future__ import print_function
import os
import sys
import filecmp
import time
import threading
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import folan

arg_dict = {'listen': False, '<ip:port>': '127.0.0.1:50000', '--save_path': 'folan_dest/', '--stayalive': False,
            '--limit': None, 'send': False, 'files': False, '<file_path>': [], 'dir': False, '<dir_path>': None,
            '--help': False}

def serv(args):
    args['listen'] = True
    folan.main(args)


def cli(args):
    args['send'] = True
    folan.main(args)


def write_dummy_file(filename='temp.txt', filesize=1048576):
    """ Creates 1MB temporary file """
    with open(filename, 'wb') as f:
        size = filesize
        f.write(b"\0" * size)


def test_empty_file_send():
    write_dummy_file(filesize=0)

    serv_args = arg_dict.copy()
    serv_args['listen'] = True
    serv_args['--limit'] = 1
    cli_args = arg_dict.copy()
    cli_args['send'] = True
    cli_args['files'] = True
    cli_args['<file_path>'] = ['temp.txt']

    server_thread = threading.Thread(target=serv, args=(serv_args,))
    client_thread = threading.Thread(target=cli, args=(cli_args,))
    server_thread.start()
    client_thread.start()
    while server_thread.is_alive():
        pass

    assert filecmp.cmp('temp.txt', 'folan_dest/temp.txt', shallow=False)  # file saved in local directory
    os.remove('temp.txt')
    shutil.rmtree('folan_dest/')
