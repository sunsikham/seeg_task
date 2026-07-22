"""
동물 분류 태스크 (PsychoPy)
- 유전자.png 를 배경 계통수로 사용
- 동물 이미지 칸을 빈 네모로 가리고, 방향키로 선택 / 엔터로 배치
- web.json["animals"] 는 문자열 리스트 OR 딕셔너리 리스트 모두 지원

 
# ── 배경 계통수 이미지 ────────────────────────────────────────────────────────
# 원본 이미지 비율 유지하면서 창에 맞게 표시
bg = visual.ImageStim(win, image=BG_IMAGE, pos=(0, 160), size=(WIN_W*0.8, WIN_H*0.45))
 
# ── 빈칸 위치 (픽셀, 중심 0,0 기준) ──────────────────────────────────────────
# 유전자.png 레이아웃에서 동물 이미지가 있던 6개 칸의 중심 좌표
# 이미지 해상도가 다르면 아래 값을 조정하세요

BOX_W, BOX_H = 115, 100
 
SLOT_POS = [
    (-530, -90),   # 0: 양
    (-350, -90),   # 1: 소
    ( -85, -90),   # 2: 여우
    ( 100, -90),   # 3: 흑곰
    ( 368, -90),   # 4: 고슴도치
    ( 550, -90),   # 5: 쥐
]
SLOT_LABELS = ["양", "소", "여우", "흑곰", "고슴도치", "쥐"]
 
# 방향키 네비게이션 맵
NAV = {
    0: {"right":1,  "left":None},
    1: {"right":2,  "left":0},
    2: {"right":3,  "left":1},
    3: {"right":4,  "left":2},
    4: {"right":5,  "left":3},
    5: {"right":None,"left":4},
}
 
# ── 프레임 설정 ───────────────────────────────────────────────────────────────
FPS = 144
FEEDBACK_FRAMES = int(0.5 * FPS)   # 피드백(초록/빨강) 표시 프레임 수 (0.5초)
END_FRAMES      = int(2.5 * FPS)   # 완료 화면 표시 프레임 수 (약 2.5초)
 
frame_n = 0   # 전체 프레임 카운터 (기록용)
 
# ── 우측 미리보기 패널 위치 ───────────────────────────────────────────────────
PRV_X, PRV_Y  = 0, -240
PRV_W, PRV_H  = 120, 70
 


"""

from utils.labjack_trigger import send_trigger, reset_trigger,  TRIG_G_CHECK_START, TRIG_G_CHECK_RESPOND
from config import (
    WAITING,
    HEIGHT,
    WIDTH,
    HANDLE,
    FRAME_EXAMPLE_gcs,
    FRAME_EXAMPLE_gcf,
    PRACTICE_DONE_FRAMES,
    PRACTICE_FEEDBACK_FRAMES,
    PRACTICE_PHASE_GAP_FRAMES,
    TARGET_REFRESH_HZ,
)
from phase_func.show_info import  show_all_gene_phase
from sys_func.frame_count import frame_timer
from utils.neon_client import CheckSectionController, NullNeonClient
 
import json, random, os, csv, datetime
from psychopy import visual, core, event
from psychopy.hardware import keyboard
 
# ── 경로 설정 ─────────────────────────────────────────────────────────────────
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR  = os.path.dirname(SCRIPT_DIR)
STIMULI_DIR = os.path.join(PARENT_DIR, "stimuli")
JSON_PATH   = os.path.join(STIMULI_DIR, "web.json")
FONT        = "Malgun Gothic"
 
if not os.path.isdir(STIMULI_DIR):
    raise FileNotFoundError(f"stimuli 폴더를 찾을 수 없습니다: {STIMULI_DIR}")
 
# ── 프레임 설정 ───────────────────────────────────────────────────────────────
FPS             = TARGET_REFRESH_HZ
FEEDBACK_FRAMES = PRACTICE_FEEDBACK_FRAMES
DONE_FRAMES     = PRACTICE_DONE_FRAMES
 
# ── 빈칸 / 선택지 크기 ────────────────────────────────────────────────────────
BOX_W, BOX_H     = 165, 150
CHOICE_W, CHOICE_H = 140, 120
 
# ── 배경 이미지 공통 설정 ─────────────────────────────────────────────────────
BG_SIZE1 = (WIDTH * 0.90, HEIGHT * 0.45)
BG_SIZE2 = (WIDTH * 0.80, HEIGHT * 0.45)
BG_POS  = (0, 160)
 
# ── 선택지 하단 배치 설정 ─────────────────────────────────────────────────────
CHOICE_Y   = -320
CHOICE_GAP = 210
 
# ── 페이즈 정의 ───────────────────────────────────────────────────────────────
#
# 계통수 구조 (web.json gene_edges 기준):
#   쥐과  → 고슴도치, 쥐
#   개과  → 여우, 흑곰
#   소과  → 양, 소
#
# 각 페이즈: 해당 과(family)의 빈칸 2개 + 선택지
#
# 배경 이미지 1 (유전자체크.png):  슬롯 위치는 원본 이미지 기준
# 배경 이미지 2 (유전자체크_-_복사본.png): 트리 위치가 조정된 버전 — 같은 정답, 다른 위치
#
# slot_valid: 각 슬롯에 넣을 수 있는 정답 동물 목록
# choices:    하단에 보여줄 선택지 (정답 + 오답 distractors)
#
# ── 원본 배경(유전자체크.png) 기준 슬롯 위치 ─────────────────────────────────
# 계통수가 화면 상단(BG_POS=(0,160))에 배치되고,
# 슬롯 6개가 계통수 하단 말단 위치에 대응:
#   쥐과 두 칸: 왼쪽 영역
#   개과 두 칸: 가운데 영역
#   소과 두 칸: 오른쪽 영역
#
# ── 복사본 배경(유전자체크_-_복사본.png) 기준 슬롯 위치 ──────────────────────
# 트리 위치가 달라졌으므로 슬롯 X/Y 좌표도 별도로 정의
 
PHASES = [

    # =====================================================
    # 원본 계통수
    # =====================================================
    {
        "name": "gene1_all",
        "bg_image": "유전자체크.png",
        "bg_flip": False,

        "slot_pos": [
            (-670, -150),   # 쥐과
            (-420, -150),   # 쥐과

            (-150, -150),   # 개과
            ( 100, -150),   # 개과

            ( 450, -150),   # 소과
            ( 700, -150),   # 소과
        ],

        "slot_valid": [
            ["양", "소"],
            ["양", "소"],
            

            ["여우", "흑곰"],
            ["여우", "흑곰"],

            ["고슴도치", "쥐"],
            ["고슴도치", "쥐"],
        ],

        "choices": [
            "고슴도치",
            "쥐",
            "여우",
            "흑곰",
            "양",
            "소",
        ],

        "slot_labels": ["?", "?", "?", "?", "?", "?"],
    },

    # =====================================================
    # 복사본 계통수
    # =====================================================
    {
        "name": "gene2_all",
        "bg_image": "유전자체크1.png",
        "bg_flip": False,

        "slot_pos": [
            (-650, -150),   # 쥐과
            (-400, -150),   # 쥐과

            ( -100, -150),   # 개과
            ( 150, -150),   # 개과

            ( 480, -150),   # 소과
            ( 700, -150),   # 소과
        ],

        "slot_valid": [
            ["고슴도치", "쥐"],
            ["고슴도치", "쥐"],

            ["여우", "흑곰"],
            ["여우", "흑곰"],

            ["양", "소"],
            ["양", "소"],
        ],

        "choices": [
            "고슴도치",
            "쥐",
            "여우",
            "흑곰",
            "양",
            "소",
        ],

        "slot_labels": ["?", "?", "?", "?", "?", "?"],
    },
]
 
# ── 헬퍼 함수 ─────────────────────────────────────────────────────────────────
def find_animal_image_path(name):
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        p = os.path.join(STIMULI_DIR, f"{name}{ext}")
        if os.path.exists(p):
            return p
    return None
 
 
def draw_white_marker_local(win, pos, size):
    visual.Rect(
        win, pos=pos, width=size[0], height=size[1],
        fillColor="white", lineColor="white",
    ).draw()
 
 
# ── 단일 페이즈 실행 ──────────────────────────────────────────────────────────
def run_gene_phase(win, kb, phase_def, handle, section_controller):
    slot_pos    = phase_def["slot_pos"]
    slot_valid  = phase_def["slot_valid"]
    slot_labels = phase_def.get("slot_labels", ["?"] * len(slot_pos))
    n_slots     = len(slot_pos)
 
    # 배경 이미지
    bg_path = os.path.join(STIMULI_DIR, phase_def["bg_image"])
    if os.path.exists(bg_path):

        bg_flip = phase_def.get("bg_flip", False)
        bg = visual.ImageStim(
            win,
            image=bg_path,
            pos=BG_POS,
            size=BG_SIZE1 if bg_flip else BG_SIZE2,
            flipHoriz=bg_flip,
        )
    else:
        bg = None
 
    # ── 헬퍼 스티뮬러스 생성 ──────────────────────────────────────────────────
    def txt(text, pos, height=26, color="black", bold=False):
        return visual.TextStim(
            win, text=text, pos=pos, height=height,
            color=color, font=FONT, bold=bold, languageStyle="LTR",
        )
 
    def rect(pos, w, h, lineCol="black", fillCol=None, lw=2):
        return visual.Rect(
            win, pos=pos, width=w, height=h,
            lineColor=lineCol, fillColor=fillCol, lineWidth=lw,
        )
 
    def load_img(path, pos, size):
        if path and os.path.exists(path):
            return visual.ImageStim(win, image=path, pos=pos, size=size)
        return None
 
    # ── 슬롯 ─────────────────────────────────────────────────────────────────
    slot_rects = [
        rect(pos, BOX_W, BOX_H, lineCol="gray", fillCol="white", lw=2)
        for pos in slot_pos
    ]
    slot_label_stims = [
        txt(lbl, (pos[0], pos[1] - 80), height=24, color="dimgray")
        for lbl, pos in zip(slot_labels, slot_pos)
    ]
    slot_filled  = [False] * n_slots
    slot_content = [None]  * n_slots
    slot_imgs    = [None]  * n_slots
 
    # ── 하단 선택지 (랜덤 순서) ───────────────────────────────────────────────
    choices   = list(phase_def["choices"])
    random.shuffle(choices)
    n_choices = len(choices)
 
    total_w          = (n_choices - 1) * CHOICE_GAP
    choice_xs        = [-total_w / 2 + i * CHOICE_GAP for i in range(n_choices)]
    choice_positions = [(x, CHOICE_Y) for x in choice_xs]
 
    choice_rects = [
        rect(pos, CHOICE_W + 10, CHOICE_H + 10, lineCol="deepskyblue", fillCol="white", lw=2)
        for pos in choice_positions
    ]
    choice_imgs = [
        load_img(find_animal_image_path(name), pos, (CHOICE_W, CHOICE_H))
        for name, pos in zip(choices, choice_positions)
    ]
    choice_name_stims = [
        txt(name, (pos[0], pos[1] - 75), height=24, color="black")
        for name, pos in zip(choices, choice_positions)
    ]
 
    guide = txt(
        "← → : 동물 선택    Enter : 칸에 넣기    Esc : 종료",
        (0, -490), height=21, color="dimgray",
    )
 
    # 피드백 상태
    feedback_state = {"slot": None, "choice": None, "color": None}
 
    def next_empty_slot():
        for i in range(n_slots):
            if not slot_filled[i]:
                return i
        return None
 
    # ── 그리기 ────────────────────────────────────────────────────────────────
    def draw_scene(active_slot, sel_choice):
        if bg:
            bg.draw()
 
        for i, (r, pos) in enumerate(zip(slot_rects, slot_pos)):
            if i == feedback_state["slot"]:
                r.lineColor = feedback_state["color"]
                r.lineWidth = 6
            elif i == active_slot:
                r.lineColor = "orange"
                r.lineWidth = 4
            else:
                r.lineColor = "gray"
                r.lineWidth = 2
            r.draw()
 
            if slot_imgs[i] is not None:
                slot_imgs[i].draw()
            elif slot_content[i] is not None:
                txt(slot_content[i], pos, height=26, color="navy").draw()
 
        #for lbl in slot_label_stims:
            #lbl.draw()
 
        for i, (r, pos) in enumerate(zip(choice_rects, choice_positions)):
            if i == feedback_state["choice"]:
                r.lineColor = feedback_state["color"]
                r.lineWidth = 6
            elif i == sel_choice:
                r.lineColor = "orange"
                r.lineWidth = 5
            else:
                r.lineColor = "gray"
                r.lineWidth = 2
            r.draw()
 
            if choice_imgs[i] is not None:
                choice_imgs[i].draw()
            else:
                txt(choices[i], pos, height=28, color="green").draw()
 
            choice_name_stims[i].draw()
 
        guide.draw()
 
    # ── 트라이얼 루프 ─────────────────────────────────────────────────────────
    selected_choice   = 0
    results           = []
    clock             = core.Clock()
    frame_n           = 0
    trial_start_frame = 0
 
    phase_mode        = "wait_response"
    phase_frame_count = 0
    feedback_is_correct = False
    pending_slot      = None
    pending_name      = None
    wrong_count = 0
 
    running = True
 
    while running:
        active_slot = next_empty_slot()
 
        if active_slot is None and phase_mode == "wait_response":
            phase_mode        = "done"
            phase_frame_count = 0
 
        # ── 응답 대기 ─────────────────────────────────────────────────────────
        if phase_mode == "wait_response":
            if phase_frame_count == 0:
                win.callOnFlip(send_trigger, handle, TRIG_G_CHECK_START)
                section_controller.begin_response_on_flip(
                    win,
                    phase_def["name"],
                )
            elif phase_frame_count == 1:
                win.callOnFlip(reset_trigger, handle)
 
            draw_scene(active_slot, selected_choice)
 
            if phase_frame_count < FRAME_EXAMPLE_gcs:
                draw_white_marker_local(
                    win,
                    pos=(-WIDTH // 2 + 120, -HEIGHT // 2 + 120),
                    size=(50, 50),
                )
 
            flip_time = win.flip()

            frame_timer(
                flip_time=flip_time,
                trial_index=None,
                task_type="gene_check",
                phase="response"
            )
            frame_n += 1
            phase_frame_count += 1
 
            kb_keys = kb.getKeys(["left", "right", "return", "escape"], waitRelease=False)
            for key in kb_keys:
                if key.duration is not None:
                    continue
                k = key.name
 
                if k == "escape":
                    section_controller.abort_open_section()
                    core.quit()
                elif k == "left":
                    selected_choice = max(0, selected_choice - 1)
                elif k == "right":
                    selected_choice = min(n_choices - 1, selected_choice + 1)
                elif k == "return":
                    if active_slot is None:
                        continue
 
                    chosen_name = choices[selected_choice]
                    response_recorded = False
 
                    # 정답 검증: slot_valid 안에 있어야 하고, 짝꿍 슬롯과 중복 불가
                    is_correct = chosen_name in slot_valid[active_slot]

                    if is_correct:

                        same_family_slots = [
                            i for i in range(n_slots)
                            if i != active_slot
                            and set(slot_valid[i]) == set(slot_valid[active_slot])
                        ]

                        for sib in same_family_slots:
                            if slot_filled[sib] and slot_content[sib] == chosen_name:
                                is_correct = False
                                break

                    else:
                        wrong_count+=1

                        if wrong_count>=5:
                            section_controller.record_response(is_correct)
                            response_recorded = True
                            event.clearEvents(eventType='keyboard')

                            slot_filled  = [False] * n_slots
                            slot_content = [None]  * n_slots
                            slot_imgs    = [None]  * n_slots
                            
                            show_all_gene_phase(
                                win,
                                handle,
                                neon_client=section_controller.neon_client,
                            )
                            event.clearEvents(eventType='keyboard')
                            wrong_count=0

                    if not response_recorded:
                        section_controller.record_response(is_correct)
 
                    results.append({
                        "phase":     phase_def["name"],
                        "animal":    chosen_name,
                        "slot_idx":  active_slot,
                        "correct":   is_correct,
                        "rt_sec":    round(clock.getTime(), 3),
                        "rt_frames": frame_n - trial_start_frame,
                    })
 
                    pending_slot        = active_slot
                    pending_name        = chosen_name
                    feedback_is_correct = is_correct
                    feedback_state["slot"]   = active_slot
                    feedback_state["choice"] = selected_choice
                    feedback_state["color"]  = "green" if is_correct else "red"
 
                    phase_mode        = "feedback"
                    phase_frame_count = 0
 
            if not running:
                break
 
        # ── 피드백 ────────────────────────────────────────────────────────────
        elif phase_mode == "feedback":
            if phase_frame_count == 0:
                win.callOnFlip(send_trigger, handle, TRIG_G_CHECK_RESPOND)
                section_controller.begin_feedback_on_flip(win)
            elif phase_frame_count == 1:
                win.callOnFlip(reset_trigger, handle)
 
            draw_scene(pending_slot, selected_choice)
 
            if phase_frame_count < FRAME_EXAMPLE_gcf:
                draw_white_marker_local(
                    win,
                    pos=(-WIDTH // 2 + 120, -HEIGHT // 2 + 120),
                    size=(50, 50),
                )
 
            flip_time = win.flip()

            frame_timer(
                flip_time=flip_time,
                trial_index=None,
                task_type="gene_check",
                phase="feedback"
            )

            frame_n += 1
            phase_frame_count += 1
            escape_keys = kb.getKeys(["escape"], waitRelease=False)
            if any(key.duration is None for key in escape_keys):
                core.quit()

            if phase_frame_count >= FEEDBACK_FRAMES:
                section_controller.end_feedback()
                feedback_state["slot"]   = None
                feedback_state["choice"] = None
                feedback_state["color"]  = None
 
                if feedback_is_correct:
                    slot_content[pending_slot] = pending_name
                    slot_filled[pending_slot]  = True
                    img_path = find_animal_image_path(pending_name)
                    slot_imgs[pending_slot] = load_img(
                        img_path, slot_pos[pending_slot], (BOX_W - 10, BOX_H - 10)
                    )
 
                clock.reset()
                trial_start_frame = frame_n
                pending_slot = None
                pending_name = None
 
                if all(slot_filled):
                    phase_mode        = "done"
                    phase_frame_count = 0
                else:
                    phase_mode        = "wait_response"
                    phase_frame_count = 0
 
        # ── 완료 ──────────────────────────────────────────────────────────────
        elif phase_mode == "done":
            draw_scene(None, selected_choice)
            flip_time = win.flip()

            frame_timer(
                flip_time=flip_time,
                trial_index=None,
                task_type="gene_check",
                phase="done"
            )

            frame_n += 1
            phase_frame_count += 1
            escape_keys = kb.getKeys(["escape"], waitRelease=False)
            if any(key.duration is None for key in escape_keys):
                core.quit()
 
            if phase_frame_count >= DONE_FRAMES:
                running = False
 
    return results
 
 
# ── 메인 태스크 함수 ──────────────────────────────────────────────────────────
def _run_gene_task_impl(win, handle, section_controller):
    """
    유전자(계통수) 분류 태스크 실행.
    페이즈 순서는 매 실행마다 랜덤하게 섞입니다.
    win: 메인에서 이미 생성된 psychopy.visual.Window 객체
    """
    kb = keyboard.Keyboard()
 
    all_results = []
 
    shuffled_phases = list(PHASES)
    random.shuffle(shuffled_phases)
 
    for phase_def in shuffled_phases:
        # 페이즈 간 공백 0.5초
        for _ in range(PRACTICE_PHASE_GAP_FRAMES):
            flip_time = win.flip()

            frame_timer(
                flip_time=flip_time,
                trial_index=None,
                task_type="gene_check",
                phase="isi"
            )
            escape_keys = kb.getKeys(["escape"], waitRelease=False)
            if any(key.duration is None for key in escape_keys):
                core.quit()
        
        phase_results = run_gene_phase(
            win,
            kb,
            phase_def,
            handle,
            section_controller,
        )
        all_results.extend(phase_results)

    return all_results


def run_gene_task(win, handle, neon_client=None):
    neon_client = neon_client or NullNeonClient()
    section_controller = CheckSectionController(neon_client, "gene")
    try:
        return _run_gene_task_impl(win, handle, section_controller)
    finally:
        section_controller.abort_open_section()
