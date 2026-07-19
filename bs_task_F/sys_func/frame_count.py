global prev_flip_time

prev_flip_time = None

frame_log = []

prev_flip_time = None
frame_count = 0


def frame_timer(
    flip_time,
    trial_index=None,
    task_type=None,
    phase=None,

):

    global prev_flip_time
    global frame_log

    if prev_flip_time is None:
        dt = 0
    else:
        dt = flip_time - prev_flip_time

   

    frame_log.append({
        "trial_index": trial_index,
        "task_type": task_type,
        "phase": phase,
        "flip_time": flip_time,
        "frame_duration": dt,
    })

    prev_flip_time = flip_time