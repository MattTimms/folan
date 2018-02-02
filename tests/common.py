import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import folan


ARGS = {'listen': False, '<ip:port>': '127.0.0.1:50000', '--save_path': 'folan_dest/','--stayalive': False,
        '--recursive': False, '--limit': None, 'send': False, 'files': False, '<file_path>': [],
        'dir': False, '<dir_path>': None, '--help': False}

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