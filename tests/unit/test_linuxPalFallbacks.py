# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

import unittest

from platform.linux.display import LinuxDisplayAdapter
from platform.linux.message_window import LinuxMessageWindowAdapter
from platform.linux.session import LinuxSessionAdapter
from platform.linux.system import LinuxSystemAdapter
from platform.linux import watchdog
from platform.linux.windowing import LinuxWindowingAdapter


class TestLinuxPalFallbacks(unittest.TestCase):
	def test_display_scaling_setup_is_non_fatal(self):
		self.assertIsNone(LinuxDisplayAdapter().set_dpi_awareness())

	def test_session_lifecycle_is_non_fatal(self):
		adapter = LinuxSessionAdapter()

		self.assertIsNone(adapter.initialize())
		self.assertIsNone(adapter.pump_all())

	def test_system_basics_are_non_fatal(self):
		adapter = LinuxSystemAdapter()

		self.assertTrue(adapter.get_os_version_string())
		self.assertIsNone(adapter.register_application_restart())
		self.assertEqual("Unknown power status", adapter.get_battery_status())

	def test_watchdog_lifecycle_is_non_fatal(self):
		watchdog.terminate()

		watchdog.initialize()
		self.assertTrue(watchdog.isRunning)
		self.assertIsNone(watchdog.alive())
		self.assertIsNone(watchdog.asleep())
		self.assertFalse(watchdog.WatchdogObserver().isAttemptingRecovery)
		watchdog.terminate()
		self.assertFalse(watchdog.isRunning)

	def test_window_show_mode_has_compatible_default(self):
		self.assertEqual(1, LinuxWindowingAdapter().show_normal)

	def test_message_window_placeholder_tracks_destroy(self):
		adapter = LinuxMessageWindowAdapter()

		window = adapter.create_message_window("NVDA")

		self.assertEqual("NVDA", window.name)
		self.assertFalse(window.isDestroyed)
		self.assertIsNone(adapter.pre_handle_window_message(1, 2, 3))
		window.destroy()
		self.assertTrue(window.isDestroyed)


if __name__ == "__main__":
	unittest.main()
