
import json
import random
import os
from psychopy import visual, core, event
from pyjosa.josa import Josa
from utils.labjack_trigger import send_trigger, reset_trigger,  TRIG_H_CHECK_START, TRIG_H_CHECK_RESPOND
from config import WAITING,HEIGHT,WIDTH, HANDLE,FRAME_EXAMPLE_hcs,FRAME_EXAMPLE_hcf,STIMULI_DIR
from draw_func.draw_marker import draw_white_marker
from phase_func.waiting import random_isi_phase
from sys_func.frame_count import frame_timer

from set_opts.visual_opts import UI_CONFIG

# =========================
# 1. JSON 로드
# =========================
def load_habitat(json_path):

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    animals = data["animals"]

    habitat_groups = data["habitat_groups"]

    # =========================
    # 같은 그룹 pair 생성
    # =========================
    habitat_web = set()

    for group in habitat_groups:

        for i in range(len(group)):

            for j in range(i + 1, len(group)):

                a = group[i]
                b = group[j]

                habitat_web.add((a, b))
                habitat_web.add((b, a))

    return animals, habitat_web


# =========================
# 2. trial 생성
# =========================
# =========================
# 2. trial 생성
# =========================
def generate_habitat_trials(
    animals,
    habitat_web,
    n_trials=7
):

    trials = []

    # 중복 방지용
    used_pairs = set()

    max_attempt = 10000
    attempt = 0

    while (
        len(trials) < n_trials
        and attempt < max_attempt
    ):

        attempt += 1

        animal1, animal2 = random.sample(
            animals,
            2
        )

        # =========================
        # 순서 무시 중복 제거
        # =========================
        pair_key = tuple(
            sorted([animal1, animal2])
        )

        if pair_key in used_pairs:
            continue

        used_pairs.add(pair_key)

        # =========================
        # 정답 계산
        # =========================
        correct = (
            1
            if (animal1, animal2)
            in habitat_web
            else 0
        )

        trials.append({

            "animal1": animal1,

            "animal2": animal2,

            "correct": correct
        })

    random.shuffle(trials)

    return trials

# =========================
# 3. single trial
# =========================
def run_habitat_trial(
    win,
    handle,
    animal1,
    animal2,
    correct
):

    cfg_q = UI_CONFIG["question"]
    cfg_opt = UI_CONFIG["option"]
    cfg_arrow = UI_CONFIG["arrow"]
    cfg_time = UI_CONFIG["timing"]
    cfg_feedback = UI_CONFIG["feedback_text"]
    cfg = UI_CONFIG

    # =========================
    # 질문
    # =========================
    # 위도와 경도 중 하나를 1/2 확률로 무작위 선택
    line_type = random.choice(["위도(가로선)", "경도(세로선)"])

    question = (
        f"{Josa.get_full_string(animal1, '은')} "
        f"{Josa.get_full_string(animal2, '와')} "
        f"같은 {line_type}에 산다."
    )

    # =========================
    # 이미지 경로
    # =========================
    animal1_image_path = os.path.join(
        STIMULI_DIR,
        f"{animal1}.png"
    )

    animal2_image_path = os.path.join(
        STIMULI_DIR,
        f"{animal2}.png"
    )

    # =========================
    # 이미지
    # =========================
    animal1_image = visual.ImageStim(
        win,
        image=animal1_image_path,

        pos=cfg["image"]["sub_left_pos"],
        size=cfg["image"]["size2"]
    )

    animal2_image = visual.ImageStim(
        win,
        image=animal2_image_path,

        pos=cfg["image"]["sub_right_pos"],
        size=cfg["image"]["size2"]
    )

    # =========================
    # 질문 텍스트
    # =========================
    title = visual.TextStim(
        win,

        text=question,

        pos=cfg_q["pos"],

        height=cfg_q["height"],

        color=cfg_q["color"],

        wrapWidth=cfg_q["wrapWidth"],

        font=cfg_q["font"]
    )

    # =========================
    # OX
    # =========================
    left_label = visual.TextStim(
        win,

        text="O",

        pos=cfg_opt["left_pos"],

        height=cfg_opt["height"],

        color=cfg_opt["color"],

        font=cfg_q["font"]
    )

    right_label = visual.TextStim(
        win,

        text="X",

        pos=cfg_opt["right_pos"],

        height=cfg_opt["height"],

        color=cfg_opt["color"],

        font=cfg_q["font"]
    )

    # =========================
    # 화살표
    # =========================
    left_arrow = visual.TextStim(
        win,

        text="◀",

        pos=cfg_arrow["left_pos"],

        height=cfg_arrow["height"],

        color=cfg_arrow["color"]
    )

    right_arrow = visual.TextStim(
        win,

        text="▶",

        pos=cfg_arrow["right_pos"],

        height=cfg_arrow["height"],

        color=cfg_arrow["color"]
    )

    clock = core.Clock()

    event.clearEvents()

    response = None
    rt = None

    # =========================
    # response phase
    # =========================
    timeout_frames = (
        cfg_time["timeout_frames"]
    )

    frame_count = 0

    while frame_count < timeout_frames:

        if frame_count < FRAME_EXAMPLE_hcs:
            draw_white_marker(
                win,
                pos=(-WIDTH//2 + 120, -HEIGHT//2 + 120),
                size=(50, 50)
            )

        title.draw()

        left_label.draw()
        right_label.draw()

        left_arrow.draw()
        right_arrow.draw()

        animal1_image.draw()
        animal2_image.draw()

        # ===== trigger =====
        if frame_count == 0:

            win.callOnFlip(
                send_trigger,
                handle,
                TRIG_H_CHECK_START
            )

        elif frame_count == 1:

            win.callOnFlip(
                reset_trigger,
                handle
            )

        flip_time = win.flip()
        frame_timer(flip_time)

        # ===== key =====
        keys = event.getKeys(
            keyList=["left", "right", "escape"],
            timeStamped=clock
        )

        if keys:

            key, rt = keys[0]

            if key == "escape":
                core.quit()

            if key == "left":

                left_arrow.color = (
                    cfg_arrow["active_color"]
                )

                response = 1

            else:

                right_arrow.color = (
                    cfg_arrow["active_color"]
                )

                response = 0

            break

        frame_count += 1

    # =========================
    # response trigger
    # =========================
    frame_count = 0

    while frame_count < 2:

        title.draw()

        left_label.draw()
        right_label.draw()

        left_arrow.draw()
        right_arrow.draw()

        animal1_image.draw()
        animal2_image.draw()

        if frame_count == 0:

            win.callOnFlip(
                send_trigger,
                handle,
                TRIG_H_CHECK_RESPOND
            )

        elif frame_count == 1:

            win.callOnFlip(
                reset_trigger,
                handle
            )

        flip_time = win.flip()
        frame_timer(flip_time)

        frame_count += 1

    # =========================
    # correctness
    # =========================
    is_correct = (
        response == correct
        if response is not None else False
    )

    # =========================
    # feedback
    # =========================
    if is_correct:

        feedback_text = visual.TextStim(
            win,

            text="정답",

            pos=cfg_feedback["left_pos"],

            height=cfg_opt["height"] * 1.7,

            color="green",

            bold=True,

            font=cfg_q["font"]
        )

    else:

        feedback_text = visual.TextStim(
            win,

            text="오답",

            pos=cfg_feedback["right_pos"],

            height=cfg_opt["height"] * 1.7,

            color="red",

            bold=True,

            font=cfg_q["font"]
        )

    # =========================
    # feedback phase
    # =========================
    feedback_frames = (
        cfg_time["feedback_frames"]
    )

    frame_count = 0

    while frame_count < feedback_frames:

        if frame_count < FRAME_EXAMPLE_hcf:
            draw_white_marker(
                win,
                pos=(-WIDTH//2 + 120, -HEIGHT//2 + 120),
                size=(50, 50)
            )

        title.draw()

        left_label.draw()
        right_label.draw()

        left_arrow.draw()
        right_arrow.draw()

        animal1_image.draw()
        animal2_image.draw()

        feedback_text.draw()

        flip_time = win.flip()
        frame_timer(flip_time)

        frame_count += 1

    return response, rt


# =========================
# 4. habitat block 실행
# =========================
def run_habitat_task(
    win,
    json_path,
    handle
):

    cfg_q = UI_CONFIG["question"]
    cfg_time = UI_CONFIG["timing"]

    animals, habitat_web = load_habitat(
        json_path
    )

    trials = generate_habitat_trials(
        animals,
        habitat_web,
        n_trials=7
    )

    results = []

    # ===== 안내문 =====
    instruction = visual.TextStim(
        win,

        text=(
            "옳다면 왼쪽 방향키(O)를 누르시오\n"
            "틀렸다면 오른쪽 방향키(X)를 누르시오"
        ),

        pos=(0, 0),

        height=cfg_q["height"] * 0.7,

        color="black",

        wrapWidth=cfg_q["wrapWidth"]
    )

    win.color = [0.5, 0.5, 0.5]

    flip_time = win.flip()
    frame_timer(flip_time)

    instruction.draw()

    flip_time = win.flip()
    frame_timer(flip_time)

    core.wait(3)

    # ===== loop =====
    for t in trials:

        random_isi_phase(win)

        response, rt = run_habitat_trial(

            win,
            handle,

            animal1=t["animal1"],

            animal2=t["animal2"],

            correct=t["correct"]
        )

        is_correct = (
            response == t["correct"]
            if response is not None else False
        )

        results.append({

            "animal_a": t["animal1"],

            "animal_b": t["animal2"],

            "correct_answer": t["correct"],

            "response": response,

            "rt": rt,

            "is_correct": is_correct
        })

        core.wait(cfg_time["iti"])

    return results
