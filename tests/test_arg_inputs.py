from __future__ import print_function
import os
import sys
import filecmp
import time
import threading


def serv(args):
    os.system(''.join(["python ../folan.py listen ", args]))


def cli(args):
    os.system(''.join(["python ../folan.py send ", args]))


def write_dummy_file(filename='temp.txt'):
    """ Creates 1MB temporary file """
    with open(filename, 'wb') as f:
        size = 1048576
        f.write(b"\0" * size)


def test_simple_inputs():
    write_dummy_file()
    serv_args = '127.0.0.1:40002 --limit 1'
    cli_args = 'files 127.0.0.1:40002 temp.txt'
    server_thread = threading.Thread(target=serv, args=(serv_args,))
    client_thread = threading.Thread(target=cli, args=(cli_args,))
    server_thread.start()
    time.sleep(1)
    client_thread.start()
    while client_thread.is_alive():
        pass

    assert filecmp.cmp('temp.txt', 'folan_dest/temp.txt', shallow=False)
    os.remove('temp.txt')
    os.remove('folan_dest/temp.txt')


def test_local_dir_save():
    if not os.path.exists('folan_dest/'):
        os.makedirs('folan_dest/')
    write_dummy_file('folan_dest/temp.txt')

    serv_args = '127.0.0.1:40002 -s . --limit 1'
    cli_args = 'files 127.0.0.1:40002 folan_dest/temp.txt'
    server_thread = threading.Thread(target=serv, args=(serv_args,))
    client_thread = threading.Thread(target=cli, args=(cli_args,))
    server_thread.start()
    time.sleep(1)
    client_thread.start()
    while client_thread.is_alive():
        pass

    assert filecmp.cmp('temp.txt', 'folan_dest/temp.txt', shallow=False)
    os.remove('temp.txt')
    os.remove('folan_dest/temp.txt')


if __name__ == '__main__':
    print("\ntest_simple_inputs()")
    test_simple_inputs()
    print("\n\ntest_local_dir_save()")
    test_local_dir_save()
    print('\nfin.')
