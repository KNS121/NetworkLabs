import heapq
from collections import defaultdict

class OSPFNode:
    def __init__(self, router_id):
        self.router_id = router_id
        self.neighbors = {}  
        self.lsdb = {}  
        self.routing_table = {}

    def add_neighbor(self, neighbor_id, cost):
        self.neighbors[neighbor_id] = cost
        self.lsdb[self.router_id] = self.neighbors

    def flood_lsa(self, network):
 
        for neighbor_id in self.neighbors:
            if neighbor_id in network:
                network[neighbor_id].receive_lsa(self.router_id, self.lsdb[self.router_id])

    def receive_lsa(self, sender_id, lsa):

        if sender_id not in self.lsdb or self.lsdb[sender_id] != lsa:
            self.lsdb[sender_id] = lsa
            self.flood_lsa(network)

    def dijkstra(self):

        distances = {self.router_id: 0}
        pq = [(0, self.router_id)]
        previous = {}

        while pq:
            current_dist, current = heapq.heappop(pq)
            if current not in self.lsdb:
                continue

            for neighbor, cost in self.lsdb[current].items():
                distance = current_dist + cost
                if neighbor not in distances or distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current
                    heapq.heappush(pq, (distance, neighbor))

        # Построение таблицы маршрутизации
        for router in self.lsdb:
            if router == self.router_id:
                continue
            path = []
            current = router
            while current in previous:
                path.insert(0, current)
                current = previous[current]
            self.routing_table[router] = (path[0] if path else None, distances.get(router, float('inf')))

    def show_routing_table(self):

        print(f"Routing Table for Router {self.router_id}:")
        print("Destination\tNext Hop\tCost")
        for dest, (next_hop, cost) in self.routing_table.items():
            print(f"{dest}\t\t{next_hop}\t\t{cost}")

if __name__ == "__main__":
    network = {}

    # Создаем маршрутизаторы
    routers = [OSPFNode(i) for i in range(1, 5)]
    for router in routers:
        network[router.router_id] = router

    # Настраиваем связи между маршрутизаторами
    routers[0].add_neighbor(2, 1)
    routers[0].add_neighbor(3, 5)
    routers[1].add_neighbor(3, 2)
    routers[1].add_neighbor(4, 4)
    routers[2].add_neighbor(4, 1)

    # Запускаем распространение LSA
    for router in routers:
        router.flood_lsa(network)

    # Вычисляем маршруты
    for router in routers:
        router.dijkstra()

    # Показываем таблицы маршрутизации
    for router in routers:
        router.show_routing_table()
        print()