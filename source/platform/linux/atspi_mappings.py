# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

from collections.abc import Iterable, Mapping

import controlTypes

_ROLE_NAME_TO_NVDA_ROLE: dict[str, controlTypes.Role] = {
	"ROLE_APPLICATION": controlTypes.Role.APPLICATION,
	"ROLE_ALERT": controlTypes.Role.ALERT,
	"ROLE_DIALOG": controlTypes.Role.DIALOG,
	"ROLE_FRAME": controlTypes.Role.FRAME,
	"ROLE_WINDOW": controlTypes.Role.WINDOW,
	"ROLE_LABEL": controlTypes.Role.LABEL,
	"ROLE_TEXT": controlTypes.Role.STATICTEXT,
	"ROLE_ENTRY": controlTypes.Role.EDITABLETEXT,
	"ROLE_PASSWORD_TEXT": controlTypes.Role.PASSWORDEDIT,
	"ROLE_PUSH_BUTTON": controlTypes.Role.BUTTON,
	"ROLE_TOGGLE_BUTTON": controlTypes.Role.TOGGLEBUTTON,
	"ROLE_CHECK_BOX": controlTypes.Role.CHECKBOX,
	"ROLE_RADIO_BUTTON": controlTypes.Role.RADIOBUTTON,
	"ROLE_MENU": controlTypes.Role.POPUPMENU,
	"ROLE_MENU_BAR": controlTypes.Role.MENUBAR,
	"ROLE_MENU_ITEM": controlTypes.Role.MENUITEM,
	"ROLE_CHECK_MENU_ITEM": controlTypes.Role.CHECKMENUITEM,
	"ROLE_RADIO_MENU_ITEM": controlTypes.Role.RADIOMENUITEM,
	"ROLE_COMBO_BOX": controlTypes.Role.COMBOBOX,
	"ROLE_LIST": controlTypes.Role.LIST,
	"ROLE_LIST_ITEM": controlTypes.Role.LISTITEM,
	"ROLE_TREE": controlTypes.Role.TREEVIEW,
	"ROLE_TREE_ITEM": controlTypes.Role.TREEVIEWITEM,
	"ROLE_TABLE": controlTypes.Role.TABLE,
	"ROLE_TABLE_CELL": controlTypes.Role.TABLECELL,
	"ROLE_COLUMN_HEADER": controlTypes.Role.TABLECOLUMNHEADER,
	"ROLE_ROW_HEADER": controlTypes.Role.TABLEROWHEADER,
	"ROLE_LINK": controlTypes.Role.LINK,
	"ROLE_IMAGE": controlTypes.Role.GRAPHIC,
	"ROLE_PROGRESS_BAR": controlTypes.Role.PROGRESSBAR,
	"ROLE_SCROLL_BAR": controlTypes.Role.SCROLLBAR,
	"ROLE_SLIDER": controlTypes.Role.SLIDER,
	"ROLE_TOOL_TIP": controlTypes.Role.TOOLTIP,
	"ROLE_STATUS_BAR": controlTypes.Role.STATUSBAR,
	"ROLE_TOOL_BAR": controlTypes.Role.TOOLBAR,
	"ROLE_PAGE_TAB": controlTypes.Role.TAB,
	"ROLE_PAGE_TAB_LIST": controlTypes.Role.TABCONTROL,
	"ROLE_PARAGRAPH": controlTypes.Role.PARAGRAPH,
	"ROLE_HEADING": controlTypes.Role.HEADING,
	"ROLE_SECTION": controlTypes.Role.SECTION,
	"ROLE_DOCUMENT_FRAME": controlTypes.Role.DOCUMENT,
	"ROLE_DOCUMENT_WEB": controlTypes.Role.DOCUMENT,
	"ROLE_DOCUMENT_TEXT": controlTypes.Role.DOCUMENT,
	"ROLE_DOCUMENT_EMAIL": controlTypes.Role.DOCUMENT,
}

_STATE_NAME_TO_NVDA_STATE: dict[str, controlTypes.State] = {
	"STATE_FOCUSED": controlTypes.State.FOCUSED,
	"STATE_ENABLED": controlTypes.State.FOCUSABLE,
	"STATE_SENSITIVE": controlTypes.State.FOCUSABLE,
	"STATE_FOCUSABLE": controlTypes.State.FOCUSABLE,
	"STATE_SELECTABLE": controlTypes.State.SELECTABLE,
	"STATE_SELECTED": controlTypes.State.SELECTED,
	"STATE_VISIBLE": controlTypes.State.INVISIBLE,
	"STATE_SHOWING": controlTypes.State.OFFSCREEN,
	"STATE_EDITABLE": controlTypes.State.EDITABLE,
	"STATE_READ_ONLY": controlTypes.State.READONLY,
	"STATE_MULTI_LINE": controlTypes.State.MULTILINE,
	"STATE_REQUIRED": controlTypes.State.REQUIRED,
	"STATE_CHECKABLE": controlTypes.State.CHECKABLE,
	"STATE_CHECKED": controlTypes.State.CHECKED,
	"STATE_INDETERMINATE": controlTypes.State.INDETERMINATE,
	"STATE_PRESSED": controlTypes.State.PRESSED,
	"STATE_EXPANDED": controlTypes.State.EXPANDED,
	"STATE_COLLAPSED": controlTypes.State.COLLAPSED,
	"STATE_BUSY": controlTypes.State.BUSY,
	"STATE_MODAL": controlTypes.State.MODAL,
	"STATE_VISITED": controlTypes.State.VISITED,
	"STATE_DEFUNCT": controlTypes.State.DEFUNCT,
}

_INVERTED_STATE_NAMES = frozenset(("STATE_VISIBLE", "STATE_SHOWING"))


def build_role_map(atspiModule: object) -> dict[int, controlTypes.Role]:
	roleMap: dict[int, controlTypes.Role] = {}
	for atspiName, nvdaRole in _ROLE_NAME_TO_NVDA_ROLE.items():
		atspiValue = getattr(atspiModule, atspiName, None)
		if atspiValue is not None:
			roleMap[atspiValue] = nvdaRole
	return roleMap


def build_state_map(atspiModule: object) -> tuple[dict[int, controlTypes.State], set[int]]:
	stateMap: dict[int, controlTypes.State] = {}
	invertedStateValues: set[int] = set()
	for atspiName, nvdaState in _STATE_NAME_TO_NVDA_STATE.items():
		atspiValue = getattr(atspiModule, atspiName, None)
		if atspiValue is None:
			continue
		stateMap[atspiValue] = nvdaState
		if atspiName in _INVERTED_STATE_NAMES:
			invertedStateValues.add(atspiValue)
	return stateMap, invertedStateValues


def map_role(
	atspiRole: int,
	roleMap: Mapping[int, controlTypes.Role],
) -> controlTypes.Role:
	return roleMap.get(atspiRole, controlTypes.Role.UNKNOWN)


def map_states(
	atspiStates: Iterable[int],
	stateMap: Mapping[int, controlTypes.State],
	invertedStateValues: set[int],
) -> set[controlTypes.State]:
	stateSet = set(atspiStates)
	nvdaStates: set[controlTypes.State] = set()
	for atspiState, nvdaState in stateMap.items():
		if atspiState in invertedStateValues:
			if atspiState not in stateSet:
				nvdaStates.add(nvdaState)
			continue
		if atspiState in stateSet:
			nvdaStates.add(nvdaState)
	return nvdaStates


def map_state_name(atspiStateName: str) -> tuple[controlTypes.State, bool] | None:
	normalizedName = f"STATE_{atspiStateName.upper().replace('-', '_')}"
	nvdaState = _STATE_NAME_TO_NVDA_STATE.get(normalizedName)
	if nvdaState is None:
		return None
	return nvdaState, normalizedName in _INVERTED_STATE_NAMES
