from psychopy import visual
from labjack import ljm   

def draw_white_marker(win, pos, size):
    # pos, size는 화면의 정규화된 위치와 크기 (1.0 = 전체화면)
    # 프레임에 넣은 수가 표시되는 프레임수 
    #pos 뒤에 윈도우 크기 곱해줘야됨 
    marker = visual.Rect(win, width=size[0], height=size[1], fillColor='white', lineColor='white', pos=pos, units="pix")
    
    marker.draw()

def trigger_on_flip(handle, duration=0.005):

    if handle is None:
        return

    return {
        "on": False,
        "off_time": None,
        "duration": duration
    }

def set_trigger(
    handle: int | None,
    code: int,
    *,
    round_num: int = 1,
    page: str = "",
    action: str = ""
):

    if handle is None:
        return


    ljm.eWriteNames(
        handle,
        2,
        ["EIO_STATE", "CIO_STATE"],
        [code, 1.0]
    )

    print(code)


def reset_trigger(handle: int | None):

    if handle is None:
        return

    try:
        ljm.eWriteNames(
            handle,
            2,
            ["EIO_STATE", "CIO_STATE"],
            [0.0, 0.0]
        )
        

    except Exception as e:
        print(f"[LabJack] 리셋 오류: {e}")