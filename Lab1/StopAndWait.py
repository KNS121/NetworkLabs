import hashlib
import time
import random

data = "Hello world"
package_data_size = 2

received_data = []
expected_seq_num = 0

def CalculateHashSum(data):
    return hashlib.sha256(data.encode()).hexdigest()

def msg_to_packages(data):
    packages = []
    
    for i in range(0, len(data), package_data_size):
        package_number = i // package_data_size
        
        package = {
            "seq_num": package_number,
            "hash_sum": CalculateHashSum(data[i:i+package_data_size]),
            "data": data[i:i+package_data_size]
        }
        packages.append(package)
    
    return packages

def Sender(data):
    packages = msg_to_packages(data)
    global expected_seq_num
    
    for package in packages:
        ack_received = False
                
        while not ack_received:
            print(f"Отправка пакета {package['seq_num']}: {package['data']}")
            
            ack_received = Receiver(package)
            
            if ack_received:
                print(f"Пакет {package['seq_num']} подтвержден")
            else:
                print(f"Таймаут для пакета {package['seq_num']}, повторная отправка...")
                time.sleep(0.5)
    
    print("\nВсе пакеты успешно отправлены!")

def Receiver(package):
    global expected_seq_num
    
    # Имитация потери пакета
    if random.random() < 0.3:
        print("  Пакет потерян!")
        return False

    # Проверяем sequence number
    if package["seq_num"] != expected_seq_num:
        print(f"  Неправильный sequence number: получен {package['seq_num']}, ожидался {expected_seq_num}")
        return False

    # Случайное искажение данных
    package_copy = package.copy()  # Работаем с копией чтобы не менять оригинал
    if random.random() < 0.2:
        data_in_package = package_copy["data"]
        random_str = ''
        for i in range(len(data_in_package)):
            char = chr(random.randint(97, 122))
            random_str = random_str + char
        package_copy["data"] = random_str
        print(f"  Данные искажены: {package_copy['data']}")

    # Проверка контрольной суммы
    if CalculateHashSum(package_copy["data"]) == package_copy["hash_sum"]:
        # Имитация задержки сети
        network_delay = random.random() * 0.8
        time.sleep(network_delay)
        
        if network_delay < 0.5:  # ACK пришел вовремя
            received_data.append((package_copy["seq_num"], package_copy["data"]))
            expected_seq_num += 1  # Переходим к ожиданию следующего пакета
            return True
        else:  # ACK опоздал / либо пропал
            print("  ACK опоздал")
            return False
    else:
        print("  Не совпадает хеш сумма")
        return False

def sort_and_combine_data(received_data):
    received_data.sort(key=lambda x: x[0])
    return ''.join([data for seq, data in received_data])

print("Начало передачи данных...")
Sender(data)

final_data = sort_and_combine_data(received_data)
print(f"\nИсходные данные: {data}")
print(f"Полученные данные: {final_data}")
print(f"Передача успешна: {data == final_data}")