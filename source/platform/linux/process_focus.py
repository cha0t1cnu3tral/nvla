# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

import importlib
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Mapping

from platform.common.errors import NotSupportedYetError


class LinuxProcessFocusAdapter:
	"""Process enumeration and X11 EWMH window discovery for the Linux preview."""

	def __init__(
		self,
		*,
		environ: Mapping[str, str] | None = None,
		procDir: Path | str = "/proc",
		loadXlibModules: Callable[[], Any] | None = None,
	) -> None:
		self._environ = os.environ if environ is None else environ
		self._procDir = Path(procDir)
		self._loadXlibModules = loadXlibModules or _loadXlibModules

	def get_desktop_window(self) -> int:
		return self._withX11RootWindow(lambda _modules, _display, rootWindow: int(rootWindow.id))

	def get_foreground_window(self) -> int:
		windowHandles = self._getRootWindowProperty("_NET_ACTIVE_WINDOW")
		if windowHandles is None:
			raise NotSupportedYetError("X11 EWMH active window discovery")
		return windowHandles[0] if windowHandles else 0

	def list_window_handles(self) -> list[int]:
		for propertyName in ("_NET_CLIENT_LIST_STACKING", "_NET_CLIENT_LIST"):
			windowHandles = self._getRootWindowProperty(propertyName)
			if windowHandles is not None:
				return windowHandles
		raise NotSupportedYetError("X11 EWMH window enumeration")

	def list_process_ids(self) -> list[int]:
		try:
			entries = self._procDir.iterdir()
			return sorted(int(entry.name) for entry in entries if entry.name.isdigit())
		except OSError as error:
			raise NotSupportedYetError("Linux /proc process enumeration") from error

	def _getRootWindowProperty(self, propertyName: str) -> list[int] | None:
		def readProperty(modules: Any, display: Any, rootWindow: Any) -> list[int] | None:
			atom = display.intern_atom(propertyName, only_if_exists=True)
			if not atom:
				return None
			propertyValue = rootWindow.get_full_property(atom, modules.X.AnyPropertyType)
			if propertyValue is None:
				return None
			return [int(value) for value in propertyValue.value]

		return self._withX11RootWindow(readProperty)

	def _withX11RootWindow(self, callback: Callable[[Any, Any, Any], Any]) -> Any:
		if not self._environ.get("DISPLAY"):
			raise NotSupportedYetError("X11 desktop window discovery")
		modules = self._loadXlibModules()
		display = modules.display.Display()
		try:
			return callback(modules, display, display.screen().root)
		finally:
			display.close()


def _loadXlibModules() -> Any:
	try:
		return SimpleNamespace(
			X=importlib.import_module("Xlib.X"),
			display=importlib.import_module("Xlib.display"),
		)
	except ImportError as error:
		raise NotSupportedYetError("python-xlib for X11 window discovery") from error
