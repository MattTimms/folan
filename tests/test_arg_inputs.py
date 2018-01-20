from __future__ import print_function
import os
import sys
import filecmp
import time
import threading
import shutil


def serv(args):
    os.system(''.join(["python ../folan.py listen ", args]))


def cli(args):
    os.system(''.join(["python ../folan.py send ", args]))


def write_dummy_file(filename='temp.txt', filesize=1048576):
    """ Creates 1MB temporary file """
    with open(filename, 'wb') as f:
        size = filesize
        f.write(b"\0" * size)


def test_simple_inputs():
    write_dummy_file()
    serv_args = '127.0.0.1:40002 --limit 1'
    cli_args = 'files 127.0.0.1:40002 temp.txt'
    server_thread = threading.Thread(target=serv, args=(serv_args,))
    client_thread = threading.Thread(target=cli, args=(cli_args,))
    server_thread.start()
    client_thread.start()
    while client_thread.is_alive():
        pass
    time.sleep(0.5)
    assert not server_thread.is_alive()  # server closed after file limit

    assert filecmp.cmp('temp.txt', 'folan_dest/temp.txt', shallow=False)  # file sent successfully
    os.remove('temp.txt')
    shutil.rmtree('folan_dest/')


def test_local_dir_save():
    if not os.path.exists('folan_dest/'):
        os.makedirs('folan_dest/')
    write_dummy_file('folan_dest/temp.txt')
    if os.path.exists('temp.txt'):
        os.remove('temp.txt')

    serv_args = '127.0.0.1:40002 -s . --limit 1'
    cli_args = 'files 127.0.0.1:40002 folan_dest/temp.txt'
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

    serv_args = '127.0.0.1:40002 -s recv/ --limit 10'
    cli_args = 'dir 127.0.0.1:40002 send/'
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

    serv_args = '127.0.0.1:40002 -s recv/ --limit=2'
    cli_args = 'dir 127.0.0.1:40002 send/ --stayalive --limit=2'
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
    print("\ntest_simple_inputs()")
    test_simple_inputs()
    print("\n\ntest_local_dir_save()")
    test_local_dir_save()
    print("\n\ntest_directory_send()")
    test_directory_send()
    print("\n\ntest_stayalive()")
    test_stayalive()
    print('\n\nfin.')
