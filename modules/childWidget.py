import asyncio
import pygame
import pygame_gui
from sceneConstants import BASE_W, BASE_H


class ChildWidget:
	def __init__(self):
		self._elements: list = []
		self._groups: dict[str, list] = {}			# named sub-groups
		self._group_builders: dict[str, callable] = {}	# name → rebuild fn
		self._rect:		pygame.Rect | None = None

		self.screen:  pygame.Surface	   | None = None
		self.manager: object			   | None = None
		self.ui:	  pygame_gui.UIManager | None = None

		self._tasks: list = []	 # concurrent.futures.Future

		self._event_handlers: list[tuple] = []	 # (event_type, predicate, callback)


		self._cancelled = False


	# ── group-aware element registration ──────────────────────────────────
	def _add(self, el, group: str | None = None):
		self._elements.append(el)
		if group is not None:
			self._groups.setdefault(group, []).append(el)
		return el

	def register_group(self, name: str, builder: callable):
		"""
		Register a callable that (re)builds a named group.
		builder receives no args — use self inside it.
		
		Usage:
			self.register_group("score_display", self._build_score_display)
		"""
		self._group_builders[name] = builder

	def mutate_group(self, name: str,mode: str):
		# Kill elements
		for el in self._groups.pop(name, []):
			self._elements.remove(el)
			el.kill()
		# Purge handlers belonging to this group
		self._event_handlers = [
			h for h in self._event_handlers if h[3] != name
		]
		# Rebuild
		builder = self._group_builders.get(name)
		if builder:
			builder(mode)



	# ── async support ─────────────────────────────────────────────────────
	@property
	def cancelled(self) -> bool:
		return self._cancelled
	def run_task(self, coro):
		if self.manager is None:
			return None
		loop = getattr(self.manager, "async_loop", None)
		if loop is None or not loop.is_running():
			print("[ChildWidget] run_task: no async loop on manager")
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

		future = asyncio.run_coroutine_threadsafe(_guarded(), loop)
		self._tasks.append(future)
		return future

	def _cancel_tasks(self):
		self._cancelled = True
		for f in self._tasks:
			f.cancel()
		self._tasks.clear()


	def on_event(self, event_type: int, callback, *, element=None, group: str | None = None):
		self._event_handlers.append((event_type, element, callback, group))

	

	def handle_event(self, event: pygame.event.Event):
		passDownCheck = False
		for ev_type, element, callback, _group in self._event_handlers:
			if event.type != ev_type:
				continue
			if element is not None and getattr(event, "ui_element", None) is not element:
				continue
			result = callback(event)
			if asyncio.iscoroutine(result):
				self.run_task(result)
				passDownCheck = True
		if passDownCheck:
			return
		else:
			self.on_non_generic_pygame_event(event)

	# ── element helpers ───────────────────────────────────────────────────


	def destroy(self):
		for el in self._elements:
			el.kill()
		self._elements.clear()
		self._groups.clear()
		self._cancel_tasks()
		self._event_handlers.clear()
		self.on_destroy()

	def build(self, rect, screen, manager, ui):
		self.destroy()
		self._cancelled = False   # reset for fresh build after resize
		self._rect	 = rect
		self.screen  = screen
		self.manager = manager
		self.ui		 = ui
		self._build_widget_ui(rect)

	# ── scale helper ──────────────────────────────────────────────────────
	def scaled(self, base: int, minimum: int = 6) -> int:
		if self.screen is None:
			return base
		w, h = self.screen.get_size()
		return max(minimum, int(base * min(w / BASE_W, h / BASE_H)))

	def sidebar_options(self) -> list[tuple[str, callable]]:
		return []

	# ── override these ────────────────────────────────────────────────────
	def _build_widget_ui(self, rect: pygame.Rect): pass
	def update(self, dt: float,midi_notes,changed_midi): pass
	def draw(self): pass
	def on_destroy(self): pass


	#THIS IS FOR ANY PUGAME EVENT THAT WAS NOT SUPPOSED TO BE DEALT WITH BEFORE COMING TO CHILD WIDGET.
	#NOW CHILD WIDGETS WILL GET THIS EVENT
	def on_non_generic_pygame_event(self,event): pass
