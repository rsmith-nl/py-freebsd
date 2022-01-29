FreeBSD module for Python 3
###########################

:date: 2019-08-02
:tags: FreeBSD, ctypes
:author: Roland Smith

.. Last modified: 2022-01-29T22:39:14+0100

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

Introduction
============

This module contains python wrappers for specific FreeBSD library functions.
Most of the functions and sysctls used in this module have been available for
a *long* time. Most of them seem to date back to FreeBSD 2.2.

Functions
=========

Currently, the following functions are provided:

* ``sysctl``
* ``sysctlbyname``
* ``setproctitle``
* ``hostuuid``
* ``osrelease``
* ``osrevision``
* ``osreldate``
* ``version``
* ``npt_gettime``

Especially the first two give access to a *wealth* of information about the
system.

The ``ntp_gettime`` function returns a ``Ntptimeval`` object. This is slightly
different from the FreeBSD libc definition because it is more Pythonic. Since
this object effectively also contains the return value of the function this is
deemed sufficient.

.. note:: The definition of ``Ntptimeval`` differs of that in the
    ``ntp_gettime(2)`` manual in FreeBSD 11.3. It follows the definition in
    /usr/include/sys/timex.h.


