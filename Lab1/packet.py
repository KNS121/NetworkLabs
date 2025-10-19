import hashlib

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