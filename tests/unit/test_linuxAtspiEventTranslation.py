# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from types import SimpleNamespace
import unittest

import controlTypes
from platform.linux import atspi_backend, atspi_mappings


class _FakeStateSet:
	def __init__(self, values):
		self._values = tuple(values)

	def getStates(self):
		return self._values


class _FakeSource:
	def __init__(
		self,
		*,
		role,
		states=(),
		name=None,
		description=None,
		path=None,
	):
		self._role = role
		self._state = _FakeStateSet(states)
		self.name = name
		self.description = description
		self.path = path

	def getRole(self):
		return self._role

	def getState(self):
		return self._state


class TestLinuxAtspiEventTranslation(unittest.TestCase):
	def setUp(self):
		fakeAtspi = SimpleNamespace(
			ROLE_PUSH_BUTTON=10,
			ROLE_ENTRY=11,
			STATE_FOCUSED=1,
			STATE_VISIBLE=2,
			STATE_SHOWING=3,
			STATE_EDITABLE=4,
		)
		self.roleMap = atspi_mappings.build_role_map(fakeAtspi)
		self.stateMap, self.invertedStateValues = atspi_mappings.build_state_map(fakeAtspi)

	def _translate(self, event):
		return atspi_backend.translate_atspi_event(
			event,
			self.roleMap,
			self.stateMap,
			self.invertedStateValues,
		)

	def test_translates_focus_event(self):
		event = SimpleNamespace(
			type="object:state-changed:focused",
			detail1=1,
			source=_FakeSource(
				role=10,
				states=(1, 2, 3),
				name="OK",
				description="Confirm",
				path=(1, 3, 7),
			),
		)

		translated = self._translate(event)

		self.assertIsNotNone(translated)
		self.assertEqual("focus", translated.kind)
		self.assertTrue(translated.isFocused)
		self.assertEqual("1:3:7", translated.sourceKey)
		self.assertEqual(controlTypes.Role.BUTTON, translated.role)
		self.assertEqual({controlTypes.State.FOCUSED}, set(translated.states))

	def test_translates_property_change_event(self):
		event = SimpleNamespace(
			type="accessible:property-change:name",
			any_data="Save As",
			source=_FakeSource(role=11, states=(2, 3, 4), name="oldName"),
		)

		translated = self._translate(event)

		self.assertIsNotNone(translated)
		self.assertEqual("propertyChange", translated.kind)
		self.assertEqual("name", translated.propertyName)
		self.assertEqual("Save As", translated.propertyValue)
		self.assertEqual(controlTypes.Role.EDITABLETEXT, translated.role)
		self.assertIn(controlTypes.State.EDITABLE, translated.states)

	def test_translates_caret_event(self):
		event = SimpleNamespace(
			type="object:text-caret-moved",
			detail1="42",
			source=_FakeSource(role=11, states=(2, 3, 4), name="editor"),
		)

		translated = self._translate(event)

		self.assertIsNotNone(translated)
		self.assertEqual("caret", translated.kind)
		self.assertEqual(42, translated.caretOffset)

	def test_ignores_unsupported_event(self):
		event = SimpleNamespace(type="object:children-changed:add", source=None)
		self.assertIsNone(self._translate(event))

	def test_backend_queues_translated_events(self):
		backend = atspi_backend.ATSPI2Backend()
		backend.roleMap = self.roleMap
		backend.stateMap = self.stateMap
		backend.invertedStateValues = self.invertedStateValues
		event = SimpleNamespace(
			type="object:state-changed:focused",
			detail1=1,
			source=_FakeSource(role=10, states=(1, 2, 3), name="OK"),
		)

		backend._onAtspiEvent(event)

		queued = backend.drainTranslatedEvents()
		self.assertEqual(1, len(queued))
		self.assertEqual("focus", queued[0].kind)
		self.assertEqual([], backend.drainTranslatedEvents())
