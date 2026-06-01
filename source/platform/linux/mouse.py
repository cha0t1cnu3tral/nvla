# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import importlib
import threading
from types import SimpleNamespace
from typing import Any, Callable, Protocol

from platform.common.errors import NotSupportedYetError


class MouseCaptureMode(Enum):
	DISABLED = "disabled"
	GLOBAL_OBSERVE_ONLY = "globalObserveOnly"
	LOCAL_ONLY = "localOnly"


@dataclass(frozen=True, slots=True)
class LinuxMouseEvent:
	"""Normalized Linux pointer event used by preview backends and smoke tools."""

	kind: str
	x: int
	y: int
	button: int | None = None


def translateRawMouseEvent(event: Any) -> LinuxMouseEvent:
	return LinuxMouseEvent(
		kind=str(getattr(event, "kind", "move")),
		x=int(getattr(event, "x", 0)),
		y=int(getattr(event, "y", 0)),
		button=getattr(event, "button", None),
	)


class LinuxMouseEventSource(Protocol):
	def start(self, emit: Callable[[Any], LinuxMouseEvent]) -> None: ...

	def stop(self) -> None: ...


class ManualMouseEventSource:
	"""Dependency-light mouse event source used by tests."""

	def __init__(self) -> None:
		self._emit: Callable[[Any], LinuxMouseEvent] | None = None
		self.isStarted = False

	def start(self, emit: Callable[[Any], LinuxMouseEvent]) -> None:
		self._emit = emit
		self.isStarted = True

	def stop(self) -> None:
		self._emit = None
		self.isStarted = False

	def emit(self, event: Any) -> LinuxMouseEvent:
		if self._emit is None:
			raise RuntimeError("Mouse event source has not been started")
		return self._emit(event)


class X11MouseEventSource:
	"""Observe global X11 pointer motion and button events through X RECORD."""

	def __init__(self, *, loadXlibModules: Callable[[], Any] | None = None) -> None:
		self._loadXlibModules = loadXlibModules or _loadXlibModules
		self._emit: Callable[[Any], LinuxMouseEvent] | None = None
		self._modules: Any | None = None
		self._controlDisplay: Any | None = None
		self._recordDisplay: Any | None = None
		self._context: Any | None = None
		self._thread: threading.Thread | None = None

	def start(self, emit: Callable[[Any], LinuxMouseEvent]) -> None:
		if self._thread is not None:
			return
		modules = self._loadXlibModules()
		controlDisplay = modules.display.Display()
		recordDisplay = modules.display.Display()
		try:
			if not controlDisplay.has_extension("RECORD"):
				raise NotSupportedYetError("X11 RECORD extension")
			context = recordDisplay.record_create_context(
				0,
				[modules.record.AllClients],
				[
					{
						"core_requests": (0, 0),
						"core_replies": (0, 0),
						"ext_requests": (0, 0, 0, 0),
						"ext_replies": (0, 0, 0, 0),
						"delivered_events": (0, 0),
						"device_events": (modules.X.ButtonPress, modules.X.MotionNotify),
						"errors": (0, 0),
						"client_started": False,
						"client_died": False,
					},
				],
			)
		except Exception:
			controlDisplay.close()
			recordDisplay.close()
			raise
		self._modules = modules
		self._emit = emit
		self._controlDisplay = controlDisplay
		self._recordDisplay = recordDisplay
		self._context = context
		self._thread = threading.Thread(
			target=recordDisplay.record_enable_context,
			args=(context, self._handleRecordReply),
			name="X11MouseEventSource",
			daemon=True,
		)
		self._thread.start()

	def stop(self) -> None:
		thread = self._thread
		controlDisplay = self._controlDisplay
		context = self._context
		if controlDisplay is not None and context is not None:
			try:
				controlDisplay.record_disable_context(context)
				controlDisplay.flush()
			except Exception:
				pass
		if thread is not None:
			thread.join(timeout=1)
		if controlDisplay is not None and context is not None:
			try:
				controlDisplay.record_free_context(context)
			except Exception:
				pass
		for display in (self._recordDisplay, controlDisplay):
			if display is not None:
				try:
					display.close()
				except Exception:
					pass
		self._emit = None
		self._modules = None
		self._controlDisplay = None
		self._recordDisplay = None
		self._context = None
		self._thread = None

	def _handleRecordReply(self, reply: Any) -> None:
		modules = self._modules
		emit = self._emit
		if (
			modules is None
			or emit is None
			or reply.category != modules.record.FromServer
			or reply.client_swapped
			or not reply.data
		):
			return
		data = reply.data
		while data:
			event, data = modules.rq.EventField(None).parse_binary_value(
				data,
				self._recordDisplay.display,
				None,
				None,
			)
			kind = {
				modules.X.ButtonPress: "buttonDown",
				modules.X.ButtonRelease: "buttonUp",
				modules.X.MotionNotify: "move",
			}.get(event.type)
			if kind is None:
				continue
			emit(
				SimpleNamespace(
					kind=kind,
					x=event.root_x,
					y=event.root_y,
					button=event.detail if kind != "move" else None,
				),
			)


class WaylandMouseEventSource:
	"""Wayland pointer event source placeholder for compositor-backed capture."""

	def start(self, emit: Callable[[Any], LinuxMouseEvent]) -> None:
		raise NotSupportedYetError("Wayland global mouse observation")

	def stop(self) -> None:
		return None


def createMouseEventSource(environ: Any) -> LinuxMouseEventSource | None:
	if environ.get("WAYLAND_DISPLAY"):
		return WaylandMouseEventSource()
	if environ.get("DISPLAY"):
		return X11MouseEventSource()
	return None


def _loadXlibModules() -> Any:
	try:
		return SimpleNamespace(
			X=importlib.import_module("Xlib.X"),
			display=importlib.import_module("Xlib.display"),
			record=importlib.import_module("Xlib.ext.record"),
			rq=importlib.import_module("Xlib.protocol.rq"),
		)
	except ImportError as error:
		raise NotSupportedYetError("python-xlib for X11 global mouse observation") from error
