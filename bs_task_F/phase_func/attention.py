import json
import os
from psychopy import visual, core, event
from sys_func.frame_count import frame_timer

def attention_check(win):

    text = visual.TextStim(
        win,
        text="Attention check\n\nPress ENTER to continue",
        height=40,
        color="white"
    )

    while True:
        text.draw()
        flip_time = win.flip()
        frame_timer(flip_time)

        keys = event.getKeys()

        if "return" in keys:   # Enter key
            break