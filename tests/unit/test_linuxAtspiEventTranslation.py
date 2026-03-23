# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from types import SimpleNamespace
import unittest
from unittest import mock

import controlTypes
import textInfos
from platform.linux import accessibility, atspi_backend, atspi_mappings


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
		text=None,
	):
		self._role = role
		self._state = _FakeStateSet(states)
		self.name = name
		self.description = description
		self.path = path
		self._text = text

	def getRole(self):
		return self._role

	def getState(self):
		return self._state

	def queryText(self):
		if self._text is None:
			raise RuntimeError("No text interface")
		return self._text


class _FakeText:
	def __init__(self, text: str, caretOffset: int = 0, selection: tuple[int, int] | None = None):
		self._text = text
		self.characterCount = len(text)
		self.caretOffset = caretOffset
		self._selection = selection

	def getText(self, start: int, end: int) -> str:
		if end < 0:
			end = len(self._text)
		return self._text[start:end]

	def setCaretOffset(self, offset: int) -> None:
		self.caretOffset = offset
		self._selection = (offset, offset)

	def getSelection(self, index: int) -> tuple[int, int]:
		if index != 0 or self._selection is None:
			raise RuntimeError("No selection")
		return self._selection

	def setSelection(self, index: int, start: int, end: int) -> None:
		if index != 0:
			raise RuntimeError("Only a single selection is supported")
		self._selection = (start, end)
		self.caretOffset = end


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

	def test_backend_coalesces_repeated_property_changes(self):
		backend = atspi_backend.ATSPI2Backend()
		backend.roleMap = self.roleMap
		backend.stateMap = self.stateMap
		backend.invertedStateValues = self.invertedStateValues
		source = _FakeSource(role=11, states=(2, 3, 4), name="editor", path=(5, 1))

		firstEvent = SimpleNamespace(
			type="accessible:property-change:name",
			any_data="Draft",
			source=source,
		)
		secondEvent = SimpleNamespace(
			type="accessible:property-change:name",
			any_data="Final",
			source=source,
		)

		backend._onAtspiEvent(firstEvent)
		backend._onAtspiEvent(secondEvent)

		queued = backend.drainTranslatedEvents()
		self.assertEqual(1, len(queued))
		self.assertEqual("Final", queued[0].propertyValue)

	def test_backend_pump_dispatches_to_registered_listeners(self):
		backend = atspi_backend.ATSPI2Backend()
		backend._initialized = True
		backend.roleMap = self.roleMap
		backend.stateMap = self.stateMap
		backend.invertedStateValues = self.invertedStateValues
		received = []
		backend.registerEventListener(received.append)
		event = SimpleNamespace(
			type="object:text-caret-moved",
			detail1=9,
			source=_FakeSource(role=11, states=(2, 3, 4), name="editor", path=(2, 4)),
		)

		backend._onAtspiEvent(event)
		backend.pump_all()

		self.assertEqual(1, len(received))
		self.assertEqual("caret", received[0].kind)
		self.assertEqual(9, received[0].caretOffset)
		self.assertEqual([], backend.drainTranslatedEvents())

	def test_backend_bounds_translated_event_queue_size(self):
		backend = atspi_backend.ATSPI2Backend()
		backend.roleMap = self.roleMap
		backend.stateMap = self.stateMap
		backend.invertedStateValues = self.invertedStateValues
		backend._maxQueuedTranslatedEvents = 3

		for i in range(4):
			backend._onAtspiEvent(
				SimpleNamespace(
					type="object:state-changed:focused",
					detail1=1,
					source=_FakeSource(
						role=10,
						states=(1, 2, 3),
						name=f"btn{i}",
						path=(7, i),
					),
				),
			)

		queued = backend.drainTranslatedEvents()
		self.assertEqual(3, len(queued))
		self.assertEqual("10:btn1", queued[0].sourceKey)
		self.assertEqual("10:btn3", queued[-1].sourceKey)

	def test_backend_queue_eviction_preserves_focus_when_possible(self):
		backend = atspi_backend.ATSPI2Backend()
		backend.roleMap = self.roleMap
		backend.stateMap = self.stateMap
		backend.invertedStateValues = self.invertedStateValues
		backend._maxQueuedTranslatedEvents = 2

		backend._onAtspiEvent(
			SimpleNamespace(
				type="object:state-changed:focused",
				detail1=1,
				source=_FakeSource(role=10, states=(1, 2, 3), name="focusA", path=(8, 1)),
			),
		)
		backend._onAtspiEvent(
			SimpleNamespace(
				type="accessible:property-change:name",
				any_data="Draft",
				source=_FakeSource(role=11, states=(2, 3, 4), name="editor", path=(8, 2)),
			),
		)
		backend._onAtspiEvent(
			SimpleNamespace(
				type="object:text-caret-moved",
				detail1=11,
				source=_FakeSource(role=11, states=(2, 3, 4), name="editor", path=(8, 2)),
			),
		)

		queued = backend.drainTranslatedEvents()
		self.assertEqual(2, len(queued))
		self.assertEqual("focus", queued[0].kind)
		self.assertEqual("caret", queued[1].kind)

	def test_linux_event_bridge_caches_objects_by_source(self):
		bridge = accessibility.LinuxATSPINVDAEventBridge()
		source = _FakeSource(role=11, states=(2, 3, 4), name="Draft", path=(9, 1))
		firstEvent = self._translate(
			SimpleNamespace(
				type="accessible:property-change:name",
				any_data="Draft",
				source=source,
			),
		)
		secondEvent = self._translate(
			SimpleNamespace(
				type="accessible:property-change:name",
				any_data="Final",
				source=_FakeSource(role=11, states=(2, 3, 4), name="Final", path=(9, 1)),
			),
		)

		firstObj = bridge.getOrCreateObjectForEvent(firstEvent)
		secondObj = bridge.getOrCreateObjectForEvent(secondEvent)

		self.assertIs(firstObj, secondObj)
		self.assertEqual("Final", secondObj.name)

	def test_linux_event_bridge_routes_focus_and_property_events(self):
		bridge = accessibility.LinuxATSPINVDAEventBridge()
		focusEvent = self._translate(
			SimpleNamespace(
				type="object:state-changed:focused",
				detail1=1,
				source=_FakeSource(role=10, states=(1, 2, 3), name="OK", path=(1, 2)),
			),
		)
		nameEvent = self._translate(
			SimpleNamespace(
				type="accessible:property-change:name",
				any_data="Save",
				source=_FakeSource(role=10, states=(2, 3), name="Save", path=(1, 2)),
			),
		)

		with mock.patch.object(accessibility.api, "setFocusObject") as setFocusObject:
			with mock.patch.object(accessibility.eventHandler, "queueEvent") as queueEvent:
				bridge.handleEvent(focusEvent)
				bridge.handleEvent(nameEvent)

		self.assertEqual(1, setFocusObject.call_count)
		self.assertEqual("gainFocus", queueEvent.call_args_list[0].args[0])
		self.assertEqual("nameChange", queueEvent.call_args_list[1].args[0])

	def test_linux_event_bridge_applies_property_change_on_first_event(self):
		bridge = accessibility.LinuxATSPINVDAEventBridge()
		event = self._translate(
			SimpleNamespace(
				type="accessible:property-change:name",
				any_data="Final Name",
				source=_FakeSource(role=11, states=(2, 3, 4), name="Old Name", path=(6, 1)),
			),
		)

		obj = bridge.getOrCreateObjectForEvent(event)

		self.assertEqual("Final Name", obj.name)

	def test_linux_event_bridge_applies_caret_offset_on_first_event(self):
		bridge = accessibility.LinuxATSPINVDAEventBridge()
		event = self._translate(
			SimpleNamespace(
				type="object:text-caret-moved",
				detail1=7,
				source=_FakeSource(role=11, states=(2, 3, 4), name="editor", path=(6, 2)),
			),
		)

		obj = bridge.getOrCreateObjectForEvent(event)
		caretText = obj.makeTextInfo(textInfos.POSITION_CARET)

		self.assertEqual((7, 7), caretText.offsets)

	def test_linux_event_bridge_evicts_oldest_cached_object(self):
		bridge = accessibility.LinuxATSPINVDAEventBridge()
		bridge._MAX_CACHED_OBJECTS = 2

		eventA = self._translate(
			SimpleNamespace(
				type="accessible:property-change:name",
				any_data="A",
				source=_FakeSource(role=11, states=(2, 3, 4), name="A", path=(1, 1)),
			),
		)
		eventB = self._translate(
			SimpleNamespace(
				type="accessible:property-change:name",
				any_data="B",
				source=_FakeSource(role=11, states=(2, 3, 4), name="B", path=(1, 2)),
			),
		)
		eventC = self._translate(
			SimpleNamespace(
				type="accessible:property-change:name",
				any_data="C",
				source=_FakeSource(role=11, states=(2, 3, 4), name="C", path=(1, 3)),
			),
		)

		bridge.getOrCreateObjectForEvent(eventA)
		bridge.getOrCreateObjectForEvent(eventB)
		bridge.getOrCreateObjectForEvent(eventC)

		self.assertEqual(2, len(bridge._objectsByKey))
		self.assertNotIn("1:1", bridge._objectsByKey)
		self.assertIn("1:2", bridge._objectsByKey)
		self.assertIn("1:3", bridge._objectsByKey)

	def test_linux_accessibility_adapter_clears_cached_objects_on_terminate(self):
		adapter = accessibility.LinuxAccessibilityAdapter()
		adapter._initialized = True
		adapter._eventBridge._objectsByKey["1:9"] = mock.Mock()

		with mock.patch.object(adapter._backend, "unregisterEventListener"):
			with mock.patch.object(adapter._backend, "terminate"):
				adapter.terminate_iaccessible()

		self.assertEqual({}, dict(adapter._eventBridge._objectsByKey))

	def test_linux_atspi_text_info_uses_accessible_text_interface(self):
		bridge = accessibility.LinuxATSPINVDAEventBridge()
		source = _FakeSource(
			role=11,
			states=(2, 3, 4),
			name="editor",
			path=(3, 4),
			text=_FakeText("hello world", caretOffset=6),
		)
		focusEvent = self._translate(
			SimpleNamespace(
				type="object:state-changed:focused",
				detail1=1,
				source=source,
			),
		)
		obj = bridge.getOrCreateObjectForEvent(focusEvent)

		allText = obj.makeTextInfo(textInfos.POSITION_ALL)
		caretText = obj.makeTextInfo(textInfos.POSITION_CARET)

		self.assertEqual("hello world", allText.text)
		self.assertEqual((6, 6), caretText.offsets)

	def test_linux_atspi_text_info_updates_caret_and_selection(self):
		bridge = accessibility.LinuxATSPINVDAEventBridge()
		text = _FakeText("abcde", caretOffset=1)
		source = _FakeSource(
			role=11,
			states=(2, 3, 4),
			name="editor",
			path=(3, 5),
			text=text,
		)
		focusEvent = self._translate(
			SimpleNamespace(
				type="object:state-changed:focused",
				detail1=1,
				source=source,
			),
		)
		obj = bridge.getOrCreateObjectForEvent(focusEvent)

		caretText = obj.makeTextInfo(textInfos.POSITION_CARET)
		caretText.move(textInfos.UNIT_CHARACTER, 2)
		caretText.updateCaret()
		self.assertEqual(3, text.caretOffset)

		selectionText = obj.makeTextInfo(textInfos.POSITION_FIRST)
		endText = obj.makeTextInfo(textInfos.POSITION_FIRST)
		endText.move(textInfos.UNIT_CHARACTER, 4)
		selectionText.setEndPoint(endText, "endToEnd")
		selectionText.updateSelection()
		self.assertEqual((0, 4), text.getSelection(0))

	def test_linux_atspi_text_info_falls_back_to_caret_event_offset(self):
		bridge = accessibility.LinuxATSPINVDAEventBridge()
		source = _FakeSource(role=11, states=(2, 3, 4), name="editor", path=(3, 9))
		nameEvent = self._translate(
			SimpleNamespace(
				type="accessible:property-change:name",
				any_data="editor",
				source=source,
			),
		)
		caretEvent = self._translate(
			SimpleNamespace(
				type="object:text-caret-moved",
				detail1=5,
				source=source,
			),
		)

		obj = bridge.getOrCreateObjectForEvent(nameEvent)
		obj.updateFromTranslatedEvent(caretEvent)
		caretText = obj.makeTextInfo(textInfos.POSITION_CARET)

		self.assertEqual((5, 5), caretText.offsets)
