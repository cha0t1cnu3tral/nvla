# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

from dataclasses import dataclass
import shutil
import subprocess
from typing import Any, Callable, Protocol, Sequence


class SpeechOutput(Protocol):
	"""Small Linux-native speech transport used before the full audio backend exists."""

	name: str

	def speak(self, text: str) -> Any: ...

	def cancel(self) -> None: ...

	def terminate(self) -> None: ...


@dataclass(frozen=True)
class SpeechCommand:
	name: str
	executable: str
	speakArguments: tuple[str, ...] = ()
	cancelArguments: tuple[str, ...] | None = None


_SPEECH_DISPATCHER_COMMAND = SpeechCommand(
	name="speechDispatcher",
	executable="spd-say",
	speakArguments=("--wait",),
	cancelArguments=("--cancel",),
)
_ESPEAK_NG_COMMAND = SpeechCommand(
	name="espeakNg",
	executable="espeak-ng",
)


class CommandSpeechOutput:
	"""Launch speech through a Linux command-line client and track active requests."""

	def __init__(
		self,
		command: SpeechCommand,
		executablePath: str,
		popen: Callable[..., Any] = subprocess.Popen,
		run: Callable[..., Any] = subprocess.run,
	) -> None:
		self.command = command
		self.executablePath = executablePath
		self._popen = popen
		self._run = run
		self._processes: list[Any] = []

	@property
	def name(self) -> str:
		return self.command.name

	def speak(self, text: str) -> Any:
		self._discardFinishedProcesses()
		process = self._popen(
			[self.executablePath, *self.command.speakArguments, text],
			stdin=subprocess.DEVNULL,
			stdout=subprocess.DEVNULL,
			stderr=subprocess.DEVNULL,
		)
		self._processes.append(process)
		return process

	def cancel(self) -> None:
		for process in self._processes:
			if process.poll() is None:
				process.terminate()
		self._processes.clear()
		if self.command.cancelArguments is not None:
			self._run(
				[self.executablePath, *self.command.cancelArguments],
				check=False,
				stdin=subprocess.DEVNULL,
				stdout=subprocess.DEVNULL,
				stderr=subprocess.DEVNULL,
			)

	def terminate(self) -> None:
		self.cancel()

	def _discardFinishedProcesses(self) -> None:
		self._processes = [process for process in self._processes if process.poll() is None]


def createSpeechOutput(
	which: Callable[[str], str | None] = shutil.which,
	popen: Callable[..., Any] = subprocess.Popen,
	run: Callable[..., Any] = subprocess.run,
	commands: Sequence[SpeechCommand] = (
		_SPEECH_DISPATCHER_COMMAND,
		_ESPEAK_NG_COMMAND,
	),
) -> CommandSpeechOutput | None:
	"""Create the preferred available Linux speech transport."""

	for command in commands:
		executablePath = which(command.executable)
		if executablePath is not None:
			return CommandSpeechOutput(
				command=command,
				executablePath=executablePath,
				popen=popen,
				run=run,
			)
	return None
