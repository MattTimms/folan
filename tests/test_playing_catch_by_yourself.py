from __future__ import print_function
import common
import os
import filecmp
import threading
import shutil
import unittest

here = os.path.dirname(__file__)


class TestPlayingCatchByYourself(unittest.TestCase):
    def __init__(self, testname):
        super(TestPlayingCatchByYourself, self).__init__(testname)
        self.arg_dict = common.ARGS
        self.test_folder = here + '/TestPlayingCatchByYourself/'
        self.destination_folder = self.test_folder + 'folan_dest/'

    def setUp(self):
        if os.path.exists(self.test_folder):
            shutil.rmtree(self.test_folder)
        os.makedirs(self.test_folder)
        os.makedirs(self.destination_folder)

    def tearDown(self):
        shutil.rmtree(self.test_folder)

    def test_throwing_file_locally(self):
        common.write_dummy_file(self.test_folder + 'temp.txt')

        serv_args = self.arg_dict.copy()
        serv_args['<ip:port>'] = '127.0.0.1:49999'
        serv_args['--limit'] = 1
        serv_args['--save_path'] = self.destination_folder
        cli_args = self.arg_dict.copy()
        cli_args['<ip:port>'] = '127.0.0.1:49999'
        cli_args['files'] = True
        cli_args['--limit'] = 1
        cli_args['<file_path>'] = [self.test_folder + 'temp.txt']

        server_thread = threading.Thread(target=common.serv, args=(serv_args,))
        client_thread = threading.Thread(target=common.cli, args=(cli_args,))
        server_thread.daemon = True
        client_thread.daemon = True
        server_thread.start()
        client_thread.start()
        while server_thread.is_alive():
            pass

        self.assertTrue(filecmp.cmp(self.test_folder + 'temp.txt', self.destination_folder + 'temp.txt', shallow=False))


if __name__ == '__main__':
    unittest.main()
