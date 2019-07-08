# file: freebsd.py
# vim:fileencoding=utf-8:fdm=marker:ft=python
#
# Copyright © 2019 R.F. Smith <rsmith@xs4all.nl>.
# SPDX-License-Identifier: MIT
# Created: 2019-07-07T23:56:25+0200
# Last modified: 2019-07-08T21:19:31+0200
"""Python bindings for some FreeBSD library calls"""

import ctypes
import ctypes.util

# Load the C library
_libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)


def to_int(value):
    """Convert binary sysctl value to integer."""
    return int.from_bytes(value, byteorder='little')


def to_degC(value):
    """Convert binary sysctl value to degree Centigrade."""
    return round(int.from_bytes(value, byteorder='little') / 10 - 273.15, 1)


def to_string(value):
    """Convert binary sysctl value to UTF-8 string."""
    return value.strip(b'\x00').decode('utf-8')


def sysctlbyname(name, buflen=4, convert=None):
    """
    Python wrapper for sysctlbyname(3).

    Arguments:
        name (str): Name of the sysctl to query
        buflen (int): Length of the data buffer to use.
        convert: Optional function to convert the data.

    Returns:
        The requested binary data, converted if desired.
    """
    name_in = ctypes.c_char_p(bytes(name, encoding='ascii'))
    oldlen = ctypes.c_size_t(buflen)
    oldlenp = ctypes.byref(oldlen)
    oldp = ctypes.create_string_buffer(buflen)
    rv = _libc.sysctlbyname(name_in, oldp, oldlenp, None, ctypes.c_size_t(0))
    if rv != 0:
        errno = ctypes.get_errno()
        raise ValueError(f'sysctlbyname error: {errno}')
    if convert:
        return convert(oldp.raw[:buflen])
    return oldp.raw[:buflen]


def sysctl(name, buflen=4, convert=None):
    """
    Python wrapper for sysctl(3).

    Arguments:
        name: list or tuple of integers.
        buflen (int): Length of the data buffer to use.
        convert: Optional function to convert the data.

    Returns:
        The requested binary data, converted if desired.
    """
    cnt = len(name)
    mib = ctypes.c_int * cnt
    name_in = mib(*name)
    oldlen = ctypes.c_size_t(buflen)
    oldlenp = ctypes.byref(oldlen)
    oldp = ctypes.create_string_buffer(buflen)
    rv = _libc.sysctl(
        ctypes.byref(name_in), ctypes.c_uint(cnt), oldp, oldlenp, None,
        ctypes.c_size_t(0)
    )
    if rv != 0:
        errno = ctypes.get_errno()
        raise ValueError(f'sysctl error: {errno}')
    if convert:
        return convert(oldp.raw[:buflen])
    return oldp.raw[:buflen]


def setproctitle(name):
    """
    Change the name of the process.

    Arguments:
        name (bytes/str): the new name for the process.
    """
    if isinstance(name, str):
        name = name.encode('ascii')
    fmt = ctypes.c_char_p(b'-%s')
    value = ctypes.c_char_p(name)
    _libc.setproctitle(fmt, value)


def hostuuid():
    """Returns the UUID of this host."""
    rv = sysctlbyname('kern.hostuuid', buflen=40, convert=to_string)
    return rv


def osrevision():
    """Returns operating system revision"""
    rv = sysctlbyname('kern.osrevision', convert=to_int)
    return rv


def osreldate():
    """
    Returns the version of the currently running FreeBSD kernel.

    This is the value of __FreeBSD_version.
    """
    return _libc.getosreldate()
