import ctypes
import os

# A few defs to handle mounting and umounting a usb key

def mount(source, target, fs, readonly=True, options=''):
    """
    Mount a device at a specified mountpoint
    :param source: str
    :param target: str
    :param fs: str
    :param readonly: bool
    :param options: str
    :return: bool
    """
    ret = ctypes.CDLL('libc.so.6', use_errno=True).mount(ctypes.c_char_p(source), ctypes.c_char_p(target), ctypes.c_char_p(fs), int(readonly), options)
    if ret < 0:
        errno = ctypes.get_errno()
        raise RuntimeError("Error mounting {} ({}) on {} with options '{}': {}".
        format(source, fs, target, options, os.strerror(errno)))

def umount(target):
    """
    Unmount a mountpoint
    :param target:
    :return:
    """
    ret = ctypes.CDLL('libc.so.6', use_errno=True).umount2(ctypes.c_char_p(target),1)
    if ret < 0:
        errno = ctypes.get_errno()
        raise RuntimeError("Error umount {} : {}".
        format(target, os.strerror(errno)))

def cleanup_umount(mountpoint):
    """
    Cleaup after a disk is pulled out
    :param mountpoint:
    :return:
    """
    try:
        if os.path.ismount(mountpoint):
            umount(mountpoint)
        if os.path.exists(mountpoint):
            os.rmdir(mountpoint)
        return True
    except:
        return False