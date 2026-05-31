# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

import os
import threading
from typing import Any, Callable, Mapping

from .input import KeyboardCaptureMode, LinuxInputAdapter, X11KeyboardEventSource


def runKeyboardSmoke(
	*,
	durationSeconds: float = 15,
	environ: Mapping[str, str] | None = None,
	source: Any | None = None,
	wait: Callable[[float], Any] | None = None,
	write: Callable[[str], None] = print,
) -> int:
	"""Observe live X11 gestures through the preview keyboard backend."""

	if environ is None:
		environ = os.environ
	if environ.get("WAYLAND_DISPLAY"):
		write("Wayland global keyboard capture is not implemented yet.")
		return 1
	if not environ.get("DISPLAY"):
		write("Set DISPLAY and run this tool from an X11 desktop session.")
		return 1
	if wait is None:
		wait = threading.Event().wait
	adapter = LinuxInputAdapter(keyboardEventSource=source if source is not None else X11KeyboardEventSource())
	adapter.registerKeyboardListener(lambda event: write(_formatEvent(event)))
	try:
		adapter.initialize_keyboard(observer=None)
		mode = adapter.keyboardCaptureMode
		write(f"Keyboard capture mode: {mode.value}")
		if mode is KeyboardCaptureMode.LOCAL_ONLY:
			write(f"X11 keyboard observation failed: {adapter.keyboardEventSourceStartError}")
			return 2
		write("Press keys in other applications. Handled keys still reach the focused application.")
		wait(durationSeconds)
	except KeyboardInterrupt:
		write("Keyboard smoke observation interrupted.")
	finally:
		adapter.terminate_keyboard()
	return 0


def _formatEvent(event: Any) -> str:
	action = "down" if event.isPressed else "up"
	passThrough = " passThrough" if event.shouldPassThrough else ""
	return f"{action}: {event.gestureName}{passThrough}"
