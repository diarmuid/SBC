import pyudev
from mountdefs import mount,umount,cleanup_umount
import os
from time import sleep

MOUNTDIR="/mnt/usbkey"


def handle_drive(action, device):
    """
    Callback function from pyudev to handle the mounting and umounting of a usb key
    :param action:
    :param device:
    :return:
    """

    if action == "add":
        if 'DEVNAME' in device and 'ID_FS_TYPE' in device and 'DEVTYPE' in device:
            fstype = device.get('ID_FS_TYPE')
            devname = device.get('DEVNAME')
            devtype = device.get('DEVTYPE')
            id_fs_label = device.get('ID_FS_LABEL')

            if 'UDISKS_PARTITION_SIZE' in device:
                size_in_MB = int(int(device.get('UDISKS_PARTITION_SIZE')) / (1024*1024))
            else:
                size_in_MB = 0

            if fstype == "vfat" and devtype == "partition" :
                # We should never have a second drive mounted
                if not os.path.exists(MOUNTDIR):
                    os.mkdir(MOUNTDIR)
                else:
                    cleanup_umount(MOUNTDIR)
                # Settling period. Not sure if needed
                sleep(2)
                try:
                    mount(devname,MOUNTDIR,fstype,readonly=True)
                except Exception as e:
                    return False
                else:
                    print "Mounted {} at {} on {} {:d} MB".format(id_fs_label,devname,MOUNTDIR,size_in_MB)
                    return True

    elif action == "remove":
        if cleanup_umount(MOUNTDIR):
            print "{} Ejected".format(device.get('ID_FS_LABEL'))
        else:
            print "Failed to cleanly eject disk"
            return False


context = pyudev.Context()
monitor = pyudev.Monitor.from_netlink(context)
monitor.filter_by('block')

observer = pyudev.MonitorObserver(monitor, handle_drive)

observer.start()

while True:
    sleep(1)