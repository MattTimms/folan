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
    if os.path.exists('test_local_dir_save/'):
        shutil.rmtree('test_local_dir_save/')
    os.makedirs('test_local_dir_save/')
    write_dummy_file('test_local_dir_save/temp.txt')
    if os.path.exists('temp.txt'):
        os.remove('temp.txt')

    serv_args = arg_dict.copy()
    serv_args['--save_path'] = '.'
    serv_args['--limit'] = 1
    cli_args = arg_dict.copy()
    cli_args['files'] = True
    cli_args['<file_path>'] = ['test_local_dir_save/temp.txt']

    server_thread = threading.Thread(target=serv, args=(serv_args,))
    client_thread = threading.Thread(target=cli, args=(cli_args,))
    server_thread.start()
    client_thread.start()
    while client_thread.is_alive():
        pass

    assert filecmp.cmp('temp.txt', 'test_local_dir_save/temp.txt', shallow=False)  # file saved in local directory
    os.remove('temp.txt')
    shutil.rmtree('test_local_dir_save/')


def test_directory_send():
    if os.path.exists('test_directory_send/'):
        shutil.rmtree('test_directory_send/')
    os.makedirs('test_directory_send')
    os.makedirs('test_directory_send/send/')
    os.makedirs('test_directory_send/recv/')
    for i in range(3):
        write_dummy_file('test_directory_send/send/{}.txt'.format(str(i)))

    serv_args = arg_dict.copy()
    serv_args['<ip:port>'] = '127.0.0.1:50001'
    serv_args['--save_path'] = 'test_directory_send/recv/'
    serv_args['--limit'] = 10
    cli_args = arg_dict.copy()
    cli_args['<ip:port>'] = '127.0.0.1:50001'
    cli_args['dir'] = True
    cli_args['<dir_path>'] = 'test_directory_send/send/'

    server_thread = threading.Thread(target=serv, args=(serv_args,))
    client_thread = threading.Thread(target=cli, args=(cli_args,))
    server_thread.start()
    client_thread.start()
    while client_thread.is_alive():
        pass

    for i in range(3):
        assert filecmp.cmp('test_directory_send/send/0.txt', 'test_directory_send/recv/{}.txt'.format(str(i)),
                           shallow=False)  # all files sent
    shutil.rmtree('test_directory_send/')


def test_stayalive():
    if os.path.exists('test_stayalive/'):
        shutil.rmtree('test_stayalive/')
    os.makedirs('test_stayalive/send/')
    os.makedirs('test_stayalive/recv/')
    write_dummy_file('test_stayalive/send/before.txt')

    serv_args = arg_dict.copy()
    serv_args['<ip:port>'] = '127.0.0.1:50002'
    serv_args['--save_path'] = 'test_stayalive/recv/'
    serv_args['--limit'] = 2
    cli_args = arg_dict.copy()
    cli_args['<ip:port>'] = '127.0.0.1:50002'
    cli_args['dir'] = True
    cli_args['<dir_path>'] = 'test_stayalive/send/'
    cli_args['--stayalive'] = True
    cli_args['--limit'] = 2

    server_thread = threading.Thread(target=serv, args=(serv_args,))
    client_thread = threading.Thread(target=cli, args=(cli_args,))
    server_thread.start()
    client_thread.start()
    time.sleep(2)  # enough time for one file to send
    write_dummy_file('test_stayalive/send/after.txt')
    while server_thread.is_alive():
        pass

    assert filecmp.cmp('test_stayalive/send/after.txt', 'test_stayalive/recv/after.txt',
                       shallow=False)  # sender stay alive for new file to be sent
    shutil.rmtree('test_stayalive/')


if __name__ == '__main__':
    print("\n\ntest_local_dir_save()")
    test_local_dir_save()
    print("\n\ntest_directory_send()")
    test_directory_send()
    print("\n\ntest_stayalive()")
    test_stayalive()
    print('\n\nfin.')
