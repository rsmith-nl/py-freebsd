# file: freebsd.py
# vim:fileencoding=utf-8:fdm=marker:ft=python
#
# Copyright © 2019 R.F. Smith <rsmith@xs4all.nl>.
# SPDX-License-Identifier: MIT
# Created: 2019-07-07T23:56:25+0200
# Last modified: 2021-03-14T09:18:26+0100
"""Python bindings for some FreeBSD library calls on 64-bit architectures."""

import ctypes
import ctypes.util

# Load the C library
_libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)


def sysctlnametomib(name):
    """
    Python wrapper for sysctlnametomib(3).

    Arguments:
        name(str): Name of the sysctl

    Returns
        A ctypes array containing the MIB vector.
    """
    ln = name.count(".") + 1
    mib_t = ctypes.c_int * ln
    mib = mib_t()
    size_t = ctypes.c_size_t * 1
    size = size_t(ln)
    name_in = ctypes.c_char_p(bytes(name, encoding='ascii'))
    rv = _libc.sysctlnametomib(name_in, ctypes.byref(mib), ctypes.byref(size))
    if rv != 0:
        errno = ctypes.get_errno()
        raise ValueError(f'sysctlnametomib error: {errno}')
    return mib


def auto(data):
    """Convert data returned from a sysctl based on the content

    Arguments:
        data: string of bytes
    """
    if len(data) in [4, 8]:
        return to_int(data)
    if data.endswith(b'\x00') and sum(1 for j in data if j == 0) == 1:
        return to_string(data)
    return data


def _internal_sysctl(mib, namelen, convert):
    """Common parts of sysctl and sysctlbyname factored out."""
    # Retrieve the length of the necessary data buffer
    datasize = ctypes.c_size_t()
    rv = _libc.sysctl(
        ctypes.byref(mib), namelen, None, ctypes.byref(datasize), None, ctypes.c_size_t(0)
    )
    # Retrieve the data
    oldlen = ctypes.c_size_t(datasize.value)
    oldp = ctypes.create_string_buffer(datasize.value)
    rv = _libc.sysctl(
        ctypes.byref(mib), namelen, ctypes.byref(oldp), ctypes.byref(oldlen), None,
        ctypes.c_size_t(0)
    )
    if rv != 0:
        errno = ctypes.get_errno()
        raise ValueError(f'sysctl error: {errno}')
    if convert:
        return convert(oldp.raw)
    return oldp.raw


def sysctlbyname(name, convert=auto):
    """
    Python wrapper for sysctlbyname(3).

    Arguments:
        name (str): Name of the sysctl to query
        convert: Function to convert the data.
            Defaults to “convert=auto” for automatic conversion.
            Use “convert=None” for no conversion.

    Returns:
        The requested binary data, converted if desired.
    """
    mib = sysctlnametomib(name)
    namelen = ctypes.c_uint(len(mib))
    return _internal_sysctl(mib, namelen, convert=convert)


def sysctl(name, convert=auto):
    """
    Python wrapper for sysctl(3).

    Arguments:
        name: List or tuple of integers.
        convert: Function to convert the data.
            Defaults to “convert=auto” for automatic conversion.
            Use “convert=None” for no conversion.

    Returns:
        The requested data, converted if desired.
    """
    mib_t = ctypes.c_int * len(name)
    mib = mib_t(*name)
    namelen = ctypes.c_uint(len(name))
    return _internal_sysctl(mib, namelen, convert=convert)


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
    rv = sysctlbyname('kern.osrelease')
    return rv


def osrevision():
    """Returns operating system revision."""
    rv = sysctlbyname('kern.osrevision')
    return rv


def osreldate():
    """
    Returns the version of the currently running FreeBSD kernel.

    This is the value of __FreeBSD_version.
    """
    return _libc.getosreldate()


def version():
    """Returns operation system version."""
    rv = sysctlbyname('kern.version')
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


def to_int(value):
    """Convert binary sysctl value to integer."""
    return int.from_bytes(value, byteorder='little')


def to_degC(value):
    """Convert binary sysctl value to degree Centigrade."""
    return round(int.from_bytes(value, byteorder='little') / 10 - 273.15, 1)


def to_string(value):
    """Convert binary sysctl value to UTF-8 string."""
    return value.strip(b'\x00').decode('utf-8')
