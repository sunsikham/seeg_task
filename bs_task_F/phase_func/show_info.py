import os
import random
from psychopy import visual, core, event
from set_opts.visual_opts import UI_CONFIG
from utils.labjack_trigger import send_trigger, reset_trigger, TRIG_FOOD_SHOW, TRIG_GENE_SHOW, TRIG_FOOD_SHOW_R, TRIG_GENE_SHOW_R, TRIG_HABITAT_SHOW, TRIG_HABITAT_SHOW_R
from config import FRAME_EXAMPLE_fa,FRAME_EXAMPLE_ga,FRAME_EXAMPLE_fr,FRAME_EXAMPLE_gr,FRAME_EXAMPLE_ha, FRAME_EXAMPLE_hr, WIDTH, HEIGHT, STIMULI_DIR
from draw_func.draw_marker import draw_white_marker
from sys_func.frame_count import frame_timer


# =========================================
# 공통: 폴더 내 이미지 경로 가져오기
# =========================================
def load_image_paths(folder_path):

    valid_ext = (".png", ".jpg", ".jpeg", ".bmp")

    files = [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if f.lower().endswith(valid_ext)
    ]

    return sorted(files)


# =========================================
# 1. food 전체 6개 보여주기 (ENTER 종료)
# =========================================
def show_all_food_phase(
    win,
    handle
):

    cfg = UI_CONFIG["image_phase"]["food_all"]

   

    image_paths = (
    os.path.join(STIMULI_DIR, "food", "먹이사슬.png")
    )

    stim = visual.ImageStim(
        win,
        image=image_paths,
        pos=cfg["position"],
        size=cfg["size"]
    )

    # 현재 배경색 저장
    original_color = win.color

    # 배경색 변경 (분홍색)
    win.color = [1, 0.75, 0.85]  # rgb 기준 pink 느낌

     # 이전 Enter 제거
    event.clearEvents(eventType='keyboard')

    # 배경 먼저 출력
    flip_time = win.flip()

    frame_timer(
        flip_time=flip_time,
        trial_index=None,
        task_type="food",
        phase="info_screen"
    )

    frame_count=0

    # ===== frame loop =====
    while True:

        if frame_count < FRAME_EXAMPLE_fa:
            draw_white_marker(
                win,
                pos=(-WIDTH//2 + 120, -HEIGHT//2 + 120),
                size=(50, 50)
            )

         # trigger ON
        if frame_count == 0:

            win.callOnFlip(
                send_trigger,
                handle,
                TRIG_FOOD_SHOW
            )

        # trigger OFF
        elif frame_count == 1:

            win.callOnFlip(
                reset_trigger,
                handle
            )


        stim.draw()

        frame_count+=1

        flip_time = win.flip()

        frame_timer(
            flip_time=flip_time,
            trial_index=None,
            task_type="food",
            phase="info_screen"
        )



        # ENTER 입력 확인
        keys = event.getKeys()

        if "return" in keys:
            break

        

    # 원래 배경색 복구
    win.color = original_color

# =========================================
# 2. gene 전체 3개 보여주기 (ENTER 종료)
# =========================================
def show_all_gene_phase(
    win,
    handle
):

    cfg = UI_CONFIG["image_phase"]["gene_all"]

    image_paths = (
    os.path.join(STIMULI_DIR, "gene", "유전자.png")
    )

    stim = visual.ImageStim(
        win,
        image=image_paths,
        pos=cfg["position"],
        size=cfg["size"]
    )

    # 현재 배경색 저장
    original_color = win.color

    # 배경색 변경 (분홍색)
    win.color = [0.75, 0.9, 1]  # rgb 기준 pink 느낌

    event.clearEvents(eventType='keyboard')

    frame_count=0

    # ===== frame loop =====
    while True:

        if frame_count < FRAME_EXAMPLE_ga:
            draw_white_marker(
                win,
                pos=(-WIDTH//2 + 120, -HEIGHT//2 + 120),
                size=(50, 50)
            )

         # trigger ON
        if frame_count == 0:

            win.callOnFlip(
                send_trigger,
                handle,
                TRIG_GENE_SHOW
            )

        # trigger OFF
        elif frame_count == 1:

            win.callOnFlip(
                reset_trigger,
                handle
            )


        stim.draw()

        frame_count+=1

        flip_time = win.flip()

        frame_timer(
            flip_time=flip_time,
            trial_index=None,
            task_type="gene",
            phase="info_screen"
        )



        # ENTER 입력 확인
        keys = event.getKeys()

        if "return" in keys:
            break

        

    # 원래 배경색 복구
    win.color = original_color


# =========================================
# 2. 서식지 전체 보여주기 (ENTER 종료)
# =========================================
def show_all_habitat_phase(
    win,
    handle
):

    cfg = UI_CONFIG["image_phase"]["habitat_all"]

    image_paths = (
    os.path.join(STIMULI_DIR, "habitat", "서식지.png")
    )

    stim = visual.ImageStim(
        win,
        image=image_paths,
        pos=cfg["position"],
        size=cfg["size"]
    )

    # 현재 배경색 저장
    original_color = win.color

    # 배경색 변경 
    win.color = [0.7, 1, 0.7]  

    event.clearEvents(eventType='keyboard')

    frame_count=0

    # ===== frame loop =====
    while True:

        if frame_count < FRAME_EXAMPLE_ha:
            draw_white_marker(
                win,
                pos=(-WIDTH//2 + 120, -HEIGHT//2 + 120),
                size=(50, 50)
            )

         # trigger ON
        if frame_count == 0:

            win.callOnFlip(
                send_trigger,
                handle,
                TRIG_HABITAT_SHOW
            )

        # trigger OFF
        elif frame_count == 1:

            win.callOnFlip(
                reset_trigger,
                handle
            )


        stim.draw()

        frame_count+=1

        flip_time = win.flip()

        frame_timer(
            flip_time=flip_time,
            trial_index=None,
            task_type="habitat",
            phase="info_screen"
        )



        # ENTER 입력 확인
        keys = event.getKeys()

        if "return" in keys:
            break

        

    # 원래 배경색 복구
    win.color = original_color


# =========================================
# 3. food 랜덤 2개 보여주기
# =========================================
def show_random_food_pair(
    win,
    handle,
    duration_frames=UI_CONFIG["timing"]["show_random"]
):

    cfg = UI_CONFIG["image_phase"]["food_pair"]


    # 1. 선택하고자 하는 파일 이름 리스트
    target_files = ["1.png", "2.png", "3.png", "4.png", "5.png", "6.png"]

    # 2. 파일 이름들을 경로(stimuli/gene/...)로 변환하여 리스트 생성
    image_paths = [os.path.join(STIMULI_DIR, "food", filename) for filename in target_files]

    selected = random.sample(image_paths, 2)

    stims = []

    for path, pos in zip(
        selected,
        cfg["positions"]
    ):

        stim = visual.ImageStim(
            win,
            image=path,
            pos=pos,
            size=cfg["size"]
        )

        stims.append(stim)

     # 현재 배경색 저장
    original_color = win.color

    # 배경색 변경 (분홍색)
    win.color = [1, 0.75, 0.85]   # rgb 기준 pink 느낌


    frame_count = 0

    # ===== frame loop =====
    for _ in range(duration_frames):

        if frame_count < FRAME_EXAMPLE_fr:
            draw_white_marker(
                win,
                pos=(-WIDTH//2 + 120, -HEIGHT//2 + 120),
                size=(50, 50)
            )

         # trigger ON
        if frame_count == 0:

            win.callOnFlip(
                send_trigger,
                handle,
                TRIG_FOOD_SHOW_R
            )

        # trigger OFF
        elif frame_count == 1:

            win.callOnFlip(
                reset_trigger,
                handle
            )

        for stim in stims:
            stim.draw()

        frame_count += 1

        flip_time = win.flip()
        frame_timer(flip_time)

    win.color = original_color


# =========================================
# 4. gene 랜덤 1개 보여주기
# =========================================
def show_random_gene_single(
    win,
    handle,
    duration_frames=UI_CONFIG["timing"]["show_random"]
):

    cfg = UI_CONFIG["image_phase"]["gene_single"]

    # 1. 선택하고자 하는 파일 이름 리스트
    target_files = ["1.png", "2.png", "3.png"]

    # 2. 파일 이름들을 경로(stimuli/gene/...)로 변환하여 리스트 생성
    image_paths = [os.path.join(STIMULI_DIR, "gene", filename) for filename in target_files]

    # 3. 생성된 경로들 중에서 랜덤으로 하나 선택
    selected = random.choice(image_paths)

    stim = visual.ImageStim(
        win,
        image=selected,
        pos=cfg["position"],
        size=cfg["size"]
    )

    # 현재 배경색 저장
    original_color = win.color

    # 배경색 변경 (분홍색)
    win.color = [0.75, 0.9, 1]  # rgb 기준 pink 느낌

    frame_count=0

    # ===== frame loop =====
    for _ in range(duration_frames):

        if frame_count < FRAME_EXAMPLE_gr:
            draw_white_marker(
                win,
                pos=(-WIDTH//2 + 120, -HEIGHT//2 + 120),
                size=(50, 50)
            )

         # trigger ON
        if frame_count == 0:

            win.callOnFlip(
                send_trigger,
                handle,
                TRIG_GENE_SHOW_R
            )

        # trigger OFF
        elif frame_count == 1:

            win.callOnFlip(
                reset_trigger,
                handle
            )


        stim.draw()

        frame_count+=1

        flip_time = win.flip()
        frame_timer(flip_time)


    win.color = original_color



def show_random_habitat_single(
    win,
    handle,
    duration_frames=UI_CONFIG["timing"]["show_random"]
):

    cfg = UI_CONFIG["image_phase"]["gene_single"]

    # 1. 선택하고자 하는 파일 이름 리스트
    target_files = ["1.png", "2.png", "3.png"]

    # 2. 파일 이름들을 경로(stimuli/gene/...)로 변환하여 리스트 생성
    image_paths = [os.path.join(STIMULI_DIR, "habitat", filename) for filename in target_files]

    # 3. 생성된 경로들 중에서 랜덤으로 하나 선택
    selected = random.choice(image_paths)

    stim = visual.ImageStim(
        win,
        image=selected,
        pos=cfg["position"],
        size=cfg["size"]
    )

    # 현재 배경색 저장
    original_color = win.color

    # 배경색 변경 (분홍색)
    win.color = [0.9, 1, 75]  # rgb 기준 pink 느낌

    frame_count=0

    # ===== frame loop =====
    for _ in range(duration_frames):

        if frame_count < FRAME_EXAMPLE_hr:
            draw_white_marker(
                win,
                pos=(-WIDTH//2 + 120, -HEIGHT//2 + 120),
                size=(50, 50)
            )

         # trigger ON
        if frame_count == 0:

            win.callOnFlip(
                send_trigger,
                handle,
                TRIG_HABITAT_SHOW_R
            )

        # trigger OFF
        elif frame_count == 1:

            win.callOnFlip(
                reset_trigger,
                handle
            )


        stim.draw()

        frame_count+=1
        flip_time = win.flip()
        frame_timer(flip_time)
                


    win.color = original_color
