# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from datetime import datetime
from types import SimpleNamespace
import unittest

from platform.linux.preview_commands import LinuxPreviewCommandController, formatObjectAnnouncement


class TestLinuxPreviewCommands(unittest.TestCase):
	def test_nvda_t_announces_cached_focused_object(self):
		announcements = []
		controller = LinuxPreviewCommandController(
			dispatcher=SimpleNamespace(
				focusObject=SimpleNamespace(
					name="Editor",
					description="Draft",
					role=SimpleNamespace(name="DOCUMENT"),
				),
			),
			announce=announcements.append,
		)

		handled = controller.handleGesture(SimpleNamespace(event=SimpleNamespace(gestureName="NVDA+T")))

		self.assertTrue(handled)
		self.assertEqual(["Editor, Draft, document"], announcements)

	def test_nvda_t_announces_top_level_ancestor(self):
		announcements = []
		window = SimpleNamespace(name="Settings", description=None, role=SimpleNamespace(name="WINDOW"), parent=None)
		focus = SimpleNamespace(name="Save", description=None, role=SimpleNamespace(name="BUTTON"), parent=window)
		controller = LinuxPreviewCommandController(
			dispatcher=SimpleNamespace(focusObject=focus),
			announce=announcements.append,
		)

		self.assertTrue(controller.handleGesture(SimpleNamespace(event=SimpleNamespace(gestureName="NVDA+T"))))
		self.assertEqual(["Settings, window"], announcements)

	def test_nvda_t_reports_no_title_without_cached_focus(self):
		announcements = []
		controller = LinuxPreviewCommandController(
			dispatcher=SimpleNamespace(focusObject=None),
			announce=announcements.append,
		)

		self.assertTrue(controller.handleGesture(SimpleNamespace(event=SimpleNamespace(gestureName="NVDA+T"))))
		self.assertEqual(["No title"], announcements)

	def test_nvda_tab_announces_cached_focused_object(self):
		announcements = []
		controller = LinuxPreviewCommandController(
			dispatcher=SimpleNamespace(
				focusObject=SimpleNamespace(
					name="Save",
					description="Write changes",
					role=SimpleNamespace(name="BUTTON"),
				),
			),
			announce=announcements.append,
		)

		self.assertTrue(controller.handleGesture(SimpleNamespace(event=SimpleNamespace(gestureName="NVDA+Tab"))))
		self.assertEqual(["Save, Write changes, button"], announcements)

	def test_nvda_b_announces_bounded_active_object_tree(self):
		announcements = []
		second = SimpleNamespace(
			name="Cancel",
			description=None,
			role=SimpleNamespace(name="BUTTON"),
			firstChild=None,
			next=None,
		)
		first = SimpleNamespace(
			name="Save",
			description=None,
			role=SimpleNamespace(name="BUTTON"),
			firstChild=None,
			next=second,
		)
		root = SimpleNamespace(
			name="Settings",
			description=None,
			role=SimpleNamespace(name="WINDOW"),
			parent=None,
			firstChild=first,
			next=None,
		)
		first.parent = root
		second.parent = root
		controller = LinuxPreviewCommandController(
			dispatcher=SimpleNamespace(focusObject=first),
			announce=announcements.append,
		)

		self.assertTrue(controller.handleGesture(SimpleNamespace(event=SimpleNamespace(gestureName="NVDA+B"))))
		self.assertEqual(["Settings, window. Save, button. Cancel, button"], announcements)

	def test_leaves_other_gestures_unhandled(self):
		controller = LinuxPreviewCommandController(
			dispatcher=SimpleNamespace(focusObject=None),
			announce=lambda text: None,
		)

		self.assertFalse(controller.handleGesture(SimpleNamespace(event=SimpleNamespace(gestureName="NVDA+F1"))))

	def test_tree_announcement_stops_on_cycle(self):
		obj = SimpleNamespace(
			name=None,
			description=None,
			role=None,
			parent=None,
			firstChild=None,
		)
		obj.next = obj

		from platform.linux.preview_commands import formatObjectTreeAnnouncement

		self.assertEqual("", formatObjectTreeAnnouncement(obj))

	def test_nvda_q_requests_clean_preview_shutdown(self):
		announcements = []
		stopRequests = []
		controller = LinuxPreviewCommandController(
			dispatcher=SimpleNamespace(focusObject=None),
			announce=announcements.append,
			requestStop=lambda: stopRequests.append(True),
		)

		self.assertTrue(controller.handleGesture(SimpleNamespace(event=SimpleNamespace(gestureName="NVDA+Q"))))
		self.assertEqual(["Exiting NVDA Linux preview"], announcements)
		self.assertEqual([True], stopRequests)

	def test_nvda_h_announces_native_preview_command_help(self):
		announcements = []
		controller = LinuxPreviewCommandController(
			dispatcher=SimpleNamespace(focusObject=None),
			announce=announcements.append,
		)

		self.assertTrue(controller.handleGesture(SimpleNamespace(event=SimpleNamespace(gestureName="NVDA+H"))))
		self.assertIn("NVDA 1 input help", announcements[0])
		self.assertIn("NVDA T active window title", announcements[0])
		self.assertIn("NVDA Q exit Linux preview", announcements[0])

	def test_nvda_1_toggles_input_help_and_reports_captured_gestures(self):
		announcements = []
		controller = LinuxPreviewCommandController(
			dispatcher=SimpleNamespace(focusObject=None),
			announce=announcements.append,
		)

		self.assertTrue(controller.handleGesture(SimpleNamespace(event=SimpleNamespace(gestureName="NVDA+1"))))
		self.assertTrue(controller.handleGesture(SimpleNamespace(event=SimpleNamespace(gestureName="NVDA+T"))))
		self.assertTrue(controller.handleGesture(SimpleNamespace(event=SimpleNamespace(gestureName="NVDA+F1"))))
		self.assertTrue(controller.handleGesture(SimpleNamespace(event=SimpleNamespace(gestureName="NVDA+1"))))
		self.assertEqual(
			[
				"Input help on",
				"NVDA+T: Speak active window title",
				"NVDA+F1: Unassigned",
				"Input help off",
			],
			announcements,
		)

	def test_nvda_f12_reports_time_then_date_on_repeat(self):
		announcements = []
		pressTimes = iter((10.0, 10.2, 11.0))
		controller = LinuxPreviewCommandController(
			dispatcher=SimpleNamespace(focusObject=None),
			announce=announcements.append,
			now=lambda: datetime(2026, 6, 1, 14, 30, 5),
			monotonic=lambda: next(pressTimes),
		)

		for _ in range(3):
			self.assertTrue(controller.handleGesture(SimpleNamespace(event=SimpleNamespace(gestureName="NVDA+F12"))))

		self.assertEqual(
			[
				datetime(2026, 6, 1, 14, 30, 5).strftime("%X"),
				datetime(2026, 6, 1, 14, 30, 5).strftime("%x"),
				datetime(2026, 6, 1, 14, 30, 5).strftime("%X"),
			],
			announcements,
		)

	def test_nvda_f2_requests_next_key_pass_through(self):
		announcements = []
		requests = []
		controller = LinuxPreviewCommandController(
			dispatcher=SimpleNamespace(focusObject=None),
			announce=announcements.append,
			passNextKeyThrough=lambda: requests.append(True),
		)

		self.assertTrue(controller.handleGesture(SimpleNamespace(event=SimpleNamespace(gestureName="NVDA+F2"))))
		self.assertEqual([True], requests)
		self.assertEqual(["Pass next key through"], announcements)

	def test_formats_distinct_object_fields(self):
		obj = SimpleNamespace(
			name="Save",
			description="Save",
			role=SimpleNamespace(displayString="button"),
		)

		self.assertEqual("Save, button", formatObjectAnnouncement(obj))


if __name__ == "__main__":
	unittest.main()
