import socket
import logging
import threading
import time

class SyslogServer(threading.Thread):
    """ This is a test"""
    def __init__(self):
        threading.Thread.__init__(self,name="Syslog")
        self.daemon = True
        self.logfile = "syslog.txt"
        self.server = None
        self.ip = "0.0.0.0"
        self.port = 514
    def run(self):
        if self.server is None:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            logging.debug("socket bound to %s:%s" % (self.ip,self.port))
            print "Binding server to %s:%s" % (self.ip,self.port)
            self.server.bind((self.ip, self.port))
        try:
            f = open(self.logfile,"a")
            while True:
                try:
                    data, addr = self.server.recvfrom(1024)
		    print data, addr
                    f.write(data+"\n")
                    f.flush()
                    #print data
                except Exception, e:
                    logging.error("Error while receiving message: %s" % e)
                    f.close()
                    raise e
        finally:
            if not f.closed:
                f.close()






if __name__ == '__main__':
    logging.basicConfig(filename="debug.log",level=logging.DEBUG)
    print "Starting server..."
    c = SyslogServer()
    c.start()
    while True:
        time.sleep(1)


