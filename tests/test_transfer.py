import os
import threading
import time

import pytest

import folan

""" 
It takes more than achieving 100% test coverage by not putting in any assertions 
in your test cases to be a great engineer. - soft skills engineering.
"""


def test_single_file_transfer(tmpdir):
    host = 'localhost', 6666

    tmp_filename = "tempfile.txt"
    target_path = tmpdir.join(tmp_filename)
    target_path.write(b'\0' * 4096)

    sender_thread = threading.Thread(target=folan.send, args=(target_path, host))
    receiver_thread = threading.Thread(target=folan.receive, args=(*host,))
    sender_thread.daemon = True
    receiver_thread.daemon = True
    sender_thread.start()
    receiver_thread.start()

    while receiver_thread.is_alive():
        pass

    assert os.path.exists(tmp_filename)
    os.remove(tmp_filename)


def test_directory_transfer(tmpdir):
    host = 'localhost', 6666

    for i in range(2):
        target_path = tmpdir.join(f"tempfile-{i}.txt")
        target_path.write(b'\0' * 4096)

    sender_thread = threading.Thread(target=folan.send, args=(tmpdir, host))
    receiver_thread = threading.Thread(target=folan.receive, args=(*host,))
    sender_thread.daemon = True
    receiver_thread.daemon = True
    sender_thread.start()
    time.sleep(1)
    receiver_thread.start()

    while receiver_thread.is_alive():
        pass

    target_archive = os.path.basename(tmpdir) + '.tar.gz'
    assert os.path.exists(target_archive)
    os.remove(target_archive)


if __name__ == '__main__':
    pytest.main()
