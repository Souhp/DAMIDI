import os
import time
import pygame
import pygame_gui
from sceneManager import SceneManager

from pygame_gui.elements.ui_button import UIButton
_orig_button_init = UIButton.__init__

def _patched_button_init(self, *args, **kwargs):
    _orig_button_init(self, *args, **kwargs)
    if not hasattr(self, 'held'):
        self.held = False

UIButton.__init__ = _patched_button_init

def main():
	pygame.init()
	pygame.mixer.init()
	screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE,vsync=1)
	pygame.display.set_caption("Scene Manager")
	clock = pygame.time.Clock()

	theme_path = os.path.join(os.path.dirname(__file__), "theme.json")
	ui_manager = pygame_gui.UIManager((800, 600))

	ui_manager.get_theme().get_font_dictionary().add_font_path(
		font_name="IosevkaCharonMono-Regular",
		font_path="src/fonts/IosevkaCharonMono-Regular.ttf"
	)

	ui_manager.get_theme().load_theme("theme.json")   
	pages_dir = os.path.join(os.path.dirname(__file__), "pages")
	manager   = SceneManager(screen, ui_manager,pages_dir=pages_dir,start_async_loop=True)	 # optional: only if you use run_task()
	manager.push("menu")

	# Debounce expensive scene/widget rebuilds during live resize.
	# pygame may emit WINDOWRESIZED repeatedly while the user drags the edge.
	debounce_s = 0.2
	resize_pending = False
	pending_w = 0
	pending_h = 0
	last_resize_at = 0.0

	running = True
	while running:
		dt = clock.tick(60) / 1000.0

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			elif event.type == pygame.WINDOWRESIZED:
				w, h = screen.get_size()
				ui_manager.set_window_resolution((w, h))
				# Keep resolution tracking immediate, but postpone full rebuild.
				pending_w, pending_h = w, h
				last_resize_at = time.monotonic()
				resize_pending = True
			ui_manager.process_events(event)
			manager.handle_event(event)

		# Flush exactly once after resizing stops for `debounce_s`.
		if resize_pending and (time.monotonic() - last_resize_at) >= debounce_s:
			manager.resize(pending_w, pending_h)
			resize_pending = False

		ui_manager.update(dt)
		manager.update(dt)

		manager.draw()
		ui_manager.draw_ui(screen)
		pygame.display.flip()

	manager.shutdown()	 # cancels any running tasks/threads, stops async loop
	pygame.quit()


if __name__ == "__main__":
	main()
