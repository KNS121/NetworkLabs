import time
import random
from router import Router, DesignatedRouter
from link import Link

def create_linear_topology():
    print("\n" + "="*60)
    print("СОЗДАНИЕ ЛИНЕЙНОЙ ТОПОЛОГИИ: 0-1-2-3-4")
    print("="*60)
    
    routers = [Router(i) for i in range(5)]
    # Добавляем разные стоимости для разных соединений
    links = [
        Link(0, 1, 0.1, cost=1.0),    # Быстрое соединение
        Link(1, 2, 0.1, cost=5.0),    # Медленное соединение  
        Link(2, 3, 0.1, cost=2.0),    # Среднее соединение
        Link(3, 4, 0.1, cost=1.0)     # Быстрое соединение
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
    # Центральный узел имеет разные стоимости до периферийных узлов
    links = [
        Link(0, 1, 0.1, cost=1.0),  # Быстрое соединение
        Link(0, 2, 0.1, cost=3.0),  # Медленное соединение
        Link(0, 3, 0.1, cost=2.0),  # Среднее соединение
        Link(0, 4, 0.1, cost=1.0)   # Быстрое соединение
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
    # В кольцевой топологии разные стоимости создают альтернативные маршруты
    links = [
        Link(0, 1, 0.1, cost=1.0),  # Быстрое соединение
        Link(1, 2, 0.1, cost=5.0),  # Медленное соединение (проблемный участок)
        Link(2, 3, 0.1, cost=1.0),  # Быстрое соединение
        Link(3, 4, 0.1, cost=1.0),  # Быстрое соединение
        Link(4, 0, 0.1, cost=2.0)   # Среднее соединение (альтернативный путь)
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
    print("Разрыв связи с маршрутизатором 2")
    if 2 in dr.routers:
        dr.routers[2].is_active = False
        # Обновляем топологию
        dr.collect_neighbors()
    
    # ОДНА проверка после разрыва
    print("\n5. ПЕРЕСЫЛКА ПОСЛЕ РАЗРЫВА:")
    recovery_test = (0, 4, "сообщение после разрыва от 0 к 4")
    
    src, dst, desc = recovery_test
    print(f"\n--- Тест: {desc} ---")
    recovery_success = 0
    if routers[src].send_data(dst, f"recovery_from_{src}"):
        recovery_success = 1
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
    
    # линия
    routers, dr = create_linear_topology()
    results['linear'] = simulate_topology(routers, dr, "ЛИНЕЙНАЯ ТОПОЛОГИЯ")
    
    # ззведзда
    routers, dr = create_star_topology()
    results['star'] = simulate_topology(routers, dr, "ЗВЕЗДООБРАЗНАЯ ТОПОЛОГИЯ")
    
    # кольцо
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
        recovery_rate = result['recovery_success'] * 100  # 1 тест после разрыва
        
        print(f"\n{topology_names[topology]} топология:")
        print(f"  Успешная доставка: {result['initial_success']}/{result['total_tests']} ({success_rate:.1f}%)")
        print(f"  Восстановление после разрыва: {result['recovery_success']}/1 ({recovery_rate:.1f}%)")
        print(f"  Всего сообщений в сети: {result['total_messages']}")
        
        # Анализ распределения нагрузки
        message_counts = [stat['message_count'] for stat in result['stats'].values()]
        if message_counts:
            avg_messages = sum(message_counts) / len(message_counts)
            max_messages = max(message_counts)
            min_messages = min(message_counts)
            load_imbalance = ((max_messages - min_messages) / avg_messages) * 100 if avg_messages > 0 else 0
            print(f"  Неравномерность нагрузки: {load_imbalance:.1f}%")
            