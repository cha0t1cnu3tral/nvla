# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

"""Run dependency-light Linux port unit tests from a Windows checkout.

The normal unit bootstrap initializes large parts of NVDA and requires built
Windows helper DLLs. The early Linux-port tests only need PAL/AT-SPI mapping,
event translation, and a small NVDAObject/TextInfo surface, so this runner
installs focused stubs before loading those test modules by file path.
"""

from __future__ import annotations

import argparse
from enum import Enum, auto
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest


ROOT_DIR = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT_DIR / "source"
DEFAULT_TESTS = (
	ROOT_DIR / "tests" / "unit" / "test_linuxAtspiMappings.py",
	ROOT_DIR / "tests" / "unit" / "test_linuxAtspiEventTranslation.py",
)


class _AutoNameEnum(Enum):
	def _generate_next_value_(name, start, count, last_values):
		return name


class _Role(_AutoNameEnum):
	UNKNOWN = auto()
	APPLICATION = auto()
	ALERT = auto()
	DIALOG = auto()
	FRAME = auto()
	WINDOW = auto()
	LABEL = auto()
	STATICTEXT = auto()
	EDITABLETEXT = auto()
	PASSWORDEDIT = auto()
	BUTTON = auto()
	TOGGLEBUTTON = auto()
	CHECKBOX = auto()
	RADIOBUTTON = auto()
	POPUPMENU = auto()
	MENUBAR = auto()
	MENUITEM = auto()
	CHECKMENUITEM = auto()
	RADIOMENUITEM = auto()
	COMBOBOX = auto()
	LIST = auto()
	LISTITEM = auto()
	TREEVIEW = auto()
	TREEVIEWITEM = auto()
	TABLE = auto()
	TABLECELL = auto()
	TABLECOLUMNHEADER = auto()
	TABLEROWHEADER = auto()
	LINK = auto()
	GRAPHIC = auto()
	PROGRESSBAR = auto()
	SCROLLBAR = auto()
	SLIDER = auto()
	TOOLTIP = auto()
	STATUSBAR = auto()
	TOOLBAR = auto()
	TAB = auto()
	TABCONTROL = auto()
	PARAGRAPH = auto()
	HEADING = auto()
	SECTION = auto()
	DOCUMENT = auto()


class _State(_AutoNameEnum):
	FOCUSED = auto()
	FOCUSABLE = auto()
	SELECTABLE = auto()
	SELECTED = auto()
	INVISIBLE = auto()
	OFFSCREEN = auto()
	EDITABLE = auto()
	READONLY = auto()
	MULTILINE = auto()
	REQUIRED = auto()
	CHECKABLE = auto()
	CHECKED = auto()
	INDETERMINATE = auto()
	PRESSED = auto()
	EXPANDED = auto()
	COLLAPSED = auto()
	BUSY = auto()
	MODAL = auto()
	VISITED = auto()
	DEFUNCT = auto()


def _install_control_types_stub() -> None:
	module = ModuleType("controlTypes")
	module.Role = _Role
	module.State = _State
	sys.modules["controlTypes"] = module


def _install_text_infos_stub() -> None:
	module = ModuleType("textInfos")
	module.POSITION_ALL = "all"
	module.POSITION_CARET = "caret"
	module.POSITION_FIRST = "first"
	module.UNIT_CHARACTER = "character"

	class OffsetsTextInfo:
		def __init__(self, obj, position):
			self.obj = obj
			if hasattr(position, "x") and hasattr(position, "y"):
				offset = self._getOffsetFromPoint(position.x, position.y)
				self._startOffset = self._endOffset = offset
			elif position == module.POSITION_ALL:
				self._startOffset = 0
				self._endOffset = self._getStoryLength()
			elif position == module.POSITION_CARET:
				self._startOffset = self._endOffset = self._getCaretOffset()
			else:
				self._startOffset = self._endOffset = 0

		@property
		def offsets(self):
			return self._startOffset, self._endOffset

		@property
		def text(self):
			return self._getStoryText()[self._startOffset : self._endOffset]

		@property
		def boundingRects(self):
			return self._get_boundingRects()

		@property
		def pointAtStart(self):
			return self._get_pointAtStart()

		def _get_boundingRects(self):
			if self._startOffset == self._endOffset:
				return []
			return [self._getBoundingRectFromOffset(self._startOffset)]

		def _get_pointAtStart(self):
			return self._getBoundingRectFromOffset(self._startOffset).topLeft

		def move(self, unit, direction):
			if unit != module.UNIT_CHARACTER:
				raise NotImplementedError("Only character movement is supported")
			offset = max(0, min(self._endOffset + direction, self._getStoryLength()))
			self._startOffset = self._endOffset = offset
			return direction

		def setEndPoint(self, other, relation):
			if relation != "endToEnd":
				raise NotImplementedError("Only endToEnd is supported")
			self._endOffset = other._endOffset

		def updateCaret(self):
			self._setCaretOffset(self._endOffset)

		def updateSelection(self):
			self._setSelectionOffsets(self._startOffset, self._endOffset)

	module.OffsetsTextInfo = OffsetsTextInfo
	sys.modules["textInfos"] = module


def _install_nvda_object_stub() -> None:
	textInfos = sys.modules["textInfos"]
	module = ModuleType("NVDAObjects")

	class NVDAObjectTextInfo(textInfos.OffsetsTextInfo):
		def _getStoryText(self):
			return self.obj.basicText

		def _getStoryLength(self):
			return len(self._getStoryText())

		def _getCaretOffset(self):
			return 0

		def _setCaretOffset(self, offset):
			return None

		def _getSelectionOffsets(self):
			return None

		def _setSelectionOffsets(self, start, end):
			return None

	class NVDAObject:
		TextInfo = NVDAObjectTextInfo

		def __init__(self, *args, **kwargs):
			super().__init__()

		def __getattr__(self, name):
			getter = getattr(self, f"_get_{name}", None)
			if getter is not None:
				return getter()
			raise AttributeError(name)

		def makeTextInfo(self, position):
			return self.TextInfo(self, position)

	module.NVDAObject = NVDAObject
	module.NVDAObjectTextInfo = NVDAObjectTextInfo
	sys.modules["NVDAObjects"] = module


def _install_core_stubs() -> None:
	api = ModuleType("api")
	api.setFocusObject = lambda obj: None
	sys.modules["api"] = api

	eventHandler = ModuleType("eventHandler")
	eventHandler.queueEvent = lambda name, obj: None
	sys.modules["eventHandler"] = eventHandler

	logHandler = ModuleType("logHandler")
	logHandler.log = SimpleNamespace(
		debug=lambda *args, **kwargs: None,
		exception=lambda *args, **kwargs: None,
	)
	sys.modules["logHandler"] = logHandler


def _load_local_platform_package() -> None:
	sys.path.insert(0, str(SOURCE_DIR))
	spec = importlib.util.spec_from_file_location(
		"platform",
		SOURCE_DIR / "platform" / "__init__.py",
		submodule_search_locations=[str(SOURCE_DIR / "platform")],
	)
	if spec is None or spec.loader is None:
		raise RuntimeError("Unable to load local platform package")
	module = importlib.util.module_from_spec(spec)
	sys.modules["platform"] = module
	spec.loader.exec_module(module)


def _load_test_module(path: Path) -> ModuleType:
	moduleName = f"_linux_port_{path.stem}"
	spec = importlib.util.spec_from_file_location(moduleName, path)
	if spec is None or spec.loader is None:
		raise RuntimeError(f"Unable to load test module: {path}")
	module = importlib.util.module_from_spec(spec)
	sys.modules[moduleName] = module
	spec.loader.exec_module(module)
	return module


def _install_stubs() -> None:
	_install_control_types_stub()
	_install_text_infos_stub()
	_install_nvda_object_stub()
	_install_core_stubs()
	_load_local_platform_package()


def main(argv: list[str] | None = None) -> int:
	parser = argparse.ArgumentParser()
	parser.add_argument(
		"tests",
		nargs="*",
		type=Path,
		default=DEFAULT_TESTS,
		help="Linux-port test files to run. Defaults to the AT-SPI focused unit tests.",
	)
	args = parser.parse_args(argv)

	_install_stubs()
	loader = unittest.TestLoader()
	suite = unittest.TestSuite()
	for testPath in args.tests:
		path = testPath if testPath.is_absolute() else ROOT_DIR / testPath
		suite.addTests(loader.loadTestsFromModule(_load_test_module(path)))
	result = unittest.TextTestRunner(verbosity=2).run(suite)
	return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
	raise SystemExit(main())
