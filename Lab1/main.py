import matplotlib.pyplot as plt
import csv
import os
from datetime import datetime
from simulator import ProtocolSimulator

def compare_protocols():
    # Данные для тестирования с разными размерами
    test_cases = [
        "HelloWorld",
        "HelloWorld" * 2,
        "HelloWorld" * 4,
        "HelloWorld" * 8,
        "HelloWorld" * 16,
        "HelloWorld" * 32
    ]
    
    results = {
        'Stop-and-Wait': {'time': [], 'efficiency': []},
        'Go-Back-N': {'time': [], 'efficiency': []},
        'Selective Repeat': {'time': [], 'efficiency': []}
    }
    
    data_sizes = [len(data) for data in test_cases]
    
    print("=" * 80)
    print("СРАВНЕНИЕ ПРОТОКОЛОВ ПЕРЕДАЧИ ДАННЫХ")
    print("=" * 80)
    
    for i, test_data in enumerate(test_cases):
        data_size = len(test_data)
        print(f"\nТестирование с размером данных: {data_size} символов")
        print("-" * 50)
        
        # Stop-and-Wait (окно=1)
        simulator_sw = ProtocolSimulator(
            test_data, 
            window_size=1,
            protocol_type="stop_and_wait",
            package_data_size=2,
            packet_loss_prob=0.1,
            corruption_prob=0.1,
            ack_loss_prob=0.1,
            timeout=0.3
        )
        simulator_sw.run_simulation()
        results['Stop-and-Wait']['time'].append(simulator_sw.stats['total_time'])
        results['Stop-and-Wait']['efficiency'].append(simulator_sw.stats.get('efficiency', 0))
        
        # Go-Back-N (окно=4)
        simulator_gbn = ProtocolSimulator(
            test_data,
            window_size=4,
            protocol_type="go_back_n",
            package_data_size=2,
            packet_loss_prob=0.1,
            corruption_prob=0.1,
            ack_loss_prob=0.1,
            timeout=0.3
        )
        simulator_gbn.run_simulation()
        results['Go-Back-N']['time'].append(simulator_gbn.stats['total_time'])
        results['Go-Back-N']['efficiency'].append(simulator_gbn.stats.get('efficiency', 0))
        
        # Selective Repeat (окно=4)
        simulator_sr = ProtocolSimulator(
            test_data,
            window_size=4,
            protocol_type="selective_repeat",
            package_data_size=2,
            packet_loss_prob=0.1,
            corruption_prob=0.1,
            ack_loss_prob=0.1,
            timeout=0.3
        )
        simulator_sr.run_simulation()
        results['Selective Repeat']['time'].append(simulator_sr.stats['total_time'])
        results['Selective Repeat']['efficiency'].append(simulator_sr.stats.get('efficiency', 0))
        
        # Вывод результатов для текущего размера данных
        print(f"Stop-and-Wait:     {simulator_sw.stats['total_time']:.2f} сек")
        print(f"Go-Back-N:         {simulator_gbn.stats['total_time']:.2f} сек")
        print(f"Selective Repeat:  {simulator_sr.stats['total_time']:.2f} сек")
    
    # Вывод сводной таблицы
    print("\n" + "=" * 80)
    print("СВОДНАЯ ТАБЛИЦА РЕЗУЛЬТАТОВ")
    print("=" * 80)
    print(f"{'Размер данных':<15} {'Stop-and-Wait':<15} {'Go-Back-N':<15} {'Selective Repeat':<15}")
    print("-" * 65)
    
    for i, size in enumerate(data_sizes):
        sw_time = results['Stop-and-Wait']['time'][i]
        gbn_time = results['Go-Back-N']['time'][i]
        sr_time = results['Selective Repeat']['time'][i]
        print(f"{size:<15} {sw_time:<15.2f} {gbn_time:<15.2f} {sr_time:<15.2f}")
    
    # Экспорт в CSV
    #export_to_csv(data_sizes, results)
    
    # Построение графика
    plot_results(data_sizes, results)
    
    # Дополнительные анализы
    analyze_packet_loss_dependency()
    analyze_window_size_dependency()

def analyze_packet_loss_dependency():
    """Анализ зависимости эффективности от вероятности потери пакетов"""
    print("\n" + "=" * 80)
    print("АНАЛИЗ ЗАВИСИМОСТИ ОТ ВЕРОЯТНОСТИ ПОТЕРИ ПАКЕТОВ")
    print("=" * 80)
    
    # Фиксированные параметры
    test_data = "HelloWorld" * 18  # 198 символов ≈ 100 пакетов
    window_size = 3
    timeout = 0.2
    
    # Вероятности потерь для тестирования
    loss_probabilities = [0.0, 0.1, 0.2, 0.3, 0.5, 0.6]
    
    results_loss = {
        'Go-Back-N': {'k': [], 't': []},
        'Selective Repeat': {'k': [], 't': []}
    }
    
    print(f"{'Вероятность':<12} {'Go-Back-N':<20} {'Selective Repeat':<20}")
    print(f"{'потерь (p)':<12} {'k':<10} {'t':<10} {'k':<10} {'t':<10}")
    print("-" * 60)
    
    for p in loss_probabilities:
        # Go-Back-N
        simulator_gbn = ProtocolSimulator(
            test_data,
            window_size=window_size,
            protocol_type="go_back_n",
            package_data_size=2,
            packet_loss_prob=p,
            corruption_prob=0.0,
            ack_loss_prob=0.0,
            timeout=timeout
        )
        simulator_gbn.run_simulation()
        
        # Selective Repeat
        simulator_sr = ProtocolSimulator(
            test_data,
            window_size=window_size,
            protocol_type="selective_repeat",
            package_data_size=2,
            packet_loss_prob=p,
            corruption_prob=0.0,
            ack_loss_prob=0.0,
            timeout=timeout
        )
        simulator_sr.run_simulation()
        
        # Расчет коэффициента эффективности k
        useful_packets = len(test_data) // 2
        k_gbn = simulator_gbn.stats['total_sent'] / useful_packets
        k_sr = simulator_sr.stats['total_sent'] / useful_packets
        
        results_loss['Go-Back-N']['k'].append(k_gbn)
        results_loss['Go-Back-N']['t'].append(simulator_gbn.stats['total_time'])
        results_loss['Selective Repeat']['k'].append(k_sr)
        results_loss['Selective Repeat']['t'].append(simulator_sr.stats['total_time'])
        
        print(f"{p:<12.1f} {k_gbn:<10.2f} {simulator_gbn.stats['total_time']:<10.2f} {k_sr:<10.2f} {simulator_sr.stats['total_time']:<10.2f}")
    
    # Построение графиков для анализа потерь
    plot_loss_analysis(loss_probabilities, results_loss)
    
    return results_loss

def analyze_window_size_dependency():
    """Анализ зависимости эффективности от размера окна"""
    print("\n" + "=" * 80)
    print("АНАЛИЗ ЗАВИСИМОСТИ ОТ РАЗМЕРА ОКНА")
    print("=" * 80)
    
    # Фиксированные параметры
    test_data = "HelloWorld" * 18  # 198 символов ≈ 100 пакетов
    packet_loss_prob = 0.3
    timeout = 0.2
    
    # Размеры окон для тестирования
    window_sizes = [2, 3, 4, 5, 6, 7, 8, 9, 10]
    
    results_window = {
        'Go-Back-N': {'k': [], 't': []},
        'Selective Repeat': {'k': [], 't': []}
    }
    
    print(f"{'Размер':<8} {'Go-Back-N':<20} {'Selective Repeat':<20}")
    print(f"{'окна':<8} {'k':<10} {'t':<10} {'k':<10} {'t':<10}")
    print("-" * 60)
    
    for window_size in window_sizes:
        # Go-Back-N
        simulator_gbn = ProtocolSimulator(
            test_data,
            window_size=window_size,
            protocol_type="go_back_n",
            package_data_size=2,
            packet_loss_prob=packet_loss_prob,
            corruption_prob=0.0,
            ack_loss_prob=0.0,
            timeout=timeout
        )
        simulator_gbn.run_simulation()
        
        # Selective Repeat
        simulator_sr = ProtocolSimulator(
            test_data,
            window_size=window_size,
            protocol_type="selective_repeat",
            package_data_size=2,
            packet_loss_prob=packet_loss_prob,
            corruption_prob=0.0,
            ack_loss_prob=0.0,
            timeout=timeout
        )
        simulator_sr.run_simulation()
        
        # Расчет коэффициента эффективности k
        useful_packets = len(test_data) // 2
        k_gbn = simulator_gbn.stats['total_sent'] / useful_packets
        k_sr = simulator_sr.stats['total_sent'] / useful_packets
        
        results_window['Go-Back-N']['k'].append(k_gbn)
        results_window['Go-Back-N']['t'].append(simulator_gbn.stats['total_time'])
        results_window['Selective Repeat']['k'].append(k_sr)
        results_window['Selective Repeat']['t'].append(simulator_sr.stats['total_time'])
        
        print(f"{window_size:<8} {k_gbn:<10.2f} {simulator_gbn.stats['total_time']:<10.2f} {k_sr:<10.2f} {simulator_sr.stats['total_time']:<10.2f}")
    
    # Построение графиков для анализа размера окна
    plot_window_analysis(window_sizes, results_window)
    
    return results_window

def plot_loss_analysis(loss_probabilities, results):
    """Построение графиков для анализа зависимости от потерь"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # График коэффициента эффективности k
    ax1.plot(loss_probabilities, results['Go-Back-N']['k'], 'o-', label='Go-Back-N', linewidth=2)
    ax1.plot(loss_probabilities, results['Selective Repeat']['k'], 'o-', label='Selective Repeat', linewidth=2)
    ax1.set_xlabel('Вероятность потери пакета (p)')
    ax1.set_ylabel('Коэффициент эффективности (k)')
    ax1.set_title('Зависимость коэффициента эффективности от вероятности потерь\n(окно=3)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # График времени передачи t
    ax2.plot(loss_probabilities, results['Go-Back-N']['t'], 'o-', label='Go-Back-N', linewidth=2)
    ax2.plot(loss_probabilities, results['Selective Repeat']['t'], 'o-', label='Selective Repeat', linewidth=2)
    ax2.set_xlabel('Вероятность потери пакета (p)')
    ax2.set_ylabel('Время передачи (t), сек')
    ax2.set_title('Зависимость времени передачи от вероятности потерь\n(окно=3)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()

def plot_window_analysis(window_sizes, results):
    """Построение графиков для анализа зависимости от размера окна"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # График коэффициента эффективности k
    ax1.plot(window_sizes, results['Go-Back-N']['k'], 'o-', label='Go-Back-N', linewidth=2)
    ax1.plot(window_sizes, results['Selective Repeat']['k'], 'o-', label='Selective Repeat', linewidth=2)
    ax1.set_xlabel('Размер окна')
    ax1.set_ylabel('Коэффициент эффективности (k)')
    ax1.set_title('Зависимость коэффициента эффективности от размера окна\n(p=0.3)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # График времени передачи t
    ax2.plot(window_sizes, results['Go-Back-N']['t'], 'o-', label='Go-Back-N', linewidth=2)
    ax2.plot(window_sizes, results['Selective Repeat']['t'], 'o-', label='Selective Repeat', linewidth=2)
    ax2.set_xlabel('Размер окна')
    ax2.set_ylabel('Время передачи (t), сек')
    ax2.set_title('Зависимость времени передачи от размера окна\n(p=0.3)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()

"""def export_to_csv(data_sizes, results):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"protocol_comparison_{timestamp}.csv"
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Заголовок
        writer.writerow(['Сравнение протоколов передачи данных'])
        writer.writerow(['Время выполнения (секунды)'])
        writer.writerow(['Размер данных', 'Stop-and-Wait', 'Go-Back-N', 'Selective Repeat'])
        
        # Данные
        for i, size in enumerate(data_sizes):
            sw_time = results['Stop-and-Wait']['time'][i]
            gbn_time = results['Go-Back-N']['time'][i]
            sr_time = results['Selective Repeat']['time'][i]
            writer.writerow([size, f"{sw_time:.2f}", f"{gbn_time:.2f}", f"{sr_time:.2f}"])
        
        # Пустая строка для разделения
        writer.writerow([])
        writer.writerow(['Эффективность (%)'])
        writer.writerow(['Размер данных', 'Stop-and-Wait', 'Go-Back-N', 'Selective Repeat'])
        
        # Данные эффективности (если доступны)
        for i, size in enumerate(data_sizes):
            sw_eff = results['Stop-and-Wait']['efficiency'][i] if i < len(results['Stop-and-Wait']['efficiency']) else 0
            gbn_eff = results['Go-Back-N']['efficiency'][i] if i < len(results['Go-Back-N']['efficiency']) else 0
            sr_eff = results['Selective Repeat']['efficiency'][i] if i < len(results['Selective Repeat']['efficiency']) else 0
            writer.writerow([size, f"{sw_eff:.1f}", f"{gbn_eff:.1f}", f"{sr_eff:.1f}"])
    
    print(f"\nРезультаты экспортированы в файл: {filename}")
    print(f"Полный путь: {os.path.abspath(filename)}")
"""
def plot_results(data_sizes, results):
    plt.figure(figsize=(12, 7))
    
    plt.plot(data_sizes, results['Stop-and-Wait']['time'], 'o-', label='Stop-and-Wait', linewidth=2, markersize=8)
    plt.plot(data_sizes, results['Go-Back-N']['time'], 'o-', label='Go-Back-N (окно=4)', linewidth=2, markersize=8)
    plt.plot(data_sizes, results['Selective Repeat']['time'], 'o-', label='Selective Repeat (окно=4)', linewidth=2, markersize=8)
    
    plt.xlabel('Размер данных (символов)')
    plt.ylabel('Время выполнения, сек')
    plt.title('Сравнение времени выполнения протоколов: Stop-And-Wait vs Go-Back-N vs Selective Repeat')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    max_time = max(max(results['Stop-and-Wait']['time']), 
                   max(results['Go-Back-N']['time']),
                   max(results['Selective Repeat']['time']))
    plt.yticks([i for i in range(0, int(max_time) + 20, 10)])

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    compare_protocols()