import heapq
import time
import random
from typing import Dict, List, Tuple, Optional
from message import Message, MessageType

class Router:
    def __init__(self, router_id: int):
        self.router_id = router_id
        self.neighbors: Dict[int, float] = {}  # {neighbor_id: cost}
        self.lsdb: Dict[int, Dict[int, float]] = {}  # Link State Database
        self.routing_table: Dict[int, Tuple[Optional[int], float]] = {}
        self.connections: List['Link'] = []
        self.is_active = True
        self.message_count = 0
        self.received_hellos = set()  # Для отслеживания полученных HELLO
        
    def add_connection(self, link: 'Link'):
        self.connections.append(link)
    
    def send_hello(self):
        """Отправка HELLO-пакетов всем соседям"""
        for link in self.connections:
            if link.is_active:
                other_end = link.get_other_end(self.router_id)
                hello_msg = Message(
                    sender_id=self.router_id,
                    receiver_id=other_end,
                    msg_type=MessageType.HELLO,
                    data={"sent_time": time.time()}
                )
                link.send_message(hello_msg, self.router_id)
    
    def receive_message(self, message: Message):
        """Обработка входящих сообщений"""
        if not self.is_active:
            return
        
        self.message_count += 1
            
        if message.msg_type == MessageType.HELLO:
            self._process_hello(message)
        elif message.msg_type == MessageType.SET_TOPOLOGY:
            self._process_topology(message)
        elif message.msg_type == MessageType.DATA:
            self._process_data(message)
    
    def _process_hello(self, message: Message):
        """Обработка HELLO-пакета"""
        if message.sender_id in self.received_hellos:
            return
            
        self.received_hellos.add(message.sender_id)
        
        # Используем реальную стоимость из линка вместо временной задержки
        cost = self._get_link_cost(message.sender_id)
        self.neighbors[message.sender_id] = cost
        print(f"Router {self.router_id}: learned neighbor {message.sender_id} with cost {cost:.3f}")
    
    def _get_link_cost(self, neighbor_id: int) -> float:
        """Получает стоимость соединения с соседом из соответствующего линка"""
        for link in self.connections:
            other_end = link.get_other_end(self.router_id)
            if other_end == neighbor_id:
                return link.get_cost()
        return 1.0  # стоимость по умолчанию
        
    def _process_topology(self, message: Message):
        """Обработка топологии от выделенного маршрутизатора"""
        self.lsdb = message.data.copy()
        
        # Добавляем собственную информацию в LSDB
        self.lsdb[self.router_id] = self.neighbors.copy()
        
        self._compute_shortest_paths()
    
    def _process_data(self, message: Message):
        """Обработка данных"""
        if message.receiver_id == self.router_id:
            print(f"Router {self.router_id}: received final message: {message.data}")
        else:
            # Пересылка сообщения дальше
            next_hop = self.routing_table.get(message.receiver_id, (None, float('inf')))[0]
            if next_hop:
                new_data = message.data + [f"via_{self.router_id}"] if isinstance(message.data, list) else [f"via_{self.router_id}"]
                new_msg = Message(
                    sender_id=message.sender_id,
                    receiver_id=message.receiver_id,
                    msg_type=MessageType.DATA,
                    data=new_data
                )
                self._send_to_neighbor(next_hop, new_msg)
    
    def _compute_shortest_paths(self):
        """Вычисление кратчайших путей алгоритмом Дейкстры"""
        distances = {self.router_id: 0}
        previous = {}
        pq = [(0, self.router_id)]
        
        # Инициализируем расстояния до всех известных роутеров
        for router in self.lsdb:
            if router != self.router_id:
                distances[router] = float('inf')
        
        while pq:
            current_dist, current = heapq.heappop(pq)
            
            if current not in self.lsdb:
                continue
                
            for neighbor, cost in self.lsdb[current].items():
                if not self._is_router_active(neighbor):
                    continue
                    
                distance = current_dist + cost
                if neighbor not in distances or distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current
                    heapq.heappush(pq, (distance, neighbor))
        
        # Построение таблицы маршрутизации
        self.routing_table = {}
        for router in distances:
            if router == self.router_id:
                continue
                
            if distances[router] < float('inf'):
                # Находим следующий хоп
                current = router
                while current in previous and previous[current] != self.router_id:
                    current = previous[current]
                
                if current in self.neighbors:
                    self.routing_table[router] = (current, distances[router])
        
        # Вывод вычисленной таблицы маршрутизации
        print(f"Router {self.router_id}: computed routing table: {self.routing_table}")
    
    def _is_router_active(self, router_id: int) -> bool:
        return True
    
    def _send_to_neighbor(self, neighbor_id: int, message: Message):
        for link in self.connections:
            other_end = link.get_other_end(self.router_id)
            if other_end == neighbor_id and link.is_active:
                link.send_message(message, self.router_id)
                return
    
    def send_data(self, destination_id: int, data: any):
        if destination_id in self.routing_table:
            next_hop, cost = self.routing_table[destination_id]
            message = Message(
                sender_id=self.router_id,
                receiver_id=destination_id,
                msg_type=MessageType.DATA,
                data=data
            )
            self._send_to_neighbor(next_hop, message)
            return True
        else:
            return False

class DesignatedRouter:
    def __init__(self):
        self.topology: Dict[int, Dict[int, float]] = {}
        self.routers: Dict[int, Router] = {}
    
    def register_router(self, router: Router):
        self.routers[router.router_id] = router
        self.topology[router.router_id] = {}
    
    def collect_neighbors(self):
        for router_id, router in self.routers.items():
            if router.is_active:
                self.topology[router_id] = router.neighbors.copy()
        
        self._broadcast_topology()
    
    def _broadcast_topology(self):
        for router in self.routers.values():
            if router.is_active:
                message = Message(
                    sender_id=-1,
                    receiver_id=router.router_id,
                    msg_type=MessageType.SET_TOPOLOGY,
                    data=self.topology
                )
                router.receive_message(message)