import json
import pygame
import pygame_gui
import importlib.util
import threading
import asyncio
import os
import sys
from modules.pychord.constants import all_scales
from modules.midiListener import MidiListener

# Ensure the directory that contains sceneManager.py itself is on sys.path so
# that sibling modules (childWidget, sceneConstants, staff_widget, …) are always
# importable regardless of where Python is launched from.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
	sys.path.insert(0, _HERE)


default_music_scale_key="C"

NAVBAR_H = 50
_NAV_BG		 = (18, 18, 42)
_NAV_DIVIDER = (38, 38, 78)

from modules.childWidget import ChildWidget  # re-exported so pages can import from one place

# Reference resolution — all geometry and fonts are designed at this size.
# Scale = min(w / BASE_W, h / BASE_H) so squeezing either axis shrinks things.
BASE_W = 800
BASE_H = 600

# WidgetScene grid / sidebar constants
_SIDEBAR_W_FRAC = 0.28	  # sidebar width as fraction of window width
_GRID_PAD_FRAC	= 0.018   # outer padding around the grid
_GRID_GAP_FRAC	= 0.012   # gap between grid cells


# ═══════════════════════════════════════════════════════════════════════════════
# Scene  —	base class for full-screen scenes
# ═══════════════════════════════════════════════════════════════════════════════
class Scene:
	"""
	Base class for all scenes.

	Override
	────────
	getName()		 → unique string id (+ module-level function of same name)
	_build_ui()		 → create ALL pygame_gui elements via self._add(...)
					   called on enter AND every resize
	on_enter()		 → one-time setup (load data, audio) — NOT called on resize
	on_exit()		 → one-time teardown
	handle_event(e)  → input; call super() to keep navbar working
	update(dt)		 → logic
	draw()			 → rendering; call super() for navbar stripe

	Navbar
	──────
	nav_left_label()   → left button text  (None = hidden)
	nav_left_action()  → what it does	   (default: manager.pop())

	Background workers
	──────────────────
	run_thread(fn, *args)  — daemon thread, joined on exit
	run_task(coro)		   — asyncio task on SceneManager's loop, cancelled on exit
	Poll self.cancelled inside workers to stop early.
	"""

	@staticmethod
	def getName() -> str:
		return "scene"

	def __init__(self, screen: pygame.Surface,
				 manager: "SceneManager",
				 ui: pygame_gui.UIManager):
		self.screen  = screen
		self.manager = manager
		self.ui		 = ui
		self.width	 = screen.get_width()
		self.height  = screen.get_height()

		self._elements:    list				   = []
		self._nav_left_btn					   = None

		self._cancel_event = threading.Event()
		self._threads:	list[threading.Thread] = []
		self._tasks:	list[asyncio.Task]	   = []


		#music
		

	# ── cancellation ──────────────────────────────────────────────────────────
	@property
	def cancelled(self) -> bool:
		return self._cancel_event.is_set()

	def run_thread(self, fn, *args, **kwargs) -> threading.Thread:
		t = threading.Thread(target=fn, args=args, kwargs=kwargs, daemon=True)
		self._threads.append(t)
		t.start()
		return t

	def run_task(self, coro):
		loop = self.manager.async_loop
		if loop is None or not loop.is_running():
			print("[Scene] run_task: no async loop available")
			return None

		async def _guarded():
			import traceback
			try:
				return await coro
			except Exception as e:
				print(f"\n{'='*60}")
				print(f"CRASH in async task ({self.__class__.__name__})")
				print(f"  {type(e).__name__}: {e}")
				traceback.print_exc()
				print(f"{'='*60}\n")

		task = asyncio.run_coroutine_threadsafe(_guarded(), loop)
		self._tasks.append(task)
		return task

	def _cancel_all(self):
		self._cancel_event.set()
		for task in self._tasks:
			task.cancel()
		self._tasks.clear()
		for t in self._threads:
			t.join(timeout=2)
			if t.is_alive():
				print(f"[Scene] Warning: thread {t.name!r} did not stop in 2 s")
		self._threads.clear()

	# ── scale ─────────────────────────────────────────────────────────────────
	@property
	def ui_scale(self) -> float:
		"""min(w/BASE_W, h/BASE_H) — either axis shrinking reduces this."""
		return min(self.width / BASE_W, self.height / BASE_H)

	def scaled(self, base: int, minimum: int = 6) -> int:
		return max(minimum, int(base * self.ui_scale))

	# ── layout ────────────────────────────────────────────────────────────────
	def R(self, xf: float, yf: float, wf: float, hf: float) -> pygame.Rect:
		"""Rect from fractions of the window: R(x_frac, y_frac, w_frac, h_frac)."""
		return pygame.Rect(int(self.width * xf), int(self.height * yf),
						   int(self.width * wf), int(self.height * hf))

	# ── element registration ──────────────────────────────────────────────────
	def _add(self, element):
		self._elements.append(element)
		return element

	def _kill_elements(self):
		for el in self._elements:
			el.kill()
		self._elements.clear()
		self._nav_left_btn = None

	# ── navbar ────────────────────────────────────────────────────────────────
	def nav_left_label(self) -> str | None:
		return "< Back" if len(self.manager.name_stack) > 1 else None

	def nav_left_action(self):
		self.manager.pop()

	def _nav_geometry(self) -> tuple[int, int, int, int]:
		"""Returns (nav_h, pad, btn_h, btn_w) — shared by Scene and WidgetScene."""
		nav_h = self.scaled(50, minimum=36)
		pad   = max(5, int(nav_h * 0.15))
		btn_h = nav_h - pad * 2
		btn_w = self.scaled(110, minimum=70)
		return nav_h, pad, btn_h, btn_w

	def _build_navbar(self):
		nav_h, pad, btn_h, btn_w = self._nav_geometry()

		label = self.nav_left_label()
		if label:
			self._nav_left_btn = self._add(pygame_gui.elements.UIButton(
				relative_rect=pygame.Rect(pad, pad, btn_w, btn_h),
				text=label,
				manager=self.ui,
				object_id="#nav_btn",
			))

		title_w = max(200, int(self.width * 0.35))
		self._add(pygame_gui.elements.UILabel(
			relative_rect=pygame.Rect(
				self.width // 2 - title_w // 2, pad, title_w, btn_h),
			text=self.getName().upper(),
			manager=self.ui,
			object_id="#nav_title",
		))

	# ── UI build / lifecycle ──────────────────────────────────────────────────
	def _build_ui(self):
		"""Override to create elements via self._add(). Always call super() first."""
		self._build_navbar()

	def on_enter(self): pass
	def on_exit(self):	pass

	def enter(self):
		self._cancel_event = threading.Event()
		self.on_enter()
		self._build_ui()

	def exit(self):
		self._kill_elements()
		self._cancel_all()
		self.on_exit()

	def pause(self):  pass
	def resume(self): pass

	def resize(self, w: int, h: int):
		self._kill_elements()
		self.width	= w
		self.height = h
		self._build_ui()

	# ── events / update / draw ────────────────────────────────────────────────
	def handle_event(self, event: pygame.event.Event):
		if event.type == pygame_gui.UI_BUTTON_PRESSED:
			if self._nav_left_btn and event.ui_element == self._nav_left_btn:
				self.nav_left_action()

	def update(self, dt: float): pass

	def draw(self):
		"""Call super().draw() to paint the navbar background stripe."""
		nav_h = self.scaled(50, minimum=36)
		pygame.draw.rect(self.screen, _NAV_BG,	   (0, 0, self.width, nav_h))
		pygame.draw.line(self.screen, _NAV_DIVIDER,
						 (0, nav_h - 1), (self.width, nav_h - 1), 2)


# ═══════════════════════════════════════════════════════════════════════════════
# WidgetScene  —  Scene with a grid layout and a sidebar overlay
# ═══════════════════════════════════════════════════════════════════════════════
class WidgetScene(Scene):
	"""
	A Scene that:
	• Lays out ChildWidget instances in a non-overlapping grid.
	• Adds a "☰" toggle button on the right of the navbar.
	• Shows a floating overlay panel (sidebar) that collects sidebar_options()
	  from every widget currently on the page.	The sidebar appears on top of
	  all content and does not shift anything when it opens.

	Usage
	─────
	Subclass WidgetScene and override setup_widgets():

		class MyPage(WidgetScene):
			@staticmethod
			def getName(): return "mypage"

			def setup_widgets(self):
				self.add_widget(ClockWidget(),	col=0, row=0)
				self.add_widget(GraphWidget(),	col=1, row=0, col_span=2)
				self.add_widget(LogWidget(),	col=0, row=1, col_span=3)

			def draw(self):
				self.screen.fill((20, 20, 40))
				super().draw()

	Grid rules
	──────────
	• col / row are 0-indexed.
	• col_span / row_span default to 1.
	• The grid is sized automatically: num_cols = max(col + col_span),
	  num_rows = max(row + row_span).
	• All columns are equal width; all rows are equal height.
	• Widgets placed at different col+row values never overlap.

	Sidebar
	───────
	• Built from all widgets' sidebar_options() lists on enter and resize.
	• Rendered on top (created last, highest pygame_gui layer).
	• Toggled with the "☰" navbar button; clicking again hides it.
	• Dismisses automatically when any sidebar button is pressed.
	"""

	def __init__(self, screen, manager, ui):
		super().__init__(screen, manager, ui)
		# (widget, col, row, col_span, row_span)
		self._widget_slots: list[tuple[ChildWidget, int, int, int, int]] = []
		self._sidebar_open:  bool				 = False
		self._sidebar_btn:	 object | None		 = None
		self._sidebar_panel: object | None		 = None
		# (UIButton, callback) for sidebar items
		self._sidebar_items: list[tuple]		 = []
		self.midiListener=self.manager.midiListener

	# ── public API ────────────────────────────────────────────────────────────
	def add_widget(self, widget: ChildWidget,
				   col: int = 0, row: int = 0,
				   col_span: int = 1, row_span: int = 1):
		"""Register a widget at a grid position.  Call from setup_widgets()."""
		self._widget_slots.append((widget, col, row, col_span, row_span))

	def setup_widgets(self):
		"""Override to populate widgets via self.add_widget(...)."""
		pass

	# ── grid geometry ─────────────────────────────────────────────────────────
	def _grid_dims(self) -> tuple[int, int]:
		if not self._widget_slots:
			return 1, 1
		cols = max(c + cs for _, c, r, cs, rs in self._widget_slots)
		rows = max(r + rs for _, c, r, cs, rs in self._widget_slots)
		return cols, rows

	def _cell_rect(self, col, row, col_span, row_span,
				   num_cols, num_rows,
				   content: pygame.Rect) -> pygame.Rect:
		pad = max(6, int(content.width * _GRID_PAD_FRAC))
		gap = max(4, int(content.width * _GRID_GAP_FRAC))

		inner_w = content.width  - pad * 2
		inner_h = content.height - pad * 2
		cell_w	= (inner_w - gap * (num_cols - 1)) / num_cols
		cell_h	= (inner_h - gap * (num_rows - 1)) / num_rows

		x = content.x + pad + col * (cell_w + gap)
		y = content.y + pad + row * (cell_h + gap)
		w = cell_w * col_span + gap * (col_span - 1)
		h = cell_h * row_span + gap * (row_span - 1)
		return pygame.Rect(int(x), int(y), int(w), int(h))

	# ── navbar: adds sidebar toggle on the right ──────────────────────────────
	def _build_navbar(self):
		super()._build_navbar()
		nav_h, pad, btn_h, _ = self._nav_geometry()
		toggle_w = self.scaled(44, minimum=30)

		self._sidebar_btn = self._add(pygame_gui.elements.UIButton(
			relative_rect=pygame.Rect(
				self.width - toggle_w - pad, pad, toggle_w, btn_h),
			text="☰",
			manager=self.ui,
			object_id="#nav_btn",
		))

	# ── sidebar overlay ───────────────────────────────────────────────────────
	def _build_sidebar(self):
		"""
		Build the floating overlay panel.  It is created AFTER all other
		elements so pygame_gui renders it on top of everything.
		"""
		nav_h	 = self.scaled(50, minimum=36)
		panel_w  = max(150, int(self.width * _SIDEBAR_W_FRAC))
		panel_h  = self.height - nav_h
		panel_x  = self.width - panel_w
		panel_y  = nav_h

		btn_h	 = self.scaled(38, minimum=24)
		btn_gap  = self.scaled(8,  minimum=4)

		# Collect all options from all widgets
		#all_options: list[tuple[str, callable]] = [("Select Scale",None)]
		all_options = []


		for widget, *_ in self._widget_slots:
			all_options.extend(widget.sidebar_options())

		# Total content height inside the panel
		content_h = len(all_options) * (btn_h + btn_gap) + btn_gap

		self._sidebar_panel = self._add(pygame_gui.elements.UIScrollingContainer(
			relative_rect=pygame.Rect(panel_x, panel_y, panel_w, panel_h),
			manager=self.ui,
		))
		self._sidebar_panel.set_scrollable_area_dimensions(
			(panel_w, max(content_h, panel_h))
		)

		# Populate buttons
		self._sidebar_items.clear()
		y = btn_gap
		for label, cb in all_options:
			btn = self._add(pygame_gui.elements.UIButton(
				relative_rect=pygame.Rect(btn_gap, y,
										  panel_w - btn_gap * 2, btn_h),
				text=label,
				manager=self.ui,
				container=self._sidebar_panel,
				object_id="#page_btn",
			))
			self._sidebar_items.append((btn, cb))
			y += btn_h + btn_gap

		# Start hidden unless it was open before the rebuild
		if not self._sidebar_open:
			self._sidebar_panel.hide()

	def _toggle_sidebar(self):
		self._sidebar_open = not self._sidebar_open
		if self._sidebar_open:
			self._sidebar_panel.show()
		else:
			self._sidebar_panel.hide()

	# ── layout widgets in the grid ────────────────────────────────────────────
	def _layout_widgets(self):
		nav_h		 = self.scaled(50, minimum=36)
		content_rect = pygame.Rect(0, nav_h, self.width, self.height - nav_h)
		num_cols, num_rows = self._grid_dims()

		for widget, col, row, cs, rs in self._widget_slots:
			rect = self._cell_rect(col, row, cs, rs,
								   num_cols, num_rows, content_rect)
			widget.build(rect, self.screen, self.manager, self.ui)

	# ── _build_ui override ────────────────────────────────────────────────────
	def _build_ui(self):
		self._sidebar_items.clear() 
		# Destroy old widget elements before killing scene elements
		for widget, *_ in self._widget_slots:
			widget.destroy()

		super()._build_ui()		  # navbar (including sidebar toggle btn)
		self._layout_widgets()	  # rebuild widget UI inside their grid cells
		self._build_sidebar()	  # sidebar LAST so it renders on top

	# ── lifecycle ─────────────────────────────────────────────────────────────
	def on_enter(self):
		self._widget_slots.clear()
		self._sidebar_open = False
		self.setup_widgets()

	def on_exit(self):
		for widget, *_ in self._widget_slots:
			widget.destroy()
		self._widget_slots.clear()

	# ── events ────────────────────────────────────────────────────────────────
	def handle_event(self, event: pygame.event.Event):
		super().handle_event(event)  # navbar back button

		if event.type == pygame_gui.UI_BUTTON_PRESSED:
			if self._sidebar_btn and event.ui_element == self._sidebar_btn:
				self._toggle_sidebar()
				return
			for btn, cb in self._sidebar_items:
				if event.ui_element == btn:
					cb()#RUNS THE CU/STOM FUNCTION OF THE CHILDWIDGETS SIDEBAR
					self._sidebar_open = False
					self._sidebar_panel.hide()
					return

		for widget, *_ in self._widget_slots:
			widget.handle_event(event)

	def update(self, dt: float):
		midi_notes=None
		if self.midiListener:
			midi_notes=self.midiListener.tick()
		for widget, *_ in self._widget_slots:
			widget.update(dt,midi_notes)

	def draw(self):
		"""Fill background, paint navbar stripe, then let widgets draw."""
		self.screen.fill((22, 22, 48))
		super().draw()
		for widget, *_ in self._widget_slots:
			widget.draw()



# ═══════════════════════════════════════════════════════════════════════════════
# SceneManager
# ═══════════════════════════════════════════════════════════════════════════════
class SceneManager:
	"""
	Name-stack navigation.	Only one scene is alive at a time.
	Going back re-instantiates the previous scene fresh from its class.

	Constructor args
	────────────────
	screen			 — pygame Surface
	ui				 — pygame_gui UIManager
	pages_dir		 — directory to auto-discover scene modules from
	start_async_loop — spin up a background asyncio loop for run_task()
	font_name		 — font name to use in dynamic theme updates
	font_path		 — path to the .ttf file (registers the font globally)
	"""

	def __init__(self, screen: pygame.Surface,
				 ui: pygame_gui.UIManager,
				 pages_dir: str | None = None,
				 start_async_loop: bool = False,
				 font_name: str | None = None,
				 font_path: str | None = None):
		self.screen		= screen
		self.ui			= ui
		self.name_stack: list[str]				= []
		self.current:	 Scene | None			= None #current scene
		self.registry:	 dict[str, type[Scene]] = {}


		self.music_scale_key  = default_music_scale_key
		self.chromatic_music_scale=all_scales.chromatic_major_scales[self.music_scale_key]
		self.non_chromatic_music_scale=all_scales.major_scales[self.music_scale_key]
		self.midiListener = None 



		# Font registration
		if font_name and font_path:
			ui.get_theme().get_font_dictionary().add_font_path(font_name, font_path)
		if not font_name:
			known = list(ui.get_theme().get_font_dictionary().known_font_paths)
			font_name = known[0] if known else None
		self._font_name: str | None = font_name

		self.async_loop: asyncio.AbstractEventLoop | None = None
		if start_async_loop:
			self._start_async_loop()

		if pages_dir:
			self.load_pages(pages_dir)


	def setupMidiListener(self,deviceName):
		self.disconnectMidiListener()
		self.midiListener=MidiListener(deviceName)

	def disconnectMidiListener(self):
		if self.midiListener:
			self.midiListener.close()
			self.midiListener=None
	

	def midi_to_scale_note(self,pitch):


		note_names = self.chromatic_music_scale 
		if 0 <= pitch <= 127:
			note = note_names[pitch % 12]
			octave = (pitch // 12) - 1
			return f"{note}{octave}"
		else:
			raise ValueError("MIDI pitch must be between 0 and 127")


	def scale_update(self,x):
		print("starting scale update")
		self.music_scale=x
		if x.endswith("Major"):
			self.music_scale=x
		else:
			raise ValueError("default strctures does not start with major fuc	fuckf cufkc fuck aaa")



	# ── async loop ────────────────────────────────────────────────────────────
	def _start_async_loop(self):
		loop = asyncio.new_event_loop()
		self.async_loop = loop
		threading.Thread(target=loop.run_forever, daemon=True,
						 name="SceneManager-AsyncLoop").start()

	def shutdown(self):
		if self.current:
			self.current.exit()
			self.current = None
		if self.async_loop:
			self.async_loop.call_soon_threadsafe(self.async_loop.stop)

	# ── page discovery ────────────────────────────────────────────────────────
	def load_pages(self, pages_dir: str):
		pages_dir  = os.path.abspath(pages_dir)
		parent_dir = os.path.dirname(pages_dir)
		# Add both the pages dir and its parent so that sibling packages
		# like modules/ (sitting next to pages/) are importable.
		for p in (pages_dir, parent_dir):
			if p not in sys.path:
				sys.path.insert(0, p)

		for fname in sorted(os.listdir(pages_dir)):
			if not (fname.endswith(".py") and not fname.startswith("_")):
				continue
			mod_name = fname[:-3]
			try:
				spec   = importlib.util.spec_from_file_location(
							 mod_name, os.path.join(pages_dir, fname))
				module = importlib.util.module_from_spec(spec)
				spec.loader.exec_module(module)
				if not hasattr(module, "getName"):
					continue
				scene_name = module.getName()
				candidate  = None
				for attr in vars(module).values():
					if not (isinstance(attr, type)
							and issubclass(attr, Scene)
							and attr not in (Scene, WidgetScene)):
						continue
					try:
						if attr.getName() == scene_name:
							candidate = attr
							break
					except Exception:
						pass
					if candidate is None:
						candidate = attr
				if candidate:
					self.registry[scene_name] = candidate
					print(f"[SceneManager] registered '{scene_name}' → {candidate.__name__}")
			except Exception as exc:
				print(f"[SceneManager] failed to load '{mod_name}': {exc}")

	def register(self, name: str, cls: type[Scene]):
		self.registry[name] = cls

	def _make(self, name: str) -> Scene:
		if name not in self.registry:
			raise KeyError(f"Unknown scene '{name}'. Known: {list(self.registry)}")
		return self.registry[name](self.screen, self, self.ui)

	# ── navigation ────────────────────────────────────────────────────────────
	def push(self, name: str):
		if self.current:
			self.current.exit()
			self.current = None
		w, h = self.screen.get_size()
		self._apply_theme(w, h)
		self.name_stack.append(name)
		self.current = self._make(name)
		self.current.enter()

	def pop(self):
		if len(self.name_stack) < 2:
			return
		self.current.exit()
		self.current = None
		self.name_stack.pop()
		w, h = self.screen.get_size()
		self._apply_theme(w, h)
		self.current = self._make(self.name_stack[-1])
		self.current.enter()

	def replace(self, name: str):
		if self.current:
			self.current.exit()
			self.current = None
		if self.name_stack:
			self.name_stack.pop()
		self.name_stack.append(name)
		self.current = self._make(name)
		self.current.enter()

	# ── dynamic font sizing ───────────────────────────────────────────────────
	def _apply_theme(self, w: int, h: int):
		scale = min(w / BASE_W, h / BASE_H)
		nav   = max(10, int(18 * scale))
		page  = max(12, int(22 * scale))

		def font_block(size: str) -> dict:
			b: dict = {"size": size}
			if self._font_name:
				b["name"] = self._font_name
			return b

		self.ui.get_theme().update_theming(json.dumps({
			"#nav_btn":   {"font": font_block(str(nav))},
			"#nav_title": {"font": font_block(str(nav))},
			"#page_btn":  {"font": font_block(str(page))},
		}))

	# ── pass-through ──────────────────────────────────────────────────────────
	def resize(self, w: int, h: int):
		self._apply_theme(w, h)
		if self.current:
			self.current.resize(w, h)

	def handle_event(self, event: pygame.event.Event):
		if self.current:
			self.current.handle_event(event)

	def update(self, dt: float):
		if self.current:
			self.current.update(dt)

	def draw(self):
		if self.current:
			self.current.draw()
