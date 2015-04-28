import logging
import os
import signal
import sys
import ConfigParser
ENV_OPT_CONFIG = 'PLOG_CONFIG'
PATH_CONFIG = '/etc/plog.cfg'
CFG_SECT_LOGGING = 'logging'
CFG_OPT_LOG_LEVEL = 'log_level'
CFG_OPT_LOG_LEVEL_DEFAULT = 'WARNING'
CFG_OPT_GROUP = 'group'
CFG_SECT_GLOBAL = 'plog'
CFG_OPT_USER = 'user'
class Application(object):
    def __init__(self, name):
        self._name = name
        self._config = None
        self._flag_run = True
        self._flag_reload = False
        self._flag_foreground = True

    def print_usage(self):
        print >> sys.stderr, "usage: %s%" % (
            sys.argv[0], self._format_parameters())
        sys.exit(plog.EXIT_USAGE)

    def _format_parameters(self):
        return '' 

    def _parse_parameters(self):
        pass

    def _validate_parameters(self):
        return True

    def main(self):
        self._parse_parameters()
        if not self._validate_parameters():
            self.print_usage()

        self._initialize_config(None)
        self._initialize_logging()
        self._initialize_signal_handlers()

        self._application_main()

    def _application_main(self):
        raise NotImplementedError()

    def _initialize_config(self, path):
        self._config = Config(path)

    def _initialize_logging(self):
	pass

    def _initialize_signal_handlers(self):
        signal.signal(signal.SIGINT, self._signal_handle_int)
        signal.signal(signal.SIGHUP, self._signal_handle_hup)

    def _drop_privileges(self, user=None, group=None):

        if group is None:
            group = self._config.get(
                CFG_SECT_GLOBAL, CFG_OPT_GROUP, None)
            group = self._config.get(self._name, CFG_OPT_GROUP, group)
        if group is not None:
            import grp
            group_info = grp.getgrnam(group)
            os.setegid(group_info.gr_gid)

        if user is None:
            user = self._config.get(
                CFG_SECT_GLOBAL,CFG_OPT_USER, None)
            user = self._config.get(self._name, CFG_OPT_USER, user)
        if user is not None:
            import pwd
            user_info = pwd.getpwnam(user)
            os.seteuid(user_info.pw_uid)

    def stop(self):
        self._flag_run = False

    def _do_run(self):
        return self._flag_run

    def reload(self):
        self._flag_reload = True

    def _do_reload(self):
        return self._flag_reload

    def _signal_handle_hup(self, signum, frame):
        assert signum == signal.SIGHUP
        self._flag_reload = True

    def _signal_handle_int(self, signum, frame):
        assert signum == signal.SIGINT
        self._flag_run = False

    def _status_msg(self, msg):
        if self._flag_foreground:
            print msg
        logging.info(msg)

class Config(object):
    def __init__(self, path=None):                                                                                  
        if path is None:                                                                                            
            path = get_path()                                                                                       
                                                                                                                    
        self.path = path                                                                                            
        self.cfg = PlogConfigParser()                                                                               
        self.cfg.read(self.path)                                                                                    
                                                                                                                    
    def get(self, section, key, default=None):                                                                      
        try:                                                                                                        
            value = self.cfg.get(section, key)                                                                      
        except ConfigParser.NoSectionError:                                                                         
            value = default                                                                                         
        except ConfigParser.NoOptionError:                                                                          
            value = default                                                                                         
        return value                                                                                                
                                                                                                                    
    def get_bool(self, section, key, default):                                                                      
        value = self.get(section, key, default).lower()                                                             
        try:                                                                                                        
            value = self._to_bool(value)                                                                            
        except ValueError:                                                                                          
            logging.warning(                                                                                        
                'invalid boolean in configuration %s.%s, setting default %s'                                        
                % (section, key, default))                                                                          
            value = self._to_bool(value)                                                                            
        return value                                                                                                
                                                                                                                    
    def _to_bool(self, value):                                                                                      
        if value in ('1', 'yes', 'true'):                                                                           
            value = True                                                                                            
        elif value in ('0', 'no', 'false'):                                                                         
            value = False                                                                                           
        else:                                                                                                       
            raise ValueError('invalid boolean value %s' % (value, ))                                                
        return value                                                                                                
                                                                                                                    
    def get_int(self, section, key, default):                                                                       
        value = self.get(section, key, default)                                                                     
        try:                                                                                                        
            value = int(value)                                                                                      
        except ValueError:                                                                                          
            logging.warning(                                                                                        
                'invalid integer in configuration %s.%s, setting default %s'                                        
                % (section, key, default))                                                                          
            value = int(default)                                                                                    
        return value                                                                                                
                                                                                                                    
                                                                                                                    
    def get_db_config(self):                                                                                        
        db_config = self.cfg.get_options(plog.CFG_SECT_DATABASE)                                                    
        if 'port' in db_config:                                                                                     
            try:                                                                                                    
                db_config['port'] = int(db_config['port'])                                                          
            except ValueError:                                                                                      
                pass                                                                                                
                                                                                                                    
        return db_config                                                                                            
                                                                                                                    
    def get_log_files(self):                                                                                        
        import plog.file_parsers                                                                                    
        import plog.file2log.file                                                                                   
                                                                                                                    
        files = []                                                                                                  
                                                                                                                    
        sections = [s for s in self.cfg.sections() if s.startswith('file2log-')]                                    
        for section in sections:                                                                                    
            name = section[len('file2log-'):]                                                                       
            path = self.cfg.get(section, plog.CFG_OPT_PATH)                                                         
                                                                                                                    
            parser_name = self.cfg.get(                                                                             
                section, plog.CFG_OPT_PARSER, plog.DEFAULT_PARSER)                                                  
            parser_options = self.cfg.get_options_with_prefix(                                                      
                section, plog.CFG_OPT_PARSER + '-')                                                                 
            parser_options['path'] = path                                                                           
            parser = plog.file_parsers.get_parser(                                                                  
                parser_name, parser_options)                                                                        
                                                                                                                    
            files.append(plog.file2log.file.File(name, path, parser))                                               
                                                                                                                    
        return files  


def get_path():
    if ENV_OPT_CONFIG in os.environ:
        return os.environ.get(ENV_OPT_CONFIG)
    elif 'PHEW_CONFIG' in os.environ:
        return os.environ.get('PHEW_CONFIG')
    else:
        return PATH_CONFIG


class PlogConfigParser(ConfigParser.SafeConfigParser):
    def get_options(self, section):
        try:
            options = dict([(option, self.get(section, option))
                            for option in self.options(section)])
        except ConfigParser.NoSectionError:
            options = {}
        return options

    def get_options_with_prefix(self, section, pre):
        options = {}                                                                                                
                                                                                                                    
        for option in [o for o in self.options(section) if o.startswith(pre)]:                                      
            options[option[len(pre):]] = self.get(section, option)                                                  
                                                                                                                    
        return options  
