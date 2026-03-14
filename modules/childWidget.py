import pygame
import pygame_gui

# Imported for the scale constants only — no circular dependency since
# sceneManager imports this file, not the other way around.
from sceneConstants import BASE_W, BASE_H


class ChildWidget:
    """
    Base class for self-contained UI widgets that live inside a WidgetScene.

    Override
    ────────
    _build_widget_ui(rect)  → create pygame_gui elements inside rect via
                              self._add(...).  Called on enter and every resize.
    sidebar_options()       → return [(label, callback), ...].  These appear
                              as buttons in the WidgetScene sidebar panel
                              automatically whenever this widget is on a page.
    handle_event(event)     → receive events forwarded by WidgetScene
    update(dt)              → per-frame logic
    draw()                  → custom pygame drawing (called before ui_manager)

    Layout
    ──────
    Widgets are placed by the parent WidgetScene via add_widget():

        scene.add_widget(MyWidget(), col=0, row=0)
        scene.add_widget(OtherWidget(), col=1, row=0, col_span=2)

    The grid is sized automatically from the highest col+span / row+span seen.
    Widgets in the same row share equal height; widgets in the same column share
    equal width — no two widgets overlap.
    """

    def __init__(self):
        self._elements: list               = []
        self._rect:     pygame.Rect | None = None

        # Injected by WidgetScene.build() before _build_widget_ui() is called.
        self.screen:  pygame.Surface       | None = None
        self.manager: object               | None = None   # SceneManager
        self.ui:      pygame_gui.UIManager | None = None

    # ── element helpers ───────────────────────────────────────────────────────
    def _add(self, el):
        """Register a pygame_gui element so it is killed on destroy()."""
        self._elements.append(el)
        return el

    def destroy(self):
        """Kill all registered elements.  Called by WidgetScene on resize/exit."""
        for el in self._elements:
            el.kill()
        self._elements.clear()

    # ── scale helper ─────────────────────────────────────────────────────────
    def scaled(self, base: int, minimum: int = 6) -> int:
        """
        Scale a pixel/point value by min(w/BASE_W, h/BASE_H).
        Squeezing either window axis shrinks the result.
        """
        if self.screen is None:
            return base
        w, h = self.screen.get_size()
        return max(minimum, int(base * min(w / BASE_W, h / BASE_H)))

    # ── sidebar contribution ──────────────────────────────────────────────────
    def sidebar_options(self) -> list[tuple[str, callable]]:
        """
        Return [(label, callback), ...] for the parent scene's sidebar panel.
        Called once when the sidebar is built (enter + resize).

        Example
        -------
            def sidebar_options(self):
                return [
                    ("Reset",  self._reset),
                    ("Export", self._export),
                ]
        """
        return []

    # ── lifecycle (called by WidgetScene) ─────────────────────────────────────
    def build(self, rect: pygame.Rect,
              screen: pygame.Surface,
              manager,
              ui: pygame_gui.UIManager):
        """Inject dependencies and build UI inside rect."""
        self.destroy()
        self._rect   = rect
        self.screen  = screen
        self.manager = manager
        self.ui      = ui
        self._build_widget_ui(rect)

    # ── override these ────────────────────────────────────────────────────────
    def _build_widget_ui(self, rect: pygame.Rect): pass
    def handle_event(self, event: pygame.event.Event): pass
    def update(self, dt: float): pass
    def draw(self): pass
