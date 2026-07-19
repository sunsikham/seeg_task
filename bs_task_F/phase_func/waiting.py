import random
from psychopy import core, event
from sys_func.frame_count import frame_timer, reset_frame_timer

def random_isi_phase(win, min_time=0.75, max_time=1.0):
    """
    지정된 범위 내에서 무작위 시간 동안 빈 화면을 보여주는 함수.
    """
    # 1. min_time과 max_time 사이의 랜덤한 소수 생성
    wait_time = random.uniform(min_time, max_time)

    reset_frame_timer()
    
    # 2. 화면을 비우고 flip
    flip_time = win.flip()
    frame_timer(flip_time)
    
    # 3. 계산된 랜덤 시간만큼 대기
    core.wait(wait_time)
    reset_frame_timer()
    
    # 4. 대기 중 눌린 키보드 입력을 삭제 (다음 루프에 영향 없도록)
    event.clearEvents()