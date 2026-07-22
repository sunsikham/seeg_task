import os
import random
from psychopy import visual, core, event
from set_opts.visual_opts import UI_CONFIG
from utils.labjack_trigger import send_trigger, reset_trigger, TRIG_FOOD_SHOW, TRIG_GENE_SHOW, TRIG_FOOD_SHOW_R, TRIG_GENE_SHOW_R, TRIG_HABITAT_SHOW, TRIG_HABITAT_SHOW_R
from config import FRAME_EXAMPLE_fa,FRAME_EXAMPLE_ga,FRAME_EXAMPLE_fr,FRAME_EXAMPLE_gr,FRAME_EXAMPLE_ha, FRAME_EXAMPLE_hr, WIDTH, HEIGHT, STIMULI_DIR
from draw_func.draw_marker import draw_white_marker
from sys_func.frame_count import frame_timer
from utils.neon_client import NullNeonClient


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


def _show_all_phase(
    win,
    handle,
    *,
    domain,
    config_key,
    image_parts,
    background_color,
    trigger_code,
    marker_frames,
    neon_client=None,
):
    neon_client = neon_client or NullNeonClient()
    cfg = UI_CONFIG["image_phase"][config_key]
    stim = visual.ImageStim(
        win,
        image=os.path.join(STIMULI_DIR, *image_parts),
        pos=cfg["position"],
        size=cfg["size"],
    )
    original_color = win.color
    win.color = background_color
    occurrence = neon_client.next_occurrence(f"{domain}_info")
    section_start = f"{domain.upper()}_INFO_SECTION_START"
    section_end = f"{domain.upper()}_INFO_SECTION_END"
    identifier = f"{domain.upper()}_INFO_O{occurrence:03d}"
    metadata = {
        "task_type": f"{domain}_info",
        "phase": "info_screen",
        "trial_index": occurrence,
    }

    event.clearEvents(eventType="keyboard")
    frame_count = 0
    section_open = False

    try:
        while True:
            if frame_count < marker_frames:
                draw_white_marker(
                    win,
                    pos=(-WIDTH // 2 + 120, -HEIGHT // 2 + 120),
                    size=(50, 50),
                )

            if frame_count == 0:
                win.callOnFlip(send_trigger, handle, trigger_code)
                neon_client.call_on_flip(
                    win,
                    (section_start, identifier),
                    **metadata,
                )
                section_open = True
            elif frame_count == 1:
                win.callOnFlip(reset_trigger, handle)

            stim.draw()
            flip_time = win.flip()
            frame_timer(
                flip_time=flip_time,
                trial_index=occurrence,
                task_type=domain,
                phase="info_screen",
            )
            frame_count += 1

            keys = event.getKeys(keyList=["return", "escape"])
            if "return" in keys:
                neon_client.enqueue_event(section_end, metadata=metadata)
                section_open = False
                break
            if "escape" in keys:
                neon_client.enqueue_event(section_end, metadata=metadata)
                section_open = False
                core.quit()
    finally:
        if section_open:
            neon_client.enqueue_event(section_end, metadata=metadata)
        win.color = original_color


def show_all_food_phase(win, handle, neon_client=None):
    _show_all_phase(
        win,
        handle,
        domain="food",
        config_key="food_all",
        image_parts=("food", "먹이사슬.png"),
        background_color=[1, 0.75, 0.85],
        trigger_code=TRIG_FOOD_SHOW,
        marker_frames=FRAME_EXAMPLE_fa,
        neon_client=neon_client,
    )


def show_all_gene_phase(win, handle, neon_client=None):
    _show_all_phase(
        win,
        handle,
        domain="gene",
        config_key="gene_all",
        image_parts=("gene", "유전자.png"),
        background_color=[0.75, 0.9, 1],
        trigger_code=TRIG_GENE_SHOW,
        marker_frames=FRAME_EXAMPLE_ga,
        neon_client=neon_client,
    )


def show_all_habitat_phase(win, handle, neon_client=None):
    _show_all_phase(
        win,
        handle,
        domain="habitat",
        config_key="habitat_all",
        image_parts=("habitat", "서식지.png"),
        background_color=[0.7, 1, 0.7],
        trigger_code=TRIG_HABITAT_SHOW,
        marker_frames=FRAME_EXAMPLE_ha,
        neon_client=neon_client,
    )


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
