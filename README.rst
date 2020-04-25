FoLAN
=====

.. image:: https://badge.fury.io/py/folan.svg
    :target: https://badge.fury.io/py/folan
.. image:: https://travis-ci.org/MattTimms/folan.svg?branch=master
    :target: https://travis-ci.org/MattTimms/folan

Files over LAN is a pretty simple script for sending Files over LAN.

* Send file
* Send directory as ``.tar.gz``


``pip install folan``

Usage
-----
::

    Files over LAN.

    Send & receives files over local area network.

    Usage:
      folan send <file_path>
      folan receive <host>
      folan (-h | --help)

    Examples:
      folan send path/to/file.py
      folan send path/to/directory
      folan receive 192.168.0.15-4567

    Options:
      -h --help         Shows this screen.



Dev Logs
--------
- Originated as a project for `Monash UAS <https://monashuas.org/>`_. Versions ``< 2.0.0`` reflect that intention.
- Recently refreshed as an exercise. Changes inspired by `magic-wormhole <https://github.com/warner/magic-wormhole>`_.

