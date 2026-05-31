# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

import threading
import time
from typing import Any, Callable

from .atspi_backend import ATSPI2Backend, TranslatedATSPIEvent
from .speech import SpeechOutput, createSpeechOutput


def runFocusSpeechSmoke(
	*,
	durationSeconds: float = 30,
	pollIntervalSeconds: float = 0.05,
	backend: Any | None = None,
	speechOutput: SpeechOutput | None = None,
	createOutput: Callable[[], SpeechOutput | None] = createSpeechOutput,
	monotonic: Callable[[], float] = time.monotonic,
	wait: Callable[[float], Any] | None = None,
	write: Callable[[str], None] = print,
) -> int:
	"""Speak focused AT-SPI objects without starting the incomplete NVDA core."""

	if wait is None:
		wait = threading.Event().wait
	output = speechOutput if speechOutput is not None else createOutput()
	if output is None:
		write("Install Speech Dispatcher or espeak-ng before running this smoke tool.")
		return 1
	atspiBackend = backend if backend is not None else ATSPI2Backend()

	def announceFocus(event: TranslatedATSPIEvent) -> None:
		if event.kind != "focus" or not event.isFocused:
			return
		announcement = _formatFocusAnnouncement(event)
		output.cancel()
		output.speak(announcement)
		write(f"focus: {announcement}")

	atspiBackend.registerEventListener(announceFocus)
	try:
		try:
			atspiBackend.initialize()
		except Exception as error:
			write(f"AT-SPI initialization failed: {error}")
			return 2
		write(f"Speech output: {output.name}")
		write("Move focus between applications and controls. Press Ctrl+C to stop.")
		output.speak("AT SPI focus speech smoke started")
		endTime = monotonic() + max(0, durationSeconds)
		while monotonic() < endTime:
			atspiBackend.pump_all()
			remaining = endTime - monotonic()
			if remaining > 0:
				wait(min(pollIntervalSeconds, remaining))
		atspiBackend.pump_all()
	except KeyboardInterrupt:
		write("AT-SPI focus speech smoke interrupted.")
	finally:
		atspiBackend.terminate()
		output.terminate()
	return 0


def _formatFocusAnnouncement(event: TranslatedATSPIEvent) -> str:
	parts = []
	for value in (event.sourceName, event.sourceDescription):
		if value and value not in parts:
			parts.append(value)
	roleLabel = getattr(event.role, "displayString", None)
	if not roleLabel:
		roleLabel = getattr(event.role, "name", str(event.role)).lower()
	if roleLabel and roleLabel not in parts:
		parts.append(roleLabel)
	return ", ".join(parts) or "unknown"
