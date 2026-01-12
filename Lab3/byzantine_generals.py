import random
from collections import Counter
from typing import List, Tuple, Dict, Optional
from simulator import ProtocolSimulator


class General:
    def __init__(self, general_id: int, is_byzantine: bool = False, initial_value: int = 0, t: int = 0, n: int = 0):
        self.id = general_id
        self.is_byzantine = is_byzantine
        self.initial_value = initial_value
        self.received_values: Dict[int, int] = {}
        self.received_vectors: List[Tuple[int, List[int]]] = []
        self.decision: Optional[int] = None
        self.t = t
        self.n = n

    def send_message(self, target_id: int, value: int) -> int:
        if self.is_byzantine:
            forged = random.randint(0, 100)
            print(f"  Узел {self.id} (НЕкорректный) отправляет G{target_id}: {forged} (подделка вместо {value})")
            return forged
        else:
            print(f"  Узел {self.id} (корректный) отправляет G{target_id}: {value}")
            return value

    def receive_value(self, sender_id: int, value: int):
        self.received_values[sender_id] = value
        print(f"  Узел {self.id} получил от G{sender_id}: {value}")

    def receive_vector(self, sender_id: int, vector: List[int]):
        self.received_vectors.append((sender_id, vector))
        print(f"  Узел {self.id} получил вектор от G{sender_id}: {vector}")

    def get_full_vector(self) -> List[int]:

        vec = []
        for j in range(self.n):
            if j == self.id:
                vec.append(self.initial_value)
            else:
                vec.append(self.received_values.get(j, 0))
        return vec

    def make_decision_after_rounds(self) -> int:
        if self.t == 0:

            all_values = [self.initial_value] + list(self.received_values.values())
            print(f"  Узел {self.id} анализирует значения (t=0): {all_values}")
            self.decision = Counter(all_values).most_common(1)[0][0]
            print(f"  Узел {self.id} принял решение: {self.decision}")
            return self.decision


        matrix: Dict[int, List[int]] = {j: [] for j in range(self.n)}

        # Добавляем свой вектор
        my_vec = self.get_full_vector()
        for j in range(self.n):
            matrix[j].append(my_vec[j])

        # Добавляем векторы от других генералов
        for sender_id, vec in self.received_vectors:
            if len(vec) != self.n:
                print(f"  Пропущен битый вектор от G{sender_id} (длина {len(vec)} != {self.n})")
                continue
            for j in range(self.n):
                matrix[j].append(vec[j])


        final_values = []
        for j in range(self.n):
            col = matrix[j]
            if col:
                most_common = Counter(col).most_common(1)[0][0]
                final_values.append(most_common)
            else:
                final_values.append(0)

        print(f"  Узел {self.id} восстановил значения по узлам: {final_values}")
        # Финальное решение — majority по этим значениям
        self.decision = Counter(final_values).most_common(1)[0][0]
        print(f"  Узел {self.id} принял окончательное решение: {self.decision}")
        return self.decision


class ByzantineGeneralsSimulator:
    def __init__(self, n: int, t: int, initial_values: List[int] = None):
        if n <= 3 * t:
            print(f" Предупреждение: n={n} <= 3t={3*t}. Консенсус не гарантирован!")

        self.n = n
        self.t = t
        self.generals = []

        byzantine_ids = set(random.sample(range(n), t)) if t > 0 else set()
        if initial_values is None:
            initial_values = [random.randint(0, 10) for _ in range(n)]

        for i in range(n):
            is_bad = i in byzantine_ids
            self.generals.append(General(i, is_bad, initial_values[i], t=t, n=n))

    def reliable_send_value(self, sender_id: int, receiver_id: int, value: int) -> Tuple[bool, Optional[int]]:
        data = str(value)
        try:
            simulator = ProtocolSimulator(
                data=data,
                window_size=4,
                protocol_type="selective_repeat",
                package_data_size=len(data),
                timeout=0.5,
                packet_loss_prob=0.1,
                corruption_prob=0.05,
                ack_loss_prob=0.05
            )
            success = simulator.run_simulation()
            if success:
                received_str = simulator.receiver.get_reassembled_data()
                try:
                    received_val = int(received_str)
                    if received_val != value:
                        print(f"Передано {value}, получено {received_val} (искажение в сети)")
                    return True, received_val
                except ValueError:
                    print(f"Получены некорректные данные: '{received_str}'")
                    return False, None
            else:
                return False, None
        except Exception as e:
            print(f"Ошибка при передаче от G{sender_id} к G{receiver_id}: {e}")
            return False, None

    def reliable_send_vector(self, sender_id: int, receiver_id: int, vector_str: str) -> Tuple[bool, Optional[str]]:
        try:
            simulator = ProtocolSimulator(
                data=vector_str,
                window_size=4,
                protocol_type="selective_repeat",
                package_data_size=len(vector_str),
                timeout=0.5,
                packet_loss_prob=0.1,
                corruption_prob=0.05,
                ack_loss_prob=0.05
            )
            success = simulator.run_simulation()
            if success:
                received_str = simulator.receiver.get_reassembled_data()
                return True, received_str
            else:
                return False, None
        except Exception as e:
            print(f"Ошибка при передаче вектора от G{sender_id} к G{receiver_id}: {e}")
            return False, None

    def run_round_1(self):
        print("\nЭТАП 1: Все узлы рассылают свои начальные значения")
        for sender in self.generals:
            print(f"\nУзел {sender.id} начинает рассылку (начальное значение: {sender.initial_value})")
            for receiver in self.generals:
                if sender.id == receiver.id:
                    continue
                value_to_send = sender.send_message(receiver.id, sender.initial_value)
                success, received_val = self.reliable_send_value(sender.id, receiver.id, value_to_send)
                if success and received_val is not None:
                    receiver.receive_value(sender.id, received_val)
                else:
                    print(f" Сообщение от G{sender.id} к G{receiver.id} НЕ ДОСТАВЛЕНО")

    def run_round_2(self):
        print("\nЭТАП 2: Все узлы рассылают векторы значений, полученные на этапе 1")
        for sender in self.generals:
            if sender.is_byzantine:
                # Византиец отправляет случайный вектор той же длины
                fake_vector = [random.randint(0, 10) for _ in range(sender.n)]
                print(f"  Узел {sender.id} (НЕкорректный) формирует поддельный вектор: {fake_vector}")
                vector_to_send = fake_vector
            else:
                vector_to_send = sender.get_full_vector()
                print(f"  Узел {sender.id} (корректный) формирует вектор: {vector_to_send}")

            vector_str = str(vector_to_send)
            for receiver in self.generals:
                if sender.id == receiver.id:
                    continue
                success, received_str = self.reliable_send_vector(sender.id, receiver.id, vector_str)
                if success and received_str is not None:
                    try:
                        received_vector = eval(received_str)  # Только для демо!
                        if isinstance(received_vector, list) and len(received_vector) == sender.n:
                            receiver.receive_vector(sender.id, received_vector)
                        else:
                            print(f"  Получен некорректный вектор от G{sender.id}: {received_str}")
                    except Exception as e:
                        print(f"  Ошибка разбора вектора от G{sender.id}: '{received_str}' — {e}")
                else:
                    print(f" Вектор от G{sender.id} к G{receiver.id} НЕ ДОСТАВЛЕН")

    def run(self) -> Tuple[List[int], bool]:
        print(f"\n{'-'*60}")
        print(f"ЗАПУСК СИМУЛЯЦИИ: {self.n} Узлов, {self.t} некорректных")
        print(f"{'-'*60}")

        self.run_round_1()

        if self.t >= 1:
            self.run_round_2()

        print("\nКаждый узел принимает решение")
        decisions = []
        for general in self.generals:
            print(f"\n--- Анализ Узла {general.id} ---")
            decision = general.make_decision_after_rounds()
            decisions.append(decision)

        honest_decisions = [
            decisions[i] for i in range(self.n)
            if not self.generals[i].is_byzantine
        ]

        consensus = len(set(honest_decisions)) == 1 if honest_decisions else False
        print(f"\n{'-'*60}")
        print("ИТОГОВЫЕ РЕШЕНИЯ:")
        for i, d in enumerate(decisions):
            status = "НЕКОРРЕКТНЫЙ" if self.generals[i].is_byzantine else "КОРРЕКТНЫЙ"
            print(f"  Узел {i} ({status}): {d}")
        print(f"\nКонсенсус среди корректных: {'ДА' if consensus else 'НЕТ'}")
        if consensus and honest_decisions:
            print(f"Общее решение: {honest_decisions[0]}")
        print(f"{'-'*60}")

        return decisions, consensus