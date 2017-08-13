"""client module to be uploaded remote machines to collect statistics

running the client script requires one command line parameter: outpath,
where the resultant encrypted serialized xml will be written.

The script reads several statistics from the underlying operating system,
for Windows environment, it also reads Security System Logs.

All data (statistics and logs) retrieved from the system are dumped into xml.
Then, the xml structure is serialized into string.
Finally, serialized xml data is encrypted with AES,
which is written into the output path.

The script is designed to handle all possible exceptions
that may raise during system calls, except one possible while writing the output.

So, it is the caller's responsibility to guarantee the required rights
to write to the outpath.

Example usage:

python client.py stat.bin

"""

from __future__ import print_function

import argparse
import time

import Crypto.Cipher.AES
import lxml.etree
import psutil

# AES constants
AES_BLOCK_SIZE = 16
AES_PADDER = '0'
AES_KEY = 'dPAE7nR7muB9JAgd'
AES_IV = 'BsJzfu9sARsUnHSH'

# xml tags
TAG_ROOT = 'root'
TAG_STATS = 'stats'
TAG_STAT = 'stat'
TAG_LOGS = 'logs'
TAG_LOG = 'log'

# xml attributes
ATTRIBUTE_TYPE = 'type'
ATTRIBUTE_VALUE = 'value'
ATTRIBUTE_LOG_ID = 'log_id'
ATTRIBUTE_EVENT_TIME = 'event_time'
ATTRIBUTE_COMPUTER_NAME = 'computer_name'
ATTRIBUTE_CATEGORY = 'category'
ATTRIBUTE_RECORD_NUMBER = 'record_number'
ATTRIBUTE_SOURCE_NAME = 'source'
ATTRIBUTE_EVENT_TYPE = 'event_type'
ATTRIBUTE_MESSAGE = 'message'

# xml stat type values
TYPE_MEMORY = 'memory'
TYPE_CPU = 'cpu'
TYPE_UPTIME = 'uptime'

# windows log types
LOG_TYPE_SYSTEM = 'System'
LOG_TYPE_APPLICATION = 'Application'
LOG_TYPE_SECURITY = 'Security'

def create_stat(stat_type, stat_value):
    """create xml representation of a stat object
    and return it by wrapping in an xml element

    Args:
    stat_type (str): type string, see TYPE_* contants
    stat_value (str): value of the stat retrieved from system

    Returns:
    lxml.etree.Element: xml stat element
    """
    stat = lxml.etree.Element(TAG_STAT)
    stat.set(ATTRIBUTE_TYPE, str(stat_type))
    stat.set(ATTRIBUTE_VALUE, str(stat_value))
    return stat

def get_memory_usage():
    """return memory usage value read from system

    Returns:
    float: memory usage percentage
    """
    percent = psutil.virtual_memory().percent
    return percent

def get_cpu_usage():
    """return cpu usage value read from system

    Returns:
    float: cpu usage percentage
    """
    percent = psutil.cpu_percent()
    return percent

def get_uptime():
    """return uptime value read from system

    Returns:
    int: uptime seconds
    """
    start_time = psutil.boot_time()
    now = time.time()
    uptime = now - start_time
    return int(uptime)

def create_stats():
    """create all stat objects, wrap in xml and return xml element

    Returns:
    lxml.etree.Element: xml root element
    """
    stats = lxml.etree.Element(TAG_STATS)

    memory = create_stat(TYPE_MEMORY, get_memory_usage())
    cpu = create_stat(TYPE_CPU, get_cpu_usage())
    uptime = create_stat(TYPE_UPTIME, get_uptime())

    stats.append(memory)
    stats.append(cpu)
    stats.append(uptime)

    return stats

def create_logs(ipaddr, log_type):
    """reads windows event logs of type specified by log_type
    for machine specified by ipaddr and returns in a tuple array

    Args:
    ipaddr (str): machine ip address
    log_type (str): System|Application|Security (see LOG_TYPE_* constants)
    """
    logs = lxml.etree.Element(TAG_LOGS)
    logs.set(ATTRIBUTE_TYPE, log_type)

    # following packages (from win32api) are not available on platforms other than windows

    try:
        import win32con
        import win32evtlog
        import win32evtlogutil
        import winerror
    except ImportError:
        # current platform is not Windows
        return logs

    try:
        hand = win32evtlog.OpenEventLog(ipaddr, log_type)
    except Exception as error: # pragma no cover
        print('Exception in win32evtlog.OpenEventLog: {error}'.format(error=error))
        return logs

    #total = win32evtlog.GetNumberOfEventLogRecords(hand)
    flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
    events = win32evtlog.ReadEventLog(hand, flags, 0)

    event_map = {
        win32con.EVENTLOG_AUDIT_FAILURE: 'EVENTLOG_AUDIT_FAILURE',
        win32con.EVENTLOG_AUDIT_SUCCESS: 'EVENTLOG_AUDIT_SUCCESS',
        win32con.EVENTLOG_INFORMATION_TYPE: 'EVENTLOG_INFORMATION_TYPE',
        win32con.EVENTLOG_WARNING_TYPE: 'EVENTLOG_WARNING_TYPE',
        win32con.EVENTLOG_ERROR_TYPE: 'EVENTLOG_ERROR_TYPE',
    }

    while events:
        events = win32evtlog.ReadEventLog(hand, flags, 0)

        for event in events:
            try:
                event_id = str(winerror.HRESULT_CODE(event.EventID))
                event_time = event.TimeGenerated.Format()
                event_computer_name = event.ComputerName
                event_category = str(event.EventCategory)
                event_type = event_map.get(event.EventType, 'unknown')
                event_source_name = event.SourceName
                event_record_number = str(event.RecordNumber)
                event_message = win32evtlogutil.SafeFormatMessage(event, log_type)

                node = lxml.etree.Element(TAG_LOG)
                node.set(ATTRIBUTE_LOG_ID, event_id)
                node.set(ATTRIBUTE_EVENT_TIME, event_time)
                node.set(ATTRIBUTE_COMPUTER_NAME, event_computer_name)
                node.set(ATTRIBUTE_CATEGORY, event_category)
                node.set(ATTRIBUTE_RECORD_NUMBER, event_record_number)
                node.set(ATTRIBUTE_SOURCE_NAME, event_source_name)
                node.set(ATTRIBUTE_EVENT_TYPE, event_type)
                node.set(ATTRIBUTE_MESSAGE, event_message)

                logs.append(node)
            except Exception as error: # pragma no cover
                print('Exception in win32evtlog.ReadEventLog.loop: {error}'.format(error=error))

    return logs

def add_padding(message, block_size, padder):
    """add left padding to the message to guarantee that
    the length of the message is a multiple of block_size

    Args:
    message (str): base message string
    block_size (int): the integer value that the message length must be multiple of
    padder (str): padding character to fill

    Returns:
    str: message with left padding
    """
    message_length = len(message)
    remaining = message_length % block_size

    if remaining > 0:
        padding_length = block_size - remaining
        padding = padding_length * padder
        padded_message = '{padding}{message}'.format(
            padding=padding,
            message=message,
        )
    else:
        padded_message = message

    return padded_message

def serialize(root):
    """serialize xml object to string and return it

    Args:
    root (lxml.etree.Element): root element of xml object

    Returns:
    str: serialized form of root
    """
    serialized = lxml.etree.tostring(root, pretty_print=True)
    return serialized

def encrypt(message, block_size, padder, key, init_vector):
    """encrypt a message with AES and return it

    Args:
    message (str): message string to be encrypted
    block_size (int): AES block size
    padder (str): padding character
    key (str): AES key (16 bytes)
    init_vector (str): AES initialization vector (16 bytes)

    Returns:
    str: encrypted message
    """
    padded_message = add_padding(message, block_size, padder)
    obj = Crypto.Cipher.AES.new(key, Crypto.Cipher.AES.MODE_CBC, init_vector)
    encrypted = obj.encrypt(padded_message)
    return encrypted

def run(outfilepath):
    """collect all stats and logs, then write to output file
    """
    root = lxml.etree.Element(TAG_ROOT)
    stats = create_stats()
    logs = create_logs('localhost', LOG_TYPE_SECURITY)
    root.append(stats)
    root.append(logs)
    serialized = serialize(root)
    encrypted = encrypt(serialized, AES_BLOCK_SIZE, AES_PADDER, AES_KEY, AES_IV)

    with open(outfilepath, 'wb') as outfile:
        outfile.write(encrypted)

def main():
    """main function, entry point to execution
    """
    parser = argparse.ArgumentParser(description='statistics collector client')
    parser.add_argument('outfilepath', type=str, help='path to write output')

    args = parser.parse_args()
    run(args.outfilepath)

if __name__ == '__main__': # pragma no cover
    main()
