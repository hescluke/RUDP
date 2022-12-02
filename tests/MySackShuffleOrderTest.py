import random

from tests.BasicTest import BasicTest

class MySackShuffleOrderTest(BasicTest):
    def __init__(self, forwarder, input_file):
        super(MySackShuffleOrderTest, self).__init__(forwarder, input_file, sackMode = True)

    def handle_packet(self):
        for p in self.forwarder.in_queue:
            self.forwarder.out_queue.append(p)
        random.shuffle(self.forwarder.out_queue) # 每一次收到后都随机打乱out_queque
        self.forwarder.in_queue = []
