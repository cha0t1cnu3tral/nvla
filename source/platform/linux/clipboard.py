# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

from dataclasses import dataclass
import os
import shutil
import subprocess
from typing import Any, Callable, Mapping, Sequence

from platform.common.errors import NotSupportedYetError


@dataclass(frozen=True)
class ClipboardCommand:
	name: str
	readExecutable: str
	readArguments: tuple[str, ...]
	writeExecutable: str
	writeArguments: tuple[str, ...]
	requiresWayland: bool = False


_CLIPBOARD_COMMANDS = (
	ClipboardCommand(
		name="wayland",
		readExecutable="wl-paste",
		readArguments=("--no-newline",),
		writeExecutable="wl-copy",
		writeArguments=(),
		requiresWayland=True,
	),
	ClipboardCommand(
		name="xclip",
		readExecutable="xclip",
		readArguments=("-selection", "clipboard", "-out"),
		writeExecutable="xclip",
		writeArguments=("-selection", "clipboard", "-in"),
	),
	ClipboardCommand(
		name="xsel",
		readExecutable="xsel",
		readArguments=("--clipboard", "--output"),
		writeExecutable="xsel",
		writeArguments=("--clipboard", "--input"),
	),
)


class LinuxClipboardAdapter:
	"""Text clipboard integration using common Wayland and X11 clients."""

	def __init__(
		self,
		*,
		environ: Mapping[str, str] | None = None,
		which: Callable[[str], str | None] = shutil.which,
		run: Callable[..., Any] = subprocess.run,
		commands: Sequence[ClipboardCommand] = _CLIPBOARD_COMMANDS,
	) -> None:
		self._environ = os.environ if environ is None else environ
		self._run = run
		self._command = self._selectCommand(which, commands)

	@property
	def available(self) -> bool:
		return self._command is not None

	def get_text(self) -> str:
		command = self._requireCommand()
		result = self._run(
			[command.readExecutable, *command.readArguments],
			check=True,
			capture_output=True,
			text=True,
		)
		return result.stdout

	def set_text(self, text: str) -> None:
		command = self._requireCommand()
		self._run(
			[command.writeExecutable, *command.writeArguments],
			check=True,
			input=text,
			text=True,
		)

	def _selectCommand(
		self,
		which: Callable[[str], str | None],
		commands: Sequence[ClipboardCommand],
	) -> ClipboardCommand | None:
		for command in commands:
			if command.requiresWayland and not self._environ.get("WAYLAND_DISPLAY"):
				continue
			if which(command.readExecutable) is not None and which(command.writeExecutable) is not None:
				return command
		return None

	def _requireCommand(self) -> ClipboardCommand:
		if self._command is None:
			raise NotSupportedYetError("Linux text clipboard client")
		return self._command
