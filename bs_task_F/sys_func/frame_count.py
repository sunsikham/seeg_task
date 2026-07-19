EXPECTED_REFRESH_HZ = 60.0
EXPECTED_FRAME_DURATION_S = 1.0 / EXPECTED_REFRESH_HZ
FRAME_DROP_THRESHOLD_S = EXPECTED_FRAME_DURATION_S * 1.2

frame_log = []
prev_flip_time = None
prev_context = None


def reset_frame_timer():
    """의도적인 대기 전후에는 다음 flip을 새 측정 구간으로 시작한다."""
    global prev_flip_time
    global prev_context

    prev_flip_time = None
    prev_context = None


def frame_timer(
    flip_time,
    trial_index=None,
    task_type=None,
    phase=None,
):
    global prev_flip_time
    global prev_context

    context = (trial_index, task_type, phase)

    if prev_flip_time is None:
        dt = 0.0
        frame_checked = False
    else:
        dt = flip_time - prev_flip_time
        same_context = context == prev_context
        same_trial = (
            trial_index is not None
            and prev_context is not None
            and trial_index == prev_context[0]
        )
        frame_checked = same_context or same_trial

    is_dropped = frame_checked and dt > FRAME_DROP_THRESHOLD_S
    estimated_dropped_frames = 0
    if is_dropped:
        estimated_dropped_frames = max(
            1,
            round(dt / EXPECTED_FRAME_DURATION_S) - 1,
        )

    frame_log.append({
        "trial_index": trial_index,
        "task_type": task_type,
        "phase": phase,
        "flip_time": flip_time,
        "frame_duration": dt,
        "expected_refresh_hz": EXPECTED_REFRESH_HZ,
        "expected_frame_duration": EXPECTED_FRAME_DURATION_S,
        "drop_threshold": FRAME_DROP_THRESHOLD_S,
        "frame_checked": frame_checked,
        "is_dropped": is_dropped,
        "estimated_dropped_frames": estimated_dropped_frames,
    })

    prev_flip_time = flip_time
    prev_context = context