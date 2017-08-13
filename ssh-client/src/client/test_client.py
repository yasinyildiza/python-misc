from __future__ import print_function

import unittest
import os
import sys
import lxml.etree
import Crypto.Cipher
import client

_IS_WINDOWS = sys.platform == 'win32'

class TestClient(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def check_log(self, log):
        self.assertEqual(log.tag, 'log')
        self.assertNotEqual(log.get('log_id'), None)
        self.assertNotEqual(log.get('event_time'), None)
        self.assertNotEqual(log.get('computer_name'), None)
        self.assertNotEqual(log.get('category'), None)
        self.assertNotEqual(log.get('record_number'), None)
        self.assertNotEqual(log.get('source'), None)
        self.assertNotEqual(log.get('event_type'), None)
        self.assertNotEqual(log.get('message'), None)

    def check_logs(self, logs, log_type):
        """helper method to check logs Element
        """

        self.assertNotEqual(logs, None)
        self.assertEqual(logs.tag, 'logs')
        self.assertEqual(logs.get('type'), log_type)

        if not _IS_WINDOWS:
            self.assertEqual(len(logs), 0)
            return

        for log in logs:
            self.check_log(log)

    def check_stats(self, stats):
        """helper method to check stats Element
        """

        self.assertNotEqual(stats, None)
        self.assertEqual(stats.tag, 'stats')
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

    def check_output(self, output):
        """helper method to check final output
        """

        obj = Crypto.Cipher.AES.new(client.AES_KEY, Crypto.Cipher.AES.MODE_CBC, client.AES_IV)
        padded_message = obj.decrypt(output)
        message = padded_message.lstrip(client.AES_PADDER)
        root = lxml.etree.fromstring(message)

        self.assertEqual(root.tag, 'root')
        self.assertEqual(len(root), 2)

        stats = root.find('stats')
        self.check_stats(stats)

        logs = root.find('logs')
        self.check_logs(logs, 'Security')

    def check_outfile(self, outfilepath):
        """helper method to check final output file
        """

        with open(outfilepath, 'rb') as outfile:
            output = outfile.read()

        self.check_output(output)

    def test_create_stat(self):
        stat_type = 'sample_type'
        stat_value = 'sample_value'

        stat = client.create_stat(stat_type, stat_value)
        self.assertEqual(stat.get('type'), stat_type)
        self.assertEqual(stat.get('value'), stat_value)

    def test_create_stat_non_str(self):
        stat_type = 3
        stat_value = 5

        stat = client.create_stat(stat_type, stat_value)
        self.assertEqual(stat.get('type'), '3')
        self.assertEqual(stat.get('value'), '5')

    def test_get_memory_usage(self):
        value = client.get_memory_usage()
        self.assertTrue(isinstance(value, float))

    def test_get_cpu_usage(self):
        value = client.get_cpu_usage()
        self.assertTrue(isinstance(value, float))

    def test_get_uptime(self):
        value = client.get_uptime()
        self.assertTrue(isinstance(value, (int, float)))

    def test_create_stats(self):
        stats = client.create_stats()
        self.check_stats(stats)

    def test_create_logs_localhost_security(self):
        ipaddr = '127.0.0.1'
        log_type = 'Security'
        logs = client.create_logs(ipaddr, log_type)
        self.check_logs(logs, log_type)

    def test_create_logs_invalid_ip_security(self):
        ipaddr = 'x'
        log_type = 'Security'
        logs = client.create_logs(ipaddr, log_type)

        self.assertNotEqual(logs, None)
        self.assertEqual(logs.tag, 'logs')
        self.assertEqual(len(logs), 0)

    def test_add_padding_message_length_less_than_block_size(self):
        message = 'this is a message'
        offset = 4
        block_size = len(message) + offset
        padder = '-'

        padded_message = client.add_padding(message, block_size, padder)

        self.assertEqual(len(padded_message), block_size)

        padding = padded_message[:offset]
        for char in padding:
            self.assertEqual(char, padder)
        base_message = padded_message[offset:]
        self.assertEqual(base_message, message)

    def test_add_padding_message_length_multiple_of_block_size(self):
        message = 'this is a message'
        block_size = len(message)
        padder = '-'

        padded_message = client.add_padding(message, block_size, padder)

        self.assertEqual(len(padded_message), block_size)
        self.assertEqual(padded_message, message)

    def test_add_padding_message_length_greater_than_block_size(self):
        block_size = 9
        offset = 4
        message = 'x' * (block_size + offset)
        padder = '-'

        padded_message = client.add_padding(message, block_size, padder)

        self.assertEqual(len(padded_message), block_size*2)

        index = block_size-offset
        padding = padded_message[:index]
        for char in padding:
            self.assertEqual(char, padder)
        base_message = padded_message[index:]
        self.assertEqual(base_message, message)

    def test_serialize(self):
        root = lxml.etree.Element('root')
        child = lxml.etree.Element('child')
        root.append(child)

        serialized = client.serialize(root)

        self.assertTrue(isinstance(serialized, (str, unicode)))

        new_root = lxml.etree.fromstring(serialized)
        self.assertEqual(new_root.tag, 'root')
        self.assertEqual(len(new_root), 1)

        new_child = new_root[0]
        self.assertEqual(new_child.tag, 'child')
        self.assertNotEqual(new_child, None)
        self.assertEqual(len(new_child), 0)

    def test_encrypt_message_length_less_than_block_size(self):
        block_size = 16
        offset = 7
        key = 'K' * block_size
        init_vector = 'I' * block_size
        message = 'M' * (block_size - offset)
        padder = '-'

        encrypted = client.encrypt(message, block_size, padder, key, init_vector)

        obj = Crypto.Cipher.AES.new(key, Crypto.Cipher.AES.MODE_CBC, init_vector)
        padded_message = obj.decrypt(encrypted)
        padding = padded_message[:offset]
        for char in padding:
            self.assertEqual(char, padder)
        new_message = padded_message[offset:]
        self.assertEqual(new_message, message)

    def test_encrypt_message_length_multiple_of_block_size(self):
        block_size = 16
        key = 'K' * block_size
        init_vector = 'I' * block_size
        message = 'M' * (block_size * 2)
        padder = '-'

        encrypted = client.encrypt(message, block_size, padder, key, init_vector)

        obj = Crypto.Cipher.AES.new(key, Crypto.Cipher.AES.MODE_CBC, init_vector)
        padded_message = obj.decrypt(encrypted)
        new_message = padded_message.lstrip(padder)

        self.assertEqual(padded_message, message)
        self.assertEqual(new_message, message)

    def test_encrypt_message_length_greater_than_block_size(self):
        block_size = 16
        offset = 7
        key = 'K' * block_size
        init_vector = 'I' * block_size
        message = 'M' * (block_size + offset)
        padder = '-'

        encrypted = client.encrypt(message, block_size, padder, key, init_vector)

        obj = Crypto.Cipher.AES.new(key, Crypto.Cipher.AES.MODE_CBC, init_vector)
        padded_message = obj.decrypt(encrypted)
        index = block_size - offset
        padding = padded_message[:index]
        for char in padding:
            self.assertEqual(char, padder)
        new_message = padded_message[index:]
        self.assertEqual(new_message, message)

    def test_run(self):
        outfilepath = 'stat.bin'
        client.run(outfilepath)
        self.check_outfile(outfilepath)
        os.remove(outfilepath)

    def test_main(self):
        outfilepath = 'stat.bin'
        sys.argv.insert(1, outfilepath)
        client.main()
        self.check_outfile(outfilepath)
        os.remove(outfilepath)

def main():
    unittest.main()

if __name__ == '__main__':
    main()
