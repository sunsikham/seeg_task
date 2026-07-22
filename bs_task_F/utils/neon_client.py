"""Non-blocking Pupil Labs Neon event transport for PsychoPy tasks."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import queue
import threading
import time
from typing import Any, Callable


LOG_COLUMNS = (
    "event_sequence",
    "session_id",
    "subject_id",
    "recording_id",
    "task_type",
    "phase",
    "trial_index",
    "attempt_index",
    "event_name",
    "host_timestamp_unix_ns",
    "companion_timestamp_unix_ns",
    "clock_offset_ns",
    "send_attempt",
    "send_success",
    "retried",
    "send_error",
)

MAIN_PHASES = (
    "question",
    "premise",
    "option_left",
    "option_right",
    "choice",
)


def main_section_transition_events(trial_index: int, phase: str) -> tuple[str, ...]:
    """Return the paired Cloud boundary/identifier events for one main phase."""
    if phase not in MAIN_PHASES:
        raise ValueError(f"Unknown main phase: {phase}")
    events = []
    if phase != MAIN_PHASES[0]:
        events.append("MAIN_SECTION_END")
    events.extend(
        (
            "MAIN_SECTION_START",
            f"MAIN_T{trial_index:03d}_{phase.upper()}",
        )
    )
    return tuple(events)


@dataclass
class _PendingEvent:
    sequence: int
    event_name: str
    host_timestamp_unix_ns: int
    companion_timestamp_unix_ns: int
    clock_offset_ns: int
    metadata: dict[str, Any] = field(default_factory=dict)
    send_attempt: int = 0


def _default_discover_devices(timeout_s: float):
    try:
        from pupil_labs.realtime_api.simple import discover_devices
    except ImportError as exc:
        raise RuntimeError(
            "Neon support is enabled, but pupil-labs-realtime-api is not installed."
        ) from exc
    return discover_devices(timeout_s)


class NeonEventClient:
    """Queues precisely timestamped events and sends them off the flip thread."""

    enabled = True

    def __init__(
        self,
        *,
        discovery_timeout_s: float = 10.0,
        retry_interval_s: float = 1.0,
        discover_devices_fn: Callable[[float], list[Any]] | None = None,
    ):
        self.discovery_timeout_s = discovery_timeout_s
        self.retry_interval_s = retry_interval_s
        self._discover_devices_fn = discover_devices_fn or _default_discover_devices
        self._device = None
        self._recording_id: str | None = None
        self._subject_id: str | None = None
        self._session_id: str | None = None
        self._clock_offset_ns = 0
        self._next_sequence = 1
        self._queue: queue.Queue[_PendingEvent] = queue.Queue()
        self._stop_requested = threading.Event()
        self._worker: threading.Thread | None = None
        self._log_lock = threading.Lock()
        self._event_log: list[dict[str, Any]] = []
        self._occurrences: Counter[str] = Counter()

    @property
    def recording_id(self) -> str | None:
        return self._recording_id

    @property
    def event_log(self) -> list[dict[str, Any]]:
        with self._log_lock:
            return [dict(row) for row in self._event_log]

    def next_occurrence(self, key: str) -> int:
        self._occurrences[key] += 1
        return self._occurrences[key]

    def _discover_one(self):
        devices = list(self._discover_devices_fn(self.discovery_timeout_s))
        if not devices:
            raise RuntimeError(
                "Neon Companion을 찾지 못했습니다. 휴대폰과 PC의 네트워크를 확인하세요."
            )
        if len(devices) != 1:
            names = [getattr(device, "phone_name", "unknown") for device in devices]
            for device in devices:
                try:
                    device.close()
                except Exception:
                    pass
            raise RuntimeError(
                "Neon 장치가 여러 대 발견되었습니다. 한 대만 연결하세요: "
                + ", ".join(names)
            )
        return devices[0]

    def _refresh_clock_offset(self) -> None:
        estimate = self._device.estimate_time_offset()
        if estimate is None:
            raise RuntimeError("Neon Companion이 시간 동기화를 지원하지 않습니다.")
        self._clock_offset_ns = round(estimate.time_offset_ms.mean * 1_000_000)

    def start_session(self, subject_id: str, session_id: str) -> str:
        self._subject_id = subject_id
        self._session_id = session_id
        self._device = self._discover_one()
        self._refresh_clock_offset()

        event_name = f"SESSION_START_{subject_id}_{session_id}"
        host_timestamp_ns = time.time_ns()
        companion_timestamp_ns = host_timestamp_ns - self._clock_offset_ns
        start_event = _PendingEvent(
            sequence=self._next_sequence,
            event_name=event_name,
            host_timestamp_unix_ns=host_timestamp_ns,
            companion_timestamp_unix_ns=companion_timestamp_ns,
            clock_offset_ns=self._clock_offset_ns,
            metadata={"task_type": "session", "phase": "start"},
            send_attempt=1,
        )
        try:
            event = self._device.send_event(
                event_name,
                event_timestamp_unix_ns=companion_timestamp_ns,
            )
        except Exception as exc:
            self._append_log(
                start_event,
                success=False,
                error=str(exc),
                recording_id=None,
            )
            self._next_sequence += 1
            self._close_device()
            raise RuntimeError("Neon SESSION_START event transmission failed.") from exc

        recording_id = getattr(event, "recording_id", None)
        if not recording_id:
            self._append_log(
                start_event,
                success=False,
                error="No active Neon recording",
                recording_id=None,
            )
            self._next_sequence += 1
            self._close_device()
            raise RuntimeError(
                "Neon 녹화가 활성화되지 않았습니다. Companion에서 녹화를 시작하세요."
            )

        self._recording_id = str(recording_id)
        self._append_log(
            start_event,
            success=True,
            error="",
            recording_id=self._recording_id,
        )
        self._next_sequence += 1
        self._worker = threading.Thread(
            target=self._worker_loop,
            name="neon-event-worker",
            daemon=True,
        )
        self._worker.start()
        return self._recording_id

    def call_on_flip(self, win, event_names: str | list[str] | tuple[str, ...], **metadata):
        """Schedule one or more events with one shared flip-adjacent timestamp."""
        win.callOnFlip(self.enqueue_events, event_names, metadata=metadata)

    def enqueue_event(
        self,
        event_name: str,
        metadata: dict[str, Any] | None = None,
        host_timestamp_unix_ns: int | None = None,
    ) -> None:
        self.enqueue_events(
            (event_name,),
            metadata=metadata,
            host_timestamp_unix_ns=host_timestamp_unix_ns,
        )

    def enqueue_events(
        self,
        event_names: str | list[str] | tuple[str, ...],
        metadata: dict[str, Any] | None = None,
        host_timestamp_unix_ns: int | None = None,
    ) -> None:
        if isinstance(event_names, str):
            event_names = (event_names,)
        timestamp_ns = host_timestamp_unix_ns or time.time_ns()
        metadata = dict(metadata or {})
        for event_name in event_names:
            pending = _PendingEvent(
                sequence=self._next_sequence,
                event_name=event_name,
                host_timestamp_unix_ns=timestamp_ns,
                companion_timestamp_unix_ns=timestamp_ns - self._clock_offset_ns,
                clock_offset_ns=self._clock_offset_ns,
                metadata=metadata,
            )
            self._next_sequence += 1
            self._append_log(
                pending,
                success=False,
                error="Queued",
                recording_id=self._recording_id,
            )
            self._queue.put_nowait(pending)

    def _worker_loop(self) -> None:
        while not self._stop_requested.is_set() or not self._queue.empty():
            try:
                pending = self._queue.get(timeout=0.05)
            except queue.Empty:
                continue

            sent = False
            while not sent:
                pending.send_attempt += 1
                returned_id = None
                try:
                    if self._device is None:
                        self._device = self._discover_one()
                        self._refresh_clock_offset()
                    event = self._device.send_event(
                        pending.event_name,
                        event_timestamp_unix_ns=pending.companion_timestamp_unix_ns,
                    )
                    returned_id = getattr(event, "recording_id", None)
                    if str(returned_id) != self._recording_id:
                        raise RuntimeError(
                            f"Unexpected recording id: {returned_id!r}"
                        )
                    self._append_log(
                        pending,
                        success=True,
                        error="",
                        recording_id=str(returned_id),
                    )
                    sent = True
                except Exception as exc:
                    self._append_log(
                        pending,
                        success=False,
                        error=str(exc),
                        recording_id=(
                            str(returned_id) if returned_id is not None else None
                        ),
                    )
                    self._close_device()
                    if self._stop_requested.wait(self.retry_interval_s):
                        break

            self._queue.task_done()

    def _append_log(
        self,
        pending: _PendingEvent,
        *,
        success: bool,
        error: str,
        recording_id: str | None,
    ) -> None:
        row = {
            "event_sequence": pending.sequence,
            "session_id": self._session_id or "",
            "subject_id": self._subject_id or "",
            "recording_id": recording_id or self._recording_id or "",
            "task_type": pending.metadata.get("task_type", ""),
            "phase": pending.metadata.get("phase", ""),
            "trial_index": pending.metadata.get("trial_index", ""),
            "attempt_index": pending.metadata.get("attempt_index", ""),
            "event_name": pending.event_name,
            "host_timestamp_unix_ns": pending.host_timestamp_unix_ns,
            "companion_timestamp_unix_ns": pending.companion_timestamp_unix_ns,
            "clock_offset_ns": pending.clock_offset_ns,
            "send_attempt": pending.send_attempt,
            "send_success": success,
            "retried": pending.send_attempt > 1,
            "send_error": error,
        }
        with self._log_lock:
            self._event_log.append(row)

    def flush(self, timeout_s: float = 5.0) -> bool:
        deadline = time.monotonic() + timeout_s
        while self._queue.unfinished_tasks and time.monotonic() < deadline:
            time.sleep(0.01)
        return self._queue.unfinished_tasks == 0

    def _close_device(self) -> None:
        if self._device is not None:
            try:
                self._device.close()
            except Exception:
                pass
            self._device = None

    def close(self, timeout_s: float = 5.0) -> bool:
        flushed = self.flush(timeout_s)
        self._stop_requested.set()
        if self._worker is not None:
            self._worker.join(timeout=max(0.0, timeout_s))
        self._close_device()
        return flushed


class NullNeonClient:
    """Drop-in no-op client used when Neon collection is disabled."""

    enabled = False
    recording_id = None
    event_log: list[dict[str, Any]] = []

    def start_session(self, subject_id: str, session_id: str):
        return None

    def next_occurrence(self, key: str) -> int:
        return 0

    def call_on_flip(self, win, event_names, **metadata) -> None:
        return None

    def enqueue_event(self, event_name, metadata=None, host_timestamp_unix_ns=None) -> None:
        return None

    def enqueue_events(self, event_names, metadata=None, host_timestamp_unix_ns=None) -> None:
        return None

    def flush(self, timeout_s: float = 5.0) -> bool:
        return True

    def close(self, timeout_s: float = 5.0) -> bool:
        return True


class CheckSectionController:
    """Emits paired Cloud sections for one domain's confirmation task."""

    def __init__(self, neon_client, domain: str):
        self.neon_client = neon_client
        self.domain = domain.lower()
        self.attempt_index = 0
        self._event_prefix = ""
        self._metadata: dict[str, Any] = {}
        self._section_open = False

    @property
    def section_start(self) -> str:
        return f"{self.domain.upper()}_CHECK_SECTION_START"

    @property
    def section_end(self) -> str:
        return f"{self.domain.upper()}_CHECK_SECTION_END"

    def begin_response_on_flip(self, win, phase: str) -> int:
        self.abort_open_section()
        self.attempt_index += 1
        phase_token = str(phase).upper().replace(" ", "_")
        self._event_prefix = (
            f"{self.domain.upper()}_CHECK_{phase_token}_A{self.attempt_index:03d}"
        )
        self._metadata = {
            "task_type": f"{self.domain}_check",
            "phase": f"{phase}:response_view",
            "attempt_index": self.attempt_index,
        }
        self.neon_client.call_on_flip(
            win,
            (self.section_start, f"{self._event_prefix}_RESPONSE_VIEW"),
            **self._metadata,
        )
        self._section_open = True
        return self.attempt_index

    def record_response(self, is_correct: bool) -> None:
        result = "CORRECT" if is_correct else "WRONG"
        self.neon_client.enqueue_events(
            (f"{self._event_prefix}_RESPONSE_{result}", self.section_end),
            metadata=self._metadata,
        )
        self._section_open = False

    def begin_feedback_on_flip(self, win) -> None:
        feedback_metadata = dict(self._metadata)
        feedback_metadata["phase"] = feedback_metadata.get("phase", "").replace(
            ":response_view", ":feedback"
        )
        self._metadata = feedback_metadata
        self.neon_client.call_on_flip(
            win,
            (self.section_start, f"{self._event_prefix}_FEEDBACK"),
            **self._metadata,
        )
        self._section_open = True

    def end_feedback(self) -> None:
        if self._section_open:
            self.neon_client.enqueue_event(
                self.section_end,
                metadata=self._metadata,
            )
            self._section_open = False

    def abort_open_section(self) -> None:
        if self._section_open:
            self.neon_client.enqueue_event(
                self.section_end,
                metadata=self._metadata,
            )
            self._section_open = False
