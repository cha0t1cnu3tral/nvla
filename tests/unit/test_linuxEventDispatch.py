# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

import sys
from types import ModuleType
import unittest
from unittest import mock

from platform.linux.event_dispatch import LinuxEventDispatcher


class TestLinuxEventDispatcher(unittest.TestCase):
	def setUp(self):
		self.globalVars = ModuleType("globalVars")
		self.globalVars.focusObject = None
		self.globalVars.mouseObject = None
		self.modulesPatch = mock.patch.dict(sys.modules, {"globalVars": self.globalVars})
		self.modulesPatch.start()

	def tearDown(self):
		self.modulesPatch.stop()

	def test_updates_linux_cached_focus_and_mouse_objects(self):
		dispatcher = LinuxEventDispatcher()
		focusObject = object()
		mouseObject = object()

		self.assertTrue(dispatcher.setFocusObject(focusObject))
		self.assertTrue(dispatcher.setMouseObject(mouseObject))

		self.assertIs(focusObject, self.globalVars.focusObject)
		self.assertIs(mouseObject, self.globalVars.mouseObject)
		self.assertIs(focusObject, dispatcher.focusObject)
		self.assertIs(mouseObject, dispatcher.mouseObject)

	def test_notifies_registered_event_listeners(self):
		dispatcher = LinuxEventDispatcher()
		events = []
		dispatcher.registerListener(lambda *args, **kwargs: events.append((args, kwargs)))
		obj = object()

		dispatcher.queueEvent("gainFocus", obj, source="atspi")

		self.assertIs(obj, dispatcher.lastQueuedFocusObject)
		self.assertEqual([(("gainFocus", obj), {"source": "atspi"})], events)


if __name__ == "__main__":
	unittest.main()
