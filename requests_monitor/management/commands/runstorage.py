import asyncore, socket
import re
import types
import json
from functools import wraps

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class error_if_another_type(object):
    def __init__(self, type):
        self.type = type

    def __call__(self, func):
        @wraps(func)
        def wrapper(cls, key, *args, **kwargs):
            if key in cls._db:
                if not isinstance(cls._db[key], self.type):
                    return '-ERR other key type\r\n'
            else:
                cls._db[key] = self.type()
            return func(cls, key, *args, **kwargs)
        return wrapper

class Storage(object):
    _db = {}
    COMMANDS = ('DEL', 'HGET', 'HKEYS', 'HMGET', 'HMSET', 'HSET', 'KEYS', 'TYPE')
    COMMANDS_CONTROL_LENGTH = {
        'DEL':   lambda x: x >= 1,
        'HGET':  lambda x: x == 2,
        'HKEYS': lambda x: x == 1,
        'HMGET': lambda x: x >= 2,
        'HMSET': lambda x: x >= 3 and x % 2 == 1,
        'HSET':  lambda x: x == 3,
        'KEYS':  lambda x: x == 0,
        'TYPE':  lambda x: x == 1,
    }

    def __new__(cls):
        if not hasattr(cls, 'instance'):
             cls.instance = super(Storage, cls).__new__(cls)
        return cls.instance

    def build_reply(self, value):
        value = json.dumps(value)
        return '%d\r\n%s' % (len(value), value)

    def run_command(self, command, *args):
        #LOG.write('-'*80 + '\n' + str(command) + ''.join(args))
        #LOG.flush()
        return getattr(self, 'command_' + command)(*args)

    def command_DEL(self, *keys):
        count = 0
        for key in keys:
            if key in self._db:
                del self._db[key]
                count += 1
        return self.build_reply(count)

    @error_if_another_type(dict)
    def command_HGET(self, key, field):
        return self.build_reply(self._db[key].get(field))

    @error_if_another_type(dict)
    def command_HKEYS(self, key):
        return self.build_reply(self._db[key].keys())

    @error_if_another_type(dict)
    def command_HMGET(self, key, *fields):
        h = self._db[key]
        return self.build_reply([h.get(field) for field in fields])

    @error_if_another_type(dict)
    def command_HMSET(self, key, *fields):
        h = self._db[key]
        count = len(fields)
        for hkey, value in [fields[i:i+2] for i in xrange(0, count, 2)]:
            h[hkey] = value
        return self.build_reply(count/2)

    @error_if_another_type(dict)
    def command_HSET(self, key, field, value):
        self._db[key][field] = value
        return self.build_reply(1)

    def command_KEYS(self):
        return self.build_reply(self._db.keys())

    def command_TYPE(self, key):
        key_type = type(self._db.get(key))
        if key_type == types.DictType:
            value = 'hash'
        else:
            value = None
        return self.build_reply(value)

storage = Storage()


class AsyncServer(asyncore.dispatcher):
    def __init__(self, addr, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.bind((addr, port))
        self.listen(5)

    def handle_accept(self):
        client, addr = self.accept()
        return AsyncServerHandler(client)


class AsyncServerHandler(asyncore.dispatcher):
    def __init__(self, sock):
        asyncore.dispatcher.__init__(self, sock)
        self.length    = None
        self.request   = ''
        self.response  = ''
        self._readable = True
        self._writable = False

    def readable(self):
        return self._readable

    def writable(self):
        return self._writable

    def handle_read(self):
        chunk = self.recv(4096)
        self.request += chunk
        if self.length is None:
            if not '\r\n' in self.request:
                return
            length, self.request = self.request.split('\r\n', 1)
            if not length.isdigit():
                self.close()
                return
            self.length = int(length)
        length = len(self.request)
        if length < self.length:
            return
        if length > self.length:
            self.close()
            return
        self._readable  = False
        if not self.process_request():
            self.close()
        else:
            self._writable = True

    def process_request(self):
        try:
            command = json.loads(self.request)
        except ValueError:
            return False
        if not isinstance(command, list):
            return False
        if command[0] not in storage.COMMANDS:
            return False
        if not storage.COMMANDS_CONTROL_LENGTH[command[0]](len(command[1:])):
            return False
        self.response = storage.run_command(command[0], *command[1:])
        return True

    def handle_write(self):
        bytes_sent = self.send(self.response)
        self.response = self.response[bytes_sent:]
        if not self.response:
            self.close()


class Command(BaseCommand):
    # from django.core.management.commands.runserver
    help = "Starts a storage for requests_monitor."
    args = '[optional port number, or ipaddr:port]'
    DEFAULT_PORT = 10627
    naiveip_re = re.compile(r"""^(?:
(?P<addr>(?P<ipv4>\d{1,3}(?:\.\d{1,3}){3})         # IPv4 address
):)?(?P<port>\d+)$""", re.X)

    def run(self, *args, **options):
        server = AsyncServer(self.addr, int(self.port))
        asyncore.loop()

    def handle(self, addrport='', *args, **options):
        if not addrport and settings.REQUESTS_MONITOR_CONFIG['STORAGE'].startswith('builtin://'):
            addrport = settings.REQUESTS_MONITOR_CONFIG['STORAGE'][10:]
        if not addrport:
            self.addr = ''
            self.port = self.DEFAULT_PORT
        else:
            m = re.match(self.naiveip_re, addrport)
            if m is None:
                raise CommandError('"%s" is not a valid port number '
                                   'or address:port pair.' % addrport)
            self.addr, _ipv4, self.port = m.groups()
            if not self.port.isdigit():
                raise CommandError("%r is not a valid port number." % self.port)
        if not self.addr:
            self.addr = '127.0.0.1'
        self.run(*args, **options)
