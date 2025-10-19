import time
from sender import Sender
from receiver import Receiver
from network import NetworkSimulator

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
            'total_time': 0,
            'efficiency': 0,
            'total_sent': 0,
            'retransmissions': 0
        }
    
    def run_simulation(self) -> bool:
        start_time = time.time()
        iteration = 0
        
        while not self.sender.all_packets_confirmed() :
            #iteration += 1

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
            
            time.sleep(0.001) 
        
        self.stats['iterations'] = iteration
        self.stats['total_time'] = time.time() - start_time
        self.stats['total_sent'] = self.sender.stats['total_sent']
        self.stats['retransmissions'] = self.sender.stats['retransmissions']
        self.stats['efficiency'] = len(self.data) / self.sender.stats['total_sent'] if self.sender.stats['total_sent'] > 0 else 0
        
        received_data = self.receiver.get_reassembled_data()
        success = self.data == received_data
        
        return success