from typing import List, Tuple, Dict
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


class SelectiveRepeatReceiver(Receiver):
    def __init__(self, package_data_size: int = 2, window_size: int = 4):
        super().__init__(package_data_size)
        self.window_size = window_size
        self.receive_window = {}  # Хранит пакеты, полученные не по порядку
        self.base_seq = 0
    
    def receive_packet(self, packet: Packet) -> Tuple[bool, int]:
        if not packet.verify_hash():
            return False, self.base_seq
        
        # Если пакет в пределах окна
        if self.base_seq <= packet.seq_num < self.base_seq + self.window_size:
            # Сохраняем пакет, даже если он не в ожидаемой последовательности
            self.receive_window[packet.seq_num] = packet.data
            
            # Обновляем базовый номер, если получили ожидаемый пакет
            while self.base_seq in self.receive_window:
                self.received_packets.append((self.base_seq, self.receive_window[self.base_seq]))
                del self.receive_window[self.base_seq]
                self.base_seq += 1
            
            return True, packet.seq_num  # Подтверждаем конкретный полученный пакет
        
        # Если пакет уже подтвержден (дубликат)
        elif packet.seq_num < self.base_seq:
            return True, packet.seq_num
        
        # Пакет вне окна приема
        else:
            return False, self.base_seq
    
    def get_reassembled_data(self) -> str:
        # Сортируем по порядковым номерам
        sorted_packets = sorted(self.received_packets, key=lambda x: x[0])
        return ''.join(data for seq, data in sorted_packets)