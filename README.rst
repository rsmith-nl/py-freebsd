FreeBSD module for Python 3
###########################

:date: 2019-07-08
:tags: FreeBSD, ctypes
:author: Roland Smith

.. Last modified: 2019-07-24T19:32:42+0200

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
* ``osrevision``
* ``osreldate``

Especially the first two give access to a *wealth* of information about the
system.
