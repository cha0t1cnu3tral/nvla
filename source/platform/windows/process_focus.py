# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.


class WindowsProcessFocusAdapter:
	def get_desktop_window(self) -> int:
		import winUser

		return winUser.getDesktopWindow()

	def get_foreground_window(self) -> int:
		import winUser

		return winUser.getForegroundWindow()

	def list_window_handles(self) -> list[int]:
		import ctypes
		import winUser
		import winBindings.user32

		windows: list[int] = []

		@winUser._WNDENUMPROC
		def enum_windows_proc(hwnd: int, _lparam: int) -> int:
			windows.append(hwnd)
			return 1

		if not winBindings.user32.EnumWindows(enum_windows_proc, 0) and (error := ctypes.get_last_error()):
			raise ctypes.WinError(error)
		return windows

	def list_process_ids(self) -> list[int]:
		import winUser

		process_ids: set[int] = set()
		for hwnd in self.list_window_handles():
			_, pid = winUser.getWindowThreadProcessID(hwnd)
			if pid:
				process_ids.add(pid)
		return sorted(process_ids)
