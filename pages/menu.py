import pygame
import pygame_gui
from sceneManager import Scene, NAVBAR_H

def getName() -> str:
    return "menu"


class Menu(Scene):

    @staticmethod
    def getName() -> str:
        return "menu"

    # ── navbar ────────────────────────────────────────────────────────────────
    def nav_left_label(self) -> str:
        return "⚙ Settings"

    def nav_left_action(self):
        self.manager.push("settings")

    # ── UI build (called on enter AND every resize) ───────────────────────────
    def _build_ui(self):
        super()._build_ui()

        self._page_buttons: dict = {}

        excluded = {"menu", "settings"}
        pages = sorted(n for n in self.manager.registry if n not in excluded)

        # ── proportional sizing via ui_scale (min of both axes) ─────────────
        # nav_h must match _build_navbar exactly — use scaled(50) not h*0.08
        nav_h = self.scaled(50, minimum=36)
        btn_w = max(160, int(self.width  * 0.38))
        btn_h = self.scaled(54, minimum=36)
        gap   = self.scaled(12, minimum=6)
        hdr_h = self.scaled(32, minimum=20)

        # ── "Pages" header ────────────────────────────────────────────────────
        hdr_y = nav_h + gap
        self._add(pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                self.width // 2 - btn_w // 2, hdr_y, btn_w, hdr_h),
            text="Pages",
            manager=self.ui,
            object_id="#nav_title",
        ))

        # ── scroll panel so buttons never overlap ─────────────────────────────
        # Fills all remaining vertical space below the header.
        panel_y = hdr_y + hdr_h + gap
        panel_h = self.height - panel_y - gap
        panel_x = self.width // 2 - btn_w // 2

        total_content_h = len(pages) * (btn_h + gap)

        panel = self._add(pygame_gui.elements.UIScrollingContainer(
            relative_rect=pygame.Rect(panel_x, panel_y, btn_w, panel_h),
            manager=self.ui,
        ))
        # Expand the inner scrollable area if content is taller than the panel
        panel.set_scrollable_area_dimensions(
            (btn_w, max(total_content_h, panel_h))
        )

        # ── buttons inside the scroll panel ───────────────────────────────────
        for i, name in enumerate(pages):
            btn = self._add(pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(0, i * (btn_h + gap), btn_w, btn_h),
                text=name.capitalize(),
                manager=self.ui,
                container=panel,
                object_id="#page_btn",
            ))
            self._page_buttons[btn] = name

    # ── input ─────────────────────────────────────────────────────────────────
    def handle_event(self, event: pygame.event.Event):
        super().handle_event(event)
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            name = self._page_buttons.get(event.ui_element)
            if name:
                self.manager.push(name)

    # ── draw ──────────────────────────────────────────────────────────────────
    def draw(self):
        self.screen.fill((22, 22, 48))
        super().draw()
