# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

import sys
from threading import Thread
from typing import Any

from platform.linux.speech import createSpeechOutput
from speech.commands import IndexCommand
from synthDriverHandler import (
	SynthDriver as BaseSynthDriver,
	VoiceInfo,
	synthDoneSpeaking,
	synthIndexReached,
)


class SynthDriver(BaseSynthDriver):
	"""Initial Linux speech driver using Speech Dispatcher or eSpeak NG commands."""

	name = "linuxSpeech"
	description = "Linux speech (Speech Dispatcher or eSpeak NG)"
	supportedSettings = frozenset()
	supportedCommands = {IndexCommand}
	supportedNotifications = {synthIndexReached, synthDoneSpeaking}

	@classmethod
	def check(cls):
		return sys.platform.startswith("linux") and createSpeechOutput() is not None

	def __init__(self):
		self._output = createSpeechOutput()
		if self._output is None:
			raise RuntimeError("No supported Linux speech command was found")
		self._generation = 0
		self._voice = self._output.name
		self._availableVoices = {
			self._voice: VoiceInfo(self._voice, self._voice),
		}

	def speak(self, speechSequence):
		self.cancel()
		textParts: list[str] = []
		lastIndex: int | None = None
		for item in speechSequence:
			if isinstance(item, str):
				textParts.append(item)
			elif isinstance(item, IndexCommand):
				lastIndex = item.index
		text = "".join(textParts)
		generation = self._generation
		if not text:
			self._notifyDone(generation, lastIndex)
			return
		process = self._output.speak(text)
		Thread(
			target=self._waitForSpeech,
			args=(process, generation, lastIndex),
			name="linuxSpeechWait",
			daemon=True,
		).start()

	def cancel(self):
		self._generation += 1
		output = getattr(self, "_output", None)
		if output is not None:
			output.cancel()

	def pause(self, switch):
		if switch:
			self.cancel()

	def terminate(self):
		self._generation += 1
		self._output.terminate()

	def _waitForSpeech(self, process: Any, generation: int, lastIndex: int | None):
		process.wait()
		self._notifyDone(generation, lastIndex)

	def _notifyDone(self, generation: int, lastIndex: int | None):
		if generation != self._generation:
			return
		if lastIndex is not None:
			synthIndexReached.notify(synth=self, index=lastIndex)
		synthDoneSpeaking.notify(synth=self)

	def _get_voice(self):
		return self._voice
