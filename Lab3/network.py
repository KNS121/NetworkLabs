import random
from packet import Packet

class NetworkSimulator:
    def __init__(self, packet_loss_prob: float = 0.2, ack_loss_prob: float = 0.1, corruption_prob: float = 0.1):
        self.packet_loss_prob = packet_loss_prob
        self.ack_loss_prob = ack_loss_prob
        self.corruption_prob = corruption_prob
        self.packets_in_transit = []
    
    def transmit_packet(self, packet: Packet) -> bool:
        packet_copy = Packet(packet.seq_num, packet.data)
        packet_copy.hash_sum = packet.hash_sum
        
        if random.random() < self.packet_loss_prob:
            return False
        
        if random.random() < self.corruption_prob:
            original_data = packet_copy.data
            corrupted_data = ''.join(chr(random.randint(97, 122)) for _ in range(len(original_data)))
            packet_copy.data = corrupted_data
        
        self.packets_in_transit.append(packet_copy)
        return True
    
    def transmit_ack(self, ack_num: int) -> bool:
        if random.random() < self.ack_loss_prob:
            return False
        return True