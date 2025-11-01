import random
from typing import Optional
from message import Message

class Link:
    def __init__(self, router1_id: int, router2_id: int, failure_probability: float = 0.0, cost: float = 1.0):
        self.router1_id = router1_id
        self.router2_id = router2_id
        self.failure_probability = failure_probability
        self.cost = cost  # ← Добавляем реальную стоимость
        self.is_active = True
        self.router1_ref = None
        self.router2_ref = None
    
    def connect_routers(self, router1: 'Router', router2: 'Router'):
        self.router1_ref = router1
        self.router2_ref = router2
    
    def get_other_end(self, router_id: int) -> int:
        return self.router2_id if router_id == self.router1_id else self.router1_id
    
    def get_cost(self) -> float:
        """Возвращает стоимость соединения"""
        return self.cost
    
    def send_message(self, message: Message, sender_id: int):
        if not self.is_active:
            return
        
        # Имитация вероятности отказа
        if random.random() < self.failure_probability:
            self.is_active = False
            return
        
        receiver_id = self.get_other_end(sender_id)
        
        # Находим получателя и доставляем сообщение
        if receiver_id == self.router1_id and self.router1_ref:
            self.router1_ref.receive_message(message)
        elif receiver_id == self.router2_id and self.router2_ref:
            self.router2_ref.receive_message(message)