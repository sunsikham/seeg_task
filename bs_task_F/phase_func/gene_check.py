import json
import random
import os
from psychopy import visual, core, event
from pyjosa.josa import Josa
from utils.labjack_trigger import send_trigger, reset_trigger,  TRIG_G_CHECK_START, TRIG_G_CHECK_RESPOND
from config import WAITING,HEIGHT,WIDTH, HANDLE,FRAME_EXAMPLE_gcs,FRAME_EXAMPLE_gcf,STIMULI_DIR
from draw_func.draw_marker import draw_white_marker
from phase_func.waiting import random_isi_phase
from sys_func.frame_count import frame_timer

from set_opts.visual_opts import UI_CONFIG


# =========================
# gene group trial 생성
# =========================
def generate_gene_trials(animals, gene_edges, n_trials=7):

    # 동물 -> 그룹 매핑
    animal_to_group = {}

    for group, animal in gene_edges:
        animal_to_group[animal] = group

    trials = []

    for _ in range(n_trials):

        a, b = random.sample(animals, 2)

        correct = (
            1
            if animal_to_group[a] == animal_to_group[b]
            else 0
        )

        trials.append({
            "animal_a": a,
            "animal_b": b,
            "correct": correct
        })

    return trials


# =========================
# gene single trial
# =========================
def run_gene_trial(
    win,
    handle,
    animal_a,
    animal_b,
    correct
):

    cfg_q = UI_CONFIG["question"]
    cfg_opt = UI_CONFIG["option"]
    cfg_arrow = UI_CONFIG["arrow"]
    cfg_time = UI_CONFIG["timing"]
    cfg_feedback = UI_CONFIG["feedback_text"]
    cfg = UI_CONFIG

    question = (
        f"{Josa.get_full_string(animal_a, '은')}"
        f" {Josa.get_full_string(animal_b, '와')} "
        f"같은 유전자 그룹이다."
    )

    # =====================================
    # 이미지 경로
    # =====================================
    animal_a_image_path = os.path.join(
        STIMULI_DIR,
        f"{animal_a}.png"
    )

    animal_b_image_path = os.path.join(
        STIMULI_DIR,
        f"{animal_b}.png"
    )

    # =====================================
    # 질문 위치 기준 이미지 위치
    # =====================================
    qx, qy = cfg_q["pos"]

    animal_a_image = visual.ImageStim(
        win,
        image=animal_a_image_path,

        pos=cfg["image"]["sub_left_pos"],
        size=cfg["image"]["size2"]
    )

    animal_b_image = visual.ImageStim(
        win,
        image=animal_b_image_path,

        pos=cfg["image"]["sub_right_pos"],
        size=cfg["image"]["size2"]

    )

    # ===== 텍스트 =====
    title = visual.TextStim(
        win,
        text=question,
        pos=cfg_q["pos"],
        height=cfg_q["height"],
        color=cfg_q["color"],
        wrapWidth=cfg_q["wrapWidth"],
        font=cfg_q["font"]
    )

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

    # ===== 화살표 =====
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

        if frame_count < FRAME_EXAMPLE_gcs:
            draw_white_marker(
                win,
                pos=(-WIDTH//2 + 120, -HEIGHT//2 + 120),
                size=(50, 50)
            )

        # ===== draw =====
        title.draw()

        left_label.draw()
        right_label.draw()

        left_arrow.draw()
        right_arrow.draw()

        # ===== 이미지 =====
        animal_a_image.draw()
        animal_b_image.draw()

        # ===== trigger =====
        if frame_count == 0:

            win.callOnFlip(
                send_trigger,
                handle,
                TRIG_G_CHECK_START
            )

        elif frame_count == 1:

            win.callOnFlip(
                reset_trigger,
                handle
            )

        # ===== flip =====
        flip_time = win.flip()
        frame_timer(flip_time)

        # ===== key check =====
        keys = event.getKeys(
            keyList=["left", "right", "escape"],
            timeStamped=clock
        )

        if keys:

            key, rt = keys[0]

            if key == "escape":
                core.quit()

            # ===== response =====
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
    # response trigger phase
    # =========================

    frame_count = 0

    while frame_count < 2:

        title.draw()

        left_label.draw()
        right_label.draw()

        left_arrow.draw()
        right_arrow.draw()

        animal_a_image.draw()
        animal_b_image.draw()

        if frame_count == 0:

            win.callOnFlip(
                send_trigger,
                handle,
                TRIG_G_CHECK_RESPOND
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
    # feedback text 생성
    # =========================

    is_correct = (
        response == correct
        if response is not None else False
    )

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

        if frame_count < FRAME_EXAMPLE_gcf:
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

        animal_a_image.draw()
        animal_b_image.draw()

        feedback_text.draw()

        flip_time = win.flip()
        frame_timer(flip_time)

        frame_count += 1

    return response, rt

# =========================
# gene block 실행
# =========================
def run_gene_task(win, json_path, handle):

    cfg_q = UI_CONFIG["question"]
    cfg_time = UI_CONFIG["timing"]

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    animals = data["animals"]
    gene_edges = data["gene_edges"]

    trials = generate_gene_trials(
        animals,
        gene_edges,
        n_trials=7
    )

    results = []

    # ===== 안내문 =====
    instruction = visual.TextStim(
        win,
        text="옳다면 왼쪽 방향키(O)를 누르시오\n틀렸다면 오른쪽 방향키(X)를 누르시오",
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

    # ===== trial loop =====
    for t in trials:

        random_isi_phase(win)

        response, rt = run_gene_trial(
            win,
            handle,
            animal_a=t["animal_a"],
            animal_b=t["animal_b"],
            correct=t["correct"]
        )

        is_correct = (
            response == t["correct"]
            if response is not None else False
        )

        results.append({
            "animal_a": t["animal_a"],
            "animal_b": t["animal_b"],
            "correct_answer": t["correct"],
            "response": response,
            "rt": rt,
            "is_correct": is_correct
        })

        core.wait(cfg_time["iti"])

    return results
