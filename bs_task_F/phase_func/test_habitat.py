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


SLOT_POS = [
    (-350,  350),   # 0: 소
    (   0,  350),   # 1: 흑곰
    ( 350,  350),   # 2: 양
    (-350,  150),   # 3: 여우
    (-350,  -50),   # 4: 쥐
    ( 350,  -50),   # 5: 고슴도치
]
SLOT_LABELS = ["소", "흑곰", "양", "여우", "쥐", "고슴도치"]
 
BG_POS        = (0, 160)
BG_SIZE_RATIO = (0.7, 0.7)


"""

from utils.labjack_trigger import send_trigger, reset_trigger,  TRIG_H_CHECK_START, TRIG_H_CHECK_RESPOND
from config import WAITING,HEIGHT,WIDTH, HANDLE,FRAME_EXAMPLE_hcs,FRAME_EXAMPLE_hcf
from phase_func.show_info import  show_all_habitat_phase
from sys_func.frame_count import frame_timer
 
import json, random, os, csv, datetime
from psychopy import visual, core, event
from psychopy.hardware import keyboard
 
# ── 경로 설정 ─────────────────────────────────────────────────────────────────
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR  = os.path.dirname(SCRIPT_DIR)
STIMULI_DIR = os.path.join(PARENT_DIR, "stimuli")
JSON_PATH   = os.path.join(STIMULI_DIR, "web.json")
BG_IMAGE    = os.path.join(STIMULI_DIR, "서식지체크.png")
FONT        = "Malgun Gothic"
 
if not os.path.isdir(STIMULI_DIR):
    raise FileNotFoundError(f"stimuli 폴더 없음: {STIMULI_DIR}")
 
# ── 프레임 설정 ───────────────────────────────────────────────────────────────
FPS             = 60
FEEDBACK_FRAMES = int(0.6 * FPS)
DONE_FRAMES     = int(2.5 * FPS)
 
# ── 레이아웃 : 슬롯 (지도 위 빈칸) ──────────────────────────────────────────
SLOT_BOX_W = 190
SLOT_BOX_H = 170
 
# 빈칸 6개 중심 좌표 [소, 흑곰, 양, 여우, 쥐, 고슴도치]
# 서식지체크.png 위치에 맞춰 조정하세요
SLOT_POS = [
    (-350,  350),   # 0: 소
    (   0,  350),   # 1: 흑곰
    ( 350,  350),   # 2: 양
    (-350,  150),   # 3: 여우
    (-350,  -50),   # 4: 쥐
    ( 350,  -50),   # 5: 고슴도치
]
SLOT_LABELS = ["소", "흑곰", "양", "여우", "쥐", "고슴도치"]
 
BG_POS        = (0, 160)
BG_SIZE_RATIO = (0.7, 0.7)
 
# ── 레이아웃 : 하단 동물 선택 바 ────────────────────────────────────────────
ANIMAL_BAR_Y  = -370          # 동물 이미지 중심 Y
ANIMAL_IMG_W  = 110
ANIMAL_IMG_H  =  90
ANIMAL_LABEL_Y_OFFSET = -60  # 이미지 중심 아래 이름 텍스트 위치
GUIDE_POS = (0, -480)
 
# 동물 6개를 균등하게 가로 배치
def calc_animal_xs(n=6, spacing=190):
    total = spacing * (n - 1)
    return [round(-total / 2 + i * spacing) for i in range(n)]
 
ANIMAL_XS = calc_animal_xs()   # [-475, -285, -95, 95, 285, 475] 근사
 
 
# ── 헬퍼 ─────────────────────────────────────────────────────────────────────
def normalize(a):
    if isinstance(a, str):
        return {"name": a, "image": None}
    return {"name": a.get("name", str(a)), "image": a.get("image", None)}
 
 
def find_animal_image_path(animal):
    candidates = []
    if animal.get("image"):
        candidates.append(animal["image"])
    name = animal.get("name", "")
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        candidates.append(f"{name}{ext}")
    for fname in candidates:
        full = os.path.join(STIMULI_DIR, fname)
        if os.path.exists(full):
            return full
    return None
 
 
def draw_white_marker_local(win, pos, size):
    visual.Rect(win, pos=pos, width=size[0], height=size[1],
                fillColor="white", lineColor="white").draw()
 
 
# ── 메인 함수 ─────────────────────────────────────────────────────────────────
def run_habitat_task(win, handle):
    kb = keyboard.Keyboard()
 
    with open(JSON_PATH, encoding="utf-8") as f:
        web_data = json.load(f)
 
    # 동물 목록 — 순서를 랜덤으로 섞어서 하단 바에 배치
    all_animals = [normalize(a) for a in web_data["animals"]]
    random.shuffle(all_animals)          # 하단 바 표시 순서 랜덤
    N = len(all_animals)                 # 6
 
    # 배경
    bg = visual.ImageStim(
        win, image=BG_IMAGE, pos=BG_POS,
        size=(WIDTH * BG_SIZE_RATIO[0], HEIGHT * BG_SIZE_RATIO[1]),
    )
 
    def txt(text, pos, height=26, color="black", bold=False):
        return visual.TextStim(win, text=text, pos=pos, height=height,
                               color=color, font=FONT, bold=bold, languageStyle="LTR")
 
    def rect(pos, w, h, lineCol="black", fillCol=None, lw=2):
        return visual.Rect(win, pos=pos, width=w, height=h,
                           lineColor=lineCol, fillColor=fillCol, lineWidth=lw)
 
    def load_img(path, pos, size):
        if path and os.path.exists(path):
            return visual.ImageStim(win, image=path, pos=pos, size=size)
        return None
 
    # ── 슬롯 (지도 위 빈칸) ──────────────────────────────────────────────────
    slot_rects = [
        rect(pos, SLOT_BOX_W, SLOT_BOX_H, lineCol="black", fillCol="white", lw=2)
        for pos in SLOT_POS
    ]
    slot_label_stims = [
        txt(lbl, (pos[0], pos[1] - SLOT_BOX_H // 2 - 25), height=22, color="black")
        for lbl, pos in zip(SLOT_LABELS, SLOT_POS)
    ]
 
    slot_animal = [None] * N   # 배치된 동물 dict
    slot_img    = [None] * N   # visual.ImageStim
    slot_filled = [False] * N
 
    # ── 하단 동물 선택 바 ────────────────────────────────────────────────────
    # 각 동물 이미지 / 이름 텍스트 / 선택 테두리
    bar_imgs  = []
    bar_names = []
    bar_rects = []   # 선택 강조 테두리
 
    for i, a in enumerate(all_animals):
        x = ANIMAL_XS[i]
        y = ANIMAL_BAR_Y
        img_path = find_animal_image_path(a)
        bar_imgs.append(load_img(img_path, (x, y), (ANIMAL_IMG_W, ANIMAL_IMG_H)))
        bar_names.append(txt(a["name"], (x, y + ANIMAL_LABEL_Y_OFFSET), height=22, color="black"))
        bar_rects.append(rect((x, y), ANIMAL_IMG_W + 10, ANIMAL_IMG_H + 10,
                              lineCol="black", fillCol=None, lw=2))
 
    # 배치 완료된 동물은 바에서 회색으로 처리 (placed 플래그)
    bar_placed = [False] * N   # True면 이미 배치됨 → 선택 불가 / 흐리게
 
    guide = txt(
        "← → : 동물 선택    Enter : 배치    Esc : 종료",
        GUIDE_POS, height=20, color="dimgray",
    )
 
    # ── 피드백 상태 ──────────────────────────────────────────────────────────
    feedback_state = {"slot": None, "color": None}
 
    # ── 그리기 ───────────────────────────────────────────────────────────────
    def draw_scene(cur_slot, cur_animal_idx, q_count):
        bg.draw()
 
        # 슬롯 (지도 위 빈칸)
        for i, (r, pos) in enumerate(zip(slot_rects, SLOT_POS)):
            # 현재 배치 대상 슬롯은 흰 테두리로 강조
            if i == feedback_state["slot"]:
                r.lineColor = feedback_state["color"]
                r.lineWidth = 6
            elif i == cur_slot:
                r.lineColor = "orange"
                r.lineWidth = 4
            else:
                r.lineColor = "black"
                r.lineWidth = 2
            r.draw()
 
            if slot_img[i] is not None:
                slot_img[i].draw()
            elif slot_animal[i] is not None:
                txt(slot_animal[i]["name"], pos, height=22, color="blue").draw()
 
        #for lbl in slot_label_stims:
            #lbl.draw()
 
        # 하단 동물 바
        for i in range(N):
            r = bar_rects[i]
            if bar_placed[i]:
                # 이미 배치된 동물: 회색 테두리
                r.lineColor = "lightgray"
                r.lineWidth = 1
            elif i == cur_animal_idx:
                # 현재 선택 중인 동물: 노란 테두리
                r.lineColor = "orange"
                r.lineWidth = 5
            else:
                r.lineColor = "black"
                r.lineWidth = 2
            r.draw()
 
            if bar_imgs[i] is not None:
                opacity = 0.3 if bar_placed[i] else 1.0
                bar_imgs[i].opacity = opacity
                bar_imgs[i].draw()
            else:
                color = "lightgray" if bar_placed[i] else "black"
                txt(all_animals[i]["name"],
                    (ANIMAL_XS[i], ANIMAL_BAR_Y), height=28, color=color).draw()
 
            bar_names[i].color = "lightgray" if bar_placed[i] else "black"
            bar_names[i].draw()
 
        # 완료 메시지
        if q_count >= N:
            txt("완료!", (0, 0), height=48, color="darkgreen", bold=True).draw()
 
        guide.draw()
 
    # ── 루프 상태 초기화 ─────────────────────────────────────────────────────
    cur_slot       = 0    # 현재 배치할 슬롯 (고정 표시)
    cur_animal_idx = 0    # 하단 바에서 현재 선택 중인 동물 인덱스
    q_count        = 0    # 완료된 배치 수
    results        = []
    clock          = core.Clock()
    frame_n        = 0
    trial_start_frame = 0
    phase             = "wait_response"
    phase_frame_count = 0
    feedback_is_correct = False
    pending_slot        = 0
    pending_animal      = None
    wrong_count = 0
 
    running = True
 
    while running:
 
        # ── 응답 대기 ────────────────────────────────────────────────────────
        if phase == "wait_response":
 
            if phase_frame_count == 0:
                win.callOnFlip(send_trigger, handle, TRIG_H_CHECK_START)
            elif phase_frame_count == 1:
                win.callOnFlip(reset_trigger, handle)
 
            draw_scene(cur_slot, cur_animal_idx, q_count)
 
            if phase_frame_count < FRAME_EXAMPLE_hcs:
                draw_white_marker_local(
                    win,
                    pos=(-WIDTH // 2 + 120, -HEIGHT // 2 + 120),
                    size=(50, 50),
                )
 
            flip_time = win.flip()

            frame_timer(
                flip_time=flip_time,
                trial_index=None,
                task_type="habitat_check",
                phase="response"
            )
            frame_n += 1
            phase_frame_count += 1
 
            keys = kb.getKeys(
                ["left", "right", "up", "down", "return", "escape"],
                waitRelease=False,
            )
            for key in keys:
                if key.duration is not None:
                    continue
                k = key.name
 
                if k == "escape":
                    running = False; break
 
                elif k == "left":
                    # 하단 바에서 왼쪽으로 이동 (배치된 건 건너뜀)
                    nxt = (cur_animal_idx - 1) % N
                    while bar_placed[nxt] and nxt != cur_animal_idx:
                        nxt = (nxt - 1) % N
                    if not bar_placed[nxt]:
                        cur_animal_idx = nxt
 
                elif k == "right":
                    # 하단 바에서 오른쪽으로 이동 (배치된 건 건너뜀)
                    nxt = (cur_animal_idx + 1) % N
                    while bar_placed[nxt] and nxt != cur_animal_idx:
                        nxt = (nxt + 1) % N
                    if not bar_placed[nxt]:
                        cur_animal_idx = nxt
 
                elif k == "up":
                    # 슬롯 순환 선택 (위로)
                    cur_slot = (cur_slot - 1) % N
 
                elif k == "down":
                    # 슬롯 순환 선택 (아래로)
                    cur_slot = (cur_slot + 1) % N
 
                elif k == "return":
                    a = all_animals[cur_animal_idx]
                    if not bar_placed[cur_animal_idx] and not slot_filled[cur_slot]:
                        is_correct = (a["name"] == SLOT_LABELS[cur_slot])
                        results.append({
                            "animal":     a["name"],
                            "slot_idx":   cur_slot,
                            "slot_label": SLOT_LABELS[cur_slot],
                            "correct":    is_correct,
                            "rt_sec":     round(clock.getTime(), 3),
                            "rt_frames":  frame_n - trial_start_frame,
                        })
                        pending_animal      = a
                        pending_slot        = cur_slot
                        feedback_is_correct = is_correct
                        feedback_state["slot"]  = cur_slot
                        feedback_state["color"] = "green" if is_correct else "red"
                        phase = "feedback"
                        phase_frame_count = 0
 
            if not running:
                break
 
        # ── 피드백 ──────────────────────────────────────────────────────────
        elif phase == "feedback":
 
            if phase_frame_count == 0:
                win.callOnFlip(send_trigger, handle, TRIG_H_CHECK_RESPOND)
            elif phase_frame_count == 1:
                win.callOnFlip(reset_trigger, handle)
 
            draw_scene(cur_slot, cur_animal_idx, q_count)
 
            if phase_frame_count < FRAME_EXAMPLE_hcf:
                draw_white_marker_local(
                    win,
                    pos=(-WIDTH // 2 + 120, -HEIGHT // 2 + 120),
                    size=(50, 50),
                )
 
            flip_time = win.flip()

            frame_timer(
                flip_time=flip_time,
                trial_index=None,
                task_type="habitat_check",
                phase="feedback"
            )

            frame_n += 1
            phase_frame_count += 1
 
            if phase_frame_count >= FEEDBACK_FRAMES:
                feedback_state["slot"]  = None
                feedback_state["color"] = None
 
                if feedback_is_correct:
                    # 슬롯에 동물 확정 배치
                    slot_animal[pending_slot] = pending_animal
                    slot_filled[pending_slot] = True
                    slot_img[pending_slot] = load_img(
                        find_animal_image_path(pending_animal),
                        SLOT_POS[pending_slot],
                        (SLOT_BOX_W - 10, SLOT_BOX_H - 10),
                    )
                    # 하단 바에서 해당 동물 비활성
                    bar_placed[cur_animal_idx] = False
                    q_count += 1
                    clock.reset()
                    trial_start_frame = frame_n
 
                    # 다음 선택: 비어있는 슬롯 + 배치 안 된 동물로 이동
                    for i in range(N):
                        if not slot_filled[i]:
                            cur_slot = i; break
                    for i in range(N):
                        if not bar_placed[i]:
                            cur_animal_idx = i; break
                else:
                    clock.reset()
                    trial_start_frame = frame_n
                    wrong_count+=1

                    if wrong_count>=5:
                        event.clearEvents(eventType='keyboard')

                            
                        slot_animal = [None] * N   # 배치된 동물 dict
                        slot_img    = [None] * N   # visual.ImageStim
                        slot_filled = [False] * N
                        q_count=0
                            
                        show_all_habitat_phase(win, handle)
                        event.clearEvents(eventType='keyboard')
                        wrong_count=0
 
                pending_animal = None
                phase = "done" if q_count >= N else "wait_response"
                phase_frame_count = 0
 
        # ── 종료 화면 ────────────────────────────────────────────────────────
        elif phase == "done":
            draw_scene(cur_slot, cur_animal_idx, q_count)
            flip_time = win.flip()

            frame_timer(
                flip_time=flip_time,
                trial_index=None,
                task_type="habitat_check",
                phase="done"
            )
            frame_n += 1
            phase_frame_count += 1
            if phase_frame_count >= DONE_FRAMES:
                running = False
 
   
    return results
 