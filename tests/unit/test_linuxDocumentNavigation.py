# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from dataclasses import dataclass, field
from types import SimpleNamespace
import unittest

import controlTypes
from platform.linux.document_navigation import LinuxDocumentNavigationController, LinuxDocumentNavigator


@dataclass
class _Object:
	role: controlTypes.Role
	name: str = ""
	basicText: str = ""
	children: list["_Object"] = field(default_factory=list)


class TestLinuxDocumentNavigator(unittest.TestCase):
	def setUp(self):
		self.heading = _Object(controlTypes.Role.HEADING, name="Account")
		self.link = _Object(controlTypes.Role.LINK, name="Profile link")
		self.edit = _Object(controlTypes.Role.EDITABLETEXT, name="Search")
		self.listItem = _Object(controlTypes.Role.LISTITEM, name="First item")
		self.list = _Object(controlTypes.Role.LIST, children=[self.listItem])
		self.table = _Object(controlTypes.Role.TABLE, name="Results")
		self.section = _Object(controlTypes.Role.SECTION, name="Main")
		self.root = _Object(
			controlTypes.Role.DOCUMENT,
			basicText="First line\nSecond line",
			children=[self.heading, self.link, self.edit, self.list, self.table, self.section],
		)
		self.navigator = LinuxDocumentNavigator(self.root)

	def testMovesForwardAndBackwardByLine(self):
		self.assertEqual("First line", self.navigator.moveLine(1).text)
		self.assertEqual("Second line", self.navigator.moveLine(1).text)
		self.assertEqual("First line", self.navigator.moveLine(-1).text)

	def testLineMovementStopsAtDocumentEdges(self):
		self.assertEqual("First line", self.navigator.moveLine(-1).text)
		for _ in range(20):
			lastPosition = self.navigator.moveLine(1)
		self.assertEqual("Main", lastPosition.text)
		self.assertEqual("Main", self.navigator.moveLine(1).text)

	def testMovesToQuickNavigationCategories(self):
		self.assertIs(self.heading, self.navigator.moveQuickNav("heading").obj)
		self.assertIs(self.link, self.navigator.moveQuickNav("link").obj)
		self.assertIs(self.edit, self.navigator.moveQuickNav("formField").obj)
		self.assertIs(self.list, self.navigator.moveQuickNav("list").obj)
		self.assertIs(self.table, self.navigator.moveQuickNav("table").obj)
		self.assertIs(self.section, self.navigator.moveQuickNav("landmark").obj)

	def testMovesBackwardByQuickNavigationCategory(self):
		for _ in range(20):
			self.navigator.moveLine(1)
		self.assertIs(self.link, self.navigator.moveQuickNav("link", direction=-1).obj)

	def testReturnsNoneWhenQuickNavigationTargetIsUnavailable(self):
		self.assertIsNone(self.navigator.moveQuickNav("table", direction=-1))

	def testRejectsUnknownQuickNavigationCategory(self):
		with self.assertRaisesRegex(ValueError, "Unsupported quick navigation"):
			self.navigator.moveQuickNav("graphic")


class TestLinuxDocumentNavigationController(unittest.TestCase):
	def setUp(self):
		self.announcements = []
		self.controller = LinuxDocumentNavigationController(self.announcements.append)
		self.root = _Object(
			controlTypes.Role.DOCUMENT,
			basicText="First line\nSecond line",
			children=[
				_Object(controlTypes.Role.HEADING, name="Account"),
				_Object(controlTypes.Role.LINK, name="Profile"),
			],
		)
		self.controller.setRoot(self.root)

	def _gesture(self, name):
		return SimpleNamespace(event=SimpleNamespace(gestureName=name))

	def testAnnouncesLineNavigation(self):
		self.assertTrue(self.controller.handleGesture(self._gesture("downArrow")))
		self.assertEqual(["First line"], self.announcements)

	def testAnnouncesQuickNavigation(self):
		self.assertTrue(self.controller.handleGesture(self._gesture("H")))
		self.assertEqual(["Account"], self.announcements)

	def testLeavesUnsupportedGestureUnhandled(self):
		self.assertFalse(self.controller.handleGesture(self._gesture("NVDA+T")))

	def testLeavesGestureUnhandledWithoutDocument(self):
		self.controller.setRoot(None)
		self.assertFalse(self.controller.handleGesture(self._gesture("downArrow")))

	def testKeepsBrowsePositionWhenFocusedDocumentRootDoesNotChange(self):
		self.assertTrue(self.controller.handleGesture(self._gesture("downArrow")))
		self.controller.setRoot(self.root)
		self.assertTrue(self.controller.handleGesture(self._gesture("downArrow")))
		self.assertEqual(["First line", "Second line"], self.announcements)

	def testAutomaticallyUsesFocusModeForEditableControls(self):
		self.controller.setFocusObject(_Object(controlTypes.Role.EDITABLETEXT, name="Search"))

		self.assertTrue(self.controller.isFocusMode)
		self.assertFalse(self.controller.handleGesture(self._gesture("downArrow")))
		self.assertFalse(self.controller.handleGesture(self._gesture("H")))
		self.assertEqual([], self.announcements)

	def testUsesBrowseModeForNonEditableControls(self):
		self.controller.setFocusObject(_Object(controlTypes.Role.LINK, name="Profile"))

		self.assertFalse(self.controller.isFocusMode)
		self.assertTrue(self.controller.handleGesture(self._gesture("downArrow")))
		self.assertEqual(["First line"], self.announcements)

	def testNvdaSpaceTogglesFocusAndBrowseModes(self):
		self.assertTrue(self.controller.handleGesture(self._gesture("NVDA+Space")))
		self.assertTrue(self.controller.isFocusMode)
		self.assertFalse(self.controller.handleGesture(self._gesture("downArrow")))
		self.assertTrue(self.controller.handleGesture(self._gesture("NVDA+Space")))
		self.assertFalse(self.controller.isFocusMode)
		self.assertEqual(["Focus mode", "Browse mode"], self.announcements)

	def testManualModeOverrideSurvivesFocusChangesWithinDocument(self):
		self.assertTrue(self.controller.handleGesture(self._gesture("NVDA+Space")))

		self.controller.setFocusObject(_Object(controlTypes.Role.LINK, name="Profile"))

		self.assertTrue(self.controller.isFocusMode)

	def testChangingDocumentResetsManualModeOverride(self):
		self.assertTrue(self.controller.handleGesture(self._gesture("NVDA+Space")))
		newRoot = _Object(controlTypes.Role.DOCUMENT, basicText="New page")

		self.controller.setRoot(newRoot)
		self.controller.setFocusObject(_Object(controlTypes.Role.LINK, name="Profile"))

		self.assertFalse(self.controller.isFocusMode)

	def testNvdaShiftSpaceTogglesSingleLetterNavigation(self):
		self.assertTrue(self.controller.handleGesture(self._gesture("NVDA+Shift+Space")))
		self.assertFalse(self.controller.isSingleLetterNavigationEnabled)
		self.assertFalse(self.controller.handleGesture(self._gesture("H")))
		self.assertTrue(self.controller.handleGesture(self._gesture("downArrow")))
		self.assertTrue(self.controller.handleGesture(self._gesture("NVDA+Shift+Space")))
		self.assertTrue(self.controller.isSingleLetterNavigationEnabled)
		self.assertTrue(self.controller.handleGesture(self._gesture("H")))
		self.assertEqual(
			[
				"Single letter navigation off",
				"First line",
				"Single letter navigation on",
				"Account",
			],
			self.announcements,
		)


if __name__ == "__main__":
	unittest.main()
