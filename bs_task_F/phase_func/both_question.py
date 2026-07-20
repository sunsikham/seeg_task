import json
import random
import os
from collections import deque
from set_opts.visual_opts import UI_CONFIG
from config import WAITING,HEIGHT,WIDTH, HANDLE,FRAME_EXAMPLE_bs,FRAME_EXAMPLE_bss,FRAME_EXAMPLE_bf,waiting_frames,MODE,STIMULI_DIR
from draw_func.draw_marker import draw_white_marker
from utils.labjack_trigger import send_trigger, reset_trigger, TRIG_B_START, TRIG_B_RESPOND,TRIG_B_WRONGRESPOND,TRIG_B_SELECTSTART
from phase_func.show_info import show_all_food_phase, show_all_gene_phase, show_all_habitat_phase
from phase_func.waiting import random_isi_phase
from psychopy import visual, core, event
from psychopy.visual import TextBox2
from pyjosa.josa import Josa
from stimuli.category import DISEASE_POOL
from sys_func.collect_option import load_both_web, build_candidate_table,  build_graph, split_by_distance, pick_option
from sys_func.make_trial import generate_trials
from sys_func.frame_count import frame_timer




# =========================
# 5. Trial 실행 (UI)
# =========================
def run_trial(win, trial, handle,index):

    cfg = UI_CONFIG
    left_option = trial["option1"]
    right_option = trial["option2"]

    left_image_path = os.path.join(STIMULI_DIR, f"{left_option}.png")
    right_image_path = os.path.join(STIMULI_DIR, f"{right_option}.png")

    # =========================
    # premise image 경로 추가
    # =========================
    premise_image_path = os.path.join(
        STIMULI_DIR,
        f"{trial['premise']}.png"
    )

    # =========================
    # 질문 (추후 종류 세분화하기)
    # =========================
    if trial["domain"] == "food":

        target = random.choice(
            DISEASE_POOL["food"]
        )

        target_color = [0.5, -1, -1]

    elif trial["domain"] == "gene":

        target = random.choice(
            DISEASE_POOL["gene"]
        )

        target_color = [0.5, -1, -1]

    else:

        target = random.choice(
            DISEASE_POOL["habitat"]
        )

        # 초록 계열 추천
        target_color = [0.5, -1, -1]

    #===== target + 조사 분리 =====
    full_target = Josa.get_full_string(target, '을')

    # 조사만 추출
    josa_part = full_target[len(target):]



    # ===== 질문 문장 =====
    if trial["domain"] == "food":

        question_text = (
            f"{Josa.get_full_string(trial['premise'], '가')} "
            f"<c={target_color}>{target}</c>{josa_part} 가지고 있다.\n"
            f"이 <c={target_color}>{target}</c>{josa_part} "
            f"{Josa.get_full_string(trial['premise'], '으로')}부터 옮은 동물은 누구일까?" 
        )
    elif trial["domain"] == "gene":

        question_text = (
            f"{Josa.get_full_string(trial['premise'], '가')} "
            f"<c={target_color}>{target}</c>{josa_part} 가진다.\n"
            f"어느 쪽이 그 "
            f"<c={target_color}>{target}</c>{josa_part} 가졌을까?"
        )

    else:

        question_text = (
        f"{Josa.get_full_string(trial['premise'], '는')} "
            f"<c={target_color}>{target}</c>때문에 피해를 입었다.\n"
            f"어느 쪽이 같은 "
            f"<c={target_color}>{target}</c>에 피해를 입었을까?"
        )
    # ===== TextBox2 =====
    question = TextBox2(
        win,

        text=question_text,

        pos=cfg["question"]["pos"],

        size=(
            cfg["question"]["wrapWidth"],
            None
        ),

        letterHeight=cfg["question"]["height"],

        color=cfg["question"]["color"],

        font=cfg["question"]["font"],

        alignment="center",

        anchor="center"
    )

    # =========================
    # premise 이미지 추가
    # =========================
    premise_image = visual.ImageStim(
        win,
        image=premise_image_path,

        pos=cfg["image"]["main_pos"],
        size=cfg["image"]["size2"]
    )

    # =========================
    # 옵션
    # =========================
    left_option = visual.TextStim(
        win,
        text=trial["option1"],
        pos=cfg["option"]["left_pos"],
        height=cfg["option"]["height"],
        color=cfg["option"]["color"],
        font=cfg["option"]["font"]
    )

    right_option = visual.TextStim(
        win,
        text=trial["option2"],
        pos=cfg["option"]["right_pos"],
        height=cfg["option"]["height"],
        color=cfg["option"]["color"],
        font=cfg["option"]["font"]
    )

    # ===== 이미지 =====
    left_image = visual.ImageStim(
        win,
        image=left_image_path,
        pos=cfg["image"]["left_pos"],
        size=cfg["image"]["size"]
    )

    right_image = visual.ImageStim(
        win,
        image=right_image_path,
        pos=cfg["image"]["right_pos"],
        size=cfg["image"]["size"]
    )

    # =========================
    # 화살표
    # =========================
    left_arrow = visual.TextStim(
        win,
        text="◀",
        pos=cfg["arrow"]["left_pos"],
        height=cfg["arrow"]["height"],
        color=cfg["arrow"]["color"]
    )

    right_arrow = visual.TextStim(
        win,
        text="▶",
        pos=cfg["arrow"]["right_pos"],
        height=cfg["arrow"]["height"],
        color=cfg["arrow"]["color"]
    )

    clock = core.Clock()
    rt2_clock = core.Clock()

    event.clearEvents()

    response = None
    rt = None
    rt2 = None

  

    # =========================
    # premise phase
    # =========================
    frame_count = 0

    while frame_count < waiting_frames:

        if frame_count < FRAME_EXAMPLE_bs:
            draw_white_marker(
                win,
                pos=(-WIDTH//2 + 120, -HEIGHT//2 + 120),
                size=(50, 50)
            )

        question.draw()
        premise_image.draw()

        if frame_count == 0:
            win.callOnFlip(
                send_trigger,
                handle,
                TRIG_B_START
            )
        elif frame_count == 1:
            win.callOnFlip(
                reset_trigger,
                handle
            )

        flip_time = win.flip()
        frame_timer(
            flip_time=flip_time,
            trial_index=index,
            task_type=trial["task_type"],
            phase="premise_onset"
        )

        event.clearEvents()
        frame_count += 1

    # =========================
    # option / response phase
    # =========================
    frame_count = 0
    timeout_frames = cfg["timing"]["timeout_frames"]

    while frame_count < timeout_frames:

        if frame_count < FRAME_EXAMPLE_bss:
            draw_white_marker(
                win,
                pos=(-WIDTH//2 + 120, -HEIGHT//2 + 120),
                size=(50, 50)
            )

        question.draw()
        premise_image.draw()
        left_option.draw()
        right_option.draw()
        left_image.draw()
        right_image.draw()
        left_arrow.draw()
        right_arrow.draw()

        if frame_count == 0:
            win.callOnFlip(rt2_clock.reset)
            win.callOnFlip(
                send_trigger,
                handle,
                TRIG_B_SELECTSTART
            )
        elif frame_count == 1:
            win.callOnFlip(
                reset_trigger,
                handle
            )

        flip_time = win.flip()
        frame_timer(
            flip_time=flip_time,
            trial_index=index,
            task_type=trial["task_type"],
            phase="option_onset"
        )

        keys = event.getKeys(
            keyList=["left", "right", "escape"],
            timeStamped=clock
        )

        if keys:
            key, rt = keys[0]
            rt2 = rt2_clock.getTime()

            if key == "escape":
                core.quit()

            if key == "left":
                left_arrow.color = cfg["arrow"]["active_color"]
                response = "left"
            else:
                right_arrow.color = cfg["arrow"]["active_color"]
                response = "right"

            break

        frame_count += 1

    # =========================
    # feedback phase (response trigger 포함, 총 0.5초)
    # =========================
    frame_count = 0
    feedback_frames = cfg["timing"]["feedback_frames"]

    while frame_count < feedback_frames:

        if frame_count < FRAME_EXAMPLE_bf:
            draw_white_marker(
                win,
                pos=(-WIDTH//2 + 120, -HEIGHT//2 + 120),
                size=(50, 50)
            )

        question.draw()
        premise_image.draw()
        left_option.draw()
        right_option.draw()
        left_image.draw()
        right_image.draw()
        left_arrow.draw()
        right_arrow.draw()

        if frame_count == 0 and trial['correct'] == response:
            win.callOnFlip(
                send_trigger,
                handle,
                TRIG_B_RESPOND
            )
        elif frame_count == 0:
            win.callOnFlip(
                send_trigger,
                handle,
                TRIG_B_WRONGRESPOND
            )
        elif frame_count == 1:
            win.callOnFlip(
                reset_trigger,
                handle
            )

        flip_time = win.flip()
        frame_timer(
            flip_time=flip_time,
            trial_index=index,
            task_type=trial["task_type"],
            phase="response"
        )

        frame_count += 1

    # =========================
    # 색 복구
    # =========================
    left_arrow.color = cfg["arrow"]["color"]
    right_arrow.color = cfg["arrow"]["color"]

    return response, rt, rt2


# =========================
# 6. 전체 실행
# =========================
def run_both_task(win, food_json_path, gene_json_path, habitat_json_path, handle):
    
    # 1. 3개의 JSON 파일 경로를 넣어 전체 180개의 트라이얼(15블록) 생성
    trials = generate_trials(food_json_path, gene_json_path, habitat_json_path)

    results = []

    # 2. enumerate를 사용하여 인덱스(i)와 트라이얼(t)을 동시에 순회
    for i, t in enumerate(trials):

        random_isi_phase(win)

        # 3. 정보 제공 화면 로직 수정 (처음 시작할 때[0]와 15문제마다 반복)
        if i % 10 == 0:

            if MODE==0:
                show_all_food_phase(win, handle)
                show_all_gene_phase(win, handle)
                show_all_habitat_phase(win, handle)

            elif MODE==1:
                #show_all_food_phase(win, handle)
                show_all_gene_phase(win, handle)
                show_all_habitat_phase(win, handle)
        

            elif MODE==2:
                show_all_food_phase(win, handle)
                #show_all_gene_phase(win, handle)
                show_all_habitat_phase(win, handle)
        
            elif MODE==3:
                show_all_food_phase(win, handle)
                show_all_gene_phase(win, handle)
                #show_all_habitat_phase(win, handle)
           

        # 4. 트라이얼 실행
        response, rt, rt2 = run_trial(win, t, handle,i)

        # 5. 정답 확인 및 결과 저장
        is_correct = (response == t["correct"]) if response else False

        results.append({
            **t,
            "response": response,
            "rt1": rt,
            "rt2":rt2,
            "is_correct": is_correct
        })

    return results

'''
# =========================
# 6. 전체 실행
# =========================
def run_both_task(win, json_path,handle):

    animals, food_edges, gene_edges, habitat_groups = load_both_web(json_path)

    trials = generate_trials(animals, food_edges, gene_edges, habitat_groups, n_trials=180)

    results = []

    i=0

    for t in trials:

        random_isi_phase(win)

       

        if i == 0 and i  % 10 == 0:

            show_all_food_phase(win, handle)
            show_all_gene_phase(win, handle)
            show_all_habitat_phase(win, handle)


        response, rt = run_trial(win, t,handle)

        
        is_correct = (response == t["correct"]) if response else False

        results.append({
            **t,
            "response": response,
            "rt": rt,
            "is_correct": is_correct
        })



        i+=1

        

    return results

'''
