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

    Options:
      -h --help                 Shows this screen.
      -s, --save_path DIR_PATH  Path to saving directory [default: serv_dest/].
      --stdout                  Use stdout.


Requirements
------------

``pip install -r requirements.txt``

-  docopt (https://github.com/docopt/docopt)