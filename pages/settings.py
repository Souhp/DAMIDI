import pygame
import pygame_gui
from sceneManager import WidgetScene
from modules.childWidget import ChildWidget

def getName() -> str:
    return "settings"


class VolumeWidget(ChildWidget):

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
            text="Volume",
            manager=self.ui,
            object_id="#nav_title",
        ))
        self._add(pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(
                rect.x + pad,
                rect.y + self.scaled(40, minimum=26),
                rect.width - pad * 2,
                self.scaled(28, minimum=18)),
            start_value=50,
            value_range=(0, 100),
            manager=self.ui,
        ))

    def _reset(self): print("[VolumeWidget] reset")
    def _mute(self):  print("[VolumeWidget] mute")


class ThemeWidget(ChildWidget):

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
            text="Theme",
            manager=self.ui,
            object_id="#nav_title",
        ))
        self._add(pygame_gui.elements.UIDropDownMenu(
            options_list=["Dark", "Light", "System"],
            starting_option="Dark",
            relative_rect=pygame.Rect(
                rect.x + pad,
                rect.y + self.scaled(40, minimum=26),
                rect.width - pad * 2,
                self.scaled(30, minimum=20)),
            manager=self.ui,
        ))

    def _apply(self): print("[ThemeWidget] apply theme")


class Settings(WidgetScene):

    @staticmethod
    def getName() -> str:
        return "settings"

    def setup_widgets(self):
        self.add_widget(VolumeWidget(), col=0, row=0)
        self.add_widget(ThemeWidget(),  col=1, row=0)
