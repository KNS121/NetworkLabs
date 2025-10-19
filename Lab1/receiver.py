from typing import List, Tuple
from packet import Packet

class Receiver:
    def __init__(self, package_data_size: int = 2):
        self.package_data_size = package_data_size
        self.expected_seq_num = 0
        self.received_packets = []
        self.last_ack_sent = -1
    
    def receive_packet(self, packet: Packet) -> Tuple[bool, int]:
        if not packet.verify_hash():
            return False, self.expected_seq_num - 1
        
        if packet.seq_num == self.expected_seq_num:
            self.received_packets.append((packet.seq_num, packet.data))
            self.expected_seq_num += 1
            ack_num = self.expected_seq_num - 1
            self.last_ack_sent = ack_num
            return True, ack_num
        
        elif packet.seq_num < self.expected_seq_num:
            return True, self.last_ack_sent
        
        else:
            return False, self.expected_seq_num - 1
    
    def get_reassembled_data(self) -> str:
        self.received_packets.sort(key=lambda x: x[0])
        return ''.join(data for seq, data in self.received_packets)