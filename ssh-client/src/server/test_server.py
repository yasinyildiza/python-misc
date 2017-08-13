from __future__ import print_function

import os
import shutil
import smtplib
import sys
import unittest
import paramiko
import lxml.etree
import Crypto.Cipher
import mysql.connector
import server

class TestObserver(server.ClientObserver):

    def did_client_executed(self, client, output): # pragma no cover
        pass

class Helper(object): # pragma no cover
    config_path = 'test.config.xml'
    config_str = ''
    config = None

    @classmethod
    def clean_sys_args(cls):
        while len(sys.argv) > 1:
            del sys.argv[-1]

    @classmethod
    def reset_db(cls):
        database = cls.config.find('database')

        reset_sql = """
            DROP DATABASE IF EXISTS {name};
            CREATE DATABASE IF NOT EXISTS {name};

            USE {name};

            CREATE TABLE IF NOT EXISTS machinestat (
                ipaddr varchar(255) NOT NULL,
                stat_type varchar(255) NOT NULL,
                stat_value varchar(255) NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS machinelog (
                ipaddr varchar(255) NOT NULL,
                log_type varchar(255),
                log_id varchar(255),
                event_time varchar(255),
                computer_name varchar(255),
                category varchar(255),
                record_number varchar(255),
                source_name varchar(255),
                event_type varchar(255),
                message varchar(255),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """.format(name=database.get('name'))

        command = "mysql -u {username} -p{password} -e '{query}'".format(
            username=database.get('username'),
            password=database.get('password'),
            query=reset_sql)
        os.system(command)

    @classmethod
    def get_database_connection(cls):
        database = cls.config.find('database')

        try:
            connection = mysql.connector.connect(
                database=database.get('name'),
                user=database.get('username'),
                password=database.get('password'),
                host=database.get('host'),
                port=database.get('port'))
        except Exception as error: # pragma no cover
            sys.exit('unable to connect to database, please check config file => {error}'.format(error=error))

        return connection

    @classmethod
    def run_select_query(cls, query):
        connection = cls.get_database_connection()
        cursor = connection.cursor()
        cursor.execute(query)

        records = []
        for record in cursor:
            records.append(record)

        cursor.close()
        connection.disconnect()

        return records

    @classmethod
    def get_stat_records(cls):
        query = 'SELECT ipaddr, stat_type, stat_value FROM machinestat;'
        records = cls.run_select_query(query)
        return records

    @classmethod
    def get_log_records(cls):
        query = 'SELECT ipaddr, log_type, log_id, event_time, computer_name, category, record_number, source_name, event_type, message FROM machinelog;'
        records = cls.run_select_query(query)
        return records

    @classmethod
    def check_db_connection(cls):
        print('checking db connection...')
        try:
            cls.reset_db()
        except Exception as error: # pragma no cover
            print('unable to reset database => {error}'.format(error=error))
            return False

        print('db connection OK')
        return True

    @classmethod
    def check_stat_table(cls):
        print('checking stat table...')

        try:
            cls.get_stat_records()
        except Exception as error: # pragma no cover
            print('unable to select from machinestat table => {error}'.format(error=error))
            return False

        print('stat table OK')
        return True

    @classmethod
    def check_log_table(cls):
        print('checking log table...')

        try:
            cls.get_log_records()
        except Exception as error: # pragma no cover
            print('unable to select from machinelog table => {error}'.format(error=error))
            return False

        print('log table OK')
        return True

    @classmethod
    def check_db(cls):
        return cls.check_db_connection() and cls.check_stat_table() and cls.check_log_table()

    @classmethod
    def check_client(cls):
        print('checking client...')

        client = cls.config.find('clients').findall('client')[0]

        ipaddr = client.get('ip')
        port = int(client.get('port'))
        username = client.get('username')
        password = client.get('password')
        execpath = client.get('execpath')
        outpath = client.get('outpath')

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(ipaddr, port=port, username=username, password=password, allow_agent=False, look_for_keys=False)
        except Exception as error: # pragma no cover
            print('unable to connect to client => {error}'.format(error=error))
            return False

        message = 'Hello, World'
        statement = 'print("{message}")'.format(message=message)

        output = None

        sftp = ssh.open_sftp()

        try:
            with sftp.open(execpath, 'w') as fileobj:
                fileobj.write(statement)
        except Exception as error: # pragma no cover
            print('unable to copy file to client => {error}'.format(error=error))
            return False

        try:
            with sftp.open(outpath, 'w') as fileobj:
                fileobj.write(statement)
        except Exception as error: # pragma no cover
            print('unable to copy file to client => {error}'.format(error=error))
            return False

        command = 'python {execpath} {outpath}'.format(execpath=execpath, outpath=outpath)

        try:
            stdin, stdout, stderr = ssh.exec_command(command)
        except Exception as error: # pragma no cover
            print('unable to run command on client => {error}'.format(error=error))
            return False

        lines = stdout.readlines()
        output = ''.join(lines).strip()

        try:
            sftp.remove(execpath)
        except paramiko.ssh_exception.SSHException as error:  #pragma no cover
            print('unable to remove file from client: {error}'.format(error=error))
            return False

        try:
            sftp.remove(outpath)
        except paramiko.ssh_exception.SSHException as error:  #pragma no cover
            print('unable to remove file from client: {error}'.format(error=error))
            return False

        sftp.close()

        result = False
        if output == message:
            print('client OK')
            result = True

        return result

    @classmethod
    def check_mailer(cls):
        print('checking mailer...')

        mailer = cls.config.find('mailer')

        ipaddr = mailer.get('ip')
        port = int(mailer.get('port'))
        timeout = int(mailer.get('timeout'))
        username = mailer.get('username')
        password = mailer.get('password')

        message = """[TRIAL] smtp test\n\n
        Hello, World!

        Regards,
        Moon
        """

        try:
            mail_server = smtplib.SMTP(ipaddr, port=port, timeout=timeout)
            mail_server.starttls()
            mail_server.login(username, password)
            mail_server.sendmail(username, [username], message)
            mail_server.quit()
        except Exception as error: # pragma no cover
            print('mailer check failed => {error}'.format(error=error))
            return False

        print('mailer OK')
        return True

    @classmethod
    def check(cls):
        print('checking config values...')
        result = cls.check_db() and cls.check_client() and cls.check_mailer()
        print('config values OK')
        return result

    @classmethod
    def read_config(cls):
        print('reading config file...')

        try:
            config = lxml.etree.parse(cls.config_path)
        except IOError as error:
            print('unable to read config file: "{error}"'.format(error=error))
            return False
        except lxml.etree.XMLSyntaxError as error:
            print('config file parse error: "{error}"'.format(error=error))
            return False

        config_str = ''
        with open(cls.config_path) as fileobj:
            config_str = fileobj.read()

        root = config.getroot()

        node = root.find('srcpath')
        if node is None:
            print('unable to find "srcpath" in config')
            return False

        srcpath = node.get('value')
        if srcpath is None:
            print('unable to find attribute "value" in "srcpath" in config')
            return False

        try:
            open(srcpath)
        except IOError as error:
            print('unable to read client script: {file_path}'.format(file_path=srcpath))
            return False

        node = root.find('clients')
        if node is None:
            print('unable to find "clients" in config')
            return False

        nodes = node.findall('client')
        if not nodes:
            print('at least one valid client must be provided in config')
            return False

        for node in nodes:
            if node.get('ip') is None:
                print('client missing attribute "ip" in config')
                return False

            if node.get('port') is None:
                print('client missing attribute "port" in config')
                return False

            if not node.get('port').isdigit():
                print('client invalid attribute "port" in config')
                return False

            if node.get('username') is None:
                print('client missing attribute "username" in config')
                return False

            if node.get('password') is None:
                print('client missing attribute "password" in config')
                return False

            if node.get('mail') is None:
                print('client missing attribute "mail" in config')
                return False

            if node.get('execpath') is None:
                print('client missing attribute "execpath" in config')
                return False

            if node.get('outpath') is None:
                print('client missing attribute "outpath" in config')
                return False

        node = root.find('database')
        if node is None:
            print('unable to find "database" in config')
            return False

        if node.get('name') is None:
            print('database missing attribute "name" in config')
            return False

        if node.get('username') is None:
            print('database missing attribute "username" in config')
            return False

        if node.get('password') is None:
            print('database missing attribute "password" in config')
            return False

        if node.get('host') is None:
            print('database missing attribute "host" in config')
            return False

        if node.get('port') is None:
            print('database missing attribute "port" in config')
            return False

        if not node.get('port').isdigit():
            print('database invalid attribute "port" in config')
            return False

        node = root.find('mailer')
        if node is None:
            print('unable to find "mailer" in config')
            return False

        if node.get('ip') is None:
            print('mailer missing attribute "ip" in config')
            return False

        if node.get('port') is None:
            print('mailer missing attribute "port" in config')
            return False

        if not node.get('port').isdigit():
            print('mailer invalid attribute "port" in config')
            return False

        if node.get('timeout') is None:
            print('mailer missing attribute "timeout" in config')
            return False

        if not node.get('timeout').isdigit():
            print('mailer invalid attribute "timeout" in config')
            return False

        if node.get('username') is None:
            print('mailer missing attribute "username" in config')
            return False

        if node.get('password') is None:
            print('mailer missing attribute "password" in config')
            return False

        cls.config_str = config_str
        cls.config = config

        print('config file OK')
        return True

    @classmethod
    def run(cls):
        print('preparing...')
        if cls.read_config() and cls.check():
            print('running...')
            unittest.main()
            print('completed')
        else:
            print('please check test config file: {file_path}'.format(file_path=cls.config_path))

class TestHelper(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_clear_padding(self):
        padder = '-'
        padding = padder * 10
        message = 'this ' + padder +  ' is ' + padder + ' a ' + padder + ' message' + padding
        padded_message = padding + message
        clean_message = server.Helper.clear_padding(padded_message, padder)
        self.assertEqual(clean_message, message)

    def test_clear_padding_no_padding(self):
        padder = '-'
        message = 'M' * 20
        clean_message = server.Helper.clear_padding(message, padder)
        self.assertEqual(clean_message, message)

    def test_deserialize_success(self):
        root = lxml.etree.Element('root')
        child = lxml.etree.Element('child')
        root.append(child)
        serialized = lxml.etree.tostring(root)

        new_root = server.Helper.deserialize(serialized)

        self.assertNotEqual(new_root, None)
        self.assertEqual(new_root.tag, 'root')
        self.assertEqual(len(new_root), 1)

        new_child = new_root[0]
        self.assertEqual(new_child.tag, 'child')
        self.assertEqual(len(new_child), 0)

    def test_deserialize_syntax_error(self):
        serialized = '<this is not a valid xml string'

        new_root = server.Helper.deserialize(serialized)

        self.assertEqual(new_root, None)

    def test_deserialize_invalid_value(self):
        serialized = 22

        new_root = server.Helper.deserialize(serialized)

        self.assertEqual(new_root, None)

    def test_decrypt_success(self):
        message = 'M' * (server.AES_BLOCK_SIZE * 2)

        obj = Crypto.Cipher.AES.new(server.AES_KEY, Crypto.Cipher.AES.MODE_CBC, server.AES_IV)
        encrypted = obj.encrypt(message)

        decrypted = server.Helper.decrypt(encrypted)

        self.assertEqual(decrypted, message)

    def test_decrypt_short_length(self):
        encrypted = 'M' * (server.AES_BLOCK_SIZE - 1)

        decrypted = server.Helper.decrypt(encrypted)

        self.assertEqual(len(decrypted), 0)

    def test_decrypt_long_length(self):
        encrypted = 'M' * (server.AES_BLOCK_SIZE + 1)

        decrypted = server.Helper.decrypt(encrypted)

        self.assertEqual(len(decrypted), 0)

    def test_decrypt_invalid_value(self):
        encrypted = 17

        decrypted = server.Helper.decrypt(encrypted)

        self.assertEqual(len(decrypted), 0)

class TestAlert(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_valid_config(self):
        stat_type = 'test_stat'
        percentage = 57.4
        stat_limit = str(percentage) + '%'

        config = lxml.etree.Element('alert')
        config.set('type', stat_type)
        config.set('limit', stat_limit)

        instance = server.Alert(config)

        self.assertTrue(instance.is_valid)
        self.assertEqual(instance.stat_type, stat_type)
        self.assertEqual(instance.limit, percentage)

    def test_invalid_config_type_missing(self):
        percentage = 57.4
        stat_limit = str(percentage) + '%'

        config = lxml.etree.Element('alert')
        config.set('limit', stat_limit)

        instance = server.Alert(config)

        self.assertFalse(instance.is_valid)
        self.assertEqual(instance.stat_type, None)
        self.assertEqual(instance.limit, percentage)

    def test_invalid_config_limit_missing(self):
        stat_type = 'test_stat'

        config = lxml.etree.Element('alert')
        config.set('type', stat_type)

        instance = server.Alert(config)

        self.assertFalse(instance.is_valid)
        self.assertEqual(instance.stat_type, stat_type)
        self.assertEqual(instance.limit, None)

    def test_invalid_config_both_missing(self):
        config = lxml.etree.Element('alert')

        instance = server.Alert(config)

        self.assertFalse(instance.is_valid)
        self.assertEqual(instance.stat_type, None)
        self.assertEqual(instance.limit, None)

    def test_invalid_config_limit_invalid(self):
        stat_type = 'test_stat'
        percentage = 57.4
        stat_limit = str(percentage) + 'A'

        config = lxml.etree.Element('alert')
        config.set('type', stat_type)
        config.set('limit', stat_limit)

        instance = server.Alert(config)

        self.assertFalse(instance.is_valid)
        self.assertEqual(instance.stat_type, stat_type)
        self.assertEqual(instance.limit, None)

    def test_invalid_config_limit_invalid2(self):
        stat_type = 'test_stat'
        percentage = 'xx'
        stat_limit = str(percentage) + '%'

        config = lxml.etree.Element('alert')
        config.set('type', stat_type)
        config.set('limit', stat_limit)

        instance = server.Alert(config)

        self.assertFalse(instance.is_valid)
        self.assertEqual(instance.stat_type, stat_type)
        self.assertEqual(instance.limit, None)

    def test_is_mail_required_true(self):
        stat_type = 'test_stat'
        percentage = 57.4
        stat_limit = str(percentage) + '%'
        value = percentage + 1.02

        config = lxml.etree.Element('alert')
        config.set('type', stat_type)
        config.set('limit', stat_limit)

        instance = server.Alert(config)

        result = instance.is_mail_required(value)
        self.assertTrue(result)

    def test_is_mail_required_false(self):
        stat_type = 'test_stat'
        percentage = 57.4
        stat_limit = str(percentage) + '%'
        value = percentage - 1.65

        config = lxml.etree.Element('alert')
        config.set('type', stat_type)
        config.set('limit', stat_limit)

        instance = server.Alert(config)

        result = instance.is_mail_required(value)
        self.assertFalse(result)

class TestClient(unittest.TestCase):

    def setUp(self):
        client = Helper.config.find('clients').findall('client')[0]

        self.ipaddr = client.get('ip')
        self.port = int(client.get('port'))
        self.username = client.get('username')
        self.password = client.get('password')
        self.mail = client.get('mail')
        self.execpath = client.get('execpath')
        self.outpath = client.get('outpath')

        self.stat_type1 = 'test_stat1'
        self.percentage1 = 57.4
        self.stat_limit1 = str(self.percentage1) + '%'

        self.stat_type2 = 'test_stat2'
        self.percentage2 = 54.2
        self.stat_limit2 = str(self.percentage2) + '%'

        self.expected_ipaddr = self.ipaddr
        self.expected_port = self.port
        self.expected_username = self.username
        self.expected_password = self.password
        self.expected_mail = self.mail
        self.expected_execpath = self.execpath
        self.expected_outpath = self.outpath
        self.valid = True

        self.expected_stat_type1 = self.stat_type1
        self.expected_percentage1 = self.percentage1
        self.expected_stat_limit1 = self.stat_limit1
        self.valid1 = True

        self.expected_stat_type2 = self.stat_type2
        self.expected_percentage2 = self.percentage2
        self.expected_stat_limit2 = self.stat_limit2
        self.valid2 = True

        self.expected_number_of_alerts = 2

        self.config_str = self.build_config_str()
        self.config = self.build_config()
        self.expected_alerts = self.build_alerts()

        self.observer = TestObserver()
        self.instance = self.build_instance()

        self.srcpath = Helper.config.find('srcpath').get('value')

    def tearDown(self):
        pass

    def build_config_str(self):
        config_str = """<client
            ip='{ipaddr}'
            port='{port}'
            username='{username}'
            password='{password}'
            mail='{mail}'
            execpath='{execpath}'
            outpath='{outpath}' >
            <alert type='{stat_type1}' limit='{stat_limit1}' />
            <alert type='{stat_type2}' limit='{stat_limit2}' />
            </client>
        """.format(
            ipaddr=self.ipaddr,
            port=self.port,
            username=self.username,
            password=self.password,
            mail=self.mail,
            execpath=self.execpath,
            outpath=self.outpath,
            stat_type1=self.stat_type1,
            stat_limit1=self.stat_limit1,
            stat_type2=self.stat_type2,
            stat_limit2=self.stat_limit2)

        return config_str

    def build_config(self):
        config = lxml.etree.fromstring(self.config_str)
        return config

    def build_alerts(self):
        alert1 = {
            'type': self.expected_stat_type1,
            'percentage': self.expected_percentage1,
            'limit': self.expected_stat_limit1,
            'valid': self.valid1,
        }

        alert2 = {
            'type': self.expected_stat_type2,
            'percentage': self.expected_percentage2,
            'limit': self.expected_stat_limit2,
            'valid': self.valid2,
        }

        alerts = [alert1, alert2]

        expected_alerts = []
        for i in range(self.expected_number_of_alerts):
            expected_alerts.append(alerts[i])

        return expected_alerts

    def build_instance(self):
        instance = server.Client(self.config)
        return instance

    def rebuild_config_str(self):
        self.config_str = self.build_config_str()

    def rebuild_config(self):
        self.config = self.build_config()

    def rebuild_alerts(self):
        self.expected_alerts = self.build_alerts()

    def rebuild_instance(self):
        self.instance = self.build_instance()

    def rebuild_all(self):
        self.rebuild_config_str()
        self.rebuild_config()
        self.rebuild_alerts()
        self.rebuild_instance()
        self.check_instance()

    def compare_alerts(self, alert, new_alert):
        self.assertEqual(new_alert.is_valid, alert['valid'])
        self.assertEqual(new_alert.stat_type, alert['type'])
        self.assertEqual(new_alert.limit, alert['percentage'])

    def check_instance(self):
        self.assertEqual(self.instance.is_valid, self.valid)
        self.assertEqual(self.instance.ipaddr, self.expected_ipaddr)
        self.assertEqual(self.instance.port, self.expected_port)
        self.assertEqual(self.instance.username, self.expected_username)
        self.assertEqual(self.instance.password, self.expected_password)
        self.assertEqual(self.instance.mail, self.expected_mail)
        self.assertEqual(self.instance.execpath, self.expected_execpath)
        self.assertEqual(self.instance.outpath, self.expected_outpath)

        self.assertEqual(len(self.instance.alerts), len(self.expected_alerts))

        for i in range(self.expected_number_of_alerts):
            alert = self.expected_alerts[i]
            new_alert = self.instance.alerts[i]
            self.compare_alerts(alert, new_alert)

    def test_constructor_valid_config_no_alert(self):
        self.config_str = self.config_str.replace('<alert', '<alertx').replace('</alert>', '</alertx>')
        self.expected_number_of_alerts = 0

        self.rebuild_config()
        self.rebuild_alerts()
        self.rebuild_instance()
        self.check_instance()

    def test_constructor_valid_config_valid_alerts(self):
        self.check_instance()

    def test_constructor_valid_config_one_invalid_alert(self):
        self.stat_limit1 = 'x'
        self.expected_percentage1 = None
        self.valid1 = False
        self.valid = False

        self.rebuild_all()
        self.check_instance()

    def test_constructor_invalid_config_ip_missing(self):
        self.config_str = self.config_str.replace(' ip=', ' ipx=')
        self.expected_ipaddr = None
        self.valid = False

        self.rebuild_config()
        self.rebuild_alerts()
        self.rebuild_instance()
        self.check_instance()

    def test_constructor_invalid_config_port_missing(self):
        self.config_str = self.config_str.replace(' port=', ' portx=')
        self.expected_port = None
        self.valid = False

        self.rebuild_config()
        self.rebuild_alerts()
        self.rebuild_instance()
        self.check_instance()

    def test_constructor_invalid_config_port_invalid(self):
        self.port = 'x'
        self.expected_port = None
        self.valid = False

        self.rebuild_all()
        self.check_instance()

    def test_constructor_invalid_config_username_missing(self):
        self.config_str = self.config_str.replace(' username=', ' usernamex=')
        self.expected_username = None
        self.valid = False

        self.rebuild_config()
        self.rebuild_alerts()
        self.rebuild_instance()
        self.check_instance()

    def test_constructor_invalid_config_password_missing(self):
        self.config_str = self.config_str.replace(' password=', ' passwordx=')
        self.expected_password = None
        self.valid = False

        self.rebuild_config()
        self.rebuild_alerts()
        self.rebuild_instance()
        self.check_instance()

    def test_constructor_invalid_config_mail_missing(self):
        self.config_str = self.config_str.replace(' mail=', ' mailx=')
        self.expected_mail = None
        self.valid = False

        self.rebuild_config()
        self.rebuild_alerts()
        self.rebuild_instance()
        self.check_instance()

    def test_constructor_invalid_config_execpath_missing(self):
        self.config_str = self.config_str.replace(' execpath=', ' execpathx=')
        self.expected_execpath = None
        self.valid = False

        self.rebuild_config()
        self.rebuild_alerts()
        self.rebuild_instance()
        self.check_instance()

    def test_constructor_invalid_config_outpath_missing(self):
        self.config_str = self.config_str.replace(' outpath=', ' outpathx=')
        self.expected_outpath = None
        self.valid = False

        self.rebuild_config()
        self.rebuild_alerts()
        self.rebuild_instance()
        self.check_instance()

    def test_register(self):
        observer = TestObserver()
        self.instance.register(observer)
        self.assertEqual(len(self.instance.observers), 1)
        self.assertEqual(self.instance.observers[0], observer)

    def test_register_duplicate(self):
        observer = TestObserver()
        self.instance.register(observer)
        self.instance.register(observer)
        self.assertEqual(len(self.instance.observers), 1)
        self.assertEqual(self.instance.observers[0], observer)

    def test_unregister(self):
        observer = TestObserver()
        self.instance.register(observer)
        self.instance.unregister(observer)
        self.assertEqual(len(self.instance.observers), 0)

    def test_unregister_not_registered(self):
        observer = TestObserver()
        self.instance.unregister(observer)
        self.assertEqual(len(self.instance.observers), 0)

    def test_unregister_all(self):
        count = 5
        for i in range(count):
            observer = TestObserver()
            self.instance.register(observer)

        self.assertEqual(len(self.instance.observers), count)
        self.instance.unregister_all()
        self.assertEqual(len(self.instance.observers), 0)

    def test_unregister_all_empty(self):
        self.instance.unregister_all()
        self.assertEqual(len(self.instance.observers), 0)

    def test_get_alert_for_stat_type_no_alert(self):
        self.config_str = self.config_str.replace('<alert', '<alertx').replace('</alert', '</alertx>')
        self.expected_number_of_alerts = 0

        self.rebuild_config()
        self.rebuild_alerts()
        self.rebuild_instance()
        self.check_instance()

        alert = self.instance.get_alert_for_stat_type(self.stat_type1)
        self.assertEqual(alert, None)

    def test_get_alert_for_stat_type_alert_not_found(self):
        self.check_instance()

        alert = self.instance.get_alert_for_stat_type(self.stat_type1*2)
        self.assertEqual(alert, None)

    def test_get_alert_for_stat_type_alert_found(self):
        self.check_instance()

        alert = self.expected_alerts[0]

        new_alert = self.instance.get_alert_for_stat_type(self.stat_type1)
        self.assertNotEqual(new_alert, None)
        self.compare_alerts(alert, new_alert)

    def test_create_mail_for_alert(self):
        stat_type = 'test_stat'
        stat_value = 'test_value'
        alert_limit = 'test_limit'

        self.check_instance()
        content = self.instance.create_mail_for_alert(stat_type, stat_value, alert_limit)

        self.assertIn(self.ipaddr, content)
        self.assertIn(stat_type, content)
        self.assertIn(stat_value, content)
        self.assertIn(alert_limit, content)

    def test_run_authentication_exception(self):
        self.username = self.username * 2
        self.expected_username = self.username

        self.rebuild_all()
        self.check_instance()

        output = self.instance.run(self.srcpath)
        self.assertEqual(output, None)

    def test_run_socket_error(self):
        self.port = 1
        self.expected_port = self.port

        self.rebuild_all()
        self.check_instance()

        output = self.instance.run(self.srcpath)
        self.assertEqual(output, None)

    def test_run_command_error(self):
        self.srcpath = 'this_path_does_not_exists'

        self.rebuild_all()
        self.check_instance()

        output = self.instance.run(self.srcpath)
        self.assertEqual(output, None)

    def test_run_successful(self):
        self.check_instance()

        output = self.instance.run(self.srcpath)
        self.assertNotEqual(output, None)

        obj = Crypto.Cipher.AES.new(server.AES_KEY, Crypto.Cipher.AES.MODE_CBC, server.AES_IV)
        padded_message = obj.decrypt(output)
        message = padded_message.lstrip(server.AES_PADDER)
        root = lxml.etree.fromstring(message)

        self.assertEqual(root.tag, 'root')

        stats = root.find('stats')
        self.assertNotEqual(stats, None)
        self.assertEqual(len(stats), 3)

        stat = stats[0]
        self.assertEqual(stat.tag, 'stat')
        self.assertEqual(stat.get('type'), 'memory')
        float(stat.get('value'))

        stat = stats[1]
        self.assertEqual(stat.tag, 'stat')
        self.assertEqual(stat.get('type'), 'cpu')
        float(stat.get('value'))

        stat = stats[2]
        self.assertEqual(stat.tag, 'stat')
        self.assertEqual(stat.get('type'), 'uptime')
        self.assertTrue(stat.get('value').isdigit())

class TestDatabase(unittest.TestCase):

    def setUp(self):
        database = Helper.config.find('database')

        self.name = database.get('name')
        self.username = database.get('username')
        self.password = database.get('password')
        self.host = database.get('host')
        self.port = int(database.get('port'))

        self.expected_name = self.name
        self.expected_username = self.username
        self.expected_password = self.password
        self.expected_host = self.host
        self.expected_port = self.port
        self.valid = True

        self.config_str = self.build_config_str()
        self.config = self.build_config()
        self.instance = self.build_instance()

    def tearDown(self):
        pass

    def build_config_str(self):
        config_str = """<database
            name='{name}'
            username='{username}'
            password='{password}'
            host='{host}'
            port='{port}' />
        """.format(
            name=self.name,
            username=self.username,
            password=self.password,
            host=self.host,
            port=self.port)

        return config_str

    def build_config(self):
        config = lxml.etree.fromstring(self.config_str)
        return config

    def build_instance(self):
        instance = server.Database(self.config)
        return instance

    def rebuild_config_str(self):
        self.config_str = self.build_config_str()

    def rebuild_config(self):
        self.config = self.build_config()

    def rebuild_instance(self):
        self.instance = self.build_instance()

    def rebuild_all(self):
        self.rebuild_config_str()
        self.rebuild_config()
        self.rebuild_instance()
        self.check_instance()

    def check_instance(self):
        self.assertEqual(self.instance.is_valid, self.valid)
        self.assertEqual(self.instance.name, self.expected_name)
        self.assertEqual(self.instance.username, self.expected_username)
        self.assertEqual(self.instance.password, self.expected_password)
        self.assertEqual(self.instance.host, self.expected_host)
        self.assertEqual(self.instance.port, self.expected_port)

    def test_constructor_valid_config(self):
        self.check_instance()

    def test_constructor_invalid_config_name_missing(self):
        self.config_str = self.config_str.replace(' name=', ' namex=')
        self.expected_name = None
        self.valid = False

        self.rebuild_config()
        self.rebuild_instance()
        self.check_instance()

    def test_constructor_invalid_config_username_missing(self):
        self.config_str = self.config_str.replace(' username=', ' usernamex=')
        self.expected_username = None
        self.valid = False

        self.rebuild_config()
        self.rebuild_instance()
        self.check_instance()

    def test_constructor_invalid_config_password_missing(self):
        self.config_str = self.config_str.replace(' password=', ' passwordx=')
        self.expected_password = None
        self.valid = False

        self.rebuild_config()
        self.rebuild_instance()
        self.check_instance()

    def test_constructor_invalid_config_host_missing(self):
        self.config_str = self.config_str.replace(' host=', ' hostx=')
        self.expected_host = None
        self.valid = False

        self.rebuild_config()
        self.rebuild_instance()
        self.check_instance()

    def test_constructor_invalid_config_port_missing(self):
        self.config_str = self.config_str.replace(' port=', ' portx=')
        self.expected_port = None
        self.valid = False

        self.rebuild_config()
        self.rebuild_instance()
        self.check_instance()

    def test_constructor_invalid_config_port_invalid(self):
        self.port = 'x'
        self.expected_port = None
        self.valid = False

        self.rebuild_all()
        self.check_instance()

    def test_insert_stats(self):
        Helper.reset_db()

        ipaddr = 'this is an ip address'
        memory_usage = '12.3'
        cpu_usage = '12.5'
        uptime = '12345'

        stats_str = """<stats>
            <stat type='memory' value='{memory_usage}' />
            <stat type='cpu' value='{cpu_usage}' />
            <stat type='uptime' value='{uptime}' />
        </stats>
        """.format(
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            uptime=uptime)

        stats = lxml.etree.fromstring(stats_str)

        self.check_instance()
        self.instance.insert_stats(ipaddr, stats)

        records = Helper.get_stat_records()
        self.assertEqual(len(records), 3)

        for db_ipaddr, db_stat_type, db_stat_value in records:
            self.assertEqual(ipaddr, db_ipaddr)
            self.assertIn(db_stat_type, ['memory', 'cpu', 'uptime'])
            if db_stat_type == 'memory':
                self.assertEqual(db_stat_value, memory_usage)
            elif db_stat_type == 'cpu':
                self.assertEqual(db_stat_value, cpu_usage)
            elif db_stat_type == 'uptime':
                self.assertEqual(db_stat_value, uptime)

    def test_insert_logs_logs_is_none(self):
        Helper.reset_db()

        ipaddr = 'this is an ip address'
        logs = None

        self.check_instance()
        self.instance.insert_logs(ipaddr, logs)
        records = Helper.get_log_records()
        self.assertEqual(len(records), 0)

    def test_insert_logs_logs_is_empty(self):
        Helper.reset_db()

        ipaddr = 'this is an ip address'
        log_type = 'this is a log_type'
        logs_str = """<logs type='{log_type}'>
        </logs>
        """.format(log_type=log_type)

        logs = lxml.etree.fromstring(logs_str)

        self.check_instance()
        self.instance.insert_logs(ipaddr, logs)
        records = Helper.get_log_records()
        self.assertEqual(len(records), 0)

    def test_insert_logs(self):
        Helper.reset_db()

        ipaddr = 'this is an ip address'

        values = [
            'this is a type',
            'this is a log_id',
            'this is a event_time',
            'this is a computer_name',
            'this is a category',
            'this is a record_number',
            'this is a source_name',
            'this is a event_type',
            'this is a message',
        ]

        logs_str = """<logs type='{0}'>
            <log log_id='{1}'
                 event_time='{2}'
                 computer_name='{3}'
                 category='{4}'
                 record_number='{5}'
                 source_name='{6}'
                 event_type='{7}'
                 message='{8}' />
        </logs>
        """.format(*values)

        logs = lxml.etree.fromstring(logs_str)

        self.check_instance()
        self.instance.insert_logs(ipaddr, logs)

        records = Helper.get_log_records()
        self.assertEqual(len(records), 1)

        record = records[0]

        self.assertEqual(record[0], ipaddr)
        for i in range(len(values)):
            self.assertEqual(record[i+1], values[i])

class TestMailer(unittest.TestCase):

    def setUp(self):
        mailer = Helper.config.find('mailer')

        self.ipaddr = mailer.get('ip')
        self.port = int(mailer.get('port'))
        self.timeout = int(mailer.get('timeout'))
        self.username = mailer.get('username')
        self.password = mailer.get('password')

        self.expected_ipaddr = self.ipaddr
        self.expected_port = self.port
        self.expected_username = self.username
        self.expected_timeout = self.timeout
        self.expected_password = self.password
        self.valid = True

        self.config_str = self.build_config_str()
        self.config = self.build_config()
        self.instance = self.build_instance()

    def tearDown(self):
        pass

    def build_config_str(self):
        config_str = """<mailer
            ip='{ipaddr}'
            port='{port}'
            timeout='{timeout}'
            username='{username}'
            password='{password}' />
        """.format(
            ipaddr=self.ipaddr,
            port=self.port,
            timeout=self.timeout,
            username=self.username,
            password=self.password)

        return config_str

    def build_config(self):
        config = lxml.etree.fromstring(self.config_str)
        return config

    def build_instance(self):
        instance = server.Mailer(self.config)
        return instance

    def rebuild_config_str(self):
        self.config_str = self.build_config_str()

    def rebuild_config(self):
        self.config = self.build_config()

    def rebuild_instance(self):
        self.instance = self.build_instance()

    def rebuild_all(self):
        self.rebuild_config_str()
        self.rebuild_config()
        self.rebuild_instance()
        self.check_instance()

    def check_instance(self):
        self.assertEqual(self.instance.is_valid, self.valid)
        self.assertEqual(self.instance.ipaddr, self.expected_ipaddr)
        self.assertEqual(self.instance.port, self.expected_port)
        self.assertEqual(self.instance.username, self.expected_username)
        self.assertEqual(self.instance.timeout, self.expected_timeout)

    def test_constructor_valid_config(self):
        self.check_instance()

    def test_constructor_invalid_config_ipaddr_missing(self):
        self.config_str = self.config_str.replace(' ip=', ' ipx=')
        self.expected_ipaddr = None
        self.valid = False

        self.rebuild_config()
        self.rebuild_instance()
        self.check_instance()

    def test_constructor_invalid_config_port_missing(self):
        self.config_str = self.config_str.replace(' port=', ' portx=')
        self.expected_port = None
        self.valid = False

        self.rebuild_config()
        self.rebuild_instance()
        self.check_instance()

    def test_constructor_invalid_config_port_invalid(self):
        self.port = 'x'
        self.expected_port = None
        self.valid = False

        self.rebuild_all()
        self.check_instance()

    def test_constructor_invalid_config_timeout_missing(self):
        self.config_str = self.config_str.replace(' timeout=', ' timeoutx=')
        self.expected_timeout = None
        self.valid = False

        self.rebuild_config()
        self.rebuild_instance()
        self.check_instance()

    def test_constructor_invalid_config_timeout_invalid(self):
        self.timeout = 'x'
        self.expected_timeout = None
        self.valid = False

        self.rebuild_all()
        self.check_instance()

    def test_constructor_invalid_config_username_missing(self):
        self.config_str = self.config_str.replace(' username=', ' usernamex=')
        self.expected_username = None
        self.valid = False

        self.rebuild_config()
        self.rebuild_instance()
        self.check_instance()

    def test_constructor_invalid_config_password_missing(self):
        self.config_str = self.config_str.replace(' password=', ' passwordx=')
        self.expected_password = None
        self.valid = False

        self.rebuild_config()
        self.rebuild_instance()
        self.check_instance()

    def test_connect(self):
        self.check_instance()
        self.instance.connect()
        self.assertNotEqual(self.instance.connection, None)

    def test_connect_already_connected(self):
        self.check_instance()
        self.instance.connect()
        self.instance.connect()
        self.assertNotEqual(self.instance.connection, None)

    def test_connect_smtp_socket_error(self):
        self.ipaddr = '255.255.255.255'
        self.expected_ipaddr = self.ipaddr

        self.rebuild_all()
        self.check_instance()
        self.instance.connect()
        self.assertEqual(self.instance.connection, None)

    def test_disconnect(self):
        self.check_instance()
        self.instance.connect()
        self.assertNotEqual(self.instance.connection, None)
        result = self.instance.disconnect()
        self.assertTrue(result)

    def test_disconnect_without_connection(self):
        self.check_instance()
        result = self.instance.disconnect()
        self.assertFalse(result)

    def test_send(self):
        receievers = [self.username]
        message = 'this is a message'

        self.check_instance()
        self.instance.connect()
        self.assertNotEqual(self.instance.connection, None)
        result = self.instance.send(receievers, message)
        self.assertTrue(result)

    def test_send_without_connection(self):
        receievers = ['recv@mail.com']
        message = 'this is a message'

        self.check_instance()
        result = self.instance.send(receievers, message)
        self.assertFalse(result)

class TestServer(unittest.TestCase):

    def setUp(self):
        self.config_path = 'test.server.config.xml'
        self.srcpath = Helper.config.find('srcpath').get('value')
        self.config_str = Helper.config_str
        self.instance = server.Server(self.config_path)

    def tearDown(self):
        pass

    def write_config(self):
        with open(self.config_path, 'w') as fileobj:
            fileobj.write(self.config_str)

    def check_default(self):
        self.assertFalse(self.instance.is_valid)
        self.assertEqual(self.instance.srcpath, None)
        self.assertTrue(isinstance(self.instance.clients, list))
        self.assertEqual(len(self.instance.clients), 0)
        self.assertEqual(self.instance.database, None)
        self.assertEqual(self.instance.mailer, None)

    def check_config_failed(self):
        result = self.instance.read_config(self.config_path)
        self.assertFalse(result)
        self.check_default()

    def check_config_str_failed(self):
        self.write_config()
        self.check_config_failed()
        os.remove(self.config_path)

    def create_client(self):
        server_config = lxml.etree.fromstring(self.config_str)
        client_config = server_config.find('clients')[0]
        client = server.Client(client_config)
        return client

    def create_stat(self, stat_type, value):
        stat = lxml.etree.Element('stat')
        stat.set('type', str(stat_type))
        stat.set('value', str(value))
        return stat

    def create_valid_instance(self):
        self.write_config()
        result = self.instance.read_config(self.config_path)
        self.assertTrue(result)
        self.assertTrue(self.instance.is_valid)
        self.assertEqual(self.instance.srcpath, self.srcpath)
        self.assertTrue(isinstance(self.instance.clients, list))
        self.assertEqual(len(self.instance.clients), 1)
        self.assertNotEqual(self.instance.database, None)
        self.assertTrue(self.instance.database.is_valid)
        self.assertNotEqual(self.instance.mailer, None)
        self.assertTrue(self.instance.mailer.is_valid)
        self.assertFalse(self.instance.multithread_enabled)
        os.remove(self.config_path)

    def test_constructor(self):
        self.check_default()

    def test_read_config_path_does_not_exist(self):
        self.config_path = 'this_file_does_not_exist'
        self.check_config_failed()

    def test_read_config_path_is_not_a_file(self):
        self.config_path = 'this_is_not_a_file_for_config'
        os.mkdir(self.config_path)
        self.check_config_failed()
        shutil.rmtree(self.config_path)

    def test_read_config_path_is_not_an_xml_file(self):
        self.config_str = """this_is_not_a_valid_xml_content"""
        self.check_config_str_failed()

    def test_read_config_srcpath_missing(self):
        self.config_str = self.config_str.replace('<srcpath', '<srcpathx').replace('</srcpath>', '</srcpathx>')
        self.check_config_str_failed()

    def test_read_config_srcpath_value_missing(self):
        self.config_str = self.config_str.replace(' value=', ' valuex=')
        self.check_config_str_failed()

    def test_read_config_srcpath_does_not_exist(self):
        srcpath = 'this_file_does_not_exist'
        self.config_str = self.config_str.replace(self.srcpath, srcpath)
        self.check_config_str_failed()

    def test_read_config_srcpath_is_not_a_file(self):
        srcpath = 'this_is_not_a_file_for_src'
        os.mkdir(srcpath)
        self.config_str = self.config_str.replace(self.srcpath, srcpath)
        self.check_config_str_failed()
        shutil.rmtree(srcpath)

    def test_read_config_clients_missing(self):
        self.config_str = self.config_str.replace('<clients', '<clientsx').replace('</clients>', '</clientsx>')

        self.write_config()
        result = self.instance.read_config(self.config_path)
        self.assertFalse(result)
        self.assertFalse(self.instance.is_valid)
        self.assertEqual(self.instance.srcpath, self.srcpath)
        self.assertTrue(isinstance(self.instance.clients, list))
        self.assertEqual(len(self.instance.clients), 0)
        self.assertEqual(self.instance.database, None)
        self.assertEqual(self.instance.mailer, None)
        self.assertFalse(self.instance.multithread_enabled)
        os.remove(self.config_path)

    def test_read_config_no_client(self):
        self.config_str = self.config_str.replace('<client ', '<clientx ').replace('</client>', '</clientx>')

        self.write_config()
        result = self.instance.read_config(self.config_path)
        self.assertTrue(result)
        self.assertTrue(self.instance.is_valid)
        self.assertEqual(self.instance.srcpath, self.srcpath)
        self.assertTrue(isinstance(self.instance.clients, list))
        self.assertEqual(len(self.instance.clients), 0)
        self.assertNotEqual(self.instance.database, None)
        self.assertNotEqual(self.instance.mailer, None)
        self.assertFalse(self.instance.multithread_enabled)
        os.remove(self.config_path)

    def test_read_config_invalid_client(self):
        self.config_str = self.config_str.replace(' mail=', ' mailx=')

        self.write_config()
        result = self.instance.read_config(self.config_path)
        self.assertTrue(result)
        self.assertTrue(self.instance.is_valid)
        self.assertEqual(self.instance.srcpath, self.srcpath)
        self.assertTrue(isinstance(self.instance.clients, list))
        self.assertEqual(len(self.instance.clients), 0)
        self.assertNotEqual(self.instance.database, None)
        self.assertTrue(self.instance.database.is_valid)
        self.assertNotEqual(self.instance.mailer, None)
        self.assertTrue(self.instance.mailer.is_valid)
        self.assertFalse(self.instance.multithread_enabled)
        os.remove(self.config_path)

    def test_read_config_database_missing(self):
        self.config_str = self.config_str.replace('<database ', '<databasex ').replace('</database>', '</databasex>')

        self.write_config()
        result = self.instance.read_config(self.config_path)
        self.assertFalse(result)
        self.assertFalse(self.instance.is_valid)
        self.assertEqual(self.instance.srcpath, self.srcpath)
        self.assertTrue(isinstance(self.instance.clients, list))
        self.assertEqual(len(self.instance.clients), 1)
        self.assertEqual(self.instance.database, None)
        self.assertEqual(self.instance.mailer, None)
        self.assertFalse(self.instance.multithread_enabled)
        os.remove(self.config_path)

    def test_read_config_database_invalid(self):
        self.config_str = self.config_str.replace(' host=', ' hostx=')

        self.write_config()
        result = self.instance.read_config(self.config_path)
        self.assertFalse(result)
        self.assertFalse(self.instance.is_valid)
        self.assertEqual(self.instance.srcpath, self.srcpath)
        self.assertTrue(isinstance(self.instance.clients, list))
        self.assertEqual(len(self.instance.clients), 1)
        self.assertNotEqual(self.instance.database, None)
        self.assertFalse(self.instance.database.is_valid)
        self.assertEqual(self.instance.mailer, None)
        self.assertFalse(self.instance.multithread_enabled)
        os.remove(self.config_path)

    def test_read_config_mailer_missing(self):
        self.config_str = self.config_str.replace('<mailer ', '<mailerx ').replace('</mailer>', '</mailerx>')

        self.write_config()
        result = self.instance.read_config(self.config_path)
        self.assertFalse(result)
        self.assertFalse(self.instance.is_valid)
        self.assertEqual(self.instance.srcpath, self.srcpath)
        self.assertTrue(isinstance(self.instance.clients, list))
        self.assertEqual(len(self.instance.clients), 1)
        self.assertNotEqual(self.instance.database, None)
        self.assertTrue(self.instance.database.is_valid)
        self.assertEqual(self.instance.mailer, None)
        self.assertFalse(self.instance.multithread_enabled)
        os.remove(self.config_path)

    def test_read_config_mailer_invalid(self):
        self.config_str = self.config_str.replace('<mailer ip=', '<mailer ipx=')

        self.write_config()
        result = self.instance.read_config(self.config_path)
        self.assertFalse(result)
        self.assertFalse(self.instance.is_valid)
        self.assertEqual(self.instance.srcpath, self.srcpath)
        self.assertTrue(isinstance(self.instance.clients, list))
        self.assertEqual(len(self.instance.clients), 1)
        self.assertNotEqual(self.instance.database, None)
        self.assertTrue(self.instance.database.is_valid)
        self.assertNotEqual(self.instance.mailer, None)
        self.assertFalse(self.instance.mailer.is_valid)
        self.assertFalse(self.instance.multithread_enabled)
        os.remove(self.config_path)

    def test_read_config_missing_multithread(self):
        self.config_str = self.config_str.replace('<multithread ', '<multithreadx ').replace('</multithread>', '</multithreadx>')

        self.write_config()
        result = self.instance.read_config(self.config_path)
        self.assertTrue(result)
        self.assertTrue(self.instance.is_valid)
        self.assertEqual(self.instance.srcpath, self.srcpath)
        self.assertTrue(isinstance(self.instance.clients, list))
        self.assertEqual(len(self.instance.clients), 1)
        self.assertNotEqual(self.instance.database, None)
        self.assertTrue(self.instance.database.is_valid)
        self.assertNotEqual(self.instance.mailer, None)
        self.assertTrue(self.instance.mailer.is_valid)
        self.assertFalse(self.instance.multithread_enabled)
        os.remove(self.config_path)

    def test_read_config_multithread_enabled(self):
        self.config_str = self.config_str.replace("<multithread enabled='false'", "<multithread enabled='true'")

        self.write_config()
        result = self.instance.read_config(self.config_path)
        self.assertTrue(result)
        self.assertTrue(self.instance.is_valid)
        self.assertEqual(self.instance.srcpath, self.srcpath)
        self.assertTrue(isinstance(self.instance.clients, list))
        self.assertEqual(len(self.instance.clients), 1)
        self.assertNotEqual(self.instance.database, None)
        self.assertTrue(self.instance.database.is_valid)
        self.assertNotEqual(self.instance.mailer, None)
        self.assertTrue(self.instance.mailer.is_valid)
        self.assertTrue(self.instance.multithread_enabled)
        os.remove(self.config_path)

    def test_read_config_valid(self):
        self.create_valid_instance()

    def test_handle_client_stat_alert_not_found(self):
        self.create_valid_instance()
        client = self.create_client()

        stat_type = 'this_stat_does_not_exist_in_the_client'
        value = 59.2
        stat = self.create_stat(stat_type, value)

        result = self.instance.handle_client_stat(client, stat)
        self.assertFalse(result)

    def test_handle_client_stat_mail_required_mail_sent(self):
        self.create_valid_instance()
        client = self.create_client()

        alert = client.alerts[0]
        stat = self.create_stat(alert.stat_type, alert.limit+10)

        result = self.instance.handle_client_stat(client, stat)
        self.assertTrue(result)

    def test_handle_client_stat_mail_required_mail_not_sent(self):
        self.create_valid_instance()
        client = self.create_client()

        alert = client.alerts[0]
        stat = self.create_stat(alert.stat_type, alert.limit+10)

        result = self.instance.handle_client_stat(client, stat)
        self.assertTrue(result)

    def test_handle_client_stat_mail_not_required(self):
        self.create_valid_instance()
        client = self.create_client()

        alert = client.alerts[0]
        stat = self.create_stat(alert.stat_type, alert.limit-10)

        result = self.instance.handle_client_stat(client, stat)
        self.assertFalse(result)

    def test_did_client_executed_output_is_none(self):
        self.create_valid_instance()
        client = self.create_client()
        output = None

        result = self.instance.did_client_executed(client, output)
        self.assertFalse(result)

    def test_did_client_executed_output_is_not_xml(self):
        self.create_valid_instance()
        client = self.create_client()
        output = 'this_not_an_xml_string'

        result = self.instance.did_client_executed(client, output)
        self.assertFalse(result)

    def test_handle_client_no_error_no_output(self):
        self.create_valid_instance()
        self.instance.srcpath = 'this_path_does_not_exists'
        client = self.create_client()

        self.instance.handle_client(client)

    def test_handle_client_with_error(self):
        self.create_valid_instance()

        srcpath = 'test_handle_client_with_error.py'
        code = '# test_handle_client_with_error\n\nimport sys\nsys.exit("this is an error")'
        with open(srcpath, 'w') as fileobj:
            fileobj.write(code)

        self.instance.srcpath = srcpath
        client = self.create_client()

        self.instance.handle_client(client)

        os.remove(srcpath)

    def test_handle_client_output_is_not_valid_xml(self):
        self.create_valid_instance()

        srcpath = 'test_handle_client_with_error.py'
        self.instance.srcpath = srcpath

        client = self.create_client()

        code = '''
# test_handle_client_output_is_not_valid_xml
with open("{}", "w") as outfile:
    outfile.write("this is not a valid xml content")
'''.format(client.outpath)

        with open(srcpath, 'w') as fileobj:
            fileobj.write(code)

        self.instance.handle_client(client)

        os.remove(srcpath)

    def test_handle_client(self):
        self.create_valid_instance()
        self.instance.mailer.connect()
        client = self.create_client()

        self.instance.handle_client(client)

        self.instance.mailer.disconnect()

    def test_run_invalid(self):
        self.create_valid_instance()
        self.instance.is_valid = False
        result = self.instance.run()
        self.assertFalse(result)

    def test_run(self):
        self.create_valid_instance()
        result = self.instance.run()
        self.assertTrue(result)

    def test_run_multithread_enabled(self):
        self.create_valid_instance()
        self.instance.multithread_enabled = True
        result = self.instance.run()
        self.assertTrue(result)

class TestMain(unittest.TestCase):

    def setUp(self):
        self.config_str = Helper.config_str
        self.config_path = 'test.main.config.xml'
        self.log_path = 'test.server.log'

    def tearDown(self):
        pass

    def create_config(self):
        with open(self.config_path, 'w') as fileobj:
            fileobj.write(self.config_str)

    def test_config_path_does_not_exist(self):
        Helper.clean_sys_args()

        sys.argv.insert(1, self.config_path)
        sys.argv.insert(2, self.log_path)
        result = server.main()
        self.assertFalse(result)

    def test_default_log_level(self):
        Helper.clean_sys_args()

        self.create_config()
        sys.argv.insert(1, self.config_path)
        sys.argv.insert(2, self.log_path)
        result = server.main()
        self.assertTrue(result)
        os.remove(self.config_path)

    def test_valid_log_level(self):
        Helper.clean_sys_args()

        self.create_config()
        sys.argv.insert(1, self.config_path)
        sys.argv.insert(2, self.log_path)
        sys.argv.insert(3, '-loglevel')
        sys.argv.insert(4, 'warning')
        result = server.main()
        self.assertTrue(result)
        os.remove(self.config_path)

if __name__ == '__main__':
    Helper.run()
