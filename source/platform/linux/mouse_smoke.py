# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

import os
import threading
from typing import Any, Callable, Mapping

from .input import LinuxInputAdapter
from .mouse import MouseCaptureMode, X11MouseEventSource


def runMouseSmoke(
	*,
	durationSeconds: float = 15,
	environ: Mapping[str, str] | None = None,
	source: Any | None = None,
	wait: Callable[[float], Any] | None = None,
	write: Callable[[str], None] = print,
) -> int:
	"""Observe live X11 pointer events through the preview mouse backend."""

	if environ is None:
		environ = os.environ
	if environ.get("WAYLAND_DISPLAY"):
		write("Wayland global mouse observation is not implemented yet.")
		return 1
	if not environ.get("DISPLAY"):
		write("Set DISPLAY and run this tool from an X11 desktop session.")
		return 1
	if wait is None:
		wait = threading.Event().wait
	if source is None:
		source = X11MouseEventSource()
	adapter = LinuxInputAdapter()
	adapter.registerMouseListener(lambda event: write(_formatEvent(event)))
	try:
		adapter.initialize_mouse(eventSource=source)
		mode = adapter.mouseCaptureMode
		write(f"Mouse capture mode: {mode.value}")
		if mode is MouseCaptureMode.LOCAL_ONLY:
			write(f"X11 mouse observation failed: {adapter.mouseEventSourceStartError}")
			return 2
		write("Move and click the pointer in other applications.")
		wait(durationSeconds)
	except KeyboardInterrupt:
		write("Mouse smoke observation interrupted.")
	finally:
		adapter.terminate_mouse()
	return 0


def _formatEvent(event: Any) -> str:
	button = f" button={event.button}" if event.button is not None else ""
	return f"{event.kind}: x={event.x} y={event.y}{button}"
