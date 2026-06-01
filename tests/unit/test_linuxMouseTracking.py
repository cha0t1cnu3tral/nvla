# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from types import SimpleNamespace
import unittest

from platform.linux.mouse_tracking import LinuxMouseTracker


class TestLinuxMouseTracker(unittest.TestCase):
	def test_updates_mouse_object_and_queues_move_event(self):
		obj = object()
		mouseObjects = []
		events = []
		tracker = LinuxMouseTracker(
			getObjectAtPoint=lambda x, y: obj,
			setMouseObject=mouseObjects.append,
			queueEvent=lambda *args, **kwargs: events.append((args, kwargs)),
		)

		tracker.handleMouseEvent(SimpleNamespace(kind="move", x=10, y=20))

		self.assertEqual([obj], mouseObjects)
		self.assertEqual([(("mouseMove", obj), {"x": 10, "y": 20})], events)

	def test_queues_motion_within_same_object_without_resetting_mouse_object(self):
		obj = object()
		mouseObjects = []
		events = []
		tracker = LinuxMouseTracker(
			getObjectAtPoint=lambda x, y: obj,
			setMouseObject=mouseObjects.append,
			queueEvent=lambda *args, **kwargs: events.append((args, kwargs)),
		)

		tracker.handleMouseEvent(SimpleNamespace(kind="move", x=10, y=20))
		tracker.handleMouseEvent(SimpleNamespace(kind="move", x=11, y=20))

		self.assertEqual([obj], mouseObjects)
		self.assertEqual(2, len(events))

	def test_ignores_duplicate_position_button_and_missing_object(self):
		lookups = []
		events = []

		def getObjectAtPoint(x, y):
			lookups.append((x, y))
			return None

		tracker = LinuxMouseTracker(
			getObjectAtPoint=getObjectAtPoint,
			setMouseObject=lambda obj: events.append(("set", obj)),
			queueEvent=lambda *args, **kwargs: events.append(("queue", args, kwargs)),
		)

		tracker.handleMouseEvent(SimpleNamespace(kind="buttonDown", x=10, y=20, button=1))
		tracker.handleMouseEvent(SimpleNamespace(kind="move", x=10, y=20))
		tracker.handleMouseEvent(SimpleNamespace(kind="move", x=10, y=20))

		self.assertEqual([(10, 20)], lookups)
		self.assertEqual([], events)

	def test_does_not_queue_move_when_mouse_object_change_is_rejected(self):
		obj = object()
		events = []
		tracker = LinuxMouseTracker(
			getObjectAtPoint=lambda x, y: obj,
			setMouseObject=lambda obj: False,
			queueEvent=lambda *args, **kwargs: events.append((args, kwargs)),
		)

		tracker.handleMouseEvent(SimpleNamespace(kind="move", x=10, y=20))

		self.assertEqual([], events)


if __name__ == "__main__":
	unittest.main()
