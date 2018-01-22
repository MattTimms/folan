FoLAN
=====

.. image:: https://badge.fury.io/py/folan.svg
    :target: https://badge.fury.io/py/folan
.. image:: https://travis-ci.org/MattTimms/folan.svg?branch=master
    :target: https://travis-ci.org/MattTimms/folan

Files over LAN is a pretty simple script used for sending Files over LAN.

Have a host listen on particular local ip:port for another host whom is sending to those same address details.

``pip install folan``

Usage
-----
::

    Files over LAN.
    Written by Matthew Timms for MonashUAS

    Send/Receives files, or polls directory until user kills process.

    Usage:
      folan.py listen <ip:port> [--save_path DIR_PATH] [options]
      folan.py send files <ip:port> [options] <file_path>...
      folan.py send dir <ip:port> <dir_path> [options]
      folan.py (-h | --help)

    Example:
      folan.py listen 196.168.0.13:40000 -s . --limit=10
      folan.py send dir 10.100.192.15:5555 imgs/ --stayalive

    Options:
      -h --help                 Shows this screen.
      --stayalive               Continues to poll directory and send new files
      --limit LEN_FILES         Limits number of files to receive before closing
      -s, --save_path DIR_PATH  Path to saving directory [default: folan_dest/].


Requirements
------------

``pip install -r requirements.txt``

-  docopt (https://github.com/docopt/docopt)
