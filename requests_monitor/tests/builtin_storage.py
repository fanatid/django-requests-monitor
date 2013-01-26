import multiprocessing
import time

from django.conf import settings
from django.core import management
from django.utils import unittest


class BuiltinStorageTest(unittest.TestCase):
    ADDR = ('127.0.0.1', 10627)

    def setUp(self):
        settings.REQUESTS_MONITOR_CONFIG['STORAGE'] = 'builtin://' + ('%s:%s' % self.ADDR)
        self.server = multiprocessing.Process(target=management.call_command,
            args=('runstorage',))
        self.server.start()
        time.sleep(0.400)
        from requests_monitor.storage.backends.builtin import BuiltinStorageClient
        self.client = BuiltinStorageClient(*self.ADDR)

    def tearDown(self):
        self.server.terminate()
        time.sleep(0.100)

    def test_DEL(self):
        self.client.hset('key1', 'field', 'value')
        self.client.hset('key2', 'field', 'value')
        self.assertEqual(self.client.delete('key1', 'key2', 'key3'), 2)

    def test_HGET(self):
        self.client.hset('key1', 'field', 'value')
        self.assertEqual(self.client.hget('key1', 'field'), 'value')

    def test_HKEYS(self):
        data = {
            'field1': 'value1',
            'field2': 'value2',
        }
        self.client.hmset('key', data)
        self.assertEqual(sorted(self.client.hkeys('key')),
            sorted(['field1', 'field2']))

    def test_HMGET(self):
        data = {
            'field1': 'value1',
            'field2': 'value2',
        }
        self.client.hmset('key', data)
        self.assertEqual(self.client.hmget('key', 'field1', 'field3', 'field2'),
            ['value1', None, 'value2'])

    def test_HMSET(self):
        data = {
            'field1': 'value1',
            'field2': 'value2',
        }
        self.assertEqual(self.client.hmset('key', data), 2)

    def test_HSET(self):
        self.assertEqual(self.client.hset('key', 'field', 'value'), 1)

    def test_KEYS(self):
        self.client.hset('key1', 'field', 'value')
        self.client.hset('key2', 'field', 'value')
        self.assertEqual(sorted(self.client.keys()), sorted(['key1', 'key2']))

    def test_TYPE(self):
        self.client.hset('key1', 'field', 'value')
        self.assertEqual(self.client.type('key1'), 'hash')
        self.assertEqual(self.client.type('key2'), None)
