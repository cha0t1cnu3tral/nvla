# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import math
import os
import shutil
import struct
import subprocess
import tempfile
import threading
from typing import Any, Callable, Sequence
import wave


@dataclass(frozen=True)
class AudioCommand:
	name: str
	executable: str


_AUDIO_COMMANDS = (
	AudioCommand(name="pipeWire", executable="pw-play"),
	AudioCommand(name="pulseAudio", executable="paplay"),
	AudioCommand(name="alsa", executable="aplay"),
)
_TONE_SAMPLE_RATE = 44100


class LinuxAudioAdapter:
	"""Command-backed wave and tone output for the early Linux preview."""

	def __init__(
		self,
		*,
		which: Callable[[str], str | None] = shutil.which,
		popen: Callable[..., Any] = subprocess.Popen,
		commands: Sequence[AudioCommand] = _AUDIO_COMMANDS,
	) -> None:
		self._which = which
		self._popen = popen
		self._commands = commands
		self._executablePath: str | None = None
		self._processes: list[Any] = []
		self._lock = threading.Lock()

	@property
	def available(self) -> bool:
		return self._executablePath is not None

	def initialize(self) -> None:
		for command in self._commands:
			executablePath = self._which(command.executable)
			if executablePath is not None:
				self._executablePath = executablePath
				return
		self._executablePath = None

	def play_wave_file(self, path: str, asynchronous: bool = True) -> None:
		self._playPath(path, asynchronous=asynchronous)

	def beep(self, hz: float, length: int, left: int = 50, right: int = 50) -> None:
		if not self.available:
			return
		with tempfile.NamedTemporaryFile(prefix="nvda-tone-", suffix=".wav", delete=False) as toneFile:
			toneFile.write(_generateToneWave(hz=hz, length=length, left=left, right=right))
			path = toneFile.name
		try:
			self._playPath(path, asynchronous=True, deleteAfterPlayback=True)
		except Exception:
			os.unlink(path)
			raise

	def terminate(self) -> None:
		with self._lock:
			processes = self._processes
			self._processes = []
		for process in processes:
			if process.poll() is None:
				process.terminate()

	def _playPath(
		self,
		path: str,
		*,
		asynchronous: bool,
		deleteAfterPlayback: bool = False,
	) -> None:
		if not self.available:
			if deleteAfterPlayback:
				os.unlink(path)
			return
		self._discardFinishedProcesses()
		process = self._popen(
			[self._executablePath, path],
			stdin=subprocess.DEVNULL,
			stdout=subprocess.DEVNULL,
			stderr=subprocess.DEVNULL,
		)
		with self._lock:
			self._processes.append(process)
		if asynchronous:
			threading.Thread(
				target=self._waitForPlayback,
				args=(process, path if deleteAfterPlayback else None),
				name=f"LinuxAudioAdapter({os.path.basename(path)})",
				daemon=True,
			).start()
			return
		self._waitForPlayback(process, path if deleteAfterPlayback else None)

	def _waitForPlayback(self, process: Any, deletePath: str | None) -> None:
		try:
			process.wait()
		finally:
			with self._lock:
				if process in self._processes:
					self._processes.remove(process)
			if deletePath is not None:
				try:
					os.unlink(deletePath)
				except FileNotFoundError:
					pass

	def _discardFinishedProcesses(self) -> None:
		with self._lock:
			self._processes = [process for process in self._processes if process.poll() is None]


def _generateToneWave(*, hz: float, length: int, left: int, right: int) -> bytes:
	"""Generate a stereo PCM WAV tone accepted by common Linux audio clients."""

	if hz <= 0:
		raise ValueError("Tone frequency must be positive")
	if length < 0:
		raise ValueError("Tone length must not be negative")
	if not 0 <= left <= 100 or not 0 <= right <= 100:
		raise ValueError("Tone channel volumes must be between 0 and 100")
	frameCount = int(_TONE_SAMPLE_RATE * length / 1000)
	frames = bytearray()
	for sampleIndex in range(frameCount):
		sample = math.sin(2 * math.pi * hz * sampleIndex / _TONE_SAMPLE_RATE)
		frames.extend(
			struct.pack(
				"<hh",
				int(32767 * sample * left / 100),
				int(32767 * sample * right / 100),
			),
		)
	buffer = BytesIO()
	with wave.open(buffer, "wb") as waveFile:
		waveFile.setnchannels(2)
		waveFile.setsampwidth(2)
		waveFile.setframerate(_TONE_SAMPLE_RATE)
		waveFile.writeframes(frames)
	return buffer.getvalue()
