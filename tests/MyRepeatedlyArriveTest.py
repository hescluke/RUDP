import random

from tests.BasicTest import BasicTest

class MyRepeatedlyArriveTest(BasicTest):
    def handle_packet(self):
        for p in self.forwarder.in_queue:
            self.forwarder.out_queue.append(p)
            if random.choice([True, False]): # 模拟重复达到报文段
                self.forwarder.out_queue.append(p)
        self.forwarder.in_queue = []
