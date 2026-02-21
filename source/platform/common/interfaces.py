# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class AccessibilityAdapter(Protocol):
	"""Object tree, event pumping, and text-range-related accessibility hooks."""

	def initialize(self) -> None: ...

	def pump_all(self) -> None: ...

	def terminate(self) -> None: ...

	def initialize_uia(self) -> None: ...

	def terminate_uia(self) -> None: ...

	def initialize_iaccessible(self) -> None: ...

	def terminate_iaccessible(self) -> None: ...

	def initialize_legacy_console_support(self) -> None: ...

	def terminate_legacy_console_support(self) -> None: ...


class InputAdapter(Protocol):
	"""Keyboard/mouse/touch hooks."""

	def initialize_keyboard(self, observer: Any) -> None: ...

	def initialize_mouse(self) -> None: ...

	def initialize_touch(self) -> None: ...

	def terminate_keyboard(self) -> None: ...

	def terminate_mouse(self) -> None: ...

	def terminate_touch(self) -> None: ...


class AudioAdapter(Protocol):
	"""Audio output and tones/wave playback hooks."""

	def initialize(self) -> None: ...

	def play_wave_file(self, path: str, asynchronous: bool = True) -> None: ...

	def beep(self, hz: int, length: int, left: int = 50, right: int = 50) -> None: ...

	def terminate(self) -> None: ...


class ClipboardAdapter(Protocol):
	"""Clipboard integration."""

	def get_text(self) -> str: ...

	def set_text(self, text: str) -> None: ...


class SystemAdapter(Protocol):
	"""System info and power/battery hooks."""

	def get_os_version_string(self) -> str: ...

	def register_application_restart(self) -> None: ...

	def get_battery_status(self) -> str: ...


class ProcessFocusAdapter(Protocol):
	"""Process/window enumeration and focus tracking primitives."""

	def get_desktop_window(self) -> int: ...

	def get_foreground_window(self) -> int: ...

	def list_window_handles(self) -> list[int]: ...

	def list_process_ids(self) -> list[int]: ...


class WindowingAdapter(Protocol):
	"""Windowing constants and helpers."""

	@property
	def show_normal(self) -> int: ...


class MessageWindowAdapter(Protocol):
	"""Message window abstraction."""

	def pre_handle_window_message(self, *args: Any, **kwargs: Any) -> Any: ...

	def create_message_window(self, name: str) -> Any: ...


class DisplayAdapter(Protocol):
	"""Display integration, including DPI awareness setup."""

	def set_dpi_awareness(self) -> None: ...


class SessionAdapter(Protocol):
	"""Session tracking lifecycle and pump hooks."""

	def initialize(self) -> None: ...

	def pump_all(self) -> None: ...


@dataclass(frozen=True)
class PlatformServices:
	accessibility: AccessibilityAdapter
	input: InputAdapter
	audio: AudioAdapter
	clipboard: ClipboardAdapter
	system: SystemAdapter
	process_focus: ProcessFocusAdapter
	windowing: WindowingAdapter
	message_window: MessageWindowAdapter
	display: DisplayAdapter
	session: SessionAdapter
