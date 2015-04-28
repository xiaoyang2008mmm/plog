import logging
import socket
import re,os
import application
DEFAULT_FACILITY = 3
LEVEL_NONE=6
CFG_OPT_DAEMONIZE = 'daemonize'
CFG_OPT_PID_PATH = '/var/run'
READ_LOG_MAX = 32768
LOG_ENTRY_PLAIN = 0
LOG_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_ENTRY_APPSERVER = 2
LOG_ENTRY_REQUEST = 1

class Entry(object):

    def __init__(self, msg, msg_extra=None, timestamp=None,
                 facility=DEFAULT_FACILITY, level=LEVEL_NONE,
                 extra_values=None, addr=None, name=None):
        self.msg = msg
        self.msg_extra = msg_extra
        self.timestamp = timestamp
        self.facility = DEFAULT_FACILITY
        self.level = level
        self.extra_values = extra_values
        self.ip_addr = None
        self.name = name

        if addr is not None:
            self.ip_addr = addr[0]
        if self.extra_values is None:
            self.extra_values = {}

    @classmethod
    def get_log_type(cls):
	pass

    @classmethod
    def get_extra_fields(cls):
        return ()

    @classmethod
    def get_signature(cls):
        return ''

    def _get_timestamp_str(self):
        if self.timestamp is None:
            self.timestamp = time.localtime()
        return time.strftime(LOG_TIME_FORMAT, self.timestamp)

    def _get_timestamp_from_str(self, timestamp_str):
        try:
            timestamp = time.strptime(timestamp_str, LOG_TIME_FORMAT)
        except ValueError:
            logging.info('failed to parse timestamp %s, falling back to now'
                         % (timestamp_str, ))
            timestamp = time.localtime()
        return timestamp

    def _format_syslog(self, name, extra_values):
        return '%s%s|%s|%s|%s|%s|%s' % (
            self.get_signature(), name,
            self._get_timestamp_str(), get_level_str(self.level),
            extra_values, self.msg, self.msg_extra)

    def to_syslog(self, name):
        extra_values = '|'.join([str(value) for value in self.extra_values])
        return self._format_syslog(name, extra_values)

    def from_syslog(self):
	pass

class PlogEntry(Entry):

    def from_syslog(self):
        extra_fields = self.get_extra_fields()
        num_fields = 5
        if extra_fields:
            num_fields += len(extra_fields)
        else:
            num_fields += 1

        info = self.msg[5:].split('|', num_fields)
        if num_fields > len(info):
            logging.warning(
                'unable to parse message %s, got %d fields expected max %d'
                % (self.msg, num_fields, info))
            return False

        self.name = info[0]
        self.msg = info[num_fields - 2]
        self.msg_extra = info[num_fields - 1]
        self.timestamp = self._get_timestamp_from_str(info[1])

        self.extra_values = []
        for pos in xrange(len(extra_fields)):
            field_name, field_type = extra_fields[pos]
            self.extra_values.append(field_type(info[pos+3]))

        return True



class AppserverEntry(PlogEntry):

    @classmethod
    def get_log_type(cls):
        return LOG_ENTRY_APPSERVER

    @classmethod
    def get_signature(cls):
        return '!!AS '

class RequestEntry(PlogEntry):

    @classmethod
    def get_log_type(cls):
        return LOG_ENTRY_REQUEST

    @classmethod
    def get_extra_fields(cls):
        return (('re_ip', str), ('re_method', str), ('re_user_agent', str),
                ('re_size', int), ('re_status', int), ('re_ms_time', int),
                ('re_uri', str))

    @classmethod
    def get_signature(cls):
        return '!!RQ '



class Entry(object):

    def __init__(self, msg, msg_extra=None, timestamp=None,
                 facility=DEFAULT_FACILITY, level=LEVEL_NONE,
                 extra_values=None, addr=None, name=None):
        self.msg = msg
        self.msg_extra = msg_extra
        self.timestamp = timestamp
        self.facility = DEFAULT_FACILITY
        self.level = level
        self.extra_values = extra_values
        self.ip_addr = None
        self.name = name

        if addr is not None:
            self.ip_addr = addr[0]
        if self.extra_values is None:
            self.extra_values = {}

    @classmethod
    def get_log_type(cls):
        return LOG_ENTRY_PLAIN

    @classmethod
    def get_extra_fields(cls):
        return ()

    @classmethod
    def get_signature(cls):
        return ''

    def _get_timestamp_str(self):
        if self.timestamp is None:
            self.timestamp = time.localtime()
        return time.strftime(LOG_TIME_FORMAT, self.timestamp)

    def _get_timestamp_from_str(self, timestamp_str):
        try:
            timestamp = time.strptime(timestamp_str, LOG_TIME_FORMAT)
        except ValueError:
            logging.info('failed to parse timestamp %s, falling back to now'
                         % (timestamp_str, ))
            timestamp = time.localtime()
        return timestamp

    def _format_syslog(self, name, extra_values):
        return '%s%s|%s|%s|%s|%s|%s' % (
            self.get_signature(), name,
            self._get_timestamp_str(), get_level_str(self.level),
            extra_values, self.msg, self.msg_extra)

    def to_syslog(self, name):
        extra_values = '|'.join([str(value) for value in self.extra_values])
        return self._format_syslog(name, extra_values)

    def from_syslog(self):
	pass


CLASSIFY_RULES = (
    (re.compile('^!!AS '), AppserverEntry),
    (re.compile('^!!RQ '), RequestEntry),
    (re.compile('^.'), Entry)
    )
class Daemon(application.Application):

    def _application_main(self):
        if self._do_daemonize():
            self._daemonize()
        self._daemon_main()

    def _daemon_main(self):
        raise NotImplementedError()

    def _daemonize(self):
        try:
            pid = os.fork()
        except OSError, exc:
            raise Exception('failed to fork: %s' % (exc.strerror, ))

        if pid == 0:
            os.setsid()

            try:
                pid = os.fork()
            except OSError, exc:
                raise Exception('failed to fork: %s' % (exc.strerror, ))
            
            if pid == 0:
                os.chdir('/')
            else:
                os._exit(0)

        else:
            os._exit(0)

        self._flag_foreground = False

        pid_path = self._config.get(self._name, CFG_OPT_PID_PATH, None)
        if pid_path is not None:
            pid_file = os.path.join(pid_path, '%s.pid' % (self._name, ))
            if not write_file(pid_file, str(os.getpid())):
                logging.error('failed to write pid to %s' % (pid_file, ))
            
    def _do_daemonize(self):
        return self._config.get_bool(self._name,CFG_OPT_DAEMONIZE, '1')

class Log2DbDaemon(Daemon):

    def __init__(self):
        Daemon.__init__(self, 'log2db')

        self._socket = None
        self._writer = None
        self._bind_address = None
        self._bind_port = None

    def _daemon_main(self):
        self._bind_address = self._config.get('log2db', 'bind_address', '0.0.0.0')
        self._bind_port = int(self._config.get('log2db', 'bind_port', '514'))
        
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.bind((self._bind_address, self._bind_port))
        self._drop_privileges()
        while self._do_run():
            data, addr = self._recv_event()
            if data is not None:
                event = self._construct_event(data, addr)

        self._writer.stop()

    def _recv_event(self):
        try:
            data, addr = self._socket.recvfrom(READ_LOG_MAX)
        except socket.error:
            logging.error('failed receiving data from the network: %s'
                          % (socket.error, ))
            data = addr = None
	print data,addr
        return (data, addr)

    def _construct_event(self, data, addr):
        message =  self._decode_syslog(data)
        if message is not None:
            facility, priority, msg = message
            event_class = self._classify_event(msg, addr)
            event = event_class(msg, None, None, facility, priority, None, addr)
            event.from_syslog()
            return event

    def _decode_syslog(self, data):
        if data[0] != '<':
            return None
        log_start = data.find('>')
        if log_start == -1:
            return None

        try:
            facility_priority = int(data[1:log_start])
            facility = (facility_priority & 0xf8) >> 3
            priority = facility_priority & 0x07
        except ValueError:
            return None

        if data[-1] == '\000':
            msg = data[log_start+1:-1]
        else:
            msg = data[log_start+1:]

        return (facility, priority, msg)

    def _classify_event(self, data, addr):
        for rule, event_class in CLASSIFY_RULES:
            if rule.match(data):
                return event_class
        return Entry

def write_file(path, data, append=False):
    try:
        if append:
            f_obj = open(path, 'a')
        else:
            f_obj = open(path, 'a')

        f_obj.write(data)
        f_obj.close()
    except IOError:
        return False
    except OSError:
        return False

    return True
def main():
    application = Log2DbDaemon()
    application.main()

if __name__ == '__main__':
    main()

