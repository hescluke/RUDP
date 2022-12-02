import random

from tests.BasicTest import BasicTest

class MyDataErrorTest(BasicTest):
    def handle_packet(self):
        for p in self.forwarder.in_queue:
            if random.choice([True, False]): # 随机插入新的字符串模拟数据链路层传输出错
                p.data = "hhh"
            self.forwarder.out_queue.append(p)
        self.forwarder.in_queue = []
