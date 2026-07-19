# LabJack T4 TTL 트리거 유틸리티

# 핀 구성 (총 9라인):
#   EIO0~EIO7 (8핀) : 트리거 코드값 (8비트 데이터)
#   CIO0       (1핀) : trigger latch (strobe) — Natus Quantum이 rising edge에서 데이터 캡처


try:
    from labjack import ljm
    _LJM_AVAILABLE = True
except ImportError:
    _LJM_AVAILABLE = False

import time

trigger_timing_log = []
_active_trigger_entry = None
_next_trigger_sequence = 1

# Trigger latch 핀: CIO0 (CIO_STATE 비트 0)
_LATCH_CIO_STATE = 0x01  # CIO0 = HIGH
_EIO_TO_LATCH_DELAY_US = 2000


# ============================================================================
# 트리거 코드 상수
# ============================================================================

TRIG_RESET            = 0

# =========================================
# check trial
# =========================================

TRIG_F_CHECK_START      = 10
TRIG_F_CHECK_RESPOND    = 11
TRIG_G_CHECK_START      = 12
TRIG_G_CHECK_RESPOND    = 13
TRIG_H_CHECK_START      = 14
TRIG_H_CHECK_RESPOND    = 15


# =========================================
# main belief trial
# =========================================

TRIG_B_START          = 20
TRIG_B_RESPOND        = 21
TRIG_B_WRONGRESPOND        = 22
TRIG_B_SELECTSTART          = 23



# =========================================
# stimulus presentation
# =========================================

TRIG_FOOD_SHOW        = 30
TRIG_FOOD_SHOW_R      = 31

TRIG_GENE_SHOW        = 32
TRIG_GENE_SHOW_R      = 33

TRIG_HABITAT_SHOW     = 34
TRIG_HABITAT_SHOW_R   = 35

# =========================================
# trial boundary
# =========================================

TRIG_TRIAL_START      = 0x40
TRIG_TRIAL_END        = 0x41




# ============================================================================
# 연결 관리
# ============================================================================

def init_labjack(device: str = "T4",
                 connection: str = "USB",
                 identifier: str = "ANY") -> int | None:
    # LabJack T4 연결
    if not _LJM_AVAILABLE:
        print("[LabJack] ljm 라이브러리를 찾을 수 없습니다. 트리거가 비활성화됩니다.")
        return None

    try:
        handle = ljm.openS(device, connection, identifier)
        info   = ljm.getHandleInfo(handle)
        print(f"[LabJack] 연결 성공: {info}")

        # EIO 핀 초기화 (8비트 데이터 라인)
        #ljm.eWriteName(handle, "EIO_INHIBIT",   0)     # 출력 활성화 (기본값이지만 명시적으로 설정)
        ljm.eWriteName(handle, "EIO_DIRECTION", 0xFF)  # 모든 EIO 핀 출력
        ljm.eWriteName(handle, "EIO_STATE",     0)     # 초기값 0

        # CIO 핀 초기화 (CIO0 = trigger latch)
        #ljm.eWriteName(handle, "CIO_INHIBIT",   0)     # 출력 활성화
        ljm.eWriteName(handle, "CIO_DIRECTION", 0x0F)  # CIO0~3 모두 출력
        ljm.eWriteName(handle, "CIO_STATE",     0)     # 초기값 0 (latch LOW)

        print("[LabJack] EIO(데이터 8핀) + CIO0(trigger latch) 초기화 완료")
        return handle

    except Exception as e:
        print(f"[LabJack] 연결 실패: {e}")
        return None


def close_labjack(handle: int | None):
    if handle is None or not _LJM_AVAILABLE:
        return
    try:
        ljm.eWriteName(handle, "CIO_STATE", 0)
        ljm.eWriteName(handle, "EIO_STATE", 0)
        ljm.close(handle)
        print("[LabJack] 연결 종료")
    except Exception as e:
        print(f"[LabJack] 종료 오류: {e}")


# ============================================================================
# 트리거 전송
# ============================================================================

def send_trigger(handle: int | None, code: int):
    """EIO 코드를 설정하고 2 ms 뒤 CIO0(latch)를 HIGH로 올립니다.

    전송 순서:
      EIO_STATE = code  →  장치 내부 2 ms 대기  →  CIO0(latch) HIGH
    CIO0 LOW와 EIO 초기화는 다음 프레임의 reset_trigger()가 수행합니다.
    Natus Quantum은 CIO0의 rising edge에서 EIO 데이터를 캡처한다.
    """
    global _active_trigger_entry
    global _next_trigger_sequence

    if _active_trigger_entry is not None:
        _active_trigger_entry["reset_success"] = False
        _active_trigger_entry["reset_error"] = (
            "reset_trigger was not called before the next trigger"
        )
        _active_trigger_entry = None

    started_at = time.perf_counter()
    success = False
    error_message = ""

    entry = {
        "trigger_sequence": _next_trigger_sequence,
        "trigger_code": int(code),
        "send_started_perf_counter": started_at,
        "send_finished_perf_counter": None,
        "send_duration_ms": None,
        "send_success": False,
        "send_error": "",
        "reset_started_perf_counter": None,
        "reset_finished_perf_counter": None,
        "reset_duration_ms": None,
        "reset_success": None,
        "reset_error": "",
        "send_start_to_reset_start_ms": None,
    }
    _next_trigger_sequence += 1
    trigger_timing_log.append(entry)
    _active_trigger_entry = entry

    try:
        if handle is None or not _LJM_AVAILABLE:
            error_message = "LabJack unavailable"
        else:
            names = ["EIO_STATE", "WAIT_US_BLOCKING", "CIO_STATE"]
            values = [int(code), _EIO_TO_LATCH_DELAY_US, _LATCH_CIO_STATE]
            ljm.eWriteNames(handle, len(names), names, values)
            success = True
    except Exception as e:
        error_message = str(e)
        print(f"[LabJack] 트리거 전송 오류 (code={code}): {e}")
    finally:
        finished_at = time.perf_counter()
        entry.update({
            "send_finished_perf_counter": finished_at,
            "send_duration_ms": (finished_at - started_at) * 1000.0,
            "send_success": success,
            "send_error": error_message,
        })


def send_trigger_async(handle: int | None, code: int):
    """EIO_STATE + CIO0(latch) 설정 (비블로킹). 리셋은 호출자가 reset_trigger()로 처리."""
    if handle is None or not _LJM_AVAILABLE:
        return
    try:
        ljm.eWriteName(handle, "EIO_STATE", int(code))
        ljm.eWriteName(handle, "CIO_STATE", _LATCH_CIO_STATE)  # latch HIGH
    except Exception as e:
        print(f"[LabJack] 비동기 트리거 오류 (code={code}): {e}")


def reset_trigger(handle: int | None):
    """CIO0(latch)를 LOW로 내리고 EIO_STATE를 0으로 리셋하고 결과를 기록합니다."""
    global _active_trigger_entry

    started_at = time.perf_counter()
    success = False
    error_message = ""

    if handle is None or not _LJM_AVAILABLE:
        error_message = "LabJack unavailable"
    else:
        try:
            names = ["CIO_STATE", "EIO_STATE"]
            values = [0, 0]
            ljm.eWriteNames(handle, len(names), names, values)
            success = True
        except Exception as e:
            error_message = str(e)
            print(f"[LabJack] 리셋 오류: {e}")
    finished_at = time.perf_counter()

    if _active_trigger_entry is None:
        trigger_timing_log.append({
            "trigger_sequence": None,
            "trigger_code": None,
            "send_started_perf_counter": None,
            "send_finished_perf_counter": None,
            "send_duration_ms": None,
            "send_success": None,
            "send_error": "orphan reset without an active trigger",
            "reset_started_perf_counter": started_at,
            "reset_finished_perf_counter": finished_at,
            "reset_duration_ms": (finished_at - started_at) * 1000.0,
            "reset_success": success,
            "reset_error": error_message,
            "send_start_to_reset_start_ms": None,
        })
        return

    send_started_at = _active_trigger_entry["send_started_perf_counter"]
    _active_trigger_entry.update({
        "reset_started_perf_counter": started_at,
        "reset_finished_perf_counter": finished_at,
        "reset_duration_ms": (finished_at - started_at) * 1000.0,
        "reset_success": success,
        "reset_error": error_message,
        "send_start_to_reset_start_ms": (
            (started_at - send_started_at) * 1000.0
        ),
    })
    _active_trigger_entry = None
