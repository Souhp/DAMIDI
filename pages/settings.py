import pygame
import pygame_gui
import rtmidi
from sceneManager import WidgetScene
from modules.childWidget import ChildWidget


def getName() -> str:
	return "settings"


# ─────────────────────────────────────────────────────────────────────────────
# HOW CONTAINERS WORK IN PYGAME_GUI
# ─────────────────────────────────────────────────────────────────────────────
# When you pass container=some_panel to any element, its relative_rect coords
# become relative to that container's top-left corner (0, 0).
#
# Example:
#	panel = UIPanel(relative_rect=pygame.Rect(200, 300, 400, 200), ...)
#	label = UILabel(relative_rect=pygame.Rect(10, 10, 100, 30),
#					container=panel, ...)
#	→ label appears on screen at (210, 310), i.e. panel_x + 10, panel_y + 10
#
# This means: build your layout as if the container starts at (0, 0).
# Use rect.width / rect.height for sizing since those don't change.
# Never use rect.x / rect.y inside a container block.
# ─────────────────────────────────────────────────────────────────────────────


def _vstack(*heights, gap=0, pad=0, start_y=0):
	"""
	Helper: given a sequence of heights, yield (y, h) for each row,
	stacking downward with optional gap and top padding.

	Usage:
		for (y, h), label in zip(_vstack(30, 30, 36, gap=8, pad=8), rows):
			UILabel(relative_rect=pygame.Rect(pad, y, width - pad*2, h), ...)
	"""
	y = start_y + pad
	for h in heights:
		yield y, h
		y += h + gap


# ─────────────────────────────────────────────────────────────────────────────
class MidiSelectWidget(ChildWidget):
	"""
	Widget that lets the user pick a MIDI input device and connect it.
	Layout (all coords relative to panel = top-left is 0,0):

		┌─────────────────────────────┐
		│  [label: "MIDI Input"]	  │  row 0
		│  [dropdown: port list]	  │  row 1
		│  [button: Connect]		  │  row 2
		└─────────────────────────────┘
	"""

	def __init__(self):
		super().__init__()
		self._midi_in = rtmidi.MidiIn()
		self._dropdown = None
		self._connect_btn = None
		self.rows=None

		self.pad		   = None
		self.label_h    = None
		self.dropdown_h = None 
		self.btn_h	   = None 
		self.gap		   = None 

		self.inner_w = None
		self.midiInfoGroup =None
		self.panel=None

	def _build_widget_ui(self, rect: pygame.Rect):
		
		self.midiInfoGroup = "midi_info"
		self.register_group(self.midiInfoGroup, self.createMidiInfo)
		# ── sizes (all scale with window) ─────────────────────────────────────
		self.pad		   = self.scaled(10, minimum=6)
		self.label_h    = self.scaled(28, minimum=18)
		self.dropdown_h = self.scaled(32, minimum=22)
		self.btn_h	   = self.scaled(34, minimum=24)
		self.gap		   = self.scaled(10, minimum=6)

		self.inner_w = rect.width - self.pad * 2	 # width available inside padding

		# ── container ─────────────────────────────────────────────────────────
		# rect is in SCREEN coordinates — use it only for the top-level panel.
		self.panel = self._add(pygame_gui.elements.UIPanel(
			relative_rect=rect,
			manager=self.ui,
		))

		# ── children: ALL coords are relative to panel (start at 0, 0) ───────
		self.rows = list(_vstack(self.label_h, self.dropdown_h, self.btn_h, gap=self.gap, pad=self.pad))

		# Row 0 — title label
		y0, h0 = self.rows[0]
		self._add(pygame_gui.elements.UILabel(
			relative_rect=pygame.Rect(self.pad, y0, self.inner_w, h0),
			text="MIDI Input Device",
			manager=self.ui,
			container=self.panel,
			object_id="#nav_title",
		))
		self.createMidiInfo()

	def createMidiInfo(self,*args,**kwargs):
		if not self.rows or not self.pad:
			return

		# Row 1 — port dropdown
		y1, h1 =self.rows[1]
		ports = self._midi_in.get_ports()
		options = ["None"] + list(ports)
		
		if self.manager.midiListener:
			startingOption=self.manager.midiListener.midiDeviceName
		else:
			startingOption="None"

		self._dropdown = self._add(
			pygame_gui.elements.UIDropDownMenu(
				options_list=options,
				starting_option=startingOption,
				relative_rect=pygame.Rect(self.pad, y1, self.inner_w, h1),
				manager=self.ui,
				container=self.panel,
				),
			group=self.midiInfoGroup
			)

		
		self.on_event(
			pygame_gui.UI_DROP_DOWN_MENU_CHANGED,
			self._on_dropdown_changed,
			element=self._dropdown,
			group=self.midiInfoGroup

		)

		# Row 2 — connect button
		y2, h2 = self.rows[2]
		self.refreshButton = self._add(
			pygame_gui.elements.UIButton(
				relative_rect=pygame.Rect(self.pad, y2, self.inner_w, h2),
				text="refresh",
				manager=self.ui,
				container=self.panel,
				),
			group=self.midiInfoGroup
			)
		

		self.on_event(
			pygame_gui.UI_BUTTON_PRESSED,
			self.refreshMidiOptions,
			element=self.refreshButton,   # <-- correct
			group=self.midiInfoGroup
		)


	def refreshMidiOptions(self,*args,**kwargs):
		self.mutate_group(self.midiInfoGroup,"refresh") 
		


		

	def _on_dropdown_changed(self,event=None):
		if self._dropdown is None:
			return
		
		selected = self._dropdown.selected_option
		
		if isinstance(selected, (list, tuple)):
			selected = selected[0]			# pygame_gui sometimes wraps it
		
		if selected == "None":
			self.manager.disconnectMidiListener()
			return
		else:
			print(f"[MidiSelectWidget] connecting to: {selected!r}")
			self.manager.setupMidiListener(selected)

	def sidebar_options(self):
		return [
			{
				"type": "dropdown",
				"label": "Select Scale",
				"options": ["C Major", "D Major", "E Major"],
				"on_change": None
			},
			{
				"type": "button",
				"label": "Refresh MIDI ports",
				"callback": self._refresh
			}
		]

	def _refresh(self):
		print("[MidiSelectWidget] this is a fake function fuckkkk refreshing ports — rebuild will happen on next resize/re-enter")


# ─────────────────────────────────────────────────────────────────────────────
class VolumeWidget(ChildWidget):
	"""
	Widget for master volume control.
	Layout:

		┌─────────────────────────────┐
		│  [label: "Volume"]		  │  row 0
		│  [slider: 0-100]			  │  row 1
		│  [label: current value]	  │  row 2	← updated in update()
		└─────────────────────────────┘
	"""

	def __init__(self):
		super().__init__()
		self._slider = None
		self._value_label = None

	def _build_widget_ui(self, rect: pygame.Rect):
		pad		= self.scaled(10, minimum=6)
		label_h = self.scaled(28, minimum=18)
		slider_h = self.scaled(30, minimum=20)
		gap		= self.scaled(10, minimum=6)
		inner_w = rect.width - pad * 2

		panel = self._add(pygame_gui.elements.UIPanel(
			relative_rect=rect,
			manager=self.ui,
		))

		rows = list(_vstack(label_h, slider_h, label_h, gap=self.gap, pad=pad))

		# Row 0 — title
		y, h = rows[0]
		self._add(pygame_gui.elements.UILabel(
			relative_rect=pygame.Rect(pad, y, inner_w, h),
			text="Volume",
			manager=self.ui,
			container=panel,
			object_id="#nav_title",
		))

		# Row 1 — slider
		y, h = rows[1]
		self._slider = self._add(pygame_gui.elements.UIHorizontalSlider(
			relative_rect=pygame.Rect(pad, y, inner_w, h),
			start_value=50,
			value_range=(0, 100),
			manager=self.ui,
			container=panel,
		))

		# Row 2 — live readout
		y, h = rows[2]
		self._value_label = self._add(pygame_gui.elements.UILabel(
			relative_rect=pygame.Rect(pad, y, inner_w, h),
			text="50",
			manager=self.ui,
			container=panel,
		))

	def update(self, dt: float, midi_notes):
		if self._slider and self._value_label:
			val = int(self._slider.get_current_value())
			self._value_label.set_text(str(val))

	def sidebar_options(self):
		return [("Reset volume", self._reset)]

	def _reset(self):
		if self._slider:
			self._slider.set_current_value(50)


# ─────────────────────────────────────────────────────────────────────────────
class ThemeWidget(ChildWidget):
	"""
	Widget for choosing the UI colour theme.
	Layout:

		┌─────────────────────────────┐
		│  [label: "Theme"]			  │  row 0
		│  [dropdown: Dark/Light/…]   │  row 1
		│  [button: Apply]			  │  row 2
		└─────────────────────────────┘
	"""

	THEMES = ["Dark", "Light", "System"]

	def __init__(self):
		super().__init__()
		self._dropdown = None
		self._apply_btn = None

	def _build_widget_ui(self, rect: pygame.Rect):
		pad		   = self.scaled(10, minimum=6)
		label_h    = self.scaled(28, minimum=18)
		dropdown_h = self.scaled(32, minimum=22)
		btn_h	   = self.scaled(34, minimum=24)
		gap		   = self.scaled(10, minimum=6)
		inner_w    = rect.width - pad * 2

		panel = self._add(pygame_gui.elements.UIPanel(
			relative_rect=rect,
			manager=self.ui,
		))

		rows = list(_vstack(label_h, dropdown_h, btn_h, gap=gap, pad=pad))

		y, h = rows[0]
		self._add(pygame_gui.elements.UILabel(
			relative_rect=pygame.Rect(pad, y, inner_w, h),
			text="Theme",
			manager=self.ui,
			container=panel,
			object_id="#nav_title",
		))

		y, h = rows[1]
		self._dropdown = self._add(pygame_gui.elements.UIDropDownMenu(
			options_list=self.THEMES,
			starting_option=self.THEMES[0],
			relative_rect=pygame.Rect(pad, y, inner_w, h),
			manager=self.ui,
			container=panel,
		))

		y, h = rows[2]
		self._apply_btn = self._add(pygame_gui.elements.UIButton(
			relative_rect=pygame.Rect(pad, y, inner_w, h),
			text="Apply",
			manager=self.ui,
			container=panel,
		))

	def handle_event(self, event: pygame.event.Event):
		if event.type == pygame_gui.UI_BUTTON_PRESSED:
			if event.ui_element == self._apply_btn:
				self._apply()

	def _apply(self):
		if self._dropdown is None:
			return
		selected = self._dropdown.selected_option
		if isinstance(selected, (list, tuple)):
			selected = selected[0]
		print(f"[ThemeWidget] applying theme: {selected!r}")


# ─────────────────────────────────────────────────────────────────────────────
class Settings(WidgetScene):
	@staticmethod
	def getName() -> str:
		return "settings"

	def setup_widgets(self):
		# Grid layout:	col=0	  col=1
		#	row=0	[ Volume ]	[ Theme ]
		#	row=1	[	 MidiSelect (span 2)   ]
		#self.add_widget(VolumeWidget(),	  col=0, row=0)
		#self.add_widget(ThemeWidget(),		  col=1, row=0)
		self.add_widget(MidiSelectWidget())
		#self.add_widget(MidiSelectWidget(),  col=0, row=1, col_span=2)
