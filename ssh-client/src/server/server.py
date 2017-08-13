"""a statistics collector from remote machines

Server class provided by this module collects and saves several statistics
from remote machines.

Server writes these statistics to a database.

It sends alert messages when required to predefined mail addresses.

Configuration of the server shall be done by an xml configuration file,
which contains information (mostly credentials) for these components:

- clients
- database
- mailer

For full reference of configuration file see *** bla bla bla ***

While the server runs, it first connect to a client via ssh,
sftp channel is opened as well on top of ssh.

Following a successful connection, server uploads the client script,
which shall also be provided in the config file (srcpath), to the target path.

The client script is executed on the remote machine, and an output file
is expected to be created under a given path.

Server reads the data from the output file (AES encrypted, serialized xml),
decrypts it, deserialize back to xml, and then it extracts required statistics
to write to the database.

If it detects any alert value for predetermined statistics,
an automatic mail is sent to the specified mail address.

Classes:

Server: manager class orchestrating the other components
Database: handles database queries, i.e., save statistics and logs
Mailer: sends mail when necessary
Client: an ssh client wrapper corresponding to remote machine
Alert: alert configuration for a specific statistics
MachineStat: database table representation for statistics
MachineLog: database table representation for Windows Event Logs

Usage:
python server.py <config-path> <log-path> [-loglevel debug|info|warning|error|critical]
"""

from __future__ import print_function

import argparse
import datetime
import logging
import smtplib
import socket
import sys
import threading

from abc import ABCMeta, abstractmethod

import paramiko
import lxml.etree
import Crypto.Cipher.AES

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils.functions import database_exists, create_database

# AES constants
AES_BLOCK_SIZE = 16
AES_PADDER = '0'
AES_KEY = 'dPAE7nR7muB9JAgd'
AES_IV = 'BsJzfu9sARsUnHSH'

# xml tags (config)
TAG_ROOT = 'root'
TAG_SRCPATH = 'srcpath'
TAG_CLIENTS = 'clients'
TAG_CLIENT = 'client'
TAG_ALERT = 'alert'
TAG_DATABASE = 'database'
TAG_MAILER = 'mailer'
TAG_MULTITHREAD = 'multithread'

# xml tags (client specific)
TAG_STATS = 'stats'
TAG_STAT = 'stat'
TAG_LOGS = 'logs'
TAG_LOG = 'log'

# xml attributes
ATTRIBUTE_ENGINE = 'engine'
ATTRIBUTE_IP = 'ip'
ATTRIBUTE_PORT = 'port'
ATTRIBUTE_USERNAME = 'username'
ATTRIBUTE_PASSWORD = 'password'
ATTRIBUTE_MAIL = 'mail'
ATTRIBUTE_EXECPATH = 'execpath'
ATTRIBUTE_OUTPATH = 'outpath'
ATTRIBUTE_TYPE = 'type'
ATTRIBUTE_LIMIT = 'limit'
ATTRIBUTE_VALUE = 'value'
ATTRIBUTE_NAME = 'name'
ATTRIBUTE_HOST = 'host'
ATTRIBUTE_PORT = 'port'
ATTRIBUTE_TIMEOUT = 'timeout'
ATTRIBUTE_ENABLED = 'enabled'

# xml attributes (client specific)
ATTRIBUTE_LOG_ID = 'log_id'
ATTRIBUTE_EVENT_TIME = 'event_time'
ATTRIBUTE_COMPUTER_NAME = 'computer_name'
ATTRIBUTE_CATEGORY = 'category'
ATTRIBUTE_RECORD_NUMBER = 'record_number'
ATTRIBUTE_SOURCE_NAME = 'source_name'
ATTRIBUTE_EVENT_TYPE = 'event_type'
ATTRIBUTE_MESSAGE = 'message'

# Base for sqlalchemy models
Base = declarative_base()

class MachineStat(Base):
    """Database table for statistics
    """

    __tablename__ = 'machinestat'

    id = Column(Integer, primary_key=True)
    ipaddr = Column(String(255))
    stat_type = Column(String(255))
    stat_value = Column(String(255))
    created_at = Column(DateTime(), default=datetime.datetime.now)

class MachineLog(Base):
    """Database table for logs
    """

    __tablename__ = 'machinelog'

    id = Column(Integer, primary_key=True)
    ipaddr = Column(String(255))
    log_type = Column(String(255))
    log_id = Column(String(255))
    event_time = Column(String(255))
    computer_name = Column(String(255))
    category = Column(String(255))
    record_number = Column(String(255))
    source_name = Column(String(255))
    event_type = Column(String(255))
    message = Column(String(255))
    created_at = Column(DateTime(), default=datetime.datetime.now)

class Helper(object):
    """provides utilities for XML and AES operations
    """

    @classmethod
    def clear_padding(cls, message, padder):
        """clear padding from AES encrypted message

        Args:
        message (str): message with padding
        padder (str): padding character

        Returns:
        str: message without padding
        """
        clean_message = message.lstrip(padder)
        return clean_message

    @classmethod
    def deserialize(cls, serialized):
        """convert string to xml

        Args:
        serialized (str): string to be converted to xml

        Returns:
        lxml.etree.Element: xml root element
        """
        root = None
        try:
            root = lxml.etree.fromstring(serialized)
        except lxml.etree.XMLSyntaxError as error:
            logging.error('unable to deserialize to XML: {error}'.format(error=error))
            root = None
        except ValueError as error:
            logging.error('unable to deserialize to XML: {error}'.format(error=error))
            root = None

        return root

    @classmethod
    def decrypt(cls, encrypted):
        """decrypt AES message

        Args:
        encrypted (str): encrypted message

        Returns:
        str: decrypted message
        """
        padded_message = ''
        obj = Crypto.Cipher.AES.new(AES_KEY, Crypto.Cipher.AES.MODE_CBC, AES_IV)
        try:
            padded_message = obj.decrypt(encrypted)
        except ValueError as error:
            logging.error('unable to decrypt: {error}'.format(error=error))
        except TypeError as error:
            logging.error('unable to decrypt: {error}'.format(error=error))

        message = cls.clear_padding(padded_message, AES_PADDER)
        return message

class Alert(object):
    """container class for alert description

    Args:
    config (lxml.etree.Element): xml Element holding config parameters

    Attributes:
    is_valid (bool): shows whether the config object is OK
    stat_type (str): name of the statistics
    limit (float): percentage limit for the statistics value
    """

    def __init__(self, config):
        self.is_valid = True
        self.stat_type = None
        self.limit = None

        stat_type = config.get(ATTRIBUTE_TYPE)
        limit = config.get(ATTRIBUTE_LIMIT)

        if stat_type is not None:
            self.stat_type = stat_type
        else:
            logging.error('missing/invalid attribute in client alert config: "{attribute}"'.format(
                attribute=ATTRIBUTE_TYPE))
            self.is_valid = False

        if limit is not None:
            limit = limit.rstrip('%')
            try:
                self.limit = float(limit)
            except ValueError:
                logging.error(
                    'missing/invalid attribute in client alert config: "{attribute}"'.format(
                        attribute=ATTRIBUTE_LIMIT))
                self.is_valid = False
        else:
            logging.error('missing/invalid attribute in client alert config: "{attribute}"'.format(
                attribute=ATTRIBUTE_LIMIT))
            self.is_valid = False

    def is_mail_required(self, value):
        """compare value to limit
        if value is above limit return True else return False

        Args:
        value (float): measured value of statistics

        Returns:
        bool: True if value is above limit else False
        """
        is_required = value >= self.limit
        return is_required

class ClientObserver(object):
    """Abstract observer class for Client
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def did_client_executed(self, client, output): # pragma no cover
        """notifies the observer that client finished execution

        Args:
        client (Client): client sending the notification
        output (str): output produced by the client
        """
        pass

class Client(object):
    """this class represents a client machine

    Args:
    config (lxml.etree.Element): xml Element holding config parameters

    Attributes:
    is_valid (bool): shows whether the config object is OK
    ipaddr (str): ip address of remote machine
    port (int): port number for ssh connection
    username (str): username for ssh connection
    password (str): password for ssh connection
    mail (str): mail address to send mail in case of alert
    execpath (str): path on the remote machine where to put the client script
    alerts (list<Alert>): alert objects
    """

    def __init__(self, config):
        self.is_valid = True
        self.ipaddr = None
        self.port = None
        self.username = None
        self.password = None
        self.mail = None
        self.execpath = None
        self.outpath = None
        self.alerts = []

        # list of registered observers (ClientObserver)
        self.observers = []

        ipaddr = config.get(ATTRIBUTE_IP)
        port = config.get(ATTRIBUTE_PORT)
        username = config.get(ATTRIBUTE_USERNAME)
        password = config.get(ATTRIBUTE_PASSWORD)
        mail = config.get(ATTRIBUTE_MAIL)
        execpath = config.get(ATTRIBUTE_EXECPATH)
        outpath = config.get(ATTRIBUTE_OUTPATH)

        if ipaddr is not None:
            self.ipaddr = ipaddr
        else:
            logging.error('missing/invalid attribute in client config: "{attribute}"'.format(
                attribute=ATTRIBUTE_IP))
            self.is_valid = False

        if port is not None and port.isdigit():
            self.port = int(port)
        else:
            logging.error('missing/invalid attribute in client config: "{attribute}"'.format(
                attribute=ATTRIBUTE_PORT))
            self.is_valid = False

        if username is not None:
            self.username = username
        else:
            logging.error('missing/invalid attribute in client config: "{attribute}"'.format(
                attribute=ATTRIBUTE_USERNAME))
            self.is_valid = False

        if password is not None:
            self.password = password
        else:
            logging.error('missing/invalid attribute in client config: "{attribute}"'.format(
                attribute=ATTRIBUTE_PASSWORD))
            self.is_valid = False

        if mail is not None:
            self.mail = mail
        else:
            logging.error('missing/invalid attribute in client config: "{attribute}"'.format(
                attribute=ATTRIBUTE_MAIL))
            self.is_valid = False

        if execpath is not None:
            self.execpath = execpath
        else:
            logging.error('missing/invalid attribute in client config: "{attribute}"'.format(
                attribute=ATTRIBUTE_EXECPATH))
            self.is_valid = False

        if outpath is not None:
            self.outpath = outpath
        else:
            logging.error('missing/invalid attribute in client config: "{attribute}"'.format(
                attribute=ATTRIBUTE_OUTPATH))
            self.is_valid = False

        cfgs = config.findall(TAG_ALERT)
        for cfg in cfgs:
            alert = Alert(cfg)
            self.alerts.append(alert)
            if not alert.is_valid:
                logging.warning('skipping invalid alert in client config')
                self.is_valid = False

    def register(self, observer):
        """registers an observer

        if observer is already registered, then ignore it silently
        """
        if not observer in self.observers:
            self.observers.append(observer)

    def unregister(self, observer):
        """unregisteres an observer

        if observer is not registered, then ignore it silently

        Args:
        observer (ClientObserver): observer object to be registered
        """
        if observer in self.observers:
            self.observers.remove(observer)

    def unregister_all(self):
        """unregister all observers
        """
        if self.observers:
            del self.observers[:]

    def notify_observers(self, output):
        """send message to all observers

        Args:
        output (str): output produced by the client (can be None)
        """
        for observer in self.observers:
            observer.did_client_executed(self, output)

    def get_alert_for_stat_type(self, stat_type):
        """traverse alerts to find a match for stat_type
        if found then return the matching alert else return None

        Args:
        stat_type (str): name of the statistics

        Returns:
        Alert: matching Alert object from alerts or None
        """
        result = None
        for alert in self.alerts:
            if alert.stat_type == stat_type:
                result = alert
                break

        return result

    def create_mail_for_alert(self, stat_type, stat_value, alert_limit):
        """create mail content (subject and body)
        for alert limit

        Args:
        stat_type (str): name of the statistics
        stat_value (int): measurement value of statistics
        alert_limit (int): alert limit value of statistics

        Returns:
        str: mail content including subject and body
        """
        message = """
            Subject: {stat_type} alert on {ip}

            {stat_type} value exceeded the alert limit on machine with ip {ip}

            limit: {alert_limit}
            measurement: {measurement}

            Sincerely,
            Server

        """.format(
            stat_type=stat_type,
            ip=self.ipaddr,
            alert_limit=alert_limit,
            measurement=stat_value)

        return message

    def run(self, srcpath):
        """copy the script to the remote machine
        run the script on the remote machine
        and return stderr and stdout lines
        via ssh/ftp

        Args:
        srcpath (str): path to client script file

        Returns:
        str: content of the client output file -- self.outpath
        """
        output = None

        command = 'python {scriptfilepath} {outfilepath}'.format(
            scriptfilepath=self.execpath,
            outfilepath=self.outpath)

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(self.ipaddr,
                        port=self.port,
                        username=self.username,
                        password=self.password,
                        allow_agent=False,
                        look_for_keys=False)
        except paramiko.ssh_exception.BadHostKeyException as error: # pragma no cover
            logging.error('BadHostKeyException error in Client.run ssh.connect: {error}'.format(
                error=error))
            self.notify_observers(None)
            return
        except paramiko.ssh_exception.AuthenticationException as error:
            logging.error('AuthenticationException error in Client.run ssh.connect: {error}'.format(
                error=error))
            self.notify_observers(None)
            return
        except paramiko.ssh_exception.SSHException as error: # pragma no cover
            logging.error('SSHException error in Client.run ssh.connect: {error}'.format(
                error=error))
            self.notify_observers(None)
            return
        except socket.error as error:
            logging.error('socket error in Client.run ssh.connect: {error}'.format(
                error=error))
            self.notify_observers(None)
            return

        sftp = ssh.open_sftp()

        try:
            sftp.put(srcpath, self.execpath)
        except OSError as error:
            logging.error('OSError in Client.run ftp.put: {error}'.format(
                error=error))
            self.notify_observers(None)
            return

        try:
            stdin, stdout, stderr = ssh.exec_command(command)
        except paramiko.ssh_exception.SSHException as error: # pragma no cover
            logging.error('SSHException error in Client.run ssh.exec_command: {error}'.format(
                error=error))
            self.notify_observers(None)
            return

        logging.debug('client [{ipaddr}] {channel}:\n{content}'.format(
            ipaddr=self.ipaddr,
            channel='stdout',
            content=stdout.read()))

        logging.debug('client [{ipaddr}] {channel}:\n{content}'.format(
            ipaddr=self.ipaddr,
            channel='stderr',
            content=stderr.read()))

        try:
            with sftp.open(self.outpath, 'rb') as outfile:
                output = outfile.read()
        except IOError as error:
            print(self.outpath)
            logging.error('IOError error in Client.run sftp.open: {error}'.format(
                error=error))
            self.notify_observers(None)
            return

        try:
            sftp.remove(self.execpath)
            sftp.remove(self.outpath)
        except paramiko.ssh_exception.SSHException as error: # pragma no cover
            logging.error('SSHException error in Client.run ftp.remove: {error}'.format(
                error=error))
        finally:
            sftp.close()

        self.notify_observers(output)

        return output

class Database(object):
    """handler for database operations

    Args:
    config (lxml.etree.Element): xml Element holding config parameters

    Attributes:
    is_valid (bool): shows whether the config object is OK
    name (str): database name
    username (str): database username
    password (str): database password
    host (str): database host ip
    port (int): database host port

    url (str): connection url for sqlalchemy
    sqlengine (sqlalchemy.engine.Engine): sqlalchemy engine
    sessionmaker (class<Session>): sqlalchemy session maker
    """

    def __init__(self, config):
        self.is_valid = True
        self.engine = 'mysql'
        self.name = None
        self.username = None
        self.password = None
        self.host = None
        self.port = None

        self.url = None
        self.sqlengine = None
        self.sessionmaker = None

        #engine = config.get(ATTRIBUTE_ENGINE)
        name = config.get(ATTRIBUTE_NAME)
        username = config.get(ATTRIBUTE_USERNAME)
        password = config.get(ATTRIBUTE_PASSWORD)
        host = config.get(ATTRIBUTE_HOST)
        port = config.get(ATTRIBUTE_PORT)

        #if engine is not None:
        #    self.engine = engine
        #else:
        #    logging.error('missing/invalid attribute in database config: "{attribute}"'.format(
        #        attribute=ATTRIBUTE_ENGINE))
        #    self.is_valid = False

        if name is not None:
            self.name = name
        else:
            logging.error('missing/invalid attribute in database config: "{attribute}"'.format(
                attribute=ATTRIBUTE_NAME))
            self.is_valid = False

        if username is not None:
            self.username = username
        else:
            logging.error('missing/invalid attribute in database config: "{attribute}"'.format(
                attribute=ATTRIBUTE_USERNAME))
            self.is_valid = False

        if password is not None:
            self.password = password
        else:
            logging.error('missing/invalid attribute in database config: "{attribute}"'.format(
                attribute=ATTRIBUTE_PASSWORD))
            self.is_valid = False

        if host is not None:
            self.host = host
        else:
            logging.error('missing/invalid attribute in database config: "{attribute}"'.format(
                attribute=ATTRIBUTE_HOST))
            self.is_valid = False

        if port is not None and port.isdigit():
            self.port = int(port)
        else:
            logging.error('missing/invalid attribute in database config: "{attribute}"'.format(
                attribute=ATTRIBUTE_PORT))
            self.is_valid = False

        if self.is_valid:
            self.url = '{engine}://{username}:{password}@{host}:{port}/{name}'.format(
                engine=self.engine,
                username=self.username,
                password=self.password,
                host=self.host,
                port=self.port,
                name=self.name)

            self.sqlengine = create_engine(self.url, echo=True)

            try:
                if not database_exists(self.sqlengine.url): # pragma no cover
                    create_database(self.sqlengine.url)
            except OperationalError as error: # pragma no cover
                logging.critical('database connection failed: {error}'.format(error=error))
                sys.exit('database connection failed')

            Base.metadata.create_all(self.sqlengine)

            self.sessionmaker = sessionmaker(bind=self.sqlengine)

    def make_session(self):
        """create a database session
        """
        return self.sessionmaker()

    def insert_stats(self, ipaddr, stats):
        """insert record to the machinestat

        A session is created per insertion, which may cause performance issues
        To avoid such issues, the client of this class can create a session by itself,
        then add records to that session. The commit operation can be triggerred at any time.

        Args:
        ipaddr (str): column value
        stats (list<lxml.etree.Element): stat elements
        """
        session = self.make_session()

        for stat in stats:
            stat_type = stat.get(ATTRIBUTE_TYPE, '0.0')
            stat_value = stat.get(ATTRIBUTE_VALUE, '0.0')

            record = MachineStat(ipaddr=ipaddr, stat_type=stat_type, stat_value=stat_value)
            session.add(record)

        session.commit()

    def insert_logs(self, ipaddr, logs):
        """insert record(s) to the machinelog

        Args:
        ipaddr (str): column value
        logs (list<lxml.etree.Element): log elements
        """
        if logs is None:
            logging.info('no logs received')
            return

        session = self.make_session()

        log_type = logs.get(ATTRIBUTE_TYPE, '')

        for log in logs:
            log_id = log.get(ATTRIBUTE_LOG_ID, '')
            event_time = log.get(ATTRIBUTE_EVENT_TIME, '')
            computer_name = log.get(ATTRIBUTE_COMPUTER_NAME, '')
            category = log.get(ATTRIBUTE_CATEGORY, '')
            record_number = log.get(ATTRIBUTE_RECORD_NUMBER, '')
            source_name = log.get(ATTRIBUTE_SOURCE_NAME, '')
            event_type = log.get(ATTRIBUTE_EVENT_TYPE, '')
            message = log.get(ATTRIBUTE_MESSAGE, '')

            record = MachineLog(
                ipaddr=ipaddr,
                log_type=log_type,
                log_id=log_id,
                event_time=event_time,
                computer_name=computer_name,
                category=category,
                record_number=record_number,
                source_name=source_name,
                event_type=event_type,
                message=message)

            session.add(record)

        session.commit()

class Mailer(object):
    """handler for sending mail

    Args:
    config (lxml.etree.Element): xml Element holding config parameters

    Attributes:
    is_valid (bool): shows whether the config object is OK
    ipaddr (str): mail server ip address
    port (str): mail server port (smtp: 25)
    timeout (int): server connection timeout
    username (str): mail sender
    password (str): mail sender password
    connection (smtplib.SMTP): connection holder
    """

    def __init__(self, config):
        self.is_valid = True
        self.ipaddr = None
        self.port = None
        self.timeout = None
        self.username = None
        self.password = None
        self.connection = None

        ipaddr = config.get(ATTRIBUTE_IP)
        port = config.get(ATTRIBUTE_PORT)
        timeout = config.get(ATTRIBUTE_TIMEOUT)
        username = config.get(ATTRIBUTE_USERNAME)
        password = config.get(ATTRIBUTE_PASSWORD)

        if ipaddr is not None:
            self.ipaddr = ipaddr
        else:
            logging.error('missing/invalid attribute in mailer config: "{attribute}"'.format(
                attribute=ATTRIBUTE_IP))
            self.is_valid = False

        if port is not None and port.isdigit():
            self.port = int(port)
        else:
            logging.error('missing/invalid attribute in mailer config: "{attribute}"'.format(
                attribute=ATTRIBUTE_PORT))
            self.is_valid = False

        if timeout is not None and timeout.isdigit():
            self.timeout = int(timeout)
        else:
            logging.error('missing/invalid attribute in mailer config: "{attribute}"'.format(
                attribute=ATTRIBUTE_TIMEOUT))
            self.is_valid = False

        if username is not None:
            self.username = username
        else:
            logging.error('missing/invalid attribute in mailer config: "{attribute}"'.format(
                attribute=ATTRIBUTE_USERNAME))
            self.is_valid = False

        if password is not None:
            self.password = password
        else:
            logging.error('missing/invalid attribute in mailer config: "{attribute}"'.format(
                attribute=ATTRIBUTE_PASSWORD))
            self.is_valid = False

    def connect(self):
        """initialize mail server connection
        """
        if self.connection is not None:
            logging.info('mailer already connected')
            return

        try:
            self.connection = smtplib.SMTP(self.ipaddr, port=self.port, timeout=self.timeout)
            self.connection.starttls()
            self.connection.login(self.username, self.password)
            logging.info('mailer connected')

        except smtplib.SMTPConnectError as error: # pragma no cover
            logging.error('SMTPConnectError in Mailer.connect: {error}'.format(error=error))

        except smtplib.SMTPAuthenticationError as error: # pragma no cover
            logging.error('SMTPAuthenticationError in Mailer.connect: {error}'.format(error=error))

        except socket.timeout as error: # pragma no cover
            logging.error('timeout in Mailer.connect: {error}'.format(error=error))

        except socket.error as error:
            logging.error('socket error in Mailer.connect: {error}'.format(error=error))

    def disconnect(self):
        """close mail server connection

        Returns:
        bool: True for successful disconnection False otherwise
        """
        result = False
        if self.connection is None:
            logging.warning('mailer is not connected')
        else:
            _ = self.connection.quit()
            logging.info('mailer disconnected')
            result = True

        return result

    def send(self, receivers, message):
        """send mail content provided in message
        to the receiver provided in receivers

        Args:
        receivers (list<str>): receiver mail address list
        message (str): mail content -- subject and body seperated by new line

        Returns:
        bool: True if message is sent successfully else False
        """
        result = False
        if self.connection is None:
            logging.warning('Mailer is not connected')
            result = False
        else:
            try:
                _ = self.connection.sendmail(self.username, receivers, message)
                result = True

            except smtplib.SMTPRecipientsRefused as error: # pragma no cover
                logging.error('SMTPRecipientsRefused exception in Mailer.send: {error}'.format(
                    error=error))
            except smtplib.SMTPHeloError as error: # pragma no cover
                logging.error('SMTPHeloError exception in Mailer.send: {error}'.format(
                    error=error))
            except smtplib.SMTPSenderRefused as error: # pragma no cover
                logging.error('SMTPSenderRefused exception in Mailer.send: {error}'.format(
                    error=error))
            except smtplib.SMTPDataError as error: # pragma no cover
                logging.error('SMTPDataError exception in Mailer.send: {error}'.format(
                    error=error))

        return result

class Server(ClientObserver):
    """handler for server to manage clients,
    client outputs, database and mailer

    Args:
    config (lxml.etree.Element): xml Element holding config parameters

    Attributes:
    is_valid (bool): shows whether the config object is OK
    srcpath (str): path to client script file
    clients (list<Client>): client list
    database (Database): database handler
    mailer (Mailer): mail handler
    threads (List<threading.Thread): keeps the thread list for multithread mode
    multithread_enabled (bool): indicates multithread mode is selected
    """

    def __init__(self, file_path):
        self.is_valid = False

        self.srcpath = None
        self.clients = []
        self.database = None
        self.mailer = None

        self.threads = []
        self.multithread_enabled = False

        self.read_config(file_path)

    def read_config(self, file_path):
        """configure server with xml file provided in file_path

        Args:
        file_path (str): path to config file

        Returns:
        bool: True if file is read successfully else False
        """
        try:
            config = lxml.etree.parse(file_path)
        except IOError as error:
            logging.error('config file read error: {error}'.format(error=error))
            return False
        except lxml.etree.XMLSyntaxError as error:
            logging.error('config file parse error: {error}'.format(error=error))
            return False

        root = config.getroot()

        node = root.find(TAG_SRCPATH)
        if node is None:
            logging.error('unable to find "{tag}" in config'.format(tag=TAG_SRCPATH))
            return False

        srcpath = node.get(ATTRIBUTE_VALUE)
        if srcpath is None:
            logging.error('unable to find attribute "{attribute}" in "{tag}" in config'.format(
                attribute=ATTRIBUTE_VALUE,
                tag=TAG_SRCPATH))
            return False

        try:
            open(srcpath)
        except IOError as error:
            logging.error('unable to read client script: {file_path}'.format(
                file_path=srcpath))
            return False

        self.srcpath = srcpath

        clients = root.find(TAG_CLIENTS)
        if clients is None:
            logging.error('unable to find "{tag}" in config'.format(tag=TAG_CLIENTS))
            return False

        client_list = clients.findall(TAG_CLIENT)
        for cfg in client_list:
            client = Client(cfg)
            if client.is_valid:
                client.register(self)
                self.clients.append(client)
            else:
                logging.warning('skipping invalid client in config')

        database = root.find(TAG_DATABASE)
        if database is None:
            logging.error('unable to find "{tag}" in config'.format(tag=TAG_DATABASE))
            return False

        self.database = Database(database)
        if not self.database.is_valid:
            logging.error('invalid database config')
            return False

        mailer = root.find(TAG_MAILER)
        if mailer is None:
            logging.error('unable to find "{tag}" in config'.format(tag=TAG_MAILER))
            return False

        self.mailer = Mailer(mailer)
        if not self.mailer.is_valid:
            logging.error('invalid mailer config')
            return False

        multithread = root.find(TAG_MULTITHREAD)
        if multithread is not None:
            enabled = multithread.get(ATTRIBUTE_ENABLED)
            self.multithread_enabled = enabled == 'true'

        self.is_valid = True
        logging.info('server initiated')

        return self.is_valid

    def handle_client_stat(self, client, stat):
        """handle a single statistics of a single client
        check if the alert exceeded and if so send mail

        Args:
        client (Client): client object to be handled
        stat (lxml.etree.Element): xml Element holding statistics

        Returns:
        bool: True if alert limit is not exceeded else False
        """
        stat_type = stat.get(ATTRIBUTE_TYPE)
        stat_value = float(stat.get(ATTRIBUTE_VALUE))
        alert = client.get_alert_for_stat_type(stat_type)
        if alert is None:
            return False

        is_mail_required = alert.is_mail_required(stat_value)

        if not is_mail_required:
            return False

        mail_content = client.create_mail_for_alert(stat_type, stat_value, alert.limit)
        logging.debug('sending mail for {ip} {stat_type} measurement...'.format(
            ip=client.ipaddr,
            stat_type=stat_type))
        is_sent = self.mailer.send([client.mail], mail_content)
        if is_sent:
            logging.debug('sending mail for {ip} {stat_type} measurement OK'.format(
                ip=client.ipaddr,
                stat_type=stat_type))
        else:
            logging.debug('sending mail for {ip} {stat_type} measurement NOK'.format(
                ip=client.ipaddr,
                stat_type=stat_type))

        return True

    def did_client_executed(self, client, output):
        """handle a single client output

        Args:
        client (Client): client object that produced the output
        output (str): client output -- encrypted serialized xml data

        Returns:
        bool: True if no error occurs else False
        """
        if output is None:
            logging.warning(
                'skipping client {ip}:{port}...'.format(ip=client.ipaddr, port=client.port))
            return False

        response = Helper.decrypt(output.strip())
        logging.debug('response:\n\n{response}'.format(response=response))
        root = Helper.deserialize(response)

        if root is None:
            logging.warning(
                'unable to parse XML {ip}:{port}...'.format(ip=client.ipaddr, port=client.port))
            return False

        stats = root.find(TAG_STATS)
        self.database.insert_stats(client.ipaddr, stats)
        for stat in stats:
            self.handle_client_stat(client, stat)
        logs = root.find(TAG_LOGS)
        self.database.insert_logs(client.ipaddr, logs)

        logging.debug(
            'handling client {ip}:{port} DONE'.format(ip=client.ipaddr, port=client.port))

        return True

    def handle_client(self, client):
        """handle a single client to run the script and evaluate the output

        Args:
        client (Client): client object to be handled
        """
        logging.debug(
            'handling client {ip}:{port}...'.format(ip=client.ipaddr, port=client.port))

        if self.multithread_enabled:
            thread = threading.Thread(target=client.run, args=[self.srcpath])
            self.threads.append(thread)
        else:
            client.run(self.srcpath)

        logging.debug(
            'handling client {ip}:{port} DONE'.format(ip=client.ipaddr, port=client.port))

    def run(self):
        """run client script in all clients

        Returns:
        bool: True if runs (i.e., config is valid) else False
        """
        result = False
        if self.is_valid:
            logging.debug('server started to run')

            logging.debug('server is connecting to mailer')
            self.mailer.connect()
            logging.debug('server connected to mailer')

            logging.debug('server started to handle clients')
            for client in self.clients:
                self.handle_client(client)

            if self.multithread_enabled:
                for thread in self.threads:
                    thread.start()

                for thread in self.threads:
                    thread.join()

            logging.debug('server completed handling clients')

            logging.debug('server is diconnecting from mailer')
            self.mailer.disconnect()
            logging.debug('server diconnected from mailer')

            logging.debug('server completed running')

            result = True
        else:
            logging.critical('server is not configured properly')

        return result

def main():
    """main function, entry point to execution
    """
    log_levels = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL}

    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    parser = argparse.ArgumentParser(description='statistics collector server')

    parser.add_argument('conffilepath', type=str, help='path to read server config')
    parser.add_argument('logfilepath', type=str, help='path to write execution logs')
    parser.add_argument('-loglevel',
                        type=str,
                        choices=log_levels.keys(),
                        nargs='?',
                        const='info',
                        default='info',
                        help='level for execution logging')

    args = parser.parse_args()

    logging.basicConfig(filename=args.logfilepath,
                        format=log_format,
                        level=log_levels.get(args.loglevel, logging.NOTSET))
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

    server = Server(args.conffilepath)

    return server.run()

if __name__ == '__main__':  # pragma no cover
    main()
