# Mount a usb key, check for expected task file.
# compile and program the task file
# Run as a daemon

import ConfigParser
import pyudev
from mountdefs import mount,umount,cleanup_umount
import os
from time import sleep
from daemonize import Daemonize
import logging

from AcraNetwork.McastSocket import McastSocket



CFG_FILE = "autocompile.cfg"
EXPECTED_FNAME = "allswi101.xidml"

SUCCESS = True
FAIL = False

class AutoCompilation(object):

    def __init__(self):

        self.usbkeydir = "/mnt/usbkey"
        self._setupObserver()
        self.taskfile = None
        self.requiredInstruments = None

    def _setupObserver(self):
        self.context = pyudev.Context()
        self.monitor = pyudev.Monitor.from_netlink(self.context)
        self.monitor.filter_by('block')
        self.observer = pyudev.MonitorObserver(self.monitor, self._handle_drive)
        self.observer.start()


    def _handle_drive(self,action, device):
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
                    size_in_MB = int(int(device.get('UDISKS_PARTITION_SIZE')) / (1024 * 1024))
                else:
                    size_in_MB = 0

                if fstype == "vfat" and devtype == "partition":
                    # We should never have a second drive mounted
                    if not os.path.exists(self.usbkeydir):
                        try:
                            os.mkdir(self.usbkeydir)
                        except:
                            return FAIL
                    else:
                        cleanup_umount(self.usbkeydir)
                    # Settling period. Not sure if needed
                    sleep(2)
                    try:
                        mount(devname, self.usbkeydir, fstype, readonly=True)
                    except Exception as e:
                        return False
                    else:
                        report_message(
                            "Mounted {} at {} on {} {:d} MB".format(id_fs_label, devname, self.usbkeydir, size_in_MB))
                        self.on_mounting()

        elif action == "remove":
            if 'DEVTYPE' in device:
                if device.get('DEVTYPE') == "partition":
                    if cleanup_umount(self.usbkeydir):
                        self.on_umounting("{} ejected cleanly".format(device.get('ID_FS_LABEL')))
                    else:
                        self.on_umounting("{} not ejected cleanly".format(device.get('ID_FS_LABEL')))



    def _validate_xml (self):
        """
        Take in a xidml task file and check that the relevant modules are present in the task file
        :return:
        """
        if not self.taskfile:
            raise Exception("Task file not defined")

        # Parse the xml file to find the required parts
        top_level_instruments = {}
        # Read in the task file
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(self.taskfile)
            root=tree.getroot()
            for instrument in root.findall("Instrumentation/InstrumentSet/Instrument"):
                part_ref = instrument.find("Manufacturer/PartReference").text
                if part_ref in top_level_instruments:
                    top_level_instruments[part_ref] += 1
                else:
                    top_level_instruments[part_ref] = 1
        except:
            raise Exception("Cound not parse the task file {}".format(self.taskfile))

        # Verify that we found the correct parts
        for part in self.requiredInstruments:
            if not part in top_level_instruments:
                raise Exception("ERROR. Did not find {} in the task file {}.".format(part,self.taskfile))
            elif self.requiredInstruments[part] != top_level_instruments[part]:
                raise Exception("ERROR. Did not find {} instances of part in task file {}".format(self.requiredInstruments[part],self.taskfile))

        return SUCCESS


    def _validate_mounted_drive (self):
        """
        If a drive is mounted, verify that it's contains a task file in the expected format and return the task file name
        :return: str
        """
        import os.path
        expected_fname = os.path.join(self.usbkeydir,EXPECTED_FNAME)
        if os.path.exists(expected_fname):
            self.taskfile = expected_fname
            return SUCCESS
        else:
            raise Exception("Cound not find expected task file {} in USB key".format(EXPECTED_FNAME))



    def _compile_task (self):
        """
        Compile a taskfile in standalone compiler and return on success
        :param taskfile: str
        :return: bool
        """
        pass

    def _program_task (self):
        """
        Program a taskfile using standalone compiler and return on success
        :param taskfile: str
        :return: bool
        """
        pass

    def on_mounting(self):
        """
        This is the core of the app. On insertion of a drive it performs all the steps to program the system.
        Returns 0 on success
        :return:
        """
        # Get the task file from the mounted drive
        try:
            self._validate_mounted_drive()
        except Exception as e:
            report_message(message="Failed to validate the mounted drive. {}".format(e),success=False)
            return 1

        # Check that the xml file has the expected products in ot
        try:
            self._validate_xml()
        except Exception as e:
            report_message(message="Failed to validate the xidml task file. {}".format(e),success=False)
            return 1

        # Attempt to compile the task
        try:
            self._compile_task()
        except Exception as e:
            report_message(message="Failed to compile task. {}".format(e),success=False)
            return 1

        # Attempt to program the task
        try:
            self._program_task()
        except Exception as e:
            report_message(message="Failed to progrma task. {}".format(e),success=False)
            return 1

        # Successfully mount and programed the task. Report success
        report_message(message="Successfully programmed task from {}".format(self.taskfile),success=True)
        return 0

    def on_umounting(self,msg=""):
        report_message(msg,success=True)
        clear_status()


def report_message (message,success=True):
    """
    Centralised reporting procedure.
    Generate iNetX or IENA packets with the message embedded in the data.
    Generate an output on the serial port for easy debug
    Pull LEDs to different colour to indicate error status
    :param message:
    :param success:
    :return:
    """
    logger.debug("Message = {}".format(message))

    # Send a message on the network
    udp_soc = McastSocket()
    udp_soc.mcast_add("235.0.0.1",iface='0.0.0.0')
    udp_soc.sendto(message,("235.0.0.1",4444))




def clear_status():
    """
    Clear any error status following the ejection of the disk
    :return:
    """
    pass


def main ():

    auto_comp = AutoCompilation()
    auto_comp.requiredInstruments = {"NET/SWI/101/B/SB2": 3, "KAM/CHS/06U": 1, "NET/REC/006/B": 1}

    while True:
        sleep(5)


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = False
fh = logging.FileHandler("/tmp/autocompile.log", "w")
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)
keep_fds = [fh.stream.fileno()]

daemon = Daemonize(app="autocompile", pid="/tmp/test.pid", action=main, keep_fds=keep_fds)
daemon.start()



