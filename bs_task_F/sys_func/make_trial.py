
import json
import random
import os
from sys_func.collect_option import load_both_web, build_candidate_table,  build_graph, split_by_distance, pick_option, generate_trials_from_set,load_trial_set
from config import MODE
def generate_trials(food_json_path, gene_json_path, habitat_json_path, n_trials=120):
    """
    미리 구성해둔 JSON 파일에서 트라이얼을 불러와,
    종류에 상관없이 전체 문제를 하나로 합친 뒤 완전히 무작위로 섞어
    요청한 개수(n_trials)만큼만 반환합니다.
    """
    # 1. 문제 불러오기 및 출처(domain) 이름표 붙이기
    food_trials = generate_trials_from_set(food_json_path)
    for t in food_trials:
        t["domain"] = "food"  # 소문자 food 강제 지정
        
    gene_trials = generate_trials_from_set(gene_json_path)
    for t in gene_trials:
        t["domain"] = "gene"  # 소문자 gene 강제 지정
        
    habitat_trials = generate_trials_from_set(habitat_json_path)
    for t in habitat_trials:
        t["domain"] = "habitat" # 소문자 habitat 강제 지정
        
    # 2. 하나의 큰 리스트로 합치기
    
    all_trials = []
    if MODE==0:
        all_trials.extend(food_trials)
        all_trials.extend(gene_trials)
        all_trials.extend(habitat_trials)
        
        
    elif MODE==1:
        all_trials.extend(gene_trials)
        all_trials.extend(habitat_trials)
        n_trials=80
    elif MODE==2:
        all_trials.extend(food_trials)
        all_trials.extend(habitat_trials)
        n_trials=80
    elif MODE==3:
        all_trials.extend(gene_trials)
        all_trials.extend(food_trials)
        n_trials=80
    
    # 3. 전체 무작위로 섞기
    random.shuffle(all_trials)
    
    # 4. 요청한 n_trials 개수만큼만 리스트를 잘라서 반환
    return all_trials[:n_trials]
'''
# =========================
# 4. Trial 생성
# =========================
def generate_trials(
    animals,
    food_edges,
    gene_edges,
    habitat_groups,
    n_trials=60
):

    trials = []

    # =========================
    # graph 생성
    # =========================
    food_graph = build_graph(
        food_edges,
        bidirectional=False
    )

    gene_graph = build_graph(
        gene_edges,
        bidirectional=True
    )

    # habitat graph 생성
    habitat_graph = build_graph(
        habitat_groups,
        bidirectional=True
    )

    # =========================
    # 거리 pool
    # =========================
    food_distances = [1, 2, 3, float("inf")]

    gene_distances = [2, 4, 5]

    # habitat도 유사성 거리 사용
    habitat_distances = [1, float("inf")]

    # =========================
    # block 단위 생성
    # =========================
    block_size = 12

    n_blocks = n_trials // block_size

    task_sequence = []

    for _ in range(n_blocks):

        block = (
            ["food"] * 4 +
            ["gene"] * 4 +
            ["habitat"] * 4
        )

        random.shuffle(block)

        task_sequence.extend(block)

    # =========================
    # 남는 trial 처리
    # =========================
    remain = n_trials % block_size

    if remain > 0:

        types = (
            ["food"] * (remain // 3) +
            ["gene"] * (remain // 3) +
            ["habitat"] * (
                remain - 2 * (remain // 3)
            )
        )

        random.shuffle(types)

        task_sequence.extend(types)

    # =========================
    # trial 생성
    # =========================
    for task_type in task_sequence:

        while True:

            premise = random.choice(animals)

            # =========================
            # graph 선택
            # =========================
            if task_type == "food":

                graph = food_graph
                possible_distances = food_distances

            elif task_type == "gene":

                graph = gene_graph
                possible_distances = gene_distances

            else:

                graph = habitat_graph
                possible_distances = habitat_distances

            # =========================
            # candidate table
            # =========================
            table = build_candidate_table(
                premise,
                animals,
                graph,
                task_type
            )

            # =========================
            # 옵션1
            # =========================
            dist1 = random.choice(
                possible_distances
            )

            if task_type == "food":

                dir1 = random.choice([
                    "forward",
                    "backward",
                    "none"
                ])

            else:

                dir1 = None

            opt1 = pick_option(
                table,
                dist=dist1,
                direction=dir1
            )

            if opt1 is None:
                continue

            # =========================
            # 옵션2
            # =========================
            dist2 = random.choice(
                possible_distances
            )

            if task_type == "food":

                dir2 = random.choice([
                    "forward",
                    "backward",
                    "none"
                ])

            else:

                dir2 = None

            opt2 = pick_option(
                table,
                dist=dist2,
                direction=dir2
            )

            if opt2 is None:
                continue

            if opt1["animal"] == opt2["animal"]:
                continue

            if opt1["dist"] == opt2["dist"]:
                continue

            # =========================
            # 정답 계산
            # =========================
            if opt1["dist"] < opt2["dist"]:
                correct = "left"
            else:
                correct = "right"

            # =========================
            # 저장
            # =========================
            trials.append({

                "task_type": task_type,

                "premise": premise,

                "option1": opt1["animal"],
                "option2": opt2["animal"],

                "dist1": opt1["dist"],
                "dist2": opt2["dist"],

                "dir1": opt1["direction"],
                "dir2": opt2["direction"],

                "correct": correct
            })

            break

    return trials

    '''