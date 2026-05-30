# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from types import SimpleNamespace
import unittest
from unittest import mock

import controlTypes
import textInfos
from platform.linux import accessibility, atspi_backend, atspi_mappings, atspi_objects


class _FakeStateSet:
	def __init__(self, values):
		self._values = tuple(values)

	def getStates(self):
		return self._values


class _FakeComponent:
	def __init__(
		self,
		extents=None,
		position=None,
		size=None,
	):
		self._extents = extents
		self._position = position
		self._size = size

	def getExtents(self, coordType=0):
		if self._extents is None:
			raise RuntimeError("No extents")
		return self._extents

	def getPosition(self, coordType=0):
		if self._position is None:
			raise RuntimeError("No position")
		return self._position

	def getSize(self):
		if self._size is None:
			raise RuntimeError("No size")
		return self._size


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
		children=None,
		component=None,
		extents=None,
		processID=0,
	):
		self._role = role
		self._state = _FakeStateSet(states)
		self.name = name
		self.description = description
		self.path = path
		self._text = text
		self.component = component
		self.extents = extents
		self.processID = processID
		self.children = list(children or ())
		self.parent = None
		self.indexInParent = -1
		for index, child in enumerate(self.children):
			child.parent = self
			child.indexInParent = index

	def getRole(self):
		return self._role

	def getState(self):
		return self._state

	def get_process_id(self):
		return self.processID

	@property
	def childCount(self):
		return len(self.children)

	def getChildAtIndex(self, index):
		return self.children[index]

	def getIndexInParent(self):
		return self.indexInParent

	def queryComponent(self):
		if self.component is None:
			raise RuntimeError("No component interface")
		return self.component

	def queryText(self):
		if self._text is None:
			raise RuntimeError("No text interface")
		return self._text


class _FakeText:
	def __init__(
		self,
		text: str,
		caretOffset: int = 0,
		selection: tuple[int, int] | None = None,
		characterExtents: dict[int, tuple[int, int, int, int]] | None = None,
		rangeExtents: dict[tuple[int, int], tuple[int, int, int, int]] | None = None,
		offsetsByPoint: dict[tuple[int, int], int] | None = None,
		textAtOffset: dict[tuple[int, str], tuple[str, int, int]] | None = None,
	):
		self._text = text
		self.characterCount = len(text)
		self.caretOffset = caretOffset
		self._selection = selection
		self._characterExtents = characterExtents or {}
		self._rangeExtents = rangeExtents or {}
		self._offsetsByPoint = offsetsByPoint or {}
		self._textAtOffset = textAtOffset or {}

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

	def getCharacterExtents(self, offset: int, coordType: int):
		try:
			return self._characterExtents[offset]
		except KeyError:
			raise RuntimeError("No character extents")

	def getRangeExtents(self, start: int, end: int, coordType: int):
		try:
			return self._rangeExtents[(start, end)]
		except KeyError:
			raise RuntimeError("No range extents")

	def getOffsetAtPoint(self, x: int, y: int, coordType: int) -> int:
		try:
			return self._offsetsByPoint[(x, y)]
		except KeyError:
			return -1

	def getTextAtOffset(self, offset: int, boundaryType: str) -> tuple[str, int, int]:
		try:
			return self._textAtOffset[(offset, boundaryType)]
		except KeyError:
			raise RuntimeError("No text at offset")


class TestLinuxAtspiEventTranslation(unittest.TestCase):
	def setUp(self):
		fakeAtspi = SimpleNamespace(
			ROLE_PUSH_BUTTON=10,
			ROLE_ENTRY=11,
			STATE_FOCUSED=1,
			STATE_VISIBLE=2,
			STATE_SHOWING=3,
			STATE_EDITABLE=4,
			STATE_CHECKED=5,
			STATE_DEFUNCT=6,
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
		self.assertEqual(0, translated.sourceProcessID)
		self.assertEqual(controlTypes.Role.BUTTON, translated.role)
		self.assertEqual({controlTypes.State.FOCUSED}, set(translated.states))

	def test_focus_event_adds_focused_state_when_source_snapshot_is_stale(self):
		translated = self._translate(
			SimpleNamespace(
				type="object:state-changed:focused",
				detail1=1,
				source=_FakeSource(role=10, states=(2, 3), name="OK"),
			),
		)

		self.assertTrue(translated.isFocused)
		self.assertIn(controlTypes.State.FOCUSED, translated.states)

	def test_blur_event_removes_focused_state_when_source_snapshot_is_stale(self):
		translated = self._translate(
			SimpleNamespace(
				type="object:state-changed:focused",
				detail1=0,
				source=_FakeSource(role=10, states=(1, 2, 3), name="OK"),
			),
		)

		self.assertFalse(translated.isFocused)
		self.assertNotIn(controlTypes.State.FOCUSED, translated.states)

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

	def test_translates_generic_property_change_event_name_from_detail1(self):
		event = SimpleNamespace(
			type="accessible:property-change",
			detail1="description",
			any_data="Primary editor",
			source=_FakeSource(role=11, states=(2, 3, 4), name="editor"),
		)

		translated = self._translate(event)

		self.assertIsNotNone(translated)
		self.assertEqual("propertyChange", translated.kind)
		self.assertEqual("description", translated.propertyName)
		self.assertEqual("Primary editor", translated.propertyValue)

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

	def test_translates_non_focus_state_change_event(self):
		translated = self._translate(
			SimpleNamespace(
				type="object:state-changed:checked",
				detail1=1,
				source=_FakeSource(role=10, states=(2, 3, 5), name="Remember"),
			),
		)

		self.assertEqual("stateChange", translated.kind)
		self.assertEqual("checked", translated.stateName)
		self.assertTrue(translated.stateEnabled)
		self.assertEqual(controlTypes.State.CHECKED, translated.mappedState)
		self.assertTrue(translated.isMappedStateEnabled)
		self.assertIn(controlTypes.State.CHECKED, translated.states)

	def test_state_change_event_applies_value_when_source_snapshot_is_stale(self):
		checked = self._translate(
			SimpleNamespace(
				type="object:state-changed:checked",
				detail1=1,
				source=_FakeSource(role=10, states=(2, 3), name="Remember"),
			),
		)
		unchecked = self._translate(
			SimpleNamespace(
				type="object:state-changed:checked",
				detail1=0,
				source=_FakeSource(role=10, states=(2, 3, 5), name="Remember"),
			),
		)

		self.assertIn(controlTypes.State.CHECKED, checked.states)
		self.assertNotIn(controlTypes.State.CHECKED, unchecked.states)

	def test_inverted_state_change_event_applies_value_when_source_snapshot_is_stale(self):
		hidden = self._translate(
			SimpleNamespace(
				type="object:state-changed:visible",
				detail1=0,
				source=_FakeSource(role=10, states=(2, 3), name="Button"),
			),
		)
		visible = self._translate(
			SimpleNamespace(
				type="object:state-changed:visible",
				detail1=1,
				source=_FakeSource(role=10, states=(3,), name="Button"),
			),
		)

		self.assertIn(controlTypes.State.INVISIBLE, hidden.states)
		self.assertNotIn(controlTypes.State.INVISIBLE, visible.states)

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

	def test_backend_coalesces_state_changes_per_state_name(self):
		backend = atspi_backend.ATSPI2Backend()
		backend.roleMap = self.roleMap
		backend.stateMap = self.stateMap
		backend.invertedStateValues = self.invertedStateValues
		source = _FakeSource(role=10, states=(2, 3), name="Remember", path=(5, 2))

		for stateName in ("checked", "selected", "checked"):
			backend._onAtspiEvent(
				SimpleNamespace(
					type=f"object:state-changed:{stateName}",
					detail1=1,
					source=source,
				),
			)

		queued = backend.drainTranslatedEvents()
		self.assertEqual(2, len(queued))
		self.assertEqual({"checked", "selected"}, {event.stateName for event in queued})

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
					type="accessible:property-change:name",
					any_data=f"btn{i}",
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
		self.assertEqual("7:1", queued[0].sourceKey)
		self.assertEqual("7:3", queued[-1].sourceKey)

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

	def test_backend_coalesces_focus_events_globally(self):
		backend = atspi_backend.ATSPI2Backend()
		backend.roleMap = self.roleMap
		backend.stateMap = self.stateMap
		backend.invertedStateValues = self.invertedStateValues

		backend._onAtspiEvent(
			SimpleNamespace(
				type="object:state-changed:focused",
				detail1=1,
				source=_FakeSource(role=10, states=(1, 2, 3), name="first", path=(4, 1)),
			),
		)
		backend._onAtspiEvent(
			SimpleNamespace(
				type="object:state-changed:focused",
				detail1=1,
				source=_FakeSource(role=10, states=(1, 2, 3), name="second", path=(4, 2)),
			),
		)

		queued = backend.drainTranslatedEvents()
		self.assertEqual(1, len(queued))
		self.assertEqual("focus", queued[0].kind)
		self.assertEqual("4:2", queued[0].sourceKey)

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

	def test_linux_event_bridge_creates_object_from_source_with_backend_mapping(self):
		backend = atspi_backend.ATSPI2Backend()
		backend.roleMap = self.roleMap
		backend.stateMap = self.stateMap
		backend.invertedStateValues = self.invertedStateValues
		bridge = accessibility.LinuxATSPINVDAEventBridge(backend)

		obj = bridge.getOrCreateObjectForSource(
			_FakeSource(role=11, states=(2, 3, 4), name="editor", description="Desc", path=(7, 3)),
		)

		self.assertIsNotNone(obj)
		self.assertEqual(controlTypes.Role.EDITABLETEXT, obj.role)
		self.assertIn(controlTypes.State.EDITABLE, obj.states)
		self.assertEqual("editor", obj.name)
		self.assertEqual("Desc", obj.description)

	def test_linux_accessibility_adapter_creates_objects_from_accessible_sources(self):
		adapter = accessibility.LinuxAccessibilityAdapter()
		adapter._backend.roleMap = self.roleMap
		adapter._backend.stateMap = self.stateMap
		adapter._backend.invertedStateValues = self.invertedStateValues
		source = _FakeSource(role=10, states=(1, 2, 3), name="OK", path=(3, 1))

		firstObj = adapter.getNVDAObjectFromAccessible(source)
		secondObj = adapter.getNVDAObjectFromAccessible(source)

		self.assertIsNotNone(firstObj)
		self.assertIs(firstObj, secondObj)
		self.assertEqual(controlTypes.Role.BUTTON, firstObj.role)
		self.assertIn(controlTypes.State.FOCUSED, firstObj.states)

	def test_linux_atspi_object_exposes_accessible_process_id(self):
		backend = atspi_backend.ATSPI2Backend()
		backend.roleMap = self.roleMap
		backend.stateMap = self.stateMap
		backend.invertedStateValues = self.invertedStateValues
		bridge = accessibility.LinuxATSPINVDAEventBridge(backend)

		obj = bridge.getOrCreateObjectForSource(
			_FakeSource(role=10, states=(2, 3), name="Button", path=(3, 2), processID=4321),
		)

		self.assertEqual(4321, obj.processID)
		self.assertEqual(4321, obj.appModule.processID)

	def test_linux_event_bridge_namespaces_source_paths_by_process_id(self):
		backend = atspi_backend.ATSPI2Backend()
		backend.roleMap = self.roleMap
		backend.stateMap = self.stateMap
		backend.invertedStateValues = self.invertedStateValues
		bridge = accessibility.LinuxATSPINVDAEventBridge(backend)

		firstObj = bridge.getOrCreateObjectForSource(
			_FakeSource(role=10, states=(2, 3), name="First", path=(3, 2), processID=1001),
		)
		secondObj = bridge.getOrCreateObjectForSource(
			_FakeSource(role=10, states=(2, 3), name="Second", path=(3, 2), processID=1002),
		)

		self.assertIsNot(firstObj, secondObj)
		self.assertEqual("1001:3:2", firstObj.sourceKey)
		self.assertEqual("1002:3:2", secondObj.sourceKey)

	def test_linux_event_bridge_keeps_same_named_sources_without_paths_distinct(self):
		backend = atspi_backend.ATSPI2Backend()
		backend.roleMap = self.roleMap
		backend.stateMap = self.stateMap
		backend.invertedStateValues = self.invertedStateValues
		bridge = accessibility.LinuxATSPINVDAEventBridge(backend)

		firstObj = bridge.getOrCreateObjectForSource(
			_FakeSource(role=10, states=(2, 3), name="Button"),
		)
		secondObj = bridge.getOrCreateObjectForSource(
			_FakeSource(role=10, states=(2, 3), name="Button"),
		)

		self.assertIsNot(firstObj, secondObj)

	def test_linux_event_bridge_keeps_source_without_path_cached_across_rename(self):
		backend = atspi_backend.ATSPI2Backend()
		backend.roleMap = self.roleMap
		backend.stateMap = self.stateMap
		backend.invertedStateValues = self.invertedStateValues
		bridge = accessibility.LinuxATSPINVDAEventBridge(backend)
		source = _FakeSource(role=10, states=(2, 3), name="Old")

		firstObj = bridge.getOrCreateObjectForSource(source)
		source.name = "New"
		secondObj = bridge.getOrCreateObjectForSource(source)

		self.assertIs(firstObj, secondObj)
		self.assertEqual("New", secondObj.name)

	def test_linux_atspi_object_exposes_parent_and_children(self):
		backend = atspi_backend.ATSPI2Backend()
		backend.roleMap = self.roleMap
		backend.stateMap = self.stateMap
		backend.invertedStateValues = self.invertedStateValues
		bridge = accessibility.LinuxATSPINVDAEventBridge(backend)
		firstChild = _FakeSource(role=10, states=(2, 3), name="First", path=(10, 1))
		secondChild = _FakeSource(role=10, states=(2, 3), name="Second", path=(10, 2))
		parent = _FakeSource(
			role=11,
			states=(2, 3, 4),
			name="Parent",
			path=(10,),
			children=(firstChild, secondChild),
		)

		parentObj = bridge.getOrCreateObjectForSource(parent)
		firstObj = bridge.getOrCreateObjectForSource(firstChild)
		secondObj = bridge.getOrCreateObjectForSource(secondChild)

		self.assertIs(firstObj.parent, parentObj)
		self.assertIs(parentObj.firstChild, firstObj)
		self.assertIs(parentObj.lastChild, secondObj)

	def test_linux_atspi_object_exposes_sibling_navigation(self):
		backend = atspi_backend.ATSPI2Backend()
		backend.roleMap = self.roleMap
		backend.stateMap = self.stateMap
		backend.invertedStateValues = self.invertedStateValues
		bridge = accessibility.LinuxATSPINVDAEventBridge(backend)
		firstChild = _FakeSource(role=10, states=(2, 3), name="First", path=(11, 1))
		secondChild = _FakeSource(role=10, states=(2, 3), name="Second", path=(11, 2))
		_FakeSource(
			role=11,
			states=(2, 3, 4),
			name="Parent",
			path=(11,),
			children=(firstChild, secondChild),
		)

		firstObj = bridge.getOrCreateObjectForSource(firstChild)
		secondObj = bridge.getOrCreateObjectForSource(secondChild)

		self.assertIs(firstObj.next, secondObj)
		self.assertIs(secondObj.previous, firstObj)
		self.assertIsNone(firstObj.previous)
		self.assertIsNone(secondObj.next)

	def test_linux_atspi_object_location_uses_component_extents(self):
		backend = atspi_backend.ATSPI2Backend()
		backend.roleMap = self.roleMap
		backend.stateMap = self.stateMap
		backend.invertedStateValues = self.invertedStateValues
		bridge = accessibility.LinuxATSPINVDAEventBridge(backend)
		source = _FakeSource(
			role=10,
			states=(2, 3),
			name="Button",
			path=(12, 1),
			component=_FakeComponent(extents=(10, 20, 100, 30)),
		)

		obj = bridge.getOrCreateObjectForSource(source)

		self.assertEqual((10, 20, 100, 30), tuple(obj.location))
		self.assertEqual(110, obj.location.right)
		self.assertEqual(50, obj.location.bottom)

	def test_linux_atspi_object_location_falls_back_to_accessible_extents(self):
		backend = atspi_backend.ATSPI2Backend()
		backend.roleMap = self.roleMap
		backend.stateMap = self.stateMap
		backend.invertedStateValues = self.invertedStateValues
		bridge = accessibility.LinuxATSPINVDAEventBridge(backend)
		source = _FakeSource(
			role=10,
			states=(2, 3),
			name="Button",
			path=(12, 2),
			extents=(3, 4, 50, 20),
		)

		obj = bridge.getOrCreateObjectForSource(source)

		self.assertEqual((3, 4, 50, 20), tuple(obj.location))

	def test_linux_atspi_object_location_ignores_invalid_extents(self):
		backend = atspi_backend.ATSPI2Backend()
		backend.roleMap = self.roleMap
		backend.stateMap = self.stateMap
		backend.invertedStateValues = self.invertedStateValues
		bridge = accessibility.LinuxATSPINVDAEventBridge(backend)
		source = _FakeSource(
			role=10,
			states=(2, 3),
			name="Button",
			path=(12, 3),
			component=_FakeComponent(extents=(10, 20, -100, 30)),
		)

		obj = bridge.getOrCreateObjectForSource(source)

		self.assertIsNone(obj.location)

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

	def test_linux_event_bridge_routes_generic_property_change_to_state_change(self):
		bridge = accessibility.LinuxATSPINVDAEventBridge()
		event = self._translate(
			SimpleNamespace(
				type="accessible:property-change",
				any_data="opaque",
				source=_FakeSource(role=11, states=(2, 3, 4), name="editor", path=(6, 9)),
			),
		)

		with mock.patch.object(accessibility.eventHandler, "queueEvent") as queueEvent:
			bridge.handleEvent(event)

		self.assertEqual("stateChange", queueEvent.call_args_list[0].args[0])

	def test_linux_event_bridge_routes_object_state_change(self):
		bridge = accessibility.LinuxATSPINVDAEventBridge()
		event = self._translate(
			SimpleNamespace(
				type="object:state-changed:checked",
				detail1=1,
				source=_FakeSource(role=10, states=(2, 3, 5), name="Remember", path=(6, 10)),
			),
		)

		with mock.patch.object(accessibility.eventHandler, "queueEvent") as queueEvent:
			bridge.handleEvent(event)

		self.assertEqual("stateChange", queueEvent.call_args_list[0].args[0])

	def test_linux_event_bridge_accumulates_named_state_changes_from_stale_snapshots(self):
		bridge = accessibility.LinuxATSPINVDAEventBridge()
		source = _FakeSource(role=10, states=(2, 3), name="Remember", path=(6, 11))

		checkedEvent = self._translate(
			SimpleNamespace(
				type="object:state-changed:checked",
				detail1=1,
				source=source,
			),
		)
		selectedEvent = self._translate(
			SimpleNamespace(
				type="object:state-changed:selected",
				detail1=1,
				source=source,
			),
		)

		obj = bridge.getOrCreateObjectForEvent(checkedEvent)
		bridge.getOrCreateObjectForEvent(selectedEvent)

		self.assertIn(controlTypes.State.CHECKED, obj.states)
		self.assertIn(controlTypes.State.SELECTED, obj.states)

	def test_linux_event_bridge_refreshes_snapshot_for_unknown_state_change(self):
		bridge = accessibility.LinuxATSPINVDAEventBridge()
		source = _FakeSource(role=10, states=(2, 3), name="Remember", path=(6, 12))
		obj = bridge.getOrCreateObjectForEvent(
			self._translate(
				SimpleNamespace(
					type="object:state-changed:custom",
					detail1=1,
					source=source,
				),
			),
		)
		source._state = _FakeStateSet((2,))

		bridge.getOrCreateObjectForEvent(
			self._translate(
				SimpleNamespace(
					type="object:state-changed:custom",
					detail1=0,
					source=source,
				),
			),
		)

		self.assertIn(controlTypes.State.OFFSCREEN, obj.states)

	def test_linux_event_bridge_evicts_defunct_object_after_state_dispatch(self):
		bridge = accessibility.LinuxATSPINVDAEventBridge()
		source = _FakeSource(role=10, states=(2, 3), name="Closed", path=(6, 13))
		event = self._translate(
			SimpleNamespace(
				type="object:state-changed:defunct",
				detail1=1,
				source=source,
			),
		)

		with mock.patch.object(accessibility.eventHandler, "queueEvent") as queueEvent:
			firstObj = bridge.getOrCreateObjectForSource(
				source,
				atspi_backend.translate_atspi_source(
					source,
					self.roleMap,
					self.stateMap,
					self.invertedStateValues,
				),
			)
			bridge.handleEvent(event)

		secondObj = bridge.getOrCreateObjectForEvent(event)

		self.assertEqual("stateChange", queueEvent.call_args_list[0].args[0])
		self.assertIsNot(firstObj, secondObj)

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
				source=_FakeSource(role=11, states=(2, 3, 4), name="editor text", path=(6, 2)),
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

	def test_linux_accessibility_adapter_cleans_up_failed_initialization(self):
		adapter = accessibility.LinuxAccessibilityAdapter()
		adapter._eventBridge._objectsByKey["1:10"] = mock.Mock()

		with mock.patch.object(adapter._backend, "initialize", side_effect=RuntimeError("Unavailable")):
			with self.assertRaises(RuntimeError):
				adapter.initialize_iaccessible()

		self.assertFalse(adapter._initialized)
		self.assertEqual([], adapter._backend._eventListeners)
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

	def test_linux_atspi_text_info_uses_character_count_for_story_length(self):
		text = _FakeText("hello world", caretOffset=6)
		text.getText = mock.Mock(wraps=text.getText)
		source = _FakeSource(
			role=11,
			states=(2, 3, 4),
			name="editor",
			path=(3, 8),
			text=text,
		)
		obj = accessibility.LinuxATSPINVDAEventBridge().getOrCreateObjectForEvent(
			self._translate(
				SimpleNamespace(
					type="object:state-changed:focused",
					detail1=1,
					source=source,
				),
			),
		)

		caretText = obj.makeTextInfo(textInfos.POSITION_CARET)

		self.assertEqual((6, 6), caretText.offsets)
		text.getText.assert_not_called()

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

	def test_linux_atspi_text_info_accepts_selection_tuple_with_text(self):
		text = _FakeText("abcde", selection=(1, 4))
		text.getSelection = lambda index: ("bcd", 1, 4)
		source = _FakeSource(
			role=11,
			states=(2, 3, 4),
			name="editor",
			path=(3, 6),
			text=text,
		)
		obj = accessibility.LinuxATSPINVDAEventBridge().getOrCreateObjectForEvent(
			self._translate(
				SimpleNamespace(
					type="object:state-changed:focused",
					detail1=1,
					source=source,
				),
			),
		)

		self.assertEqual((1, 4), obj._getAccessibleSelectionOffsets())

	def test_linux_atspi_text_info_falls_back_from_malformed_selection_tuple(self):
		text = _FakeText("abcde")
		text.getSelection = lambda index: ("invalid",)
		source = _FakeSource(
			role=11,
			states=(2, 3, 4),
			name="editor",
			path=(3, 7),
			text=text,
		)
		obj = accessibility.LinuxATSPINVDAEventBridge().getOrCreateObjectForEvent(
			self._translate(
				SimpleNamespace(
					type="object:state-changed:focused",
					detail1=1,
					source=source,
				),
			),
		)
		obj._selectionOffsets = (2, 3)

		self.assertEqual((2, 3), obj._getAccessibleSelectionOffsets())

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

	def test_linux_atspi_text_info_uses_character_extents_for_point_at_start(self):
		bridge = accessibility.LinuxATSPINVDAEventBridge()
		source = _FakeSource(
			role=11,
			states=(2, 3, 4),
			name="editor",
			path=(4, 1),
			text=_FakeText(
				"abc",
				caretOffset=1,
				characterExtents={
					1: (15, 20, 5, 10),
				},
			),
		)
		obj = bridge.getOrCreateObjectForEvent(
			self._translate(
				SimpleNamespace(
					type="object:state-changed:focused",
					detail1=1,
					source=source,
				),
			),
		)

		caretText = obj.makeTextInfo(textInfos.POSITION_CARET)

		self.assertEqual((15, 20), tuple(caretText.pointAtStart))
		self.assertEqual((15, 20, 5, 10), tuple(caretText._getBoundingRectFromOffset(1)))

	def test_linux_atspi_text_info_uses_range_extents_for_bounding_rects(self):
		bridge = accessibility.LinuxATSPINVDAEventBridge()
		source = _FakeSource(
			role=11,
			states=(2, 3, 4),
			name="editor",
			path=(4, 2),
			text=_FakeText(
				"abcdef",
				rangeExtents={
					(0, 6): (10, 20, 60, 10),
				},
			),
		)
		obj = bridge.getOrCreateObjectForEvent(
			self._translate(
				SimpleNamespace(
					type="object:state-changed:focused",
					detail1=1,
					source=source,
				),
			),
		)

		allText = obj.makeTextInfo(textInfos.POSITION_ALL)

		self.assertEqual([(10, 20, 60, 10)], [tuple(rect) for rect in allText.boundingRects])

	def test_linux_atspi_text_info_supports_hit_testing_from_screen_point(self):
		bridge = accessibility.LinuxATSPINVDAEventBridge()
		source = _FakeSource(
			role=11,
			states=(2, 3, 4),
			name="editor",
			path=(4, 3),
			text=_FakeText(
				"abcdef",
				offsetsByPoint={
					(42, 24): 3,
				},
			),
		)
		obj = bridge.getOrCreateObjectForEvent(
			self._translate(
				SimpleNamespace(
					type="object:state-changed:focused",
					detail1=1,
					source=source,
				),
			),
		)

		textAtPoint = obj.makeTextInfo(atspi_objects.LinuxPoint(42, 24))

		self.assertEqual((3, 3), textAtPoint.offsets)

	def test_linux_atspi_text_info_expands_to_line_from_story_text(self):
		bridge = accessibility.LinuxATSPINVDAEventBridge()
		source = _FakeSource(
			role=11,
			states=(2, 3, 4),
			name="editor",
			path=(4, 4),
			text=_FakeText("alpha\nbravo\ncharlie", caretOffset=8),
		)
		obj = bridge.getOrCreateObjectForEvent(
			self._translate(
				SimpleNamespace(
					type="object:state-changed:focused",
					detail1=1,
					source=source,
				),
			),
		)

		caretText = obj.makeTextInfo(textInfos.POSITION_CARET)
		caretText.expand(textInfos.UNIT_LINE)

		self.assertEqual((6, 12), caretText.offsets)
		self.assertEqual("bravo\n", caretText.text)

	def test_linux_atspi_text_info_expands_to_word_from_story_text(self):
		bridge = accessibility.LinuxATSPINVDAEventBridge()
		source = _FakeSource(
			role=11,
			states=(2, 3, 4),
			name="editor",
			path=(4, 5),
			text=_FakeText("alpha bravo charlie", caretOffset=8),
		)
		obj = bridge.getOrCreateObjectForEvent(
			self._translate(
				SimpleNamespace(
					type="object:state-changed:focused",
					detail1=1,
					source=source,
				),
			),
		)

		caretText = obj.makeTextInfo(textInfos.POSITION_CARET)
		caretText.expand(textInfos.UNIT_WORD)

		self.assertEqual((6, 11), caretText.offsets)
		self.assertEqual("bravo", caretText.text)

	def test_linux_atspi_text_info_prefers_atspi_text_at_offset_for_word(self):
		bridge = accessibility.LinuxATSPINVDAEventBridge()
		source = _FakeSource(
			role=11,
			states=(2, 3, 4),
			name="editor",
			path=(4, 6),
			text=_FakeText(
				"alpha bravo charlie",
				caretOffset=8,
				textAtOffset={
					(8, "TEXT_BOUNDARY_WORD_START"): ("bravo", 6, 11),
				},
			),
		)
		obj = bridge.getOrCreateObjectForEvent(
			self._translate(
				SimpleNamespace(
					type="object:state-changed:focused",
					detail1=1,
					source=source,
				),
			),
		)

		caretText = obj.makeTextInfo(textInfos.POSITION_CARET)
		caretText.expand(textInfos.UNIT_WORD)

		self.assertEqual((6, 11), caretText.offsets)
		self.assertEqual("bravo", caretText.text)

	def test_linux_atspi_text_info_expands_to_sentence_from_story_text(self):
		bridge = accessibility.LinuxATSPINVDAEventBridge()
		source = _FakeSource(
			role=11,
			states=(2, 3, 4),
			name="editor",
			path=(4, 7),
			text=_FakeText("First sentence. Second sentence! Third.", caretOffset=20),
		)
		obj = bridge.getOrCreateObjectForEvent(
			self._translate(
				SimpleNamespace(
					type="object:state-changed:focused",
					detail1=1,
					source=source,
				),
			),
		)

		caretText = obj.makeTextInfo(textInfos.POSITION_CARET)
		caretText.expand(textInfos.UNIT_SENTENCE)

		self.assertEqual((16, 33), caretText.offsets)
		self.assertEqual("Second sentence! ", caretText.text)

	def test_linux_atspi_text_info_expands_to_paragraph_from_story_text(self):
		bridge = accessibility.LinuxATSPINVDAEventBridge()
		source = _FakeSource(
			role=11,
			states=(2, 3, 4),
			name="editor",
			path=(4, 8),
			text=_FakeText("First paragraph.\n\nSecond paragraph line.", caretOffset=22),
		)
		obj = bridge.getOrCreateObjectForEvent(
			self._translate(
				SimpleNamespace(
					type="object:state-changed:focused",
					detail1=1,
					source=source,
				),
			),
		)

		caretText = obj.makeTextInfo(textInfos.POSITION_CARET)
		caretText.expand(textInfos.UNIT_PARAGRAPH)

		self.assertEqual((18, 40), caretText.offsets)
		self.assertEqual("Second paragraph line.", caretText.text)

	def test_linux_atspi_text_info_prefers_atspi_text_at_offset_for_sentence(self):
		bridge = accessibility.LinuxATSPINVDAEventBridge()
		source = _FakeSource(
			role=11,
			states=(2, 3, 4),
			name="editor",
			path=(4, 9),
			text=_FakeText(
				"First sentence. Second sentence!",
				caretOffset=20,
				textAtOffset={
					(20, "TEXT_BOUNDARY_SENTENCE_START"): ("Second sentence!", 16, 32),
				},
			),
		)
		obj = bridge.getOrCreateObjectForEvent(
			self._translate(
				SimpleNamespace(
					type="object:state-changed:focused",
					detail1=1,
					source=source,
				),
			),
		)

		caretText = obj.makeTextInfo(textInfos.POSITION_CARET)
		caretText.expand(textInfos.UNIT_SENTENCE)

		self.assertEqual((16, 32), caretText.offsets)
		self.assertEqual("Second sentence!", caretText.text)
