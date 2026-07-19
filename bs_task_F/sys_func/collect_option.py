import json
import random
import os
from collections import deque



# =========================S
# 1. JSON 로드
# =========================
def load_both_web(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    animals = data["animals"]
    food_edges = [tuple(e) for e in data["food_edges"]]
    gene_edges = [tuple(e) for e in data["gene_edges"]]
    habitat_groups =[tuple(e) for e in data["habitat_groups"]]

    return animals, food_edges, gene_edges, habitat_groups

# =========================
# trial set 로드
# =========================
def load_trial_set(json_path):

    with open(
        json_path,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    return data["trials"]


# =========================
# 2. 그래프 생성
# =========================
def build_graph(edges, bidirectional=False):
    graph = {}

    for a, b in edges:
        graph.setdefault(a, []).append(b)
        if bidirectional:
            graph.setdefault(b, []).append(a)

    return graph


# =========================
# 3. 거리 계산
# =========================
def compute_all_distances(start, graph):
    queue = deque([(start, 0)])
    visited = {}

    while queue:
        node, dist = queue.popleft()

        if node in visited:
            continue

        visited[node] = dist

        for neighbor in graph.get(node, []):
            queue.append((neighbor, dist + 1))

    return visited


def split_by_distance(dist_dict, animals):
    groups = {}

    for a in animals:
        d = dist_dict.get(a, float("inf"))
        groups.setdefault(d, []).append(a)

    return groups

def compute_distance(start, target, graph):
    """
    graph: dict 형태 {node: [neighbors]}
    start → target까지 최단 거리 (hop 수)
    """

    queue = deque([(start, 0)])
    visited = set()

    while queue:
        node, dist = queue.popleft()

        if node == target:
            return dist

        if node in visited:
            continue
        visited.add(node)

        for neighbor in graph.get(node, []):
            queue.append((neighbor, dist + 1))

    return float("inf")  # 연결 안됨

def build_candidate_table(premise, animals, graph, task_type):

    table = []

    for a in animals:
        if a == premise:
            continue

        d_forward = compute_distance(premise, a, graph)

        if task_type == "food":
            d_backward = compute_distance(a, premise, graph)

            if d_forward < float("inf"):
                direction = "forward"
                dist = d_forward
            elif d_backward < float("inf"):
                direction = "backward"
                dist = d_backward
            else:
                direction = "none"
                dist = float("inf")
        else:
            # gene은 방향 없음
            direction = "undirected"
            dist = d_forward

        table.append({
            "animal": a,
            "dist": dist,
            "direction": direction
        })

    return table

def pick_option(candidates, dist=None, direction=None):

    filtered = candidates

    if dist is not None:
        filtered = [c for c in filtered if c["dist"] == dist]

    if direction is not None:
        filtered = [c for c in filtered if c["direction"] == direction]

    if not filtered:
        return None

    return random.choice(filtered)

# =========================
# trial 순서 랜덤화
# =========================
def generate_trials_from_set(
    json_path
):

    trials = load_trial_set(
        json_path
    )

    random.shuffle(trials)

    return trials
