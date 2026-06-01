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

	def test_formats_distinct_object_fields(self):
		obj = SimpleNamespace(
			name="Save",
			description="Save",
			role=SimpleNamespace(displayString="button"),
		)

		self.assertEqual("Save, button", formatObjectAnnouncement(obj))


if __name__ == "__main__":
	unittest.main()
