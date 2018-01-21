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


def test_local_dir_save():
    if not os.path.exists('folan_dest/'):
        os.makedirs('folan_dest/')
    write_dummy_file('folan_dest/temp.txt')
    if os.path.exists('temp.txt'):
        os.remove('temp.txt')

    serv_args = arg_dict.copy()
    serv_args['--save_path'] = '.'
    serv_args['--limit'] = 1
    cli_args = arg_dict.copy()
    cli_args['files'] = True
    cli_args['<file_path>'] = ['folan_dest/temp.txt']

    server_thread = threading.Thread(target=serv, args=(serv_args,))
    client_thread = threading.Thread(target=cli, args=(cli_args,))
    server_thread.start()
    client_thread.start()
    while client_thread.is_alive():
        pass

    assert filecmp.cmp('temp.txt', 'folan_dest/temp.txt', shallow=False)  # file saved in local directory
    os.remove('temp.txt')
    shutil.rmtree('folan_dest/')


def test_directory_send():
    if not os.path.exists('send/'):
        os.makedirs('send/')
    if not os.path.exists('recv/'):
        os.makedirs('recv/')
    for i in range(10):
        write_dummy_file('send/{}.txt'.format(str(i)))  #, (1024*1024))

    serv_args = arg_dict.copy()
    serv_args['--save_path'] = 'recv'
    serv_args['--limit'] = 10
    cli_args = arg_dict.copy()
    cli_args['dir'] = True
    cli_args['<dir_path>'] = 'send'

    server_thread = threading.Thread(target=serv, args=(serv_args,))
    client_thread = threading.Thread(target=cli, args=(cli_args,))
    server_thread.start()
    client_thread.start()
    while client_thread.is_alive():
        pass

    for i in range(10):
        assert filecmp.cmp('send/0.txt', 'recv/{}.txt'.format(str(i)), shallow=False)  # all files sent
    shutil.rmtree('send/')
    shutil.rmtree('recv/')


def test_stayalive():
    if not os.path.exists('send/'):
        os.makedirs('send/')
    write_dummy_file('send/before.txt')

    serv_args = arg_dict.copy()
    serv_args['--save_path'] = 'recv/'
    serv_args['--limit'] = 2
    cli_args = arg_dict.copy()
    cli_args['dir'] = True
    cli_args['<dir_path>'] = 'send/'
    cli_args['--stayalive'] = True
    cli_args['--limit'] = 2

    server_thread = threading.Thread(target=serv, args=(serv_args,))
    client_thread = threading.Thread(target=cli, args=(cli_args,))
    server_thread.start()
    client_thread.start()
    time.sleep(2)  # enough time for one file to send
    write_dummy_file('send/after.txt')
    while client_thread.is_alive():
        pass

    assert filecmp.cmp('send/after.txt', 'recv/after.txt', shallow=False)  # sender stay alive for new file to be sent
    shutil.rmtree('send/')
    shutil.rmtree('recv/')


if __name__ == '__main__':
    print("\n\ntest_local_dir_save()")
    test_local_dir_save()
    print("\n\ntest_directory_send()")
    test_directory_send()
    print("\n\ntest_stayalive()")
    test_stayalive()
    print('\n\nfin.')
