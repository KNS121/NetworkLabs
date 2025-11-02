import time
from typing import List, Dict
from packet import Packet

class Sender:
    def __init__(self, data: str, package_data_size: int = 2, window_size: int = 1, timeout: float = 1.0):
        self.data = data
        self.package_data_size = package_data_size
        self.window_size = window_size
        self.timeout = timeout
        
        self.base = 0
        self.next_seq_num = 0
        self.timer = None
        self.packets = self._create_packets()
        
        self.stats = {
            'total_sent': 0,
            'retransmissions': 0,
            'start_time': None,
            'end_time': None
        }
    
    def _create_packets(self) -> List[Packet]:
        packets = []
        for i in range(0, len(self.data), self.package_data_size):
            packet_data = self.data[i:i+self.package_data_size]
            packet_number = i // self.package_data_size
            packets.append(Packet(packet_number, packet_data))
        return packets
    
    def can_send_new_packet(self) -> bool:
        return (self.next_seq_num < len(self.packets) and 
                self.next_seq_num < self.base + self.window_size)
    
    def send_new_packet(self) -> Packet:
        if not self.can_send_new_packet():
            return None
        
        packet = self.packets[self.next_seq_num]
        packet.sent_time = time.time()
        
        if self.base == self.next_seq_num:
            self.timer = time.time()
        
        self.next_seq_num += 1
        self.stats['total_sent'] += 1
        
        return packet
    
    def receive_ack(self, ack_num: int) -> bool:
        if ack_num >= self.base:
            # Помечаем пакеты как подтвержденные
            for seq_num in range(self.base, ack_num + 1):
                if seq_num < len(self.packets):
                    self.packets[seq_num].ack_received = True
            
            self.base = ack_num + 1
            
            if self.base < self.next_seq_num:
                self.timer = time.time()
            else:
                self.timer = None
            
            return True
        return False
    
    def check_timeout(self) -> List[Packet]:
        if (self.timer is not None and 
            time.time() - self.timer > self.timeout and 
            self.base < len(self.packets)):
            
            packets_to_resend = []
            for seq_num in range(self.base, self.next_seq_num):
                packet = self.packets[seq_num]
                packet.sent_time = time.time()
                packets_to_resend.append(packet)
                
                self.stats['total_sent'] += 1
                self.stats['retransmissions'] += 1
            
            if packets_to_resend:
                self.timer = time.time()
            
            return packets_to_resend
        
        return []
    
    def all_packets_confirmed(self) -> bool:
        return self.base >= len(self.packets)
    
    def get_protocol_name(self) -> str:
        return "Stop-and-Wait" if self.window_size == 1 else f"Go-Back-N (окно={self.window_size})"


class SelectiveRepeatSender(Sender):
    def __init__(self, data: str, package_data_size: int = 2, window_size: int = 4, timeout: float = 1.0):
        super().__init__(data, package_data_size, window_size, timeout)
        self.ack_received = [False] * len(self.packets)  # Отслеживание подтверждений для каждого пакета
        self.packet_timers = {}  # Индивидуальные таймеры для каждого пакета
    
    def send_new_packet(self) -> Packet:
        if not self.can_send_new_packet():
            return None
        
        packet = self.packets[self.next_seq_num]
        packet.sent_time = time.time()
        self.packet_timers[self.next_seq_num] = time.time()
        
        self.next_seq_num += 1
        self.stats['total_sent'] += 1
        
        return packet
    
    def receive_ack(self, ack_num: int) -> bool:
        if 0 <= ack_num < len(self.packets):
            self.ack_received[ack_num] = True
            # Удаляем таймер для подтвержденного пакета
            if ack_num in self.packet_timers:
                del self.packet_timers[ack_num]
            
            # Сдвигаем базовый номер, если подтверждены все предыдущие пакеты
            while self.base < len(self.packets) and self.ack_received[self.base]:
                self.base += 1
            
            return True
        return False
    
    def check_timeout(self) -> List[Packet]:
        current_time = time.time()
        packets_to_resend = []
        
        # Проверяем таймауты для всех пакетов в окне
        for seq_num in range(self.base, min(self.next_seq_num, len(self.packets))):
            if (seq_num in self.packet_timers and 
                current_time - self.packet_timers[seq_num] > self.timeout and
                not self.ack_received[seq_num]):
                
                packet = self.packets[seq_num]
                packet.sent_time = current_time
                self.packet_timers[seq_num] = current_time
                packets_to_resend.append(packet)
                
                self.stats['total_sent'] += 1
                self.stats['retransmissions'] += 1
        
        return packets_to_resend
    
    def all_packets_confirmed(self) -> bool:
        return all(self.ack_received) if self.ack_received else True
    
    def get_protocol_name(self) -> str:
        return f"Selective Repeat (окно={self.window_size})"