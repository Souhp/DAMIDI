import os
import pygame
import pygame_gui
from sceneManager import SceneManager


def main():
	pygame.init()
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

	running = True
	while running:
		dt = clock.tick(100) / 1000.0

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			elif event.type == pygame.WINDOWRESIZED:
				w, h = screen.get_size()
				ui_manager.set_window_resolution((w, h))
				manager.resize(w, h)
			ui_manager.process_events(event)
			manager.handle_event(event)

		ui_manager.update(dt)
		manager.update(dt)

		manager.draw()
		ui_manager.draw_ui(screen)
		pygame.display.flip()

	manager.shutdown()	 # cancels any running tasks/threads, stops async loop
	pygame.quit()


if __name__ == "__main__":
	main()
