import sys
import getopt
import time
import Checksum
import BasicSender

'''
This is a skeleton sender class. Create a fantastic transport protocol here.
'''


class Sender(BasicSender.BasicSender):
    def __init__(self, dest, port, filename, debug=False, sackMode=False):
        super(Sender, self).__init__(dest, port, filename, debug)
        self.sackMode = sackMode
        self.base = 0  # 发送窗口的起始处，发送窗口为[base，base+sendWindow-1]
        self.iter = 0  # 现在在发顺序号为iter的包，iter在[base，base+sendWindow-1]中
        self.seqno = 0  # 即将发送的包的顺序号
        self.sendWin = 5  # 发送窗口大小为5
        self.packets = []  # 所有
        self.timeout = 0.5  # 超过500ms就算超时
        self.timers = []  # 每个包的超时计时器
        self.ack = -1 # 累计确认ack
        if sackMode:
            self.sacks = [] # 记录选择重传中已经收到的选择确认ack

    def baseMax(self):  # 获得发送窗口最大值
        return min(self.base + self.sendWin - 1, len(self.packets) - 1)

    def make_packets(self):  # 一次性生成所有的包，并储存在packets数组中
        seqno = 0  # 顺序号
        msg = self.infile.read(1000)  # 每1000个字节一个段
        msg_type = None
        while not msg_type == 'end':
            next_msg = self.infile.read(1000)  # 检测接下来是否还有数据要发
            msg_type = 'data'
            if seqno == 0:  # 顺序号为0说明这是起始段
                msg_type = 'start'
            elif next_msg == "":  # 如果没有数据就说明这一段就是最后一段，循环终止
                msg_type = 'end'

            packet = self.make_packet(msg_type, seqno, msg)  # 将（数据类别，顺序号，数据）封装成包
            self.packets.append(packet)

            msg = next_msg
            seqno += 1

        self.infile.close()
        self.timers = [0 for i in range(len(self.packets))]

    # Main sending loop.
    def start(self):
        self.make_packets()  # 首先将所有数据打包好
        self.iter = self.base
        while self.ack < len(self.packets):
            while self.base <= self.iter <= self.baseMax():  # 将发送窗口的包全部发出去
                if not sackMode or (self.iter not in self.sacks):
                    self.send(self.packets[self.iter])
                    self.timers[self.iter] = time.time()

                    if self.debug:
                        print("send seqno={} timer={} ...".format(self.iter, self.timers[self.iter]))
                    self.iter += 1

            # 接收receiver发来的确认的ack
            response = self.receive(self.timeout)

            if response != None:
                response = response.decode()
                self.handle_response(response)

            for i in range(self.base, self.iter):  # 检测发送窗口中的包是否超时
                now = time.time()
                if now - self.timers[i] > self.timeout and self.ack <= i : # 这个包超时，并且累计确认的ack不能确认这个包
                    self.handle_timeout(i)
                    break # 这一个包超时就可以直接从这里开始重传了，后面的都不用再检测了

    def handle_timeout(self, i):
        self.iter = i  # 下一次从这个包开始重新传

    def handle_new_ack(self, ack):
        self.ack = max(self.ack, ack)  # 如果收到的ack更新则更新ack
        if self.debug:
            print("update base from {} to {}".format(self.base, self.ack))
        self.base = self.ack

    def handle_dup_ack(self, ack):
        pass # 重复ack不做处理直接丢弃

    def log(self, msg):
        if self.debug:
            print(msg)

    def handle_response(self,response_packet):
        if Checksum.validate_checksum(response_packet): # 计算检验和
            pass
            # print("recv: %s" % response_packet)
        else:
            print("recv: %s <--- CHECKSUM FAILED" % response_packet)
            return # 校验和不对直接退出

        msg_type, seqno, data, checksum = self.split_packet(response_packet) # 解析收到的包
        if msg_type == 'ack':
            if int(seqno) > self.base:
                self.handle_new_ack(int(seqno))
            else:
                self.handle_dup_ack(int(seqno))
        if msg_type == 'sack':
            seqno = seqno.split(";")
            sacks = [seqno[i] for i in range(1, len(seqno))] # 选择确认的sacks
            seqno = seqno[0] # 得到累计确认的ack
            if len(sacks) > 0:
                if int(seqno) > self.base:
                    self.handle_new_ack(int(seqno))
                else:
                    self.handle_dup_ack(int(seqno))
                for i in sacks:
                    if i not in self.sacks:
                        self.sacks.append(i)


'''
This will be run if you run this script from the command line. You should not
change any of this; the grader may rely on the behavior here to test your
submission.
'''
if __name__ == "__main__":
    def usage():
        print("RUDP Sender")
        print("-f FILE | --file=FILE The file to transfer; if empty reads from STDIN")
        print("-p PORT | --port=PORT The destination port, defaults to 33122")
        print("-a ADDRESS | --address=ADDRESS The receiver address or hostname, defaults to localhost")
        print("-d | --debug Print debug messages")
        print("-h | --help Print this usage message")
        print("-k | --sack Enable selective acknowledgement mode")


    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   "f:p:a:dk", ["file=", "port=", "address=", "debug=", "sack="])
    except:
        usage()
        exit()

    port = 33122
    dest = "localhost"
    filename = None
    debug = False
    sackMode = False

    for o, a in opts:
        if o in ("-f", "--file="):
            filename = a
        elif o in ("-p", "--port="):
            port = int(a)
        elif o in ("-a", "--address="):
            dest = a
        elif o in ("-d", "--debug="):
            debug = True
        elif o in ("-k", "--sack="):
            sackMode = True

    s = Sender(dest, port, filename, debug, sackMode)
    try:
        s.start()
    except (KeyboardInterrupt, SystemExit):
        exit()
