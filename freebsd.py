# file: freebsd.py
# vim:fileencoding=utf-8:fdm=marker:ft=python
#
# Copyright © 2019 R.F. Smith <rsmith@xs4all.nl>.
# SPDX-License-Identifier: MIT
# Created: 2019-07-07T23:56:25+0200
# Last modified: 2019-08-12T21:51:02+0200
"""Python bindings for some FreeBSD library calls on 64-bit architectures."""

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


def osrelease():
    """Returns operating system release."""
    # buflen according to /usr/include/sys/jail.h
    rv = sysctlbyname('kern.osrelease', buflen=32, convert=to_string)
    return rv


def osrevision():
    """Returns operating system revision."""
    rv = sysctlbyname('kern.osrevision', convert=to_int)
    return rv


def osreldate():
    """
    Returns the version of the currently running FreeBSD kernel.

    This is the value of __FreeBSD_version.
    """
    return _libc.getosreldate()


def version():
    """Returns operation system version."""
    rv = sysctlbyname('kern.version', buflen=256, convert=to_string)
    return rv


# Note: On FreeBSD 11.3, the definition of “struct ntptimeval” used in
# ntp_gettime(2) do not match those of /usr/include/sys/timex.h! In this
# module, I have therefore followed the latter!

_time_state = {
    0:  'TIME_OK',
    1:  'TIME_INS',
    2:  'TIME_DEL',
    3:  'TIME_OOP',
    4:  'TIME_WAIT',
    5:  'TIME_ERROR',
}


class Ntptimeval(ctypes.Structure):
    _fields_ = [("tv_sec", ctypes.c_longlong), ("tv_nsec", ctypes.c_long),
                ("maxerror", ctypes.c_long), ("esterror", ctypes.c_long),
                ("tai", ctypes.c_long), ("time_state", ctypes.c_int)]

    def __repr__(self):
        a = f"Ntptimeval(tv_sec={self.tv_sec}, tv_nsec={self.tv_nsec}, "
        b = f"maxerror={self.maxerror}, esterror={self.esterror}, "
        c = f"tai={self.tai}, time_state={_time_state[self.time_state]})"
        return a + b + c


def ntp_gettime():
    """Fills and returns an Ntptimeval instance."""
    tv = Ntptimeval(0, 0, 0, 0, 0, 0)
    # Note: the return value of ntp_gettime is the same as the time_state
    # member of Ntptimeval. So don't bother returning it separately.
    _libc.ntp_gettime(ctypes.byref(tv))
    return tv
