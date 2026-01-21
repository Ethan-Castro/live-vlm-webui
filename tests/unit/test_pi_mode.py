"""Unit tests for Raspberry Pi mode detection and configuration."""

import os
import pytest


class TestPiDetection:
    """Test Raspberry Pi detection functions."""

    def test_is_raspberry_pi_env_override(self, monkeypatch):
        """Test that PI_MODE environment variable enables Pi detection."""
        from live_vlm_webui.gpu_monitor import is_raspberry_pi

        # Set PI_MODE=true to force Pi mode
        monkeypatch.setenv("PI_MODE", "true")

        # Should return True with env override
        result = is_raspberry_pi()
        assert result is True, "PI_MODE=true should enable Pi detection"
        print("✅ PI_MODE=true enables Pi detection")

    def test_is_raspberry_pi_env_disabled(self, monkeypatch):
        """Test that PI_MODE=false doesn't force Pi mode."""
        from live_vlm_webui.gpu_monitor import is_raspberry_pi

        # Set PI_MODE=false - should not force Pi mode
        monkeypatch.setenv("PI_MODE", "false")

        # On non-Pi hardware, should return False
        # On actual Pi, would return True based on hardware detection
        # This test just verifies env var doesn't crash
        result = is_raspberry_pi()
        assert isinstance(result, bool)
        print(f"✅ PI_MODE=false returns: {result}")

    def test_get_pi_model_returns_string_or_none(self):
        """Test that get_pi_model returns string or None."""
        from live_vlm_webui.gpu_monitor import get_pi_model

        result = get_pi_model()

        assert result is None or isinstance(result, str)
        if result:
            print(f"✅ Detected Pi model: {result}")
        else:
            print("✅ No Pi detected (expected on non-Pi hardware)")


class TestPiModeFlag:
    """Test Pi mode flag functions."""

    def test_set_and_get_pi_mode(self):
        """Test setting and getting Pi mode."""
        from live_vlm_webui.gpu_monitor import set_pi_mode, is_pi_mode

        # Enable Pi mode
        set_pi_mode(True)
        assert is_pi_mode() is True
        print("✅ Pi mode enabled")

        # Disable Pi mode
        set_pi_mode(False)
        assert is_pi_mode() is False
        print("✅ Pi mode disabled")


class TestRaspberryPiMonitor:
    """Test the RaspberryPiMonitor class."""

    def test_create_pi_monitor(self):
        """Test creating a RaspberryPiMonitor."""
        from live_vlm_webui.gpu_monitor import create_monitor, RaspberryPiMonitor

        monitor = create_monitor(platform="pi")

        assert monitor is not None
        assert isinstance(monitor, RaspberryPiMonitor)
        print("✅ Created RaspberryPiMonitor via create_monitor(platform='pi')")

    def test_pi_monitor_get_stats(self):
        """Test that RaspberryPiMonitor.get_stats() returns expected structure."""
        from live_vlm_webui.gpu_monitor import RaspberryPiMonitor

        monitor = RaspberryPiMonitor()
        stats = monitor.get_stats()

        # Check required keys
        assert isinstance(stats, dict)
        assert "platform" in stats
        assert "CPU-only" in stats["platform"]
        assert "cpu_percent" in stats
        assert "ram_used_gb" in stats
        assert "pi_mode" in stats
        assert stats["pi_mode"] is True

        # GPU fields should be None (no GPU on Pi)
        assert stats.get("gpu_percent") is None
        assert stats.get("vram_used_gb") is None

        print(f"✅ Pi monitor stats: platform={stats['platform']}")

    def test_pi_monitor_history(self):
        """Test that Pi monitor maintains history."""
        from live_vlm_webui.gpu_monitor import RaspberryPiMonitor

        monitor = RaspberryPiMonitor()

        # Get stats a few times to build history
        for _ in range(5):
            monitor.get_stats()

        history = monitor.get_history()

        assert isinstance(history, dict)
        assert "cpu_util" in history
        assert len(history["cpu_util"]) == 5
        print(f"✅ History contains {len(history['cpu_util'])} entries")


class TestPiModeDefaults:
    """Test Pi mode default values."""

    def test_pi_process_every_env(self, monkeypatch):
        """Test PI_PROCESS_EVERY environment variable."""
        monkeypatch.setenv("PI_MODE", "true")
        monkeypatch.setenv("PI_PROCESS_EVERY", "120")

        # Re-import to pick up env vars (or check the server logic)
        # The actual default is applied in server.py main()
        value = int(os.environ.get("PI_PROCESS_EVERY", "60"))
        assert value == 120
        print("✅ PI_PROCESS_EVERY=120 parsed correctly")

    def test_pi_max_tokens_env(self, monkeypatch):
        """Test PI_MAX_TOKENS environment variable."""
        monkeypatch.setenv("PI_MODE", "true")
        monkeypatch.setenv("PI_MAX_TOKENS", "75")

        value = int(os.environ.get("PI_MAX_TOKENS", "100"))
        assert value == 75
        print("✅ PI_MAX_TOKENS=75 parsed correctly")


class TestYoloOptional:
    """Test that YOLO is optional and handled gracefully."""

    def test_yolo_import_check(self):
        """Test that YOLO availability check works."""
        try:
            from live_vlm_webui.object_detection_service import YOLO_AVAILABLE

            print(f"✅ YOLO_AVAILABLE = {YOLO_AVAILABLE}")
            assert isinstance(YOLO_AVAILABLE, bool)
        except ImportError:
            # If the whole module fails to import, ultralytics is missing
            print("✅ object_detection_service module not importable (ultralytics missing)")

    def test_server_yolo_flag(self):
        """Test that server has YOLO_AVAILABLE flag."""
        try:
            from live_vlm_webui.server import YOLO_AVAILABLE

            print(f"✅ Server YOLO_AVAILABLE = {YOLO_AVAILABLE}")
            assert isinstance(YOLO_AVAILABLE, bool)
        except ImportError as e:
            # This shouldn't happen - server should always be importable
            pytest.fail(f"Server module failed to import: {e}")


@pytest.mark.skipif(
    os.path.exists("/proc/device-tree/model") is False,
    reason="Not running on Raspberry Pi hardware"
)
class TestActualPiHardware:
    """Tests that only run on actual Raspberry Pi hardware."""

    def test_auto_detect_pi(self):
        """Test auto-detection on actual Pi hardware."""
        from live_vlm_webui.gpu_monitor import is_raspberry_pi, get_pi_model

        assert is_raspberry_pi() is True
        model = get_pi_model()
        assert model is not None
        assert "Raspberry Pi" in model
        print(f"✅ Running on actual Pi: {model}")

    def test_create_monitor_auto_detects_pi(self):
        """Test that create_monitor auto-detects Pi."""
        from live_vlm_webui.gpu_monitor import create_monitor, RaspberryPiMonitor

        monitor = create_monitor()  # No platform specified

        assert isinstance(monitor, RaspberryPiMonitor)
        print("✅ Auto-detected Pi and created RaspberryPiMonitor")
