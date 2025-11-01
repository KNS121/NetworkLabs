import heapq
import time
import random
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class MessageType(Enum):
    HELLO = "HELLO"
    GET_NEIGHBORS = "GET_NEIGHBORS"
    SET_NEIGHBORS = "SET_NEIGHBORS"
    SET_TOPOLOGY = "SET_TOPOLOGY"
    DATA = "DATA"
    DISCONNECT = "DISCONNECT"

@dataclass
class Message:
    sender_id: int
    receiver_id: Optional[int]
    msg_type: MessageType
    data: any
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

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
        cost = time.time() - message.data["sent_time"]
        self.neighbors[message.sender_id] = max(0.1, cost)  # Минимальная стоимость 0.1
        
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

class Link:
    def __init__(self, router1_id: int, router2_id: int, failure_probability: float = 0.0):
        self.router1_id = router1_id
        self.router2_id = router2_id
        self.failure_probability = failure_probability
        self.is_active = True
        self.router1_ref = None
        self.router2_ref = None
    
    def connect_routers(self, router1: Router, router2: Router):
        self.router1_ref = router1
        self.router2_ref = router2
    
    def get_other_end(self, router_id: int) -> int:
        return self.router2_id if router_id == self.router1_id else self.router1_id
    
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

def create_linear_topology():
    print("\n" + "="*60)
    print("СОЗДАНИЕ ЛИНЕЙНОЙ ТОПОЛОГИИ: 0-1-2-3-4")
    print("="*60)
    
    routers = [Router(i) for i in range(5)]
    links = [
        Link(0, 1, 0.1),
        Link(1, 2, 0.1), 
        Link(2, 3, 0.1),
        Link(3, 4, 0.1)
    ]
    
    dr = DesignatedRouter()
    for router in routers:
        dr.register_router(router)
    
    # Связываем роутеры с линками
    for link in links:
        router1 = next(r for r in routers if r.router_id == link.router1_id)
        router2 = next(r for r in routers if r.router_id == link.router2_id)
        link.connect_routers(router1, router2)
        
        router1.add_connection(link)
        router2.add_connection(link)
    
    return routers, dr

def create_star_topology():
    print("\n" + "="*60)
    print("СОЗДАНИЕ ЗВЕЗДООБРАЗНОЙ ТОПОЛОГИИ")
    print("="*60)
    
    routers = [Router(i) for i in range(5)]
    links = [
        Link(0, 1, 0.1),
        Link(0, 2, 0.1),
        Link(0, 3, 0.1), 
        Link(0, 4, 0.1)
    ]
    
    dr = DesignatedRouter()
    for router in routers:
        dr.register_router(router)
    
    for link in links:
        router1 = next(r for r in routers if r.router_id == link.router1_id)
        router2 = next(r for r in routers if r.router_id == link.router2_id)
        link.connect_routers(router1, router2)
        
        router1.add_connection(link)
        router2.add_connection(link)
    
    return routers, dr

def create_ring_topology():
    print("\n" + "="*60)
    print("СОЗДАНИЕ КОЛЬЦЕВОЙ ТОПОЛОГИИ")
    print("="*60)
    
    routers = [Router(i) for i in range(5)]
    links = [
        Link(0, 1, 0.1),
        Link(1, 2, 0.1),
        Link(2, 3, 0.1),
        Link(3, 4, 0.1),
        Link(4, 0, 0.1)  # Замыкаем кольцо
    ]
    
    dr = DesignatedRouter()
    for router in routers:
        dr.register_router(router)
    
    for link in links:
        router1 = next(r for r in routers if r.router_id == link.router1_id)
        router2 = next(r for r in routers if r.router_id == link.router2_id)
        link.connect_routers(router1, router2)
        
        router1.add_connection(link)
        router2.add_connection(link)
    
    return routers, dr

def simulate_topology(routers, dr, topology_name):
    print(f"\n{'='*50}")
    print(f"МОДЕЛИРОВАНИЕ: {topology_name}")
    print(f"{'='*50}")
    
    # Фаза установления соседства
    print("\n1. ФАЗА УСТАНОВЛЕНИЯ СОСЕДСТВА:")
    for router in routers:
        router.send_hello()
    time.sleep(0.2)
    
    # Сбор информации о топологии
    print("\n2. ФАЗА РАСПРОСТРАНЕНИЯ ТОПОЛОГИИ:")
    dr.collect_neighbors()
    
    # Тестовая отправка данных
    print("\n3. ТЕСТОВАЯ ПЕРЕСЫЛКА ДАННЫХ:")
    test_cases = [
        (0, 4, "сообщение от 0 к 4"),
        (2, 0, "сообщение от 2 к 0"), 
        (1, 3, "сообщение от 1 к 3")
    ]
    
    success_count = 0
    for src, dst, desc in test_cases:
        print(f"\n--- Тест: {desc} ---")
        if routers[src].send_data(dst, f"data_from_{src}"):
            success_count += 1
            print(f"УСПЕХ: Router {src} отправил данные Router {dst}")
            time.sleep(0.1)
        else:
            print(f"НЕУДАЧА: Router {src} не может отправить данные Router {dst}")
    
    # Имитация разрыва связи
    print("\n4. ТЕСТ УСТОЙЧИВОСТИ К РАЗРЫВАМ:")
    print("--- Разрыв связи с маршрутизатором 2 ---")
    if 2 in dr.routers:
        dr.routers[2].is_active = False
        # Обновляем топологию
        dr.collect_neighbors()
    
    # Попытка отправки после разрыва
    print("\n5. ПЕРЕСЫЛКА ПОСЛЕ РАЗРЫВА:")
    recovery_tests = [
        (0, 4, "сообщение после разрыва от 0 к 4"),
        (1, 3, "сообщение после разрыва от 1 к 3")
    ]
    
    recovery_success = 0
    for src, dst, desc in recovery_tests:
        print(f"\n--- Тест: {desc} ---")
        if routers[src].send_data(dst, f"recovery_from_{src}"):
            recovery_success += 1
            print(f"УСПЕХ: Router {src} отправил данные Router {dst} после разрыва")
            time.sleep(0.1)
        else:
            print(f"НЕУДАЧА: Router {src} не может отправить данные Router {dst} после разрыва")
    
    # Сбор статистики
    stats = {}
    total_messages = 0
    for router in routers:
        stats[router.router_id] = {
            'message_count': router.message_count,
            'neighbors_count': len(router.neighbors),
            'routing_table_size': len(router.routing_table)
        }
        total_messages += router.message_count
    
    print(f"\n6. СТАТИСТИКА ДЛЯ {topology_name}:")
    for router_id, stat in stats.items():
        print(f"  Router {router_id}: сообщений={stat['message_count']}, соседей={stat['neighbors_count']}, маршрутов={stat['routing_table_size']}")
    
    return {
        'initial_success': success_count,
        'recovery_success': recovery_success,
        'total_tests': len(test_cases),
        'total_messages': total_messages,
        'stats': stats
    }

def compare_topologies():
    print("СРАВНЕНИЕ ТОПОЛОГИЙ СЕТИ")
    print("="*80)
    
    results = {}
    
    # Тестируем линейную топологию
    routers, dr = create_linear_topology()
    results['linear'] = simulate_topology(routers, dr, "ЛИНЕЙНАЯ ТОПОЛОГИЯ")
    
    # Тестируем звездообразную топологию  
    routers, dr = create_star_topology()
    results['star'] = simulate_topology(routers, dr, "ЗВЕЗДООБРАЗНАЯ ТОПОЛОГИЯ")
    
    # Тестируем кольцевую топологию
    routers, dr = create_ring_topology()
    results['ring'] = simulate_topology(routers, dr, "КОЛЬЦЕВАЯ ТОПОЛОГИЯ")
    
    # Сравниваем результаты
    print("\n" + "="*80)
    print("ИТОГОВОЕ СРАВНЕНИЕ ТОПОЛОГИЙ")
    print("="*80)
    
    topology_names = {
        'linear': 'Линейная',
        'star': 'Звездообразная', 
        'ring': 'Кольцевая'
    }
    
    for topology, result in results.items():
        success_rate = (result['initial_success'] / result['total_tests']) * 100
        recovery_rate = (result['recovery_success'] / 2) * 100  # 2 теста после разрыва
        
        print(f"\n{topology_names[topology]} топология:")
        print(f"  Успешная доставка: {result['initial_success']}/{result['total_tests']} ({success_rate:.1f}%)")
        print(f"  Восстановление после разрыва: {result['recovery_success']}/2 ({recovery_rate:.1f}%)")
        print(f"  Всего сообщений в сети: {result['total_messages']}")
        
        # Анализ распределения нагрузки
        message_counts = [stat['message_count'] for stat in result['stats'].values()]
        if message_counts:
            avg_messages = sum(message_counts) / len(message_counts)
            max_messages = max(message_counts)
            min_messages = min(message_counts)
            load_imbalance = ((max_messages - min_messages) / avg_messages) * 100 if avg_messages > 0 else 0
            print(f"  Неравномерность нагрузки: {load_imbalance:.1f}%")
            
        # Анализ связности
        avg_neighbors = sum(stat['neighbors_count'] for stat in result['stats'].values()) / len(result['stats'])
        print(f"  Среднее число соседей: {avg_neighbors:.1f}")

if __name__ == "__main__":
    compare_topologies()