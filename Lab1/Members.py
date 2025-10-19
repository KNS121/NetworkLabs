import hashlib
import time
import random
from typing import List, Tuple

class Packet:
    def __init__(self, seq_num: int, data: str):
        self.seq_num = seq_num
        self.data = data
        self.hash_sum = self.calculate_hash_sum(data)
        self.sent_time = None
        self.ack_received = False
    
    def calculate_hash_sum(self, data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()
    
    def verify_hash(self) -> bool:
        return self.calculate_hash_sum(self.data) == self.hash_sum

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

class ProtocolSimulator:
    def __init__(self, data: str, window_size: int = 1, **kwargs):
        self.data = data
        
        package_data_size = kwargs.get('package_data_size', 2)
        timeout = kwargs.get('timeout', 2.0)
        packet_loss = kwargs.get('packet_loss_prob', 0.2)
        ack_loss = kwargs.get('ack_loss_prob', 0.1)
        corruption = kwargs.get('corruption_prob', 0.1)
        
        self.sender = Sender(data, package_data_size, window_size, timeout)
        self.receiver = Receiver(package_data_size)
        self.network = NetworkSimulator(packet_loss, ack_loss, corruption)
        
        self.stats = {
            'protocol': self.sender.get_protocol_name(),
            'iterations': 0,
            'total_time': 0
        }
    
    def run_simulation(self, max_iterations: int = 1000) -> bool:
        start_time = time.time()
        iteration = 0
        
        while not self.sender.all_packets_confirmed():
            #iteration += 1
            
            # Проверка таймаута и повторная отправка
            resent_packets = self.sender.check_timeout()
            for packet in resent_packets:
                self.network.transmit_packet(packet)
            
            # Отправка новых пакетов
            while self.sender.can_send_new_packet():
                packet = self.sender.send_new_packet()
                if packet:
                    self.network.transmit_packet(packet)
            
            # Обработка пакетов в сети
            for packet in self.network.packets_in_transit[:]:
                success, ack_num = self.receiver.receive_packet(packet)
                if success:
                    # ACK отправляется только если пакет успешно принят
                    if self.network.transmit_ack(ack_num):
                        self.sender.receive_ack(ack_num)
                # Пакет удаляется из сети после обработки
                self.network.packets_in_transit.remove(packet)
            
            time.sleep(0.01)  # Уменьшил задержку для скорости
        
        self.stats['iterations'] = iteration
        self.stats['total_time'] = time.time() - start_time
        
        received_data = self.receiver.get_reassembled_data()
        success = self.data == received_data
        
        self._print_results(success, received_data)
        return success
    
    def _print_results(self, success: bool, received_data: str):
        print(f"\n📊 РЕЗУЛЬТАТЫ {self.stats['protocol']}")
        print("=" * 50)
        print(f"Успешно: {'ДА' if success else 'НЕТ'}")
        print(f"Итераций: {self.stats['iterations']}")
        print(f"Время: {self.stats['total_time']:.2f} сек")
        print(f"Всего отправок: {self.sender.stats['total_sent']}")
        print(f"Повторных отправок: {self.sender.stats['retransmissions']}")
        print(f"Эффективность: {len(self.data) / self.sender.stats['total_sent']:.2%}")
        print(f"Исходные данные: '{self.data}'")
        print(f"Полученные данные: '{received_data}'")

def compare_protocols():
    """Сравнение Go-Back-N (окно=2) и Stop-and-Wait"""
    test_data = "HelloWorld" *5
    
    print("СРАВНЕНИЕ ПРОТОКОЛОВ")
    print("=" * 60)
    
    # Stop-and-Wait (окно=1)
    print("\n1. STOP-AND-WAIT:")
    simulator_sw = ProtocolSimulator(
        test_data, 
        window_size=1,
        package_data_size=2,
        packet_loss_prob=0.2,  # Увеличил для наглядности
        corruption_prob=0.2,
        ack_loss_prob=0.2,
        timeout=0.5
    )
    simulator_sw.run_simulation()
    
    # Go-Back-N (окно=2)
    print("\n2. GO-BACK-N:")
    simulator_gbn = ProtocolSimulator(
        test_data,
        window_size=2,
        package_data_size=2, 
        packet_loss_prob=0.2,
        corruption_prob=0.2,
        ack_loss_prob=0.2,
        timeout=0.5
    )
    simulator_gbn.run_simulation()

if __name__ == "__main__":
    compare_protocols()