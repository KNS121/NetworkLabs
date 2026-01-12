from byzantine_generals import ByzantineGeneralsSimulator

if __name__ == "__main__":
    import random

    test_cases = [
        {"n": 4, "t": 1},
        {"n": 7, "t": 2},
        {"n": 5, "t": 2},
    ]

    random.seed(42)

    for case in test_cases:
        n, t = case["n"], case["t"]
        print(f"\n{'-'*60}")
        print(f"ТЕСТ: n = {n}, t = {t}")
        print(f"{'-'*60}")

        initial_values = [5] * n  # все корректные передают 5

        sim = ByzantineGeneralsSimulator(n=n, t=t, initial_values=initial_values)
        decisions, consensus = sim.run()

        theoretical = n > 3 * t
        print(f"\nТеория: n > 3t → {theoretical}")
        print(f"Результат: консенсус = {consensus}")