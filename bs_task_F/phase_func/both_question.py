import json
import random
import os
from collections import deque
from set_opts.visual_opts import UI_CONFIG
from config import (
    HEIGHT,
    WIDTH,
    FRAME_EXAMPLE_bq,
    FRAME_EXAMPLE_bp,
    FRAME_EXAMPLE_bl,
    FRAME_EXAMPLE_br,
    FRAME_EXAMPLE_bss,
    FRAME_EXAMPLE_bf,
    QUESTION_FRAMES,
    REVEAL_FRAMES,
    MODE,
    STIMULI_DIR,
)
from draw_func.draw_marker import draw_white_marker
from utils.labjack_trigger import (
    send_trigger,
    reset_trigger,
    TRIG_B_QUESTION_ON,
    TRIG_B_PREMISE_ON,
    TRIG_B_OPTION_LEFT_ON,
    TRIG_B_OPTION_RIGHT_ON,
    TRIG_B_CHOICE_ON,
    TRIG_B_CORRECT_RESPONSE,
    TRIG_B_WRONG_RESPONSE,
    TRIG_B_NO_RESPONSE,
)
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

    response = None
    rt = None
    rt2 = None

    marker_pos = (-WIDTH//2 + 120, -HEIGHT//2 + 120)
    marker_size = (50, 50)

    def draw_scene(
        *,
        show_premise=False,
        show_left=False,
        show_right=False,
        show_arrows=False,
    ):
        question.draw()
        if show_premise:
            premise_image.draw()
        if show_left:
            left_option.draw()
            left_image.draw()
        if show_right:
            right_option.draw()
            right_image.draw()
        if show_arrows:
            left_arrow.draw()
            right_arrow.draw()

    def run_timed_phase(
        *,
        phase,
        duration_frames,
        trigger_code,
        marker_frames,
        reset_trial_clock=False,
        **scene_flags,
    ):
        onset_flip_time = None

        for frame_count in range(duration_frames):
            draw_scene(**scene_flags)

            if frame_count < marker_frames:
                draw_white_marker(
                    win,
                    pos=marker_pos,
                    size=marker_size,
                )

            if frame_count == 0:
                if reset_trial_clock:
                    win.callOnFlip(clock.reset)
                win.callOnFlip(
                    send_trigger,
                    handle,
                    trigger_code,
                    trial_index=index,
                    task_type=trial["task_type"],
                    phase=phase,
                )
            elif frame_count == 1:
                win.callOnFlip(reset_trigger, handle)

            flip_time = win.flip()
            if onset_flip_time is None:
                onset_flip_time = flip_time

            frame_timer(
                flip_time=flip_time,
                trial_index=index,
                task_type=trial["task_type"],
                phase=phase,
            )

        return onset_flip_time

    event.clearEvents()

    question_onset = run_timed_phase(
        phase="question_onset",
        duration_frames=QUESTION_FRAMES,
        trigger_code=TRIG_B_QUESTION_ON,
        marker_frames=FRAME_EXAMPLE_bq,
        reset_trial_clock=True,
    )
    premise_onset = run_timed_phase(
        phase="premise_onset",
        duration_frames=REVEAL_FRAMES,
        trigger_code=TRIG_B_PREMISE_ON,
        marker_frames=FRAME_EXAMPLE_bp,
        show_premise=True,
    )
    option_left_onset = run_timed_phase(
        phase="option_left_onset",
        duration_frames=REVEAL_FRAMES,
        trigger_code=TRIG_B_OPTION_LEFT_ON,
        marker_frames=FRAME_EXAMPLE_bl,
        show_premise=True,
        show_left=True,
    )
    option_right_onset = run_timed_phase(
        phase="option_right_onset",
        duration_frames=REVEAL_FRAMES,
        trigger_code=TRIG_B_OPTION_RIGHT_ON,
        marker_frames=FRAME_EXAMPLE_br,
        show_premise=True,
        show_left=True,
        show_right=True,
    )

    # 선택 전 입력은 버리고 CHOICE_ON reset 이후부터 응답을 허용한다.
    event.clearEvents()
    choice_onset = None
    timeout_frames = cfg["timing"]["timeout_frames"]

    for frame_count in range(timeout_frames):
        draw_scene(
            show_premise=True,
            show_left=True,
            show_right=True,
            show_arrows=True,
        )

        if frame_count < FRAME_EXAMPLE_bss:
            draw_white_marker(
                win,
                pos=marker_pos,
                size=marker_size,
            )

        if frame_count == 0:
            win.callOnFlip(rt2_clock.reset)
            win.callOnFlip(
                send_trigger,
                handle,
                TRIG_B_CHOICE_ON,
                trial_index=index,
                task_type=trial["task_type"],
                phase="choice_onset",
            )
        elif frame_count == 1:
            win.callOnFlip(reset_trigger, handle)

        flip_time = win.flip()
        if choice_onset is None:
            choice_onset = flip_time

        frame_timer(
            flip_time=flip_time,
            trial_index=index,
            task_type=trial["task_type"],
            phase="choice_onset",
        )

        if frame_count == 0:
            event.clearEvents()
            continue

        keys = event.getKeys(
            keyList=["left", "right", "escape"],
            timeStamped=clock,
        )

        if not keys:
            continue

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

        response_trigger = (
            TRIG_B_CORRECT_RESPONSE
            if response == trial["correct"]
            else TRIG_B_WRONG_RESPONSE
        )
        send_trigger(
            handle,
            response_trigger,
            trial_index=index,
            task_type=trial["task_type"],
            phase="response",
        )
        break

    if response is None:
        send_trigger(
            handle,
            TRIG_B_NO_RESPONSE,
            trial_index=index,
            task_type=trial["task_type"],
            phase="no_response",
        )

    # 응답/무응답 트리거를 유지한 뒤 다음 feedback 프레임에서 reset한다.
    feedback_frames = cfg["timing"]["feedback_frames"]
    for frame_count in range(feedback_frames):
        draw_scene(
            show_premise=True,
            show_left=True,
            show_right=True,
            show_arrows=True,
        )

        if frame_count < FRAME_EXAMPLE_bf:
            draw_white_marker(
                win,
                pos=marker_pos,
                size=marker_size,
            )

        if frame_count == 1:
            win.callOnFlip(reset_trigger, handle)

        flip_time = win.flip()
        frame_timer(
            flip_time=flip_time,
            trial_index=index,
            task_type=trial["task_type"],
            phase="feedback",
        )

    def relative_to_question(flip_time):
        return round(flip_time - question_onset, 6)

    trial_metadata = {
        "question_target": target,
        "question_text": question_text,
        "question_onset_s": 0.0,
        "premise_onset_s": relative_to_question(premise_onset),
        "option_left_onset_s": relative_to_question(option_left_onset),
        "option_right_onset_s": relative_to_question(option_right_onset),
        "choice_onset_s": relative_to_question(choice_onset),
        "response_detected_s": round(rt, 6) if rt is not None else None,
    }

    left_arrow.color = cfg["arrow"]["color"]
    right_arrow.color = cfg["arrow"]["color"]

    return response, rt, rt2, trial_metadata


# =========================
# 6. 전체 실행
# =========================
def run_both_task(
    win,
    food_json_path,
    gene_json_path,
    habitat_json_path,
    handle,
    on_trial_complete=None,
):
    
    # 1. 3개의 JSON 파일 경로를 넣어 전체 180개의 트라이얼(15블록) 생성
    trials = generate_trials(food_json_path, gene_json_path, habitat_json_path)

    results = []

    # 2. enumerate를 사용하여 인덱스(i)와 트라이얼(t)을 동시에 순회
    for i, t in enumerate(trials, start=1):
        # 3. 정보 제공 화면 로직 수정 (처음 시작할 때[0]와 15문제마다 반복)
        if (i - 1) % 10 == 0:

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

        # 정보 화면이 있는 trial도 질문 직전에 동일한 ISI를 둔다.
        random_isi_phase(win)

        # 4. 트라이얼 실행
        response, rt, rt2, trial_metadata = run_trial(win, t, handle, i)

        # 5. 정답 확인 및 결과 저장
        is_correct = (response == t["correct"]) if response else False

        results.append({
            **t,
            "response": response,
            "rt1": rt,
            "rt2":rt2,
            "is_correct": is_correct,
            **trial_metadata,
        })

        if on_trial_complete is not None:
            on_trial_complete(results)

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
