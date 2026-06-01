# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

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

	def test_nvda_t_reports_unknown_without_cached_focus(self):
		announcements = []
		controller = LinuxPreviewCommandController(
			dispatcher=SimpleNamespace(focusObject=None),
			announce=announcements.append,
		)

		self.assertTrue(controller.handleGesture(SimpleNamespace(event=SimpleNamespace(gestureName="NVDA+T"))))
		self.assertEqual(["unknown"], announcements)

	def test_leaves_other_gestures_unhandled(self):
		controller = LinuxPreviewCommandController(
			dispatcher=SimpleNamespace(focusObject=None),
			announce=lambda text: None,
		)

		self.assertFalse(controller.handleGesture(SimpleNamespace(event=SimpleNamespace(gestureName="NVDA+B"))))

	def test_formats_distinct_object_fields(self):
		obj = SimpleNamespace(
			name="Save",
			description="Save",
			role=SimpleNamespace(displayString="button"),
		)

		self.assertEqual("Save, button", formatObjectAnnouncement(obj))


if __name__ == "__main__":
	unittest.main()
