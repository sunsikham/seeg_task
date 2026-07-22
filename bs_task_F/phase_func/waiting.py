import random
from psychopy import core, event
from config import ISI_MAX_S, ISI_MIN_S, seconds_to_frames
from sys_func.frame_count import frame_timer, reset_frame_timer

def random_isi_phase(win, min_time=ISI_MIN_S, max_time=ISI_MAX_S):
    """
    지정된 범위를 144 Hz 프레임 수로 변환해 빈 화면을 보여주는 함수.
    """
    min_frames = seconds_to_frames(min_time)
    max_frames = seconds_to_frames(max_time)
    wait_frames = random.randint(min_frames, max_frames)

    reset_frame_timer()

    for _ in range(wait_frames):
        flip_time = win.flip()
        frame_timer(
            flip_time=flip_time,
            task_type="isi",
            phase="blank",
        )
        if "escape" in event.getKeys(keyList=["escape"]):
            core.quit()

    reset_frame_timer()

    event.clearEvents()
