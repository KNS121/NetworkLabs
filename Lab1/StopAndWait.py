import hashlib
import time
import random

data = "Hello worldaa"
package_data_size = 2

def CalculateHashSum(data):
    return hashlib.sha256(data.encode()).hexdigest()

def msg_to_packages(data):
    packages = []
    #package_number = 0
    

    for i in range(0, len(data), package_data_size):

        package_number = (i//package_data_size)%2
        
        package = {
            "seq_num": package_number,
            "hash_sum": CalculateHashSum(data[i:i+package_data_size]),
            "data": data[i:i+package_data_size]
        }
        packages.append(package)
    
    return packages

def Sender(data):
    packages = msg_to_packages(data)
    
    for package in packages:
        ack_received = False
        
        while not ack_received:

            print(f"Отправка пакета {package}")
            
            # Отправляем пакет и получаем ACK
            ack_received = Reciever(package)
            
            if ack_received:
                print(f"Пакет {package} подтвержден")

            else:
                print(f"Таймаут для пакета {package}, повторная отправка...")
                # Ждем перед повторной отправкой
                time.sleep(0.5)
    
    print("\nВсе пакеты успешно отправлены!")


def Reciever(package):
    # Имитация потери пакета (30% вероятность)
    if random.random() < 0.3:
        print("  Пакет потерян!")
        return False
    
    # Проверка контрольной суммы
    if CalculateHashSum(package["data"]) == package["hash_sum"]:
        # Имитация задержки сети
        network_delay = random.random() * 0.8
        time.sleep(network_delay)
        
        if network_delay < 0.5:  # ACK пришел вовремя
            print(f"  Пакет {package} принят, отправка ACK")
            return True
        else:  # ACK опоздал
            print(f"  Пакет {package} принят, но ACK опоздал")
            return False
    else:
        print("  Ошибка контрольной суммы!")
        return False

# Запуск
print("Начало передачи данных...")
sent = Sender(data)
print(f"\nУспешно отправлено пакетов: {len(sent)}")