# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from platform.common.interfaces import PlatformServices

from .accessibility import WindowsAccessibilityAdapter
from .audio import WindowsAudioAdapter
from .clipboard import WindowsClipboardAdapter
from .display import WindowsDisplayAdapter
from .input import WindowsInputAdapter
from .message_window import WindowsMessageWindowAdapter
from .process_focus import WindowsProcessFocusAdapter
from .session import WindowsSessionAdapter
from .system import WindowsSystemAdapter
from .windowing import WindowsWindowingAdapter


def create_platform_services() -> PlatformServices:
	return PlatformServices(
		accessibility=WindowsAccessibilityAdapter(),
		input=WindowsInputAdapter(),
		audio=WindowsAudioAdapter(),
		clipboard=WindowsClipboardAdapter(),
		system=WindowsSystemAdapter(),
		process_focus=WindowsProcessFocusAdapter(),
		windowing=WindowsWindowingAdapter(),
		message_window=WindowsMessageWindowAdapter(),
		display=WindowsDisplayAdapter(),
		session=WindowsSessionAdapter(),
	)
