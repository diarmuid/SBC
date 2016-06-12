import ctypes
import os

def mount(source, target, fs, readonly=True, options=''):
    ret = ctypes.CDLL('libc.so.6', use_errno=True).mount(source, target, fs, int(readonly), options)
    if ret < 0:
        errno = ctypes.get_errno()
        raise RuntimeError("Error mounting {} ({}) on {} with options '{}': {}".
        format(source, fs, target, options, os.strerror(errno)))


mount('/dev/sda1','/mnt/usbkey','vfat',readonly=True)