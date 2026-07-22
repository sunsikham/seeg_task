import os

import pandas as pd
from psychopy import visual

from config import (
    MODE,
    NEON_APRILTAG_POSITIONS,
    NEON_APRILTAG_SIZE,
    NEON_DISCOVERY_TIMEOUT_S,
    NEON_RETRY_INTERVAL_S,
    NEON_SHUTDOWN_FLUSH_TIMEOUT_S,
    REFRESH_RATE_TOLERANCE_HZ,
    SESSION_TYPE,
    STIMULI_DIR,
    TARGET_REFRESH_HZ,
    USE_NEON,
)
from initiate import initiate
from phase_func.both_question import run_both_task
from phase_func.fixation import attention_check
from phase_func.show_info import (
    show_all_food_phase,
    show_all_gene_phase,
    show_all_habitat_phase,
)
from phase_func.test_food import run_food_task
from phase_func.test_gene import run_gene_task
from phase_func.test_habitat import run_habitat_task
from save_func.save_results import (
    save_check_results_to_excel,
    save_results_to_excel,
)
from sys_func.frame_count import frame_log
from utils.labjack_trigger import close_labjack, trigger_timing_log
from utils.neon_client import LOG_COLUMNS, NeonEventClient, NullNeonClient


def save_diagnostic_logs(save_directory, neon_event_log=None):
    diagnostic_logs = (
        (frame_log, "frame_log.xlsx"),
        (trigger_timing_log, "trigger_timing_log.xlsx"),
        (neon_event_log if neon_event_log is not None else [], "neon_event_log.xlsx"),
    )

    for log_data, filename in diagnostic_logs:
        save_path = os.path.join(save_directory, filename)
        try:
            columns = LOG_COLUMNS if filename == "neon_event_log.xlsx" else None
            pd.DataFrame(log_data, columns=columns).to_excel(save_path, index=False)
            print(f"[Diagnostics] saved: {save_path}")
        except Exception as exc:
            print(f"[Diagnostics] failed to save {filename}: {exc}")


def save_display_metadata(save_directory, actual_refresh_hz):
    metadata_path = os.path.join(save_directory, "metadata.txt")
    with open(metadata_path, "a", encoding="utf-8") as metadata_file:
        metadata_file.write(f"Actual Refresh Hz: {actual_refresh_hz:.2f}\n")


def save_neon_metadata(save_directory, recording_id):
    metadata_path = os.path.join(save_directory, "metadata.txt")
    recording_value = recording_id or ("UNAVAILABLE" if USE_NEON else "DISABLED")
    with open(metadata_path, "a", encoding="utf-8") as metadata_file:
        metadata_file.write(f"Neon Recording ID: {recording_value}\n")


def create_neon_apriltags(win):
    if not USE_NEON:
        return []

    try:
        from psychopy_eyetracker_pupil_labs.pupil_labs.stimuli import AprilTagStim
    except ImportError as exc:
        raise RuntimeError(
            "Neon support is enabled, but psychopy-eyetracker-pupil-labs is not installed."
        ) from exc

    tags = []
    for marker_id, pos in enumerate(NEON_APRILTAG_POSITIONS):
        tag = AprilTagStim(
            win=win,
            marker_id=marker_id,
            units="height",
            pos=pos,
            size=(NEON_APRILTAG_SIZE, NEON_APRILTAG_SIZE),
            interpolate=False,
            autoLog=False,
        )
        tag.setAutoDraw(True)
        tags.append(tag)
    return tags


def _active_domains():
    domains_by_mode = {
        0: ("food", "gene", "habitat"),
        1: ("gene", "habitat"),
        2: ("food", "habitat"),
        3: ("food", "gene"),
    }
    try:
        return domains_by_mode[MODE]
    except KeyError as exc:
        raise ValueError(f"Unsupported MODE: {MODE}") from exc


def _show_active_info(win, handle, neon_client):
    show_functions = {
        "food": show_all_food_phase,
        "gene": show_all_gene_phase,
        "habitat": show_all_habitat_phase,
    }
    for domain in _active_domains():
        show_functions[domain](win, handle, neon_client=neon_client)


def _run_confirmation_tasks(
    win,
    handle,
    neon_client,
    save_directory,
    session_id,
    neon_recording_id,
):
    check_functions = {
        "food": run_food_task,
        "gene": run_gene_task,
        "habitat": run_habitat_task,
    }

    for domain in _active_domains():
        # Preserve the existing learning refresh before each domain check.
        _show_active_info(win, handle, neon_client)
        results = check_functions[domain](
            win,
            handle,
            neon_client=neon_client,
        )
        save_check_results_to_excel(
            results,
            domain,
            save_directory,
            f"results_{domain}_check.xlsx",
            session_id=session_id,
            neon_recording_id=neon_recording_id,
        )


def run_experiment(
    save_directory,
    handle,
    neon_client,
    session_id,
    neon_recording_id,
):
    win = None
    experiment_completed = False

    try:
        win = visual.Window(
            size=(1280, 800),
            fullscr=True,
            units="pix",
            color="lightgray",
        )
        # Keep strong references for the lifetime of the window.
        apriltags = create_neon_apriltags(win)

        actual_refresh_hz = win.getActualFrameRate()
        if actual_refresh_hz is None:
            raise RuntimeError(
                "모니터 주사율을 안정적으로 측정하지 못했습니다. "
                "실험을 시작하지 않습니다."
            )
        if abs(actual_refresh_hz - TARGET_REFRESH_HZ) > REFRESH_RATE_TOLERANCE_HZ:
            raise RuntimeError(
                f"모니터 주사율이 {actual_refresh_hz:.2f} Hz로 측정되었습니다. "
                f"{TARGET_REFRESH_HZ} Hz로 설정한 뒤 다시 실행하세요."
            )

        print(f"[Session] type: {SESSION_TYPE}")
        print(f"[Display] refresh rate: {actual_refresh_hz:.2f} Hz")
        print(f"[Neon] AprilTags active: {len(apriltags)}")
        save_display_metadata(save_directory, actual_refresh_hz)

        neon_client.enqueue_event(
            "EXPERIMENT_START",
            metadata={"task_type": "experiment", "phase": "start"},
        )

        food_json_path = os.path.join(STIMULI_DIR, "trial_list2.json")
        gene_json_path = os.path.join(STIMULI_DIR, "trial_list1.json")
        habitat_json_path = os.path.join(STIMULI_DIR, "trial_list3.json")

        _run_confirmation_tasks(
            win,
            handle,
            neon_client,
            save_directory,
            session_id,
            neon_recording_id,
        )

        attention_check(win)

        def save_completed_trials(completed_results):
            save_results_to_excel(
                completed_results,
                save_directory,
                "results_t.xlsx",
                session_id=session_id,
                neon_recording_id=neon_recording_id,
            )

        results = run_both_task(
            win=win,
            food_json_path=food_json_path,
            gene_json_path=gene_json_path,
            habitat_json_path=habitat_json_path,
            handle=handle,
            neon_client=neon_client,
            on_trial_complete=save_completed_trials,
        )
        print(results)

        neon_client.enqueue_event(
            "EXPERIMENT_END",
            metadata={"task_type": "experiment", "phase": "end"},
        )
        experiment_completed = True
    finally:
        if not experiment_completed:
            neon_client.enqueue_event(
                "EXPERIMENT_ABORT",
                metadata={"task_type": "experiment", "phase": "abort"},
            )
        if win is not None:
            win.close()


def main():
    save_directory = None
    handle = None
    neon_client = None

    try:
        save_directory, handle, subject_id, session_id = initiate()
        if USE_NEON:
            neon_client = NeonEventClient(
                discovery_timeout_s=NEON_DISCOVERY_TIMEOUT_S,
                retry_interval_s=NEON_RETRY_INTERVAL_S,
            )
        else:
            neon_client = NullNeonClient()

        try:
            neon_recording_id = neon_client.start_session(subject_id, session_id)
        except Exception:
            save_neon_metadata(save_directory, None)
            raise
        save_neon_metadata(save_directory, neon_recording_id)
        run_experiment(
            save_directory,
            handle,
            neon_client,
            session_id,
            neon_recording_id,
        )
    finally:
        try:
            if neon_client is not None:
                flushed = neon_client.close(NEON_SHUTDOWN_FLUSH_TIMEOUT_S)
                if not flushed:
                    print(
                        "[Neon] Some events were not sent before the shutdown "
                        "flush timeout. Check neon_event_log.xlsx."
                    )
        finally:
            try:
                if save_directory is not None:
                    neon_log = neon_client.event_log if neon_client is not None else []
                    save_diagnostic_logs(save_directory, neon_log)
            finally:
                close_labjack(handle)


if __name__ == "__main__":
    main()
