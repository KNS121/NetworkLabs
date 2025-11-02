import time
from sender import Sender, SelectiveRepeatSender
from receiver import Receiver, SelectiveRepeatReceiver
from network import NetworkSimulator

class ProtocolSimulator:
    def __init__(self, data: str, window_size: int = 1, protocol_type: str = "auto", **kwargs):
        self.data = data
        
        package_data_size = kwargs.get('package_data_size', 2)
        timeout = kwargs.get('timeout', 2.0)
        packet_loss = kwargs.get('packet_loss_prob', 0.2)
        ack_loss = kwargs.get('ack_loss_prob', 0.1)
        corruption = kwargs.get('corruption_prob', 0.1)
        
        # Определяем тип протокола автоматически или по указанию
        if protocol_type == "auto":
            if window_size == 1:
                protocol_type = "stop_and_wait"
            else:
                protocol_type = "go_back_n"
        
        # Создаем отправителя и получателя в зависимости от типа протокола
        if protocol_type == "selective_repeat":
            self.sender = SelectiveRepeatSender(data, package_data_size, window_size, timeout)
            self.receiver = SelectiveRepeatReceiver(package_data_size, window_size)
        else:
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
        
        while not self.sender.all_packets_confirmed():
            iteration += 1

            # Проверка таймаутов и повторная отправка
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
        useful_packets = len(self.data) // self.sender.package_data_size
        
        if useful_packets > 0:
            self.stats['efficiency'] = useful_packets / self.sender.stats['total_sent']
        else:
            self.stats['efficiency'] = 0
    
        received_data = self.receiver.get_reassembled_data()
        success = self.data == received_data
        
        return success