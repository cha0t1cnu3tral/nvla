# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from types import SimpleNamespace
import unittest

import controlTypes
from platform.linux import atspi_mappings


class TestLinuxAtspiMappings(unittest.TestCase):
	def test_role_mapping_fallback(self):
		fakeAtspi = SimpleNamespace(
			ROLE_PUSH_BUTTON=10,
		)
		roleMap = atspi_mappings.build_role_map(fakeAtspi)

		self.assertEqual(
			controlTypes.Role.BUTTON,
			atspi_mappings.map_role(10, roleMap),
		)
		self.assertEqual(
			controlTypes.Role.UNKNOWN,
			atspi_mappings.map_role(999, roleMap),
		)

	def test_maps_browser_document_roles(self):
		fakeAtspi = SimpleNamespace(
			ROLE_DOCUMENT_FRAME=10,
			ROLE_DOCUMENT_WEB=11,
			ROLE_DOCUMENT_TEXT=12,
			ROLE_DOCUMENT_EMAIL=13,
		)
		roleMap = atspi_mappings.build_role_map(fakeAtspi)

		for role in (10, 11, 12, 13):
			with self.subTest(role=role):
				self.assertEqual(controlTypes.Role.DOCUMENT, atspi_mappings.map_role(role, roleMap))

	def test_state_mapping_handles_inverted_visibility(self):
		fakeAtspi = SimpleNamespace(
			STATE_FOCUSED=1,
			STATE_VISIBLE=2,
			STATE_SHOWING=3,
			STATE_CHECKED=4,
		)
		stateMap, inverted = atspi_mappings.build_state_map(fakeAtspi)

		# Visible/showing are inverted in NVDA flags: only add INVISIBLE/OFFSCREEN when missing.
		mappedVisible = atspi_mappings.map_states((1, 2, 3, 4), stateMap, inverted)
		self.assertEqual(
			{
				controlTypes.State.FOCUSED,
				controlTypes.State.CHECKED,
			},
			mappedVisible,
		)

		mappedHidden = atspi_mappings.map_states((1, 4), stateMap, inverted)
		self.assertEqual(
			{
				controlTypes.State.FOCUSED,
				controlTypes.State.CHECKED,
				controlTypes.State.INVISIBLE,
				controlTypes.State.OFFSCREEN,
			},
			mappedHidden,
		)

	def test_missing_constants_are_ignored(self):
		fakeAtspi = SimpleNamespace()
		roleMap = atspi_mappings.build_role_map(fakeAtspi)
		stateMap, inverted = atspi_mappings.build_state_map(fakeAtspi)
		self.assertEqual({}, roleMap)
		self.assertEqual({}, stateMap)
		self.assertEqual(set(), inverted)

	def test_maps_named_state_event(self):
		self.assertEqual(
			(controlTypes.State.CHECKED, False),
			atspi_mappings.map_state_name("checked"),
		)
		self.assertEqual(
			(controlTypes.State.INVISIBLE, True),
			atspi_mappings.map_state_name("visible"),
		)
		self.assertIsNone(atspi_mappings.map_state_name("not-real"))
