import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APP_HEADER = ROOT / "main" / "application.h"
APP_SOURCE = ROOT / "main" / "application.cc"
PROTOCOL_HEADER = ROOT / "main" / "protocols" / "protocol.h"
WEBSOCKET_SOURCE = ROOT / "main" / "protocols" / "websocket_protocol.cc"
WEBSOCKET_HEADER = ROOT / "main" / "protocols" / "websocket_protocol.h"


class ConnectionRecoveryWiringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = APP_SOURCE.read_text()
        cls.application_header = APP_HEADER.read_text()
        cls.protocol = PROTOCOL_HEADER.read_text()
        cls.websocket = WEBSOCKET_SOURCE.read_text()
        cls.websocket_header = WEBSOCKET_HEADER.read_text()

    def test_application_owns_policy_and_background_open_job(self):
        self.assertIn("ConnectionRecoveryPolicy recovery_policy_", self.application_header)
        self.assertIn("std::shared_ptr<Protocol> protocol_", self.application_header)
        self.assertIn("xTaskCreate(", self.application)
        recovery_job = self.application[
            self.application.index("void Application::StartRecoveryTask") :
            self.application.index("void Application::HandleRecoveryOpenResult")
        ]
        self.assertIn("context->protocol->OpenAudioChannelForEpoch(context->reservation_epoch)", recovery_job)
        self.assertIn("recovery_worker_active_", recovery_job)
        self.assertIn("uint32_t remaining_ms = context->delay_ms", recovery_job)
        self.assertIn("slice_ms = remaining_ms > 100 ? 100 : remaining_ms", recovery_job)
        self.assertIn("vTaskDelay(pdMS_TO_TICKS(slice_ms))", recovery_job)
        self.assertIn("std::unique_ptr<RecoveryTaskContext>", recovery_job)

    def test_close_and_user_stop_are_epoch_and_intent_gated(self):
        self.assertIn("OnAudioChannelClosedWithEpoch", self.application)
        self.assertNotIn("OnAudioChannelClosed([", self.application)
        close_handler = self.application[
            self.application.index("void Application::HandleAudioChannelClosed") :
            self.application.index("void Application::CancelRecoveryIntent")
        ]
        self.assertIn("protocol_epoch != accepted_connection_epoch_", close_handler)
        self.assertIn("recovery_policy_.UnexpectedClose()", close_handler)
        stop_handler = self.application[
            self.application.index("void Application::HandleStopListeningEvent") :
            self.application.index("void Application::HandleWakeWordDetectedEvent")
        ]
        self.assertIn("CancelRecoveryIntent(true);", stop_handler)
        self.assertIn("SetDeviceState(kDeviceStateIdle);", stop_handler)

    def test_recovery_restore_does_not_replay_wake_or_audio(self):
        restore = self.application[
            self.application.index("void Application::HandleRecoveryOpenResult") :
            self.application.index("void Application::HandleRecoveryRetryTimer")
        ]
        self.assertIn("audio_service_.ResetDecoder();", restore)
        self.assertIn("PopPacketFromSendQueue", restore)
        self.assertIn("SetListeningMode(mode);", restore)
        self.assertNotIn("EncodeWakeWord", restore)
        self.assertNotIn("SendWakeWordDetected", restore)
        self.assertNotIn("PlaySound", restore)

    def test_transport_epoch_cancellation_blocks_late_callbacks(self):
        self.assertIn("std::atomic<bool> open_cancelled_", self.websocket_header)
        self.assertIn("WEBSOCKET_PROTOCOL_OPEN_CANCEL_EVENT", self.websocket_header)
        self.assertIn("BeginConnectionAttempt();", self.websocket)
        self.assertIn("epoch != connection_epoch()", self.websocket)
        self.assertIn("websocket.reset();", self.websocket)
        self.assertIn("vEventGroupDelete(event_group_handle_);", self.websocket)
        self.assertIn("OnAudioChannelClosedWithEpoch", self.protocol)
        self.assertIn("OnAudioChannelClosed(std::function<void()>", self.protocol)

    def test_backoff_is_bounded_and_exact(self):
        policy = (ROOT / "main" / "protocols" / "connection_recovery.cc").read_text()
        for delay in ("1000U", "2000U", "4000U", "8000U", "16000U"):
            if delay == "1000U":
                self.assertIn("1000U << (attempt - 1)", policy)
        self.assertIn("kMaxRecoveryAttempts = 5", (ROOT / "main" / "protocols" / "connection_recovery.h").read_text())
        self.assertRegex(policy, re.compile(r"if \(attempt_ >= kMaxRecoveryAttempts\)"))


if __name__ == "__main__":
    unittest.main()
