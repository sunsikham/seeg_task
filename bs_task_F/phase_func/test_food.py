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
FPS = 60   # 모니터 주사율에 맞춰 조정 (60Hz 가정)
FEEDBACK_FRAMES = int(0.6 * FPS)   # 피드백(초록/빨강) 표시 프레임 수 (약 0.6초)
END_FRAMES      = int(2.5 * FPS)   # 완료 화면 표시 프레임 수 (약 2.5초)
 
frame_n = 0   # 전체 프레임 카운터 (기록용)
 
# ── 우측 미리보기 패널 위치 ───────────────────────────────────────────────────
PRV_X, PRV_Y  = 0, -240
PRV_W, PRV_H  = 120, 70
 


"""

from utils.labjack_trigger import send_trigger, reset_trigger,  TRIG_F_CHECK_START, TRIG_F_CHECK_RESPOND
from config import WAITING,HEIGHT,WIDTH, HANDLE,FRAME_EXAMPLE_fcs,FRAME_EXAMPLE_fcf
from phase_func.show_info import show_all_food_phase
from sys_func.frame_count import frame_timer
 
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
    raise FileNotFoundError(
        f"stimuli 폴더를 찾을 수 없습니다: {STIMULI_DIR}"
    )
 
# ── 프레임 설정 ───────────────────────────────────────────────────────────────
FPS             = 60
FEEDBACK_FRAMES = int(0.6 * FPS)   # 피드백 약 0.6초
DONE_FRAMES     = int(2.5 * FPS)   # 완료 화면 약 2.5초
 
BOX_W, BOX_H   = 180, 150   # 빈칸 크기
CHOICE_W, CHOICE_H = 140, 120   # 선택지 이미지 크기
 
# 배경 이미지 공통 설정
BG_SIZE = (WIDTH * 0.4, HEIGHT * 0.48)
BG_POS  = (0, 100)
 
 
# ── 페이즈 정의 ───────────────────────────────────────────────────────────────
# 슬롯 위치 기준:
#   배경 이미지 왼쪽 = '먹음(포식자)' 영역, 오른쪽 = '먹힘(피식자)' 영역
#   플립(bg_flip=True) 시 좌우가 반전되므로 슬롯 X좌표도 반전
 
PHASES = [
    # ── 페이즈 1: 흑곰(소, 고슴도치) ─────────────────────────────────────────
    {
        "name": "phase1_bear",
        "bg_image": "먹이사슬1.png",
        "bg_flip": False,
        "slot_pos": [
            (-160,  80),   # 슬롯0: 흑곰(포식자) — 왼쪽 '먹음' 영역
            ( 150,  210),  # 슬롯1: 피식자(위)   — 오른쪽 '먹힘' 영역 위
            ( 150,   -10),  # 슬롯2: 피식자(아래) — 오른쪽 '먹힘' 영역 아래
        ],
        "slot_valid": [
            ["흑곰"],
            ["소", "고슴도치"],
            ["소", "고슴도치"],
        ],
        "choices": ["흑곰", "소", "고슴도치"],
        "arrows": [(1, 0), (2, 0)],
    },
    # ── 페이즈 1 플립: 흑곰(소, 고슴도치) 좌우반전 ───────────────────────────
    {
        "name": "phase1_bear_flip",
        "bg_image": "먹이사슬1.png",
        "bg_flip": True,
        "slot_pos": [
            ( 160,  80),   # 슬롯0: 흑곰(포식자) — 오른쪽 (반전 후 '먹음')
            (-150,  210),  # 슬롯1: 피식자(위)   — 왼쪽 (반전 후 '먹힘') 위
            (-150,   -10),  # 슬롯2: 피식자(아래) — 왼쪽 아래
        ],
        "slot_valid": [
            ["흑곰"],
            ["소", "고슴도치"],
            ["소", "고슴도치"],
        ],
        "choices": ["흑곰", "소", "고슴도치"],
        "arrows": [(1, 0), (2, 0)],
    },
    # ── 페이즈 2: 여우(양, 고슴도치) ─────────────────────────────────────────
    {
        "name": "phase2_fox",
        "bg_image": "먹이사슬2.png",
        "bg_flip": False,
        "slot_pos": [
            (-160,  80),
            ( 150,  210),
            ( 150,   -10),
        ],
        "slot_valid": [
            ["여우"],
            ["양", "고슴도치"],
            ["양", "고슴도치"],
        ],
        "choices": ["여우", "양", "고슴도치"],
        "arrows": [(1, 0), (2, 0)],
    },
    # ── 페이즈 2 플립: 여우(양, 고슴도치) 좌우반전 ───────────────────────────
    {
        "name": "phase2_fox_flip",
        "bg_image": "먹이사슬2.png",
        "bg_flip": True,
        "slot_pos": [
            ( 160,  80),
            (-150,  210),
            (-150,   -10),
        ],
        "slot_valid": [
            ["여우"],
            ["양", "고슴도치"],
            ["양", "고슴도치"],
        ],
        "choices": ["여우", "양", "고슴도치"],
        "arrows": [(1, 0), (2, 0)],
    },
    # ── 페이즈 3: 고슴도치(쥐) ────────────────────────────────────────────────
    {
        "name": "phase3_hedgehog",
        "bg_image": "먹이사슬3.png",
        "bg_flip": False,
        "slot_pos": [
            (-170,  80),   # 슬롯0: 고슴도치(포식자) — 왼쪽
            ( 170,  80),   # 슬롯1: 쥐(피식자)       — 오른쪽
        ],
        "slot_valid": [
            ["고슴도치"],
            ["쥐"],
        ],
        "choices": ["고슴도치", "쥐"],
        "arrows": [(1, 0)],
    },
    # ── 페이즈 3 플립: 고슴도치(쥐) 좌우반전 ────────────────────────────────
    {
        "name": "phase3_hedgehog_flip",
        "bg_image": "먹이사슬3.png",
        "bg_flip": True,
        "slot_pos": [
            ( 170,  80),   # 슬롯0: 고슴도치(포식자) — 오른쪽 (반전 후 '먹음')
            (-170,  80),   # 슬롯1: 쥐(피식자)       — 왼쪽  (반전 후 '먹힘')
        ],
        "slot_valid": [
            ["고슴도치"],
            ["쥐"],
        ],
        "choices": ["고슴도치", "쥐"],
        "arrows": [(1, 0)],
    },
    # ── 페이즈 4: 여우(양, 고슴도치) + 고슴도치(쥐) 합산 구조 ─────────────────
    # 이미지 레이아웃: 왼쪽=먹음(여우), 가운데=먹음/먹힘(양 위, 고슴도치 아래), 오른쪽=먹힘(쥐)
    # 슬롯0: 여우(왼쪽)  슬롯1: 양(가운데 위)  슬롯2: 고슴도치(가운데 아래)  슬롯3: 쥐(오른쪽)
    {
        "name": "phase4_combined",
        "bg_image": "먹이사슬4.png",
        "bg_flip": False,
        "slot_pos": [
            (-270,  60),   # 슬롯0: 여우 — 왼쪽 '먹음' 영역
            (   0,  200),  # 슬롯1: 양   — 가운데 위
            (   0,   20),  # 슬롯2: 고슴도치 — 가운데 아래
            ( 270,   20),  # 슬롯3: 쥐   — 오른쪽 '먹힘' 영역
        ],
        "slot_valid": [
            ["여우"],
            ["양"],
            ["고슴도치"],
            ["쥐"],
        ],
        "choices": ["여우", "양", "고슴도치", "쥐"],
        "arrows": [(1, 0), (2, 0), (3, 2)],
    }
]
 
# 선택지 동물을 하단에 배치할 Y좌표 및 간격
CHOICE_Y   = -310
CHOICE_GAP = 210
 
 
def normalize(a):
    if isinstance(a, str):
        return {"name": a, "image": None}
    return {"name": a.get("name", str(a)), "image": a.get("image", None)}
 
 
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
 
 
# ── 단일 페이즈 실행 함수 ─────────────────────────────────────────────────────
def run_phase(win, kb, phase_def, food_edges, all_animals,handle):
    """
    하나의 페이즈(먹이사슬 그룹)를 실행합니다.
    반환: 해당 페이즈의 결과 리스트
    """
    slot_pos   = phase_def["slot_pos"]
    slot_valid = phase_def["slot_valid"]
    n_slots    = len(slot_pos)
 
    # ── 배경 이미지 로드 ──────────────────────────────────────────────────────
    bg_path = os.path.join(STIMULI_DIR, phase_def["bg_image"])
    if os.path.exists(bg_path):
        bg = visual.ImageStim(
            win, image=bg_path,
            pos=BG_POS,
            size=BG_SIZE,
            flipHoriz=phase_def.get("bg_flip", False),
        )
    else:
        bg = None
 
    # ── 헬퍼 함수 ─────────────────────────────────────────────────────────────
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
 
    # ── 슬롯 생성 ─────────────────────────────────────────────────────────────
    slot_rects = [
        rect(pos, BOX_W, BOX_H, lineCol="gray", fillCol="white", lw=2)
        for pos in slot_pos
    ]
 
    slot_filled  = [False] * n_slots
    slot_content = [None]  * n_slots   # 채워진 동물 이름
    slot_imgs    = [None]  * n_slots   # 채워진 동물 이미지 stim
 # ── 하단 선택지 생성 (네거티브 보기 포함) ──────────────────────────────

    NEGATIVE_COUNT = 1   # 추가할 오답 개수

    choices = list(phase_def["choices"])

    # 현재 문제에 없는 동물들
    negative_pool = [
        animal for animal in all_animals
        if animal not in choices
    ]

    # 랜덤 오답 추가
    negatives = random.sample(
        negative_pool,
        min(NEGATIVE_COUNT, len(negative_pool))
    )

    choices.extend(negatives)

    # 최종 셔플
    random.shuffle(choices)

    n_choices = len(choices)
 
    # 선택지를 가운데 정렬로 배치
    total_w = (n_choices - 1) * CHOICE_GAP
    choice_xs = [- total_w / 2 + i * CHOICE_GAP for i in range(n_choices)]
    choice_positions = [(x, CHOICE_Y) for x in choice_xs]
 
    choice_rects = [
        rect(pos, CHOICE_W + 10, CHOICE_H + 10, lineCol="deepskyblue", fillCol="white", lw=2)
        for pos in choice_positions
    ]
    choice_imgs = []
    for name, pos in zip(choices, choice_positions):
        img_path = find_animal_image_path(name)
        choice_imgs.append(load_img(img_path, pos, (CHOICE_W, CHOICE_H)))
 
    choice_name_stims = [
        txt(name, (pos[0], pos[1] - 80), height=24, color="black")
        for name, pos in zip(choices, choice_positions)
    ]
 
    # ── 활성 슬롯 표시 (항상 다음 빈 칸이 활성) ─────────────────────────────
    def next_empty_slot():
        for i in range(n_slots):
            if not slot_filled[i]:
                return i
        return None
 
    # ── 안내 문구 ─────────────────────────────────────────────────────────────
    guide = txt(
        "← → : 동물 선택    Enter : 칸에 넣기    Esc : 종료",
        (0, -490), height=21, color="dimgray",
    )
 
    # ── 피드백 상태 ───────────────────────────────────────────────────────────
    feedback_state = {"slot": None, "color": None, "choice": None}
 
    # ── 그리기 함수 ───────────────────────────────────────────────────────────
    def draw_scene(active_slot, selected_choice):
        if bg:
            bg.draw()
 
        # 슬롯 그리기
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
 
        # 선택지 그리기
        for i, (r, pos) in enumerate(zip(choice_rects, choice_positions)):
            if i == feedback_state["choice"]:
                r.lineColor = feedback_state["color"]
                r.lineWidth = 6
            elif i == selected_choice:
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
 
    # ── 상태 초기화 ───────────────────────────────────────────────────────────
    selected_choice   = 0       # 현재 선택된 하단 선택지 인덱스
    results           = []
    clock             = core.Clock()
    frame_n           = 0
    trial_start_frame = 0
 
    phase_mode        = "wait_response"
    phase_frame_count = 0
    feedback_is_correct = False
    pending_slot      = None
    pending_name      = None
 
    running = True
 
    while running:
        active_slot = next_empty_slot()
 
        # 모든 슬롯이 채워지면 done
        if active_slot is None and phase_mode == "wait_response":
            phase_mode        = "done"
            phase_frame_count = 0
 
        # ── 응답 대기 ─────────────────────────────────────────────────────────
        if phase_mode == "wait_response":
 
            # 트라이얼 시작 트리거: 새 트라이얼 첫 프레임에만 발송
            if phase_frame_count == 0:
                win.callOnFlip(send_trigger, handle, TRIG_F_CHECK_START)
            elif phase_frame_count == 1:
                win.callOnFlip(reset_trigger, handle)
 
            draw_scene(active_slot, selected_choice)
 
            if phase_frame_count < FRAME_EXAMPLE_fcs:
                draw_white_marker_local(
                    win,
                    pos=(-WIDTH // 2 + 120, -HEIGHT // 2 + 120),
                    size=(50, 50),
                )
 
            flip_time = win.flip()

            frame_timer(
                flip_time=flip_time,
                trial_index=None,
                task_type="food_check",
                phase="response"
            )
            frame_n += 1
            phase_frame_count += 1
 
            keys = kb.getKeys(["left", "right", "return", "escape"], waitRelease=False)
            for key in keys:
                if key.duration is not None:
                    continue
                k = key.name
 
                if k == "escape":
                    running = False
                    break
 
                elif k == "left":
                    selected_choice = max(0, selected_choice - 1)
 
                elif k == "right":
                    selected_choice = min(n_choices - 1, selected_choice + 1)
 
                elif k == "return":
                    if active_slot is None:
                        continue
 
                    chosen_name = choices[selected_choice]
 
                    # ── 정답 검증 ─────────────────────────────────────────────
                    is_correct = chosen_name in slot_valid[active_slot]
 
                    # 피식자 슬롯이 2개인 경우: 짝꿍 슬롯과 같은 동물이면 오답
                    if is_correct and n_slots == 3 and active_slot in [1, 2]:
                        sibling = 2 if active_slot == 1 else 1
                        if slot_filled[sibling] and slot_content[sibling] == chosen_name:
                            is_correct = False
 
                    results.append({
                        "phase":        phase_def["name"],
                        "animal":       chosen_name,
                        "slot_idx":     active_slot,
                        "correct":      is_correct,
                        "rt_sec":       round(clock.getTime(), 3),
                        "rt_frames":    frame_n - trial_start_frame,
                    })
 
                    pending_slot = active_slot
                    pending_name = chosen_name
                    feedback_is_correct = is_correct
                    feedback_state["slot"]   = active_slot
                    feedback_state["choice"] = selected_choice
                    feedback_state["color"]  = "green" if is_correct else "red"
 
                    phase_mode        = "feedback"
                    phase_frame_count = 0
 
            if not running:
                break
 
        # ── 피드백 단계 ───────────────────────────────────────────────────────
        elif phase_mode == "feedback":
            if phase_frame_count == 0:
                win.callOnFlip(send_trigger, handle, TRIG_F_CHECK_RESPOND)
            elif phase_frame_count == 1:
                win.callOnFlip(reset_trigger, handle)
 
            draw_scene(pending_slot, selected_choice)
 
            if phase_frame_count < FRAME_EXAMPLE_fcf:
                draw_white_marker_local(
                    win,
                    pos=(-WIDTH // 2 + 120, -HEIGHT // 2 + 120),
                    size=(50, 50),
                )
 
            flip_time = win.flip()

            frame_timer(
                flip_time=flip_time,
                trial_index=None,
                task_type="food_check",
                phase="feedback"
            )
            frame_n += 1
            phase_frame_count += 1
 
            if phase_frame_count >= FEEDBACK_FRAMES:
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
 
                # 모든 슬롯 완료 확인
                if all(slot_filled):
                    phase_mode        = "done"
                    phase_frame_count = 0
                else:
                    phase_mode        = "wait_response"
                    phase_frame_count = 0
 
        # ── 완료 단계 ─────────────────────────────────────────────────────────
        elif phase_mode == "done":
            draw_scene(None, selected_choice)
            flip_time = win.flip()

            frame_timer(
                flip_time=flip_time,
                trial_index=None,
                task_type="food_check",
                phase="done"
            )
            frame_n += 1
            phase_frame_count += 1
 
            if phase_frame_count >= DONE_FRAMES:
                running = False
 
    return results
 
 
# ── 메인 태스크 함수 ──────────────────────────────────────────────────────────
def run_food_task(win,handle):
    """
    동물 먹이사슬 태스크 실행 (3페이즈).
    win: 메인에서 이미 생성된 psychopy.visual.Window 객체
    """
    kb = keyboard.Keyboard()
 
    # web.json 로드 (food_edges 참조용)
    with open(JSON_PATH, encoding="utf-8") as f:
        web_data = json.load(f)
    food_edges = web_data.get("food_edges", [])
    all_animals = web_data.get("animals", [])
 
    all_results = []
 
    # 페이즈 순서를 매 실행마다 랜덤하게 섞기
    shuffled_phases = list(PHASES)
    random.shuffle(shuffled_phases)
 
    for phase_def in shuffled_phases:
        # 페이즈 간 짧은 공백 (0.5초)
        for _ in range(int(0.5 * FPS)):
            flip_time = win.flip()

            frame_timer(
                flip_time=flip_time,
                trial_index=None,
                task_type="food_check",
                phase="isi"
            )
 
        phase_results = run_phase(win, kb, phase_def, food_edges, all_animals,handle)
        all_results.extend(phase_results)
 
    return all_results
 