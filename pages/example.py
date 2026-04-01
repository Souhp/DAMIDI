import pygame
import pygame_gui
from sceneManager import WidgetScene
from modules.childWidget import ChildWidget
from modules.staff_widget import StaffWidget 

def getName() -> str:
	return "example"


class InfoWidget(ChildWidget):
	"""A simple labelled panel. label= is set in __init__ for reuse."""

	def __init__(self, label: str):
		super().__init__()
		self._label = label

	def _build_widget_ui(self, rect: pygame.Rect):
		pad = self.scaled(8, minimum=4)
		self._add(pygame_gui.elements.UIPanel(
			relative_rect=rect,
			manager=self.ui,
		))
		self._add(pygame_gui.elements.UILabel(
			relative_rect=pygame.Rect(
				rect.x + pad, rect.y + pad,
				rect.width - pad * 2, self.scaled(30, minimum=18)),
			text=self._label,
			manager=self.ui,
			object_id="#nav_title",
		))

	def sidebar_options(self):
		return [(f"Action: {self._label}", lambda l=self._label: print(f"[{l}] action"))]


class Example(WidgetScene):

	@staticmethod
	def getName() -> str:
		return "example"

	def setup_widgets(self):
		self.staff = StaffWidget(bg_color=(255, 255, 255))
		self.add_widget(self.staff, col=0, row=0)
		# 2-column, 2-row grid
		# [  Top-left  ] [	Top-right (spans 1)  ]
		# [  Bottom wide (spans 2 columns)		  ]
		self.add_widget(InfoWidget("Top Right"),	col=1, row=0)
		self.add_widget(InfoWidget("Bottom Wide"),	col=0, row=1, col_span=2)
