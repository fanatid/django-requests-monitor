import asyncore, asynchat, socket
import re
import types
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

    def bulk_reply(self, value):
        if value is None:
            return '$-1\r\n'
        return '$%d\r\n%s\r\n' % (len(value), value)

    def multi_bulk_reply(self, values):
        response = '*%d\r\n' % (len(values), )
        for value in values:
            if value is None:
                response += '$-1\r\n'
            else:
                response += '$%d\r\n%s\r\n' % (len(value), value)
        return response

    def run_command(self, command, *args):
        return getattr(self, 'command_' + command)(*args)

    def command_DEL(self, *keys):
        count = 0
        for key in keys:
            if key in self._db:
                del self._db[key]
                count += 1
        return ':%s\r\n' % count

    @error_if_another_type(dict)
    def command_HGET(self, key, field):
        return self.bulk_reply(self._db[key].get(field))

    @error_if_another_type(dict)
    def command_HKEYS(self, key):
        return self.multi_bulk_reply(self._db[key].keys())

    @error_if_another_type(dict)
    def command_HMGET(self, key, *fields):
        h = self._db[key]
        return self.multi_bulk_reply([h.get(field) for field in fields])

    @error_if_another_type(dict)
    def command_HMSET(self, key, *fields):
        h = self._db[key]
        count = len(fields)
        for hkey, value in [fields[i:i+2] for i in xrange(0, count, 2)]:
            h[hkey] = value
        return ':%s\r\n' % (count/2, )

    @error_if_another_type(dict)
    def command_HSET(self, key, field, value):
        self._db[key][field] = value
        return ':1\r\n'

    def command_KEYS(self):
        return self.multi_bulk_reply(self._db.keys())

    def command_TYPE(self, key):
        key_type = type(self._db.get(key))
        if key_type == types.DictType:
            value = 'hash'
        else:
            value = None
        return self.bulk_reply(value)

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


class AsyncServerHandler(asynchat.async_chat):
    terminator = '\r\n'

    def __init__(self, conn=None):
        asynchat.async_chat.__init__(self, conn)
        self.data = ''
        self.command_args  = None
        self.command       = []
        self.arg_length    = None

    def collect_incoming_data(self, data):
        self.data += data

    def found_terminator(self):
        if self.command_args is None:
            if self.data[:1] == '*' and self.data[1:].isdigit() \
             and int(self.data[1:]) > 0:
                self.command_args = int(self.data[1:])
            else:
                self.push('-ERR unknown count arguments of the command\r\n')
            self.data = ''
            return
        if self.arg_length is None:
            if self.data[:1] == '$' and self.data[1:].isdigit() \
             and int(self.data[1:]) > 0:
                self.arg_length = int(self.data[1:])
            else:
                self.command_args = None
                self.command      = []
                self.push('-ERR unknown length of the command\r\n')
            self.data = ''
            return
        length = len(self.data)
        if length < self.arg_length:
            return
        if length > self.arg_length:
            self.command_args = None
            self.command      = []
            self.arg_length   = None
            self.push('-ERR argument length is greater then submitted early\r\n')
            return
        self.command.append(self.data)
        self.data = ''
        self.command_args -= 1
        if self.command_args == 0:
            data = self.run_command()
            self.push_with_producer(asynchat.simple_producer(data))
            self.command_args = None
            self.command = []
        self.arg_length = None

    def run_command(self):
        if self.command[0] not in storage.COMMANDS:
            return '-ERR unknown command\r\n'
        if not storage.COMMANDS_CONTROL_LENGTH[self.command[0]](len(self.command[1:])):
            return '-ERR invalid arguments\r\n'
        return storage.run_command(self.command[0], *self.command[1:])


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
