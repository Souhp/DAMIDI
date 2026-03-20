import pygame
import pygame_gui
from sceneManager import WidgetScene
from modules.staff_widget import StaffWidget 

def getName() -> str:
	return "Piano Rush"





class PRScene(WidgetScene):

	@staticmethod
	def getName() -> str:
		return "example"

	def setup_widgets(self):
		self.staff = StaffWidget(bg_color=(255, 255, 255))
		self.add_widget(self.staff, col=0, row=0)

