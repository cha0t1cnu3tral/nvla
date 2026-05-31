# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from platform.common.interfaces import PlatformServices

from .accessibility import LinuxAccessibilityAdapter
from .audio import LinuxAudioAdapter
from .clipboard import LinuxClipboardAdapter
from .display import LinuxDisplayAdapter
from .input import LinuxInputAdapter
from .message_window import LinuxMessageWindowAdapter
from .process_focus import LinuxProcessFocusAdapter
from .session import LinuxSessionAdapter
from .system import LinuxSystemAdapter
from .windowing import LinuxWindowingAdapter


def create_platform_services() -> PlatformServices:
	accessibility = LinuxAccessibilityAdapter()
	input = LinuxInputAdapter()
	input.registerKeyboardGestureHandler(accessibility.handleKeyboardGesture)
	return PlatformServices(
		accessibility=accessibility,
		input=input,
		audio=LinuxAudioAdapter(),
		clipboard=LinuxClipboardAdapter(),
		system=LinuxSystemAdapter(),
		process_focus=LinuxProcessFocusAdapter(),
		windowing=LinuxWindowingAdapter(),
		message_window=LinuxMessageWindowAdapter(),
		display=LinuxDisplayAdapter(),
		session=LinuxSessionAdapter(),
	)
