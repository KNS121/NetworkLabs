import matplotlib.pyplot as plt
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
        'Stop-and-Wait': {'time': []},
        'Go-Back-N': {'time': []}
    }
    
    data_sizes = [len(data) for data in test_cases]
    
    for i, test_data in enumerate(test_cases):
        print(f"Тестирование с размером данных: {len(test_data)} символов")
        
        # Stop-and-Wait (окно=1)
        simulator_sw = ProtocolSimulator(
            test_data, 
            window_size=1,
            package_data_size=2,
            packet_loss_prob=0.2,
            corruption_prob=0.1,
            ack_loss_prob=0.1,
            timeout=0.5
        )
        simulator_sw.run_simulation()
        
        results['Stop-and-Wait']['time'].append(simulator_sw.stats['total_time'])
        
        # Go-Back-N (окно=4)
        simulator_gbn = ProtocolSimulator(
            test_data,
            window_size=4,
            package_data_size=2,
            packet_loss_prob=0.2,
            corruption_prob=0.1,
            ack_loss_prob=0.1,
            timeout=0.5
        )
        simulator_gbn.run_simulation()
        
        results['Go-Back-N']['time'].append(simulator_gbn.stats['total_time'])
    

    plt.figure(figsize=(10, 6))
    
    plt.plot(data_sizes, results['Stop-and-Wait']['time'], 'o-', label='Stop-and-Wait', linewidth=2, markersize=8)
    plt.plot(data_sizes, results['Go-Back-N']['time'], 'o-', label='Go-Back-N (окно=4)', linewidth=2, markersize=8)
    
    plt.xlabel('Размер данных (символов)')
    plt.ylabel('Время выполнения, сек')
    plt.title('Сравнение времени выполнения Stop-And-Wait || Go-Back-N')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    max_time = max(max(results['Stop-and-Wait']['time']), max(results['Go-Back-N']['time']))
    plt.yticks([i for i in range(0, int(max_time) + 20, 10)])


    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    compare_protocols()