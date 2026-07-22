import time
import unittest

from utils.neon_client import (
    CheckSectionController,
    MAIN_PHASES,
    NeonEventClient,
    NullNeonClient,
    main_section_transition_events,
)


class _Mean:
    def __init__(self, value):
        self.mean = value


class _OffsetEstimate:
    def __init__(self, offset_ms):
        self.time_offset_ms = _Mean(offset_ms)


class _Event:
    def __init__(self, recording_id):
        self.recording_id = recording_id


class _FakeDevice:
    def __init__(self, recording_id="recording-1", offset_ms=2.0, outcomes=None):
        self.recording_id = recording_id
        self.offset_ms = offset_ms
        self.outcomes = list(outcomes or [])
        self.calls = []
        self.closed = False
        self.phone_name = "fake-phone"

    def estimate_time_offset(self):
        return _OffsetEstimate(self.offset_ms)

    def send_event(self, name, event_timestamp_unix_ns):
        self.calls.append((name, event_timestamp_unix_ns))
        if self.outcomes:
            outcome = self.outcomes.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            return _Event(outcome)
        return _Event(self.recording_id)

    def close(self):
        self.closed = True


class _Discovery:
    def __init__(self, *device_lists):
        self.device_lists = list(device_lists)
        self.calls = 0

    def __call__(self, timeout_s):
        index = min(self.calls, len(self.device_lists) - 1)
        self.calls += 1
        return self.device_lists[index]


class _FlipWindow:
    def __init__(self):
        self.callbacks = []

    def callOnFlip(self, callback, *args, **kwargs):
        self.callbacks.append((callback, args, kwargs))

    def flip(self):
        callbacks = self.callbacks
        self.callbacks = []
        for callback, args, kwargs in callbacks:
            callback(*args, **kwargs)


class _CollectingClient:
    def __init__(self):
        self.events = []

    def call_on_flip(self, win, event_names, **metadata):
        win.callOnFlip(self.enqueue_events, event_names, metadata=metadata)

    def enqueue_event(self, event_name, metadata=None, host_timestamp_unix_ns=None):
        self.enqueue_events((event_name,), metadata=metadata)

    def enqueue_events(self, event_names, metadata=None, host_timestamp_unix_ns=None):
        self.events.extend(event_names)


class NeonEventClientTests(unittest.TestCase):
    def test_queue_order_and_host_to_companion_conversion(self):
        device = _FakeDevice(offset_ms=2.0)
        client = NeonEventClient(
            discover_devices_fn=_Discovery([device]),
            retry_interval_s=0.01,
        )
        self.assertEqual(client.start_session("P01", "S01"), "recording-1")

        client.enqueue_events(
            ("FIRST", "SECOND"),
            host_timestamp_unix_ns=1_000_000_000,
        )
        self.assertTrue(client.flush(1.0))
        client.close(0.1)

        self.assertEqual([call[0] for call in device.calls], [
            "SESSION_START_P01_S01",
            "FIRST",
            "SECOND",
        ])
        self.assertEqual(device.calls[1][1], 998_000_000)
        self.assertEqual(device.calls[2][1], 998_000_000)
        successful = [row for row in client.event_log if row["send_success"]]
        self.assertEqual([row["event_sequence"] for row in successful], [1, 2, 3])

    def test_retry_preserves_original_companion_timestamp(self):
        first = _FakeDevice(outcomes=["recording-1", OSError("disconnected")])
        second = _FakeDevice(offset_ms=7.0)
        client = NeonEventClient(
            discover_devices_fn=_Discovery([first], [second]),
            retry_interval_s=0.01,
        )
        client.start_session("P01", "S01")
        client.enqueue_event("RETRY_ME", host_timestamp_unix_ns=1_000_000_000)

        self.assertTrue(client.flush(1.0))
        client.close(0.1)
        self.assertEqual(first.calls[-1], ("RETRY_ME", 998_000_000))
        self.assertEqual(second.calls[-1], ("RETRY_ME", 998_000_000))
        retry_rows = [
            row
            for row in client.event_log
            if row["event_name"] == "RETRY_ME" and row["send_attempt"] > 0
        ]
        self.assertEqual([row["send_success"] for row in retry_rows], [False, True])
        self.assertTrue(retry_rows[-1]["retried"])

    def test_recording_id_mismatch_is_not_success(self):
        device = _FakeDevice(recording_id="recording-2", outcomes=["recording-1"])
        client = NeonEventClient(
            discover_devices_fn=_Discovery([device]),
            retry_interval_s=0.01,
        )
        client.start_session("P01", "S01")
        client.enqueue_event("WRONG_RECORDING")

        self.assertFalse(client.flush(0.05))
        client.close(0.05)
        rows = [
            row
            for row in client.event_log
            if row["event_name"] == "WRONG_RECORDING"
        ]
        self.assertTrue(rows)
        self.assertTrue(all(not row["send_success"] for row in rows))
        attempted_rows = [row for row in rows if row["send_attempt"] > 0]
        self.assertTrue(attempted_rows)
        self.assertTrue(
            all(row["recording_id"] == "recording-2" for row in attempted_rows)
        )

    def test_no_active_recording_aborts_and_is_logged(self):
        device = _FakeDevice(recording_id=None)
        client = NeonEventClient(discover_devices_fn=_Discovery([device]))
        with self.assertRaisesRegex(RuntimeError, "녹화가 활성화되지 않았습니다"):
            client.start_session("P01", "S01")
        self.assertEqual(client.event_log[0]["send_attempt"], 1)
        self.assertFalse(client.event_log[0]["send_success"])

    def test_no_device_and_multiple_devices_abort(self):
        no_device = NeonEventClient(discover_devices_fn=_Discovery([]))
        with self.assertRaisesRegex(RuntimeError, "찾지 못했습니다"):
            no_device.start_session("P01", "S01")

        first = _FakeDevice()
        second = _FakeDevice()
        multiple = NeonEventClient(
            discover_devices_fn=_Discovery([first, second])
        )
        with self.assertRaisesRegex(RuntimeError, "여러 대"):
            multiple.start_session("P01", "S01")
        self.assertTrue(first.closed)
        self.assertTrue(second.closed)

    def test_close_flush_timeout_is_bounded(self):
        device = _FakeDevice(outcomes=["recording-1", OSError("offline")])
        client = NeonEventClient(
            discover_devices_fn=_Discovery([device]),
            retry_interval_s=1.0,
        )
        client.start_session("P01", "S01")
        client.enqueue_event("PENDING")
        started = time.monotonic()
        self.assertFalse(client.close(0.05))
        self.assertLess(time.monotonic() - started, 0.25)

    def test_null_client_is_a_no_op(self):
        client = NullNeonClient()
        self.assertIsNone(client.start_session("P01", "S01"))
        client.enqueue_event("IGNORED")
        self.assertTrue(client.flush())
        self.assertTrue(client.close())
        self.assertEqual(client.event_log, [])


class CheckSectionControllerTests(unittest.TestCase):
    def test_response_and_feedback_are_separate_paired_sections(self):
        client = _CollectingClient()
        win = _FlipWindow()
        controller = CheckSectionController(client, "food")

        controller.begin_response_on_flip(win, "phase1_bear")
        win.flip()
        controller.record_response(False)
        controller.begin_feedback_on_flip(win)
        win.flip()
        controller.end_feedback()

        self.assertEqual(client.events, [
            "FOOD_CHECK_SECTION_START",
            "FOOD_CHECK_PHASE1_BEAR_A001_RESPONSE_VIEW",
            "FOOD_CHECK_PHASE1_BEAR_A001_RESPONSE_WRONG",
            "FOOD_CHECK_SECTION_END",
            "FOOD_CHECK_SECTION_START",
            "FOOD_CHECK_PHASE1_BEAR_A001_FEEDBACK",
            "FOOD_CHECK_SECTION_END",
        ])

    def test_main_trials_have_five_paired_sections_for_80_and_120_items(self):
        for trial_count in (80, 120):
            events = []
            identifiers = []
            for trial_index in range(1, trial_count + 1):
                for phase in MAIN_PHASES:
                    transition = main_section_transition_events(trial_index, phase)
                    events.extend(transition)
                    identifiers.append(transition[-1])
                events.append("MAIN_SECTION_END")

            self.assertEqual(events.count("MAIN_SECTION_START"), trial_count * 5)
            self.assertEqual(events.count("MAIN_SECTION_END"), trial_count * 5)
            self.assertEqual(len(set(identifiers)), trial_count * 5)


if __name__ == "__main__":
    unittest.main()
