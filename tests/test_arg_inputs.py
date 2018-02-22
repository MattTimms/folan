from __future__ import print_function
import common
import os
import filecmp
import threading
import shutil
import unittest

here = os.path.dirname(__file__)


class TestArgInputs(unittest.TestCase):
    def __init__(self, testname):
        super(TestArgInputs, self).__init__(testname)
        self.arg_dict = common.ARGS
        self.test_folder = here + '/TestArgInputs/'
        self.destination_folder = self.test_folder + 'folan_dest/'

    def setUp(self):
        if os.path.exists(self.test_folder):
            shutil.rmtree(self.test_folder)
        os.makedirs(self.test_folder)
        os.makedirs(self.destination_folder)

    def tearDown(self):
        shutil.rmtree(self.test_folder)
        if os.path.exists('temp.txt'):
            os.remove('temp.txt')

    def test_local_dir_save(self):
        common.write_dummy_file(self.test_folder + 'temp.txt')

        serv_args = self.arg_dict.copy()
        serv_args['<ip:port>'] = '127.0.0.1:50000'
        serv_args['--save_path'] = '.'
        serv_args['--limit'] = 1
        cli_args = self.arg_dict.copy()
        cli_args['<ip:port>'] = '127.0.0.1:50000'
        cli_args['files'] = True
        cli_args['<file_path>'] = [self.test_folder + 'temp.txt']

        server_thread = threading.Thread(target=common.serv, args=(serv_args,))
        client_thread = threading.Thread(target=common.cli, args=(cli_args,))
        server_thread.start()
        client_thread.start()
        while client_thread.is_alive():
            pass

        # file saved in local directory
        self.assertTrue(filecmp.cmp(self.test_folder + 'temp.txt', 'temp.txt', shallow=False))

    def test_directory_send(self):
        no_of_files = 3
        for i in range(no_of_files):
            common.write_dummy_file(self.test_folder + '{}.txt'.format(str(i)), filesize=1024)

        serv_args = self.arg_dict.copy()
        serv_args['<ip:port>'] = '127.0.0.1:50001'
        serv_args['--save_path'] = self.destination_folder
        serv_args['--limit'] = no_of_files
        cli_args = self.arg_dict.copy()
        cli_args['<ip:port>'] = '127.0.0.1:50001'
        cli_args['dir'] = True
        cli_args['<dir_path>'] = self.test_folder

        server_thread = threading.Thread(target=common.serv, args=(serv_args,))
        client_thread = threading.Thread(target=common.cli, args=(cli_args,))
        server_thread.daemon = True
        client_thread.daemon = True
        server_thread.start()
        client_thread.start()
        while client_thread.is_alive():
            pass

        for i in range(no_of_files):
            self.assertTrue(filecmp.cmp(self.test_folder + '0.txt', self.destination_folder + '{}.txt'.format(str(i)),
                                        shallow=False))

    def test_stayalive(self):
        common.write_dummy_file(self.test_folder + '0.txt')

        serv_args = self.arg_dict.copy()
        serv_args['<ip:port>'] = '127.0.0.1:50002'
        serv_args['--save_path'] = self.destination_folder
        serv_args['--limit'] = 2
        cli_args = self.arg_dict.copy()
        cli_args['<ip:port>'] = '127.0.0.1:50002'
        cli_args['dir'] = True
        cli_args['<dir_path>'] = self.test_folder
        cli_args['--stayalive'] = True
        cli_args['--limit'] = 2

        server_thread = threading.Thread(target=common.serv, args=(serv_args,))
        client_thread = threading.Thread(target=common.cli, args=(cli_args,))
        server_thread.daemon = True
        client_thread.daemon = True
        server_thread.start()
        client_thread.start()

        common.write_dummy_file(self.test_folder + '1.txt')
        while server_thread.is_alive():
            pass

        assert filecmp.cmp(self.test_folder + '1.txt', self.destination_folder + '1.txt',
                           shallow=False)  # sender stay alive for new file to be sent

    def test_recursive_dir(self):
        fold_0 = self.test_folder + 'dir/fold_0/'
        fold_1 = self.test_folder + 'dir/fold_1/'
        os.makedirs(fold_0)
        os.makedirs(fold_1)
        for i in range(2):
            common.write_dummy_file(fold_0 + '%i.txt' % i, 1024)
            common.write_dummy_file(fold_1 + '%i.txt' % i, 1024)

        serv_args = self.arg_dict.copy()
        serv_args['<ip:port>'] = '127.0.0.1:50003'
        serv_args['--save_path'] = self.destination_folder
        serv_args['--limit'] = 4
        cli_args = self.arg_dict.copy()
        cli_args['<ip:port>'] = '127.0.0.1:50003'
        cli_args['dir'] = True
        cli_args['<dir_path>'] = self.test_folder + 'dir/'
        cli_args['--recursive'] = True

        server_thread = threading.Thread(target=common.serv, args=(serv_args,))
        client_thread = threading.Thread(target=common.cli, args=(cli_args,))
        server_thread.daemon = True
        client_thread.daemon = True
        server_thread.start()
        client_thread.start()
        while server_thread.is_alive():
            pass

        assert filecmp.cmp(fold_0 + '0.txt', self.destination_folder + 'fold_0/0.txt',
                           shallow=False)  # sender stay alive for new file to be sent

    def test_data_limit(self):
        no_of_files = 2
        for i in range(no_of_files):
            common.write_dummy_file(self.test_folder + '{}.txt'.format(str(i)), filesize=3*1024**2)

        serv_args = self.arg_dict.copy()
        serv_args['<ip:port>'] = '127.0.0.1:50004'
        serv_args['--save_path'] = self.destination_folder
        serv_args['--limit'] = 1
        cli_args = self.arg_dict.copy()
        cli_args['<ip:port>'] = '127.0.0.1:50004'
        cli_args['dir'] = True
        cli_args['<dir_path>'] = self.test_folder
        cli_args['--limit'] = '3mb'

        server_thread = threading.Thread(target=common.serv, args=(serv_args,))
        client_thread = threading.Thread(target=common.cli, args=(cli_args,))
        server_thread.daemon = True
        client_thread.daemon = True
        server_thread.start()
        client_thread.start()
        while client_thread.is_alive():
            pass
        server_thread.join(timeout=1)

        self.assertTrue(filecmp.cmp(self.test_folder + '0.txt', self.destination_folder + '0.txt', shallow=False))


if __name__ == '__main__':
    unittest.main()
