import random

from tests.BasicTest import BasicTest

class MySackRepeatedlyArriveTest(BasicTest):
    def __init__(self, forwarder, input_file):
        super(MySackRepeatedlyArriveTest, self).__init__(forwarder, input_file, sackMode = True)
    def handle_packet(self):
        for p in self.forwarder.in_queue:
            self.forwarder.out_queue.append(p)
            if random.choice([True, False]): # 模拟重复达到报文段
                self.forwarder.out_queue.append(p)
        self.forwarder.in_queue = []
