# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from enum import Enum, auto
import importlib
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest import mock


_ROLE_NAMES = (
	"APPLICATION ALERT DIALOG FRAME WINDOW LABEL STATICTEXT EDITABLETEXT PASSWORDEDIT "
	"BUTTON TOGGLEBUTTON CHECKBOX RADIOBUTTON POPUPMENU MENUBAR MENUITEM CHECKMENUITEM "
	"RADIOMENUITEM COMBOBOX LIST LISTITEM TREEVIEW TREEVIEWITEM TABLE TABLECELL "
	"TABLECOLUMNHEADER TABLEROWHEADER LINK GRAPHIC PROGRESSBAR SCROLLBAR SLIDER TOOLTIP "
	"STATUSBAR TOOLBAR TAB TABCONTROL PARAGRAPH HEADING SECTION DOCUMENT UNKNOWN"
)
_STATE_NAMES = (
	"FOCUSED FOCUSABLE SELECTABLE SELECTED INVISIBLE OFFSCREEN EDITABLE READONLY MULTILINE "
	"REQUIRED CHECKABLE CHECKED INDETERMINATE PRESSED EXPANDED COLLAPSED BUSY MODAL VISITED DEFUNCT"
)


class _Accessible:
	def __init__(self, children=(), hit=None):
		self.children = tuple(children)
		self.hit = hit

	def __iter__(self):
		return iter(self.children)

	def queryComponent(self):
		return SimpleNamespace(getAccessibleAtPoint=lambda x, y, coordinateType: self.hit)


def _loadBackendModule():
	controlTypes = ModuleType("controlTypes")
	controlTypes.Role = Enum("Role", _ROLE_NAMES)
	controlTypes.State = Enum("State", _STATE_NAMES)
	logHandler = ModuleType("logHandler")
	logHandler.log = SimpleNamespace(
		debug=lambda *args, **kwargs: None,
		exception=lambda *args, **kwargs: None,
	)
	for moduleName in ("platform.linux.atspi_backend", "platform.linux.atspi_mappings"):
		sys.modules.pop(moduleName, None)
	with mock.patch.dict(
		sys.modules,
		{
			"controlTypes": controlTypes,
			"logHandler": logHandler,
		},
	):
		return importlib.import_module("platform.linux.atspi_backend")


class TestLinuxAtspiHitTesting(unittest.TestCase):
	def test_returns_accessible_at_point_from_topmost_desktop_application(self):
		backendModule = _loadBackendModule()
		firstHit = object()
		secondHit = object()
		desktop = _Accessible(
			children=(
				_Accessible(hit=firstHit),
				_Accessible(hit=secondHit),
			),
		)
		backend = backendModule.ATSPI2Backend()
		backend._initialized = True
		backend._atspi = SimpleNamespace(
			DESKTOP_COORDS=1,
			Registry=SimpleNamespace(
				getDesktopCount=lambda: 1,
				getDesktop=lambda index: desktop,
			),
		)

		self.assertIs(secondHit, backend.getAccessibleAtPoint(10, 20))

	def test_returns_none_before_backend_initialization(self):
		backendModule = _loadBackendModule()

		self.assertIsNone(backendModule.ATSPI2Backend().getAccessibleAtPoint(10, 20))

	def test_returns_none_when_no_application_contains_point(self):
		backendModule = _loadBackendModule()
		desktop = _Accessible(children=(_Accessible(hit=None),))
		backend = backendModule.ATSPI2Backend()
		backend._initialized = True
		backend._atspi = SimpleNamespace(
			Registry=SimpleNamespace(
				getDesktopCount=lambda: 1,
				getDesktop=lambda index: desktop,
			),
		)

		self.assertIsNone(backend.getAccessibleAtPoint(10, 20))


if __name__ == "__main__":
	unittest.main()
