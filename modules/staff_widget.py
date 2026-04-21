"""
working version


staff_widget.py
───────────────
A ChildWidget that owns a pygame.Surface canvas for drawing music notation.
"""

import logging
import bisect
from fractions import Fraction
from modules.pygame_note_shapes import pygame_shape_constructor
import pygame
import pygame_gui
from modules.childWidget import ChildWidget
from time import monotonic
import logging

_VISIBLE_16 = {6, 8, 10, 12, 14}
_VISIBLE_32 = {6, 8, 10, 12, 14, 18, 20, 22, 24, 26}
_MAX_CHUNK_W = 8000

_MEDIA_BAR_H_BASE = 44	 # design-space pixels, will be scaled

class StaffWidget(ChildWidget):

	class Timer:
		__slots__ = (
			"duration",
			"end_time",
			"time_scale",
			"_paused_remaining",
		)

		def __init__(self, duration_seconds, scale=0.2):
			self.duration = float(duration_seconds)
			self.time_scale = float(scale)
			self.end_time = None
			self._paused_remaining = None

		def play(self):
			if self._paused_remaining is not None:
				self.resume()
			else:
				self.start()

		def set_position(self, seconds):
			if self.running():
				self.end_time = monotonic() + float(seconds) / self.time_scale
			else:
				self._paused_remaining = float(seconds)
		
		def start(self):
			self.end_time = monotonic() + self.duration / self.time_scale
			self._paused_remaining = None

		def restart(self, staff_widget):
			staff_widget.staffEventIterGate = 0	
			self.start()

		def stop(self):
			self.end_time = None
			self._paused_remaining = None

		def pause(self):
			if self.running():
				self._paused_remaining = self.remaining()
				self.end_time = None

		def resume(self):
			if self._paused_remaining is not None:
				self.end_time = monotonic() + self._paused_remaining / self.time_scale	# was: no division
				self._paused_remaining = None

		def skip(self, seconds):
			if not self.running():
				return
			self.end_time -= seconds / self.time_scale	# was: no division

		def set_scale(self, scale):
			if scale <= 0:
				raise ValueError("Scale must be > 0")
			if self.running():
				remaining = self.remaining()
				self.time_scale = float(scale)
				self.end_time = monotonic() + remaining / self.time_scale
			else:
				self.time_scale = float(scale)

		def tick(self, now: float | None = None):
			if not self.running():
				return
			if now is None:
				now = monotonic()
			if now >= self.end_time:
				self.end_time = None
				self.on_finish()

		def remaining(self, now: float | None = None):
			if self.running():
				if now is None:
					now = monotonic()
				return max(0.0, (self.end_time - now) * self.time_scale)  # was: end_time - now
			elif self._paused_remaining is not None:
				return self._paused_remaining
			return self.duration

		def running(self):
			return self.end_time is not None

		def on_finish(self):
			print("Timer finished")


	def __init__(
		self,
		bg_color:	  tuple = (0, 0, 0, 0),
		border:		  int	= 1,
		border_color: tuple = (180, 180, 200, 255),
		showBass=True,
		injected_note_staff_division=None
	):

		self.scrollingCanvas: pygame.Surface | None = None
		self._canvas:		  pygame.Surface | None = None
		self._canvas_rect:	  pygame.Rect	 | None = None
		super().__init__()
		self._bg_color	   = bg_color
		self._border	   = border
		self._border_color = border_color

		self.injected_note_staff_division = injected_note_staff_division		
		self.numIndexes = 32 if showBass else 18
		self.showBass = showBass
		self._file_dialog = None 
		self.staffEvent = None
		self.dumb_staffEvent = None
		self.user_note_shapes=[]
		self.changedBuffer=False
		
		if showBass:
			self.note_range = [2, 6]
		else:
			self.note_range = [4, 6]

		self.note_dic = {}
		self.set_note_dic()
		self.accidentals	  = {}
		self.accidental_state = {}
		self.pl				  = []
		self.new_scale_note   = ''
		self.jumped			  = False
		self.last_played_index = float('inf')
		self.staffEventIterGate = 0
		self._pixels_per_second	= 75
		self.midiCache=None
		self.noteMatchMode=0
		self.changedScrollMode=False
		# CHANGE 1: note_spacing_scale decouples visual spacing from scroll speed.
		# Increase to spread notes further apart without changing how fast they scroll.
		# layout_pps = pixels_per_second * note_spacing_scale is used everywhere
		# notes are placed or measured, so the two stay in sync automatically.
		self.note_spacing_scale = 12.0
		self.press_window_sec	= 0.05
		self.current_allowed_pressed_midi = {}
		self.staff_timer = None
		self.scrolling_events_to_spawn=[]
		self.overlayEventIndex=0

		
		#for proper note time
		self._bpm = 120


		#for snap cannvas
		self.snap_index=0
		self._per_press_prev_pitches: set = set()
		self._prev_note_count: int = 0          # how many notes were held last frame
		self._chord_was_shrinking: bool = False  # True once notes start being released

		# ── Proper Staff Time (case 1) state ─────────────────────────────────
		# Elapsed PT seconds since playback started (or was reset).
		self._pt_elapsed: float = 0.0
		# _pt_map: list of dicts built by _build_pt_map().
		#   Each entry covers one chord:
		#     pt_time   – cumulative PT seconds when this chord should hit the line
		#     scroll_x  – _scroll_x value that places this chord at default_note_position
		#     hold_sec  – how long (PT seconds) this chord occupies before the next
		# scroll_x is interpolated between consecutive entries over hold_sec seconds,
		# producing variable-speed scrolling on the unchanged scrollingCanvas.
		self._pt_map: list = []

		self.canvas_width:	int = 0
		self.canvas_height: int = 0
		self._scroll_x = 0

		self.logger = logging.getLogger(__name__)
		self.logger.setLevel(logging.DEBUG)

		if not self.logger.handlers:  # avoid duplicate handlers
			handler = logging.FileHandler("debug.log", mode="w")  # 🔥 overwrite
			formatter = logging.Formatter(
				"%(asctime)s [%(levelname)s] %(message)s"
			)
			handler.setFormatter(formatter)
			self.logger.addHandler(handler)
	# CHANGE 2: single property so every consumer is guaranteed to agree.
	@property
	def layout_pps(self) -> float:
		"""Pixels per music-second for note layout AND scroll offset."""
		return self.pixels_per_second * self.note_spacing_scale

	# ── bpm property ──────────────────────────────────────────────────────────
	# Changing BPM only affects hold_sec values in _pt_map (how long the scroll
	# spends on each chord).  The scrollingCanvas positions are untouched because
	# they are derived from start_sec × layout_pps, which is independent of BPM.
	@property
	def bpm(self) -> float:
		return self._bpm

	@bpm.setter
	def bpm(self, value: float):
		self._bpm = float(value)
		if self.dumb_staffEvent:
			print("resetting pt map")
			self._build_pt_map()    # rebuild timing map only; canvas stays valid
			self._reset_pt_state()  # reset elapsed so we don't land mid-map with wrong segments

	# ── pixels_per_second property ────────────────────────────────────────────
	# Changing PPS alters layout_pps, which changes BOTH where notes are baked on
	# scrollingCanvas AND the scroll_x_target values in _pt_map.  Both must be
	# rebuilt together or they go out of sync.
	@property
	def pixels_per_second(self) -> float:
		return self._pixels_per_second

	@pixels_per_second.setter
	def pixels_per_second(self, value: float):
		self._pixels_per_second = float(value)
		if self.dumb_staffEvent:
			# Full rebuild: canvas positions and map targets both depend on layout_pps.
			mode = (
				"addMediaBar"
				if self.staffEvent and self.noteMatchMode != 2
				else "removeMediaBar"
			)
			self.buildCanvasElements(mode)
			self._reset_pt_state()


	def _compute_line_ys(self) -> list[float]:
		n	 = self.numIndexes
		pad  = self.canvas_height * 0.1
		step = (self.canvas_height - pad * 2) / (n - 1)
		return [pad + i * step for i in range(n)]

	
	def precompute_sizes(self):
		self._line_ys = self._compute_line_ys()
		self.note_height = (self._line_ys[1] - self._line_ys[0])*1.5
		self.note_width  = self.note_height * 1.3
		self.default_note_position = self.canvas_width // (
			self.injected_note_staff_division or 7.5
		)
		self.look_ahead_sec = self.compute_lookahead_seconds(
				self.canvas_width, self.layout_pps	# CHANGE 3a: use layout_pps
			)

		self.hit_time_offset = (self.canvas_width - self.default_note_position) / self.layout_pps

	def overlayStaffSetup(self):
		if self._canvas is not None:
			del self._canvas
			self._canvas = None

		totalHeight = self._rect.height

		if self.staffEvent and self.noteMatchMode!=2:			   # ← was: if self.dumb_staffEvent
			media_bar_h = int(_MEDIA_BAR_H_BASE * (totalHeight / 600))
			self.media_bar_height = max(32, min(media_bar_h, 900))
		else:
			self.media_bar_height = 0

		self._canvas_rect  = self._rect.copy()
		self.canvas_width  = self._rect.width
		self.canvas_height = self._rect.height - self.media_bar_height
		self._canvas = pygame.Surface((self.canvas_width, self.canvas_height), pygame.SRCALPHA)
		self._press_canvas = pygame.Surface((self.canvas_width, self.canvas_height), pygame.SRCALPHA)

	


	def scrollingStaffSetup(self):
		total_scroll_width = self.canvas_width
		shapes_by_chunk: dict[int, list] = {}

		if self.dumb_staffEvent:
			total_scroll_width = self.staffEvent[1] * self.layout_pps + self.canvas_width

			for event in self.dumb_staffEvent:
				start = event.get("start_sec")
				if start is None:
					continue

				shift    = start * self.layout_pps
				canvas_x = round(self.default_note_position + shift)
				event["x_position"] = canvas_x
				event["current_x"]  = canvas_x

				chunk_idx = int(canvas_x // _MAX_CHUNK_W)
				shapes_by_chunk.setdefault(chunk_idx, [])
				
				# also paint into next chunk if close to the right edge
				near_boundary = (canvas_x % _MAX_CHUNK_W) > (_MAX_CHUNK_W - self.note_width * 2)
				if near_boundary:
					shapes_by_chunk.setdefault(chunk_idx + 1, [])
				
				event_type = event.get("type")
				if event_type == "bar":
					for shape_tuple in event['shapes']:
						shapes_list, _ = shape_tuple
						for shape in shapes_list:
							shape.shift_x(shift)
						shapes_by_chunk[chunk_idx].extend(shapes_list)
						if near_boundary:
							shapes_by_chunk[chunk_idx + 1].extend(shapes_list)
				elif event_type == "chord":
					for shape in event['flat_shapes']:
						shape.shift_x(shift)
					shapes_by_chunk[chunk_idx].extend(event['flat_shapes'])
					if near_boundary:
						shapes_by_chunk[chunk_idx + 1].extend(event['flat_shapes'])
		num_chunks = max(1, (int(total_scroll_width) + _MAX_CHUNK_W - 1) // _MAX_CHUNK_W)
		self._scroll_chunks: list[pygame.Surface] = []

		visible = _VISIBLE_32 if self.numIndexes == 32 else _VISIBLE_16
		color   = (0, 0, 0, 255)
		line_w  = max(1, self.canvas_height // 200)

		for ci in range(num_chunks):
			chunk_w = min(_MAX_CHUNK_W, int(total_scroll_width) - ci * _MAX_CHUNK_W)
			chunk   = pygame.Surface((max(1, chunk_w), self.canvas_height))
			chunk.fill((255, 255, 255))

			for li in visible:
				y = int(self._line_ys[li])
				pygame.draw.line(chunk, color, (0, y), (chunk_w, y), line_w)

			offset = ci * _MAX_CHUNK_W
			for shape in shapes_by_chunk.get(ci, []):
				shape.shift_x(-offset)
				shape.draw(chunk)
				shape.shift_x(offset)

			self._scroll_chunks.append(chunk)

		self.scrollingCanvas = self._scroll_chunks[0] if self._scroll_chunks else None


	def mediaBarSetup(self):
		media_rect = pygame.Rect(
			self._rect.x,
			self._rect.bottom - self.media_bar_height,
			self._rect.width,
			self.media_bar_height,
		)
		self._media_panel = self._add(pygame_gui.elements.UIPanel(
			relative_rect=media_rect,
			manager=self.ui,
			),
			group=self.staffElementGroup
		)
		btn_h = self.media_bar_height - 8
		self._play_btn = self._add(pygame_gui.elements.UIButton(
			relative_rect=pygame.Rect(4, 4, 80, btn_h),
			text="▶ Play",
			manager=self.ui,
			container=self._media_panel,
			),
		
			group=self.staffElementGroup
		)
		self.on_event(pygame_gui.UI_BUTTON_PRESSED, self._on_play_btn, element=self._play_btn,group=self.staffElementGroup)

	def _build_debug_overlay(self):

		hit_x = self.default_note_position+(self.note_width/1.9)
		press_window_px = self.press_window_sec * self.layout_pps

		lead_sec = hit_x / self.layout_pps


		self._debug_overlay = pygame.Surface((self.canvas_width, self.canvas_height), pygame.SRCALPHA)
		self._debug_font = pygame.font.SysFont("monospace", 14)

		#pygame.draw.line(self._debug_overlay, (255, 255, 255, 255),
		#				(int(hit_x), 0), (int(hit_x), self.canvas_height), 2)

		band_surf = pygame.Surface((int(press_window_px * 2), self.canvas_height), pygame.SRCALPHA)
		band_surf.fill((0, 255, 0, 100))
		self._debug_overlay.blit(band_surf, (int(hit_x - press_window_px), 0))

		txt = self._debug_font.render(
			f"hit_x:{hit_x:.0f}  lead:{lead_sec:.3f}s  win:±{self.press_window_sec:.3f}s  ({press_window_px:.0f}px)",
			True, (255, 255, 0)
		)
		self._debug_overlay.blit(txt, (4, 4))


	def buildCanvasElements(self,*args,**kwargs):

		
		mode=args[0]
		
		match mode:
			case "addMediaBar":
				self.staffElementGroup="staffElementGroup"
				self.register_group(self.staffElementGroup, self.buildCanvasElements)
				self.clear()
				self.overlayStaffSetup()
				self.precompute_sizes()
				if self.staffEvent:			   # ← guard both together
					self.mediaBarSetup()
					self.dumb_staffEvent = self.create_dumb_events(self.staffEvent[0])
					self._build_pt_map()
				self.scrollingStaffSetup()
				self._build_debug_overlay()

			case "removeMediaBar":
				self.staffElementGroup="staffElementGroup"
				self.register_group(self.staffElementGroup, self.buildCanvasElements)
				self.clear()
				self.overlayStaffSetup()
				self.precompute_sizes()
				if self.staffEvent:			   # ← guard both together
					self.dumb_staffEvent = self.create_dumb_events(self.staffEvent[0])
					self._build_pt_map()
					self.staff_timer.play()
				self.scrollingStaffSetup()
				self._build_debug_overlay()



	def _build_widget_ui(self, rect: pygame.Rect):
		if self.staffEvent and self.noteMatchMode != 2:
			self.buildCanvasElements("addMediaBar")
		else:
			self.buildCanvasElements("removeMediaBar")



	def line_y(self, index: int) -> float:
		return self._line_ys[index]


	def _on_play_btn(self, event):
		if self.staff_timer is None:
			return
		if self.staff_timer.running():
			self.staff_timer.pause()
			self._play_btn.set_text("▶ Play")
		else:
			self.staff_timer.play()
			self._play_btn.set_text("⏸ Pause")


	def set_note_dic(self):
		note_names = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
		if self.showBass:
			start_line_index = 30
		else:
			start_line_index = 16

		for i in range(int(self.note_range[0]), int(self.note_range[1])):
			for x in note_names:
				self.note_dic[x + str(i)] = start_line_index
				start_line_index -= 1

		self.note_dic["C" + str(self.note_range[1])] = start_line_index

		for i, x in self.note_dic.items():
			print(f"key:{i},   item{x}:")


	def assign_positions(self, row, index, prev_positions=None, width=5, accidentals_list=None):
		accs = accidentals_list if accidentals_list is not None else self.accidentals
		curr_positions = []
		prev_positions = prev_positions or set()
		if not prev_positions:
			if len(row) == 1:
				step = 1
			else:
				if (index - 1 in accs):
					step = 2
					print("stepping 2 AAAAA")
				else:
					print("steppa only 1 AAAAAA")
					step = 1

			col = 0
			for _ in row:
				if col >= width:
					raise ValueError("Not enough columns for first row spacing")
				curr_positions.append(col)
				col += step
		else:
			free_cols = [c for c in range(width) if c not in prev_positions]
			if len(free_cols) < len(row):
				raise ValueError("Not enough columns to avoid stacking")
			curr_positions = free_cols[:len(row)]

		return curr_positions


	def make_accidentals(self, accidentals_list, width=5):
		note_height			  = self.note_height
		note_width			  = self.note_width
		default_note_position = self.default_note_position
		return_list			  = []
		width				  = 8
		prev_positions		  = None

		for i in sorted(accidentals_list.keys(), reverse=True):
			row = accidentals_list[i]
			if (i + 1 not in accidentals_list):
				prev_positions = None

			curr = self.assign_positions(row, i, prev_positions, width, accidentals_list)
			prev_positions = set(curr)

			count = 0
			y = self.line_y(i)

			for x in row:
				if isinstance(x, tuple):
					accidental_char, note_x = x
				else:
					accidental_char = x
					note_x = default_note_position

				position_mult = curr[count] + 1
				count += 1

				accidental_x = (note_x + note_width / 2) - ((note_width * 0.9) * int(position_mult))

				accidental_shapes = pygame_shape_constructor(
					shape_x=accidental_x,
					shape_y=y,
					shape_width=note_width,
					shape_height=note_height,
					type=accidental_char,
				)

				if accidental_shapes is None:
					raise ValueError(f"shape_constructor returned None for accidental '{accidental_char}' at x={accidental_x}, y={y}, width={note_width}, height={note_height}")

				return_list.extend(accidental_shapes)

		return return_list


	def accidental_type(self, note, always_accidental=False):
		if always_accidental:
			length = len(note)
			if length > 2:
				return (note[1] + note[2])
			elif length > 1:
				return note[1]
			else:
				return "N"
		else:
			if note not in self.manager.non_chromatic_music_scale:
				length = len(note)
				if length > 2:
					return note[1] + note[2]
				elif length > 1:
					return note[1]
				else:
					return "N"
			else:
				return None


	def make_note(
		self,
		pl_index,
		position=None,
		index=6,
		accidentals_list=None,
		new_scale_note=None,
		pitch_list=None,
		jumped=None,
		last_played_index=None,
		note_type='whole',
		dotted=False,
	):
		return_list = []
		note_height = self.note_height
		note_width	= self.note_width
		
		if position is None:
			position = self.default_note_position

		is_xml_mode = (accidentals_list is not None)

		if accidentals_list is None:
			accidentals = self.accidentals
		else:
			accidentals = accidentals_list
		
		if new_scale_note is None:
			new_scale_note = self.new_scale_note

		if pitch_list is None:
			pitch_list = self.pl
		
		default_jump = False
		if jumped is None:
			default_jump = True	
			jumped = self.jumped

		default_last_played = False
		if last_played_index is None:
			default_last_played = True
			last_played_index = self.last_played_index

		y = self.line_y(index)
		
		final_position = position
		
		if not jumped:

			if last_played_index - 1 == index:
				final_position = position + (note_width * 0.8)
				jumped = True
			elif last_played_index == index:  # ← restore this guard
				final_position = position + note_width
				jumped = True
		else:
			jumped = False

		x = final_position

		accidental_ref_x = position

		note_shapes = pygame_shape_constructor(
			shape_x=x,
			shape_y=y,
			shape_width=note_width,
			shape_height=note_height,
			type=note_type,
			paint=None,
			dotted=dotted,
		)
		if note_shapes is None:
			raise ValueError(f"shape_constructor returned None for whole note at x={x}, y={y}, width={note_width}, height={note_height}")
		
		shapes, note_type = note_shapes[0]
		
		accidental = self.accidental_type(new_scale_note, always_accidental=False)

		if accidental is None:
			if index in accidentals:
				t_accidental = self.accidental_type(new_scale_note, always_accidental=True)
				t_list = accidentals[index]
				if is_xml_mode:
					t_list.append((t_accidental, accidental_ref_x))
				else:
					t_list.append(t_accidental)
				accidentals[index] = t_list
			# ← both octave-migration for-loops removed entirely
		else:
			if index in accidentals:
				t_list = accidentals[index]
				if is_xml_mode:
					t_list.append((accidental, accidental_ref_x))
				else:
					t_list.append(accidental)
				accidentals[index] = t_list
			else:
				if last_played_index == index:
					if pl_index >= 2:
						old_note = str(self.manager.midi_to_scale_note(pitch_list[pl_index - 2]))
						old_note_name_only = old_note[0] + ''.join(ch for ch in old_note[1:] if ch in ('#', 'b'))
						old_accidental = self.accidental_type(old_note_name_only, always_accidental=True)
						if is_xml_mode:
							accidentals[index] = [(old_accidental, accidental_ref_x), (accidental, accidental_ref_x)]
						else:
							accidentals[index] = [old_accidental, accidental]
					else:
						if is_xml_mode:
							accidentals[index] = [(accidental, accidental_ref_x)]
						else:
							accidentals[index] = [accidental]
				else:
					if is_xml_mode:
						accidentals[index] = [(accidental, accidental_ref_x)]
					else:
						accidentals[index] = [accidental]

		if accidentals_list is None:
			self.accidentals = accidentals
		else:
			accidentals_list = accidentals

		if default_jump:
			self.jumped = jumped

		if default_last_played:
			self.last_played_index = last_played_index
			
		try:
			last_played_index = index
			self.last_played_index = index
		except UnboundLocalError:
			print("error 1647 ds")
			pass

		return_list.append([*shapes, note_type])
		
		if accidentals_list is not None:
			return return_list, accidentals_list, jumped, last_played_index, final_position
		else:
			return return_list

	def create_dumb_events(self, events):
		dumb_events			= []
		global_note_counter = 0
		last_playable_shape = None

		for index, i in enumerate(events):
			event_type = i.get("type")

			if event_type == "bar":
				bar_start_sec = i.get('start_sec')
				if last_playable_shape is not None:
					prev_start	  = last_playable_shape.get('start_sec', bar_start_sec)
					bar_start_sec = (prev_start + bar_start_sec) / 2

				bar_top    = self._line_ys[0]
				bar_bottom = self._line_ys[-1]
				bar_shapes = pygame_shape_constructor(
					shape_x		 = self.default_note_position + self.note_width / 2,
					shape_y		 = bar_top,
					shape_height = bar_bottom - bar_top,
					shape_width  = max(1, self.canvas_height // 200),
					type		 = "bar",
				)
				dumb_events.append({
					"type"	   : event_type,
					"shapes"   : bar_shapes,
					"start_sec": bar_start_sec,
					"color"		 : None
				})

			elif event_type == "chord":
				pl				  = []
				beatFracList = []
				notes			  = i.get("notes", [])
				accidentals_list  = {}
				jumped			  = False
				last_played_index = float('inf')
				note_shapes_list  = []
				current_position  = self.default_note_position

				for note in notes:
					pl.append(note.get('pitch'))
					beatFracList.append(note.get("type"))

				for pl_index, note in enumerate(notes, start=1):
					global_note_counter += 1
					pitch = note.get('display_pitch', note.get('pitch'))
					tscale_note  = str(self.manager.midi_to_scale_note(pitch))
					note_name	 = tscale_note[0]
					note_octave  = tscale_note[-1]
					new_scale_note = tscale_note[0]
					for ch in tscale_note[1:]:
						if ch in ('#', 'b'):
							new_scale_note += ch
						else:
							break  # hit the octave number (or '-'), stop
					#scales like F# will have C## so to not have c,c#,c## we make c to b#.
					#but my systems is crude and does not work like that. it just takes in an index and note
					#so I have to switch it back for this function to let the staff know that this is the first appeance of B and not the last B in the scale
					if new_scale_note == "B#":
						lookup_key = str(note_name + str(int(note_octave) - 1))
					else:
						lookup_key = str(note_name + note_octave)

					if lookup_key in self.note_dic:
						idx = self.note_dic[lookup_key]
						note_shapes, accidentals_list, jumped, last_played_index, current_position = \
							self.make_note(
								pl_index,
								position		  = current_position,
								index			  = idx,
								accidentals_list  = accidentals_list,
								new_scale_note	  = new_scale_note,
								pitch_list		  = pl,
								jumped			  = jumped,
								last_played_index = last_played_index,
								note_type		  = note.get('note_type', 'quarter'),
								dotted			  = note.get('dots', 0) > 0,
							)
						note_shapes_list.append(note_shapes)

				make_accidentals_result = self.make_accidentals(accidentals_list)

				flat  = [s for nw in note_shapes_list for ni in nw for s in ni[:-1]]
				flat += [s for acc in make_accidentals_result for s in acc[0]]

				dumb_events.append({
					"type"		 : event_type,
					"shapes"	 : [note_shapes_list, make_accidentals_result],
					"flat_shapes": flat,
					"start_sec"  : i.get('start_sec'),
					"pitch_list" : pl,
					"typeList"	: beatFracList,
					"min_fraction": i.get('min_fraction', Fraction(1, 4)),
					"color"		 : None,
					"sound_played": False
				})
				last_playable_shape = i

		return dumb_events


	def _find_next_note_time(self, events, current_div):
		for event in events:
			if event.get("type") == "chord" and event.get("start_div") > current_div:
				return event.get("start_sec")
		return None


	def _shift_drawable_x(self, shape, dx):
		from modules.pygame_note_shapes import PygameShape
		if isinstance(shape, PygameShape):
			shape.shift_x(dx)


	def edit_shape(self, shape_to_resize, color=None):
		event_type = shape_to_resize.get("type")
		x_target   = shape_to_resize.get("x_position")

		if x_target is None:
			return

		previous_x = shape_to_resize.get("current_x", round(self.canvas_width))
		dx		   = -(x_target - previous_x)
		shape_to_resize["current_x"] = x_target

		if event_type == "bar":
			for shape_group in shape_to_resize.get("shapes", []):
				if isinstance(shape_group, tuple):
					shape_list, _ = shape_group
					for shape in shape_list:
						self._shift_drawable_x(shape, dx)
			return

		if event_type != "chord":
			return

		note_shapes, accidental_shapes = shape_to_resize["shapes"]

		_GREEN = (0, 200, 0, 255)

		def _shift_and_color(shape, color=None):
			self._shift_drawable_x(shape, dx)
			if color is not None:
				shape.set_color(color)

		if color is None:
			for note_group in note_shapes:
				for note_block in note_group:
					if isinstance(note_block, list):
						for shape in note_block[:-1]:
							self._shift_drawable_x(shape, dx)
			for acc_block in accidental_shapes:
				for shape in acc_block[0]:
					self._shift_drawable_x(shape, dx)
		else:
			for note_group in note_shapes:
				for note_block in note_group:
					if isinstance(note_block, list):
						for shape in note_block[:-1]:
							_shift_and_color(shape, color=color)
			for acc_block in accidental_shapes:
				for shape in acc_block[0]:
					_shift_and_color(shape, color=color)


	def compute_lookahead_seconds(self, screen_length_px, pixels_per_second,
								  buffer_seconds=0.1):
		return screen_length_px / pixels_per_second + buffer_seconds


	def get_events_lookahead_and_place(
		self,
		total_time,
		countdown_time,
		look_ahead_sec,
		backward_window_sec=1.6,
		events=None,
		check_index=True,
		color=None,
		true_time=None,
		debug=False
	):
		"""Amortized O(1) lookahead."""
		_GREEN = (0, 200, 0, 255)

		current_time = total_time - countdown_time
		if true_time is None:
			true_time = current_time

		window_end = current_time + look_ahead_sec

		if events is None:
			events = self.dumb_staffEvent

		if events is None:
			return []

		result	 = []
		n		 = len(events)
		i		 = self.staffEventIterGate if check_index else 0
		commit_i = i

		while i < n:
			event = events[i]
			#what a shitty language I hate this place
			chosenColor = event["color"] if event["color"] else color
			start = event.get("start_sec")
			if start is None:
				i += 1
				continue

			start = float(start)

			if current_time > start + backward_window_sec:	 # ← was hardcoded 1.6
				commit_i = i + 1
				i += 1
				continue

			if start >= window_end:
				break

			event['x_position'] = round(
				self.canvas_width - ((start - current_time) * self.layout_pps)
			)

			if debug==True:
				self.logger.debug(f"[start]: {start}")
				self.logger.debug(f"[x_position]: {event['x_position']}")
				self.logger.debug(f"[TOTAL TIME]: {total_time}")
				self.logger.debug(f"[countdown_time]: {countdown_time}")
				self.logger.debug(f"[true_time]: {true_time}")
				self.logger.debug(f"[iter gate]: {self.staffEventIterGate}")

			in_press_window = abs(true_time - start) <= self.press_window_sec

			if in_press_window:
				temp_midi = self.current_allowed_pressed_midi
				if "pitch_list" in event:
					pitch_list = event["pitch_list"]
					if len(pitch_list) > 1:

						blocked=False
						for index,pitch in enumerate(pitch_list):
							if pitch not in temp_midi or not temp_midi[pitch][1]:
								blocked=True
								break

						if not blocked:

							self.edit_shape(event, color=_GREEN)
							
							event["color"]=_GREEN
						else:
							self.edit_shape(event, color=chosenColor)
					elif pitch_list[0] in temp_midi and not temp_midi[pitch_list[0]][1]:
						event["color"]=_GREEN
						self.edit_shape(event, color=_GREEN)
						print(f"single note turned green {pitch_list}")
					else:
						self.edit_shape(event, color=chosenColor)

				else:
					self.edit_shape(event, color=chosenColor)
			else:
				self.edit_shape(event, color=chosenColor)
			result.append(event)
			i += 1

		if check_index:
			self.staffEventIterGate = commit_i

		return result

	def clear(self):
		if self._canvas is not None:
			self._canvas.fill(self._bg_color)


	def draw_shape(self, shape, canvas):
		if canvas is not None:
			shape.draw(canvas)


	def draw_shapes(self, shapes, canvas):
		if canvas is not None:
			for shape in shapes:
				shape.draw(canvas)


	def draw(self):
		if self._canvas is None or self._canvas_rect is None:
			return

		if hasattr(self, '_scroll_chunks') and self._scroll_chunks:
			sx = round(self._scroll_x)
			for ci, chunk in enumerate(self._scroll_chunks):
				screen_x = sx + ci * _MAX_CHUNK_W
				if screen_x + chunk.get_width() < 0:
					continue   # fully off the left edge
				if screen_x > self.canvas_width:
					break      # fully off the right edge
				self.screen.blit(chunk, (self._canvas_rect.x + screen_x, self._canvas_rect.y))
		elif self.scrollingCanvas is not None:
			self.screen.blit(
				self.scrollingCanvas,
				(self._canvas_rect.x + self._scroll_x, self._canvas_rect.y)
			)

		self.screen.blit(self._press_canvas, self._canvas_rect.topleft)
		self.screen.blit(self._canvas, self._canvas_rect.topleft)
		if self._border:
			pygame.draw.rect(self.screen, self._border_color, self._canvas_rect, self._border)
		self.screen.blit(self._debug_overlay, self._canvas_rect.topleft)

	def canvas_rect(self) -> pygame.Rect | None:
		return self._canvas_rect.copy() if self._canvas_rect else None

	def to_canvas(self, screen_x: float, screen_y: float) -> tuple[float, float]:
		if self._canvas_rect is None:
			return screen_x, screen_y
		return (screen_x - self._canvas_rect.x,
				screen_y - self._canvas_rect.y)

	def to_screen(self, canvas_x: float, canvas_y: float) -> tuple[float, float]:
		if self._canvas_rect is None:
			return canvas_x, canvas_y
		return (canvas_x + self._canvas_rect.x,
				canvas_y + self._canvas_rect.y)


	def _reset_pt_state(self):
		"""Reset Proper Staff Time elapsed clock and overlay gate to the beginning."""
		self._pt_elapsed       = 0.0
		self.overlayEventIndex = 0

	def changeScrollMode(self,selected: str):
		match selected:
			case "Real Time Scroll":
				self.noteMatchMode=0
			case "Proper Staff Time":
				self.noteMatchMode=1
				self._reset_pt_state()
			case "Per Press":
				self.noteMatchMode=2
				self.mutate_group(self.staffElementGroup,"removeMediaBar")
			case "None":
				self.noteMatchMode=3
		self.changedScrollMode=True

		

	def sidebar_options(self):
		return [
			{
				"type": "dropdown",
				"label": "Note Match Mode",
				"options": ["Real Time Scroll", "Proper Staff Time", "Per Press","None"],
				"on_change": self.changeScrollMode
			},
			{
				"type": "button",
				"label": "open Music XML File",
				"callback": self._open_file_dialog
			}
		]

	def _open_file_dialog(self):
		if self._file_dialog is not None:
			return
		self._file_dialog = pygame_gui.windows.UIFileDialog(
			rect=pygame.Rect(100, 100, 500, 400),
			manager=self.ui,
			window_title="Open MusicXML",
			allowed_suffixes={"xml", "mxl", "musicxml"},
		)
		self.on_event(pygame_gui.UI_FILE_DIALOG_PATH_PICKED, self._on_path_picked, element=self._file_dialog)
		self.on_event(pygame_gui.UI_WINDOW_CLOSE,			 self._on_dialog_close, element=self._file_dialog)

	def _on_path_picked(self, event):
		self.run_task(self._load_xml(event.text))
		self._file_dialog = None

	def _on_dialog_close(self, event):
		self._file_dialog = None

	async def _load_xml(self, path):
		from modules.mxmlParser import parse_musicxml_chords
		self.staffEvent = parse_musicxml_chords(path)
		self.staff_timer = self.Timer(self.staffEvent[1])
		self.dumb_staffEvent = None
		self.snap_index = 0  # ← reset so first press shows note 1
		self._reset_pt_state()   # ← reset Proper Staff Time to chord 0

		if self.noteMatchMode != 2:
			self.mutate_group(self.staffElementGroup, "addMediaBar")
		else:
			self.mutate_group(self.staffElementGroup, "removeMediaBar")
			# Don't call snap here — let the first keypress trigger it naturally

	def on_non_generic_pygame_event(self, event):
		pass


			
	#note matching modules




	
	def processUserEvents(self, midi, changedMidi, trueTime=None):
		if not changedMidi:
			if self.changedBuffer:
				return self.user_note_shapes
			else:
				self.changedBuffer = True
		else:
			self.changedBuffer = False

		accidentals = {}
		accidental_state = {}
		last_played_index = float('inf')
		jumped = False
		old_pressed_midi = self.current_allowed_pressed_midi
		self.current_allowed_pressed_midi = {}
		pl_count = 0
		self.user_note_shapes = []

		if midi:
			active = [(p, v) for p, v in enumerate(midi) if v != 0]  # already sorted low→high
			pitch_list = [p for p, _ in active]
			current_position = self.default_note_position

			for pitch, velocity in active:
				pl_count += 1

				tscale_note = str(self.manager.midi_to_scale_note(pitch))
				note_name   = tscale_note[0]
				note_octave = tscale_note[-1]
				new_scale_note = tscale_note[0]
				for ch in tscale_note[1:]:
					if ch in ('#', 'b'):
						new_scale_note += ch
					else:
						break

				if str(note_name + note_octave) in self.note_dic:

					if self.staff_timer and trueTime:
						if pitch in old_pressed_midi:
							timestamp, pressedTooLong = old_pressed_midi[pitch]
							if not pressedTooLong:
								self.current_allowed_pressed_midi[pitch] = (timestamp, True)
							else:
								self.current_allowed_pressed_midi[pitch] = old_pressed_midi[pitch]
						else:
							self.current_allowed_pressed_midi[pitch] = (trueTime, False)

					if new_scale_note == "B#":
						index = self.note_dic[str(note_name + str(int(note_octave) - 1))]
					else:
						index = self.note_dic[str(note_name + note_octave)]

					note_result, accidentals, jumped, last_played_index, current_position = self.make_note(
						pl_count,
						position=None,          # ← tracks offset across notes
						index=index,
						accidentals_list=accidentals,
						new_scale_note=new_scale_note,
						pitch_list=pitch_list,
						jumped=jumped,
						last_played_index=last_played_index
					)

					for note_block in note_result:
						for shape in note_block[:-1]:
							self.user_note_shapes.append(shape)

					accidental_state[str(index)] = [s for note_block in note_result for s in note_block[:-1]]

			canvas_art = self.make_accidentals(accidentals)
			for i in canvas_art:
				if i[-1] in {'#', 'b', 'N', '##', 'bb'}:
					i = i[:-1]
				for e in i:
					if type(e) == list:
						for x in e:
							self.user_note_shapes.append(x)
					else:
						self.user_note_shapes.append(e)

		return self.user_note_shapes
	
	


	def _build_pt_map(self):
		"""
		Build self._pt_map from dumb_staffEvent using BPM + time signature + note fractions.

		For each chord:
		  hold_sec  = float(min_fraction) × time_sig_denominator × (60 / bpm)

		  Example – 4/4 @ 120 bpm, quarter note  (Fraction 1/4):
		    hold_sec = (1/4) × 4 × 0.5 = 0.5 s

		  Example – 6/8 @ 60 bpm, dotted-quarter  (Fraction 3/8):
		    hold_sec = (3/8) × 8 × 1.0 = 3.0 s

		scroll_x_target = -(start_sec × layout_pps)
		  This is the _scroll_x value that places the chord exactly at
		  default_note_position on screen (canvas_x + scroll_x = default_note_position).
		  scrollingCanvas is never touched; only the scroll offset changes.

		pt_time is stored directly on each dumb_staffEvent chord dict so that
		_draw_press_window_pt can compare it against _pt_elapsed.

		Also stores scroll_x on bar events so they scroll correctly too.
		"""
		if not self.dumb_staffEvent:
			self._pt_map = []
			return

		# Resolve time-signature denominator from parsed doc (staffEvent[2]).
		time_sig_denom = 4
		if self.staffEvent and len(self.staffEvent) > 2:
			sigs = self.staffEvent[2]
			if sigs:
				time_sig_denom = sigs[0].denominator

		beat_sec = 60.0 / max(self.bpm, 1)
		pt_time  = 0.0
		pt_map   = []

		# We need bar events in the map too so they scroll smoothly between chords.
		# Strategy: iterate all events; for bars, interpolate their pt_time linearly
		# between the surrounding chords based on their start_sec ratio.
		# Simpler: just assign them the pt_time of the next chord they precede.
		# We do two passes – first build chord entries, then slot bars in between.

		chord_entries = []   # (dumb_event_index, pt_time_at_chord, scroll_x_target)

		for ev in self.dumb_staffEvent:
			if ev['type'] != 'chord':
				continue

			start_sec      = float(ev.get('start_sec') or 0.0)
			scroll_x_target = -(start_sec * self.layout_pps)
			min_frac        = ev.get('min_fraction', Fraction(1, 4))
			hold_sec        = float(min_frac) * time_sig_denom * beat_sec

			# Tag the event so _draw_press_window_pt can use it without a dict lookup.
			ev['pt_time']      = pt_time
			ev['pt_scroll_x']  = scroll_x_target

			chord_entries.append({
				'pt_time'  : pt_time,
				'scroll_x' : scroll_x_target,
				'hold_sec' : hold_sec,
			})
			pt_time += hold_sec

		# Tag bar events with the pt_time + scroll_x of the nearest preceding chord.
		last_pt_time   = 0.0
		last_scroll_x  = 0.0
		for ev in self.dumb_staffEvent:
			if ev['type'] == 'chord':
				last_pt_time  = ev['pt_time']
				last_scroll_x = ev['pt_scroll_x']
			elif ev['type'] == 'bar':
				ev['pt_time']     = last_pt_time
				ev['pt_scroll_x'] = last_scroll_x

		self._pt_map = chord_entries

	def _draw_press_window_pt(self, trueTime: float):
		"""
		Draw the green press-window highlight for Proper Staff Time mode.

		Identical in purpose to _draw_press_window, but uses event['pt_time']
		(BPM-computed) instead of event['start_sec'] (wall-clock).  Shapes are
		temporarily shifted to their current screen position using _scroll_x and
		then restored – scrollingCanvas bitmaps are never modified.
		"""
		_GREEN = (0, 200, 0, 255)
		self._press_canvas.fill((0, 0, 0, 0))

		if not self.dumb_staffEvent:
			return

		sx = round(self._scroll_x)

		for event in self.dumb_staffEvent[self.overlayEventIndex:]:
			if event.get('type') != 'chord':
				continue
			pt_time = event.get('pt_time')
			if pt_time is None:
				continue
			if pt_time - trueTime > self.press_window_sec:
				if event.get("sound_played"):
					for i in event.get("pitch_list"):
						self.manager.midiAudioPlayer.note_off(i)
					event["sound_played"]=False
				break

				# all later events are further in the future
			if trueTime - pt_time > self.press_window_sec:
				if event.get("sound_played"):
					for i in event.get("pitch_list", []):
						self.manager.midiAudioPlayer.note_off(i)
					event["sound_played"] = False
				continue                      # gate should have caught this; be safe
			
			#play sound
			if not event.get("sound_played",False):
				for i in event.get("pitch_list"):
					self.manager.midiAudioPlayer.note_on(i)
				event["sound_played"]=True
			

			for shape in event.get('flat_shapes', []):
				shape.shift_x(sx)             # → current screen position
				if getattr(shape, '_is_fill_mask', False):
					shape.draw(self._press_canvas)
				else:
					old_color   = shape.color
					shape.color = _GREEN
					shape.draw(self._press_canvas)
					shape.color = old_color
				shape.shift_x(-sx)            # exact undo

	def _draw_press_window(self, trueTime):
		"""
		Clear _press_canvas and re-draw only the notes inside the press window.

		How it works
		------------
		scrollingCanvas has every note baked at (default_pos + start*layout_pps).
		We can't recolour those pixels without a full redraw.  Instead:
		  1. Clear this transparent overlay (cheap — one fill)
		  2. For each chord in the press window:
			   shift_x( +sx )   move shape to its current screen-x
			   draw green copy  onto _press_canvas (the overlay)
			   shift_x( -sx )   restore _dx so scrollingCanvas is untouched
		  3. draw() blits the overlay on top of scrollingCanvas at fixed position

		Gate
		----
		Uses overlayEventIndex (advanced in case 0 update loop) so we never scan
		events that have already scrolled off the left edge.
		staffEventIterGate belongs to per-press mode — NOT used here.

		Cost: O(events_in_window) — typically 1-3 chords per frame.
		"""
		_GREEN = (0, 200, 0, 255)
		self._press_canvas.fill((0, 0, 0, 0))

		if not self.dumb_staffEvent:
			return

		# Round once — shift_x stores int _dx; repeated float add/undo drifts.
		sx = round(self._scroll_x)

		for event in self.dumb_staffEvent[self.overlayEventIndex:]:
			if event.get("type") != "chord":
				continue
			start = event.get("start_sec")
			if start is None:
				continue

			# Events are time-sorted — past the window means all later ones are too.
			if start - trueTime > self.press_window_sec:
				if event.get("sound_played"):
					for i in event.get("pitch_list"):
						self.manager.midiAudioPlayer.note_off(i)
					event["sound_played"]=False
				break

			# Before the window (gate should have caught this, but be safe)
			if trueTime - start > self.press_window_sec:
				if event.get("sound_played"):
					for i in event.get("pitch_list", []):
						self.manager.midiAudioPlayer.note_off(i)
					event["sound_played"] = False
				continue
			
			#play sound
			if not event.get("sound_played",False):
				for i in event.get("pitch_list"):
					self.manager.midiAudioPlayer.note_on(i)
				event["sound_played"]=True


			#color
			for shape in event.get("flat_shapes", []):
				shape.shift_x(sx)                          # → current screen position

				if getattr(shape, '_is_fill_mask', False):
					shape.draw(self._press_canvas)         # white hole — keep white
				else:
					old_color   = shape.color
					shape.color = _GREEN
					shape.draw(self._press_canvas)
					shape.color = old_color                # restore original

				shape.shift_x(-sx)                         # ← undo, scrollingCanvas clean

	def update(self, deltaTime, midi_notes, changedMidi):
		if self._canvas is None:
			return

		if not (self.staff_timer and self.staff_timer.running()):
			if self.noteMatchMode != 2:
				self.processUserEvents(midi_notes, changedMidi, trueTime=None)
				self.clear()
				self.draw_shapes(self.user_note_shapes, self._canvas)
				# FIX 1: remove self._canvas.blit(self._debug_overlay) here too
				return

		self.clear()

		temp_shape_list = []
		match self.noteMatchMode:
			case 0:
				events_to_spawn = []
				now = monotonic()
				countdown_time = max(0.0, (self.staff_timer.end_time - now) * self.staff_timer.time_scale)
				trueTime = self.staffEvent[1] - countdown_time
				target_x = -(trueTime * self.layout_pps)
				smoothing = 2
				self._scroll_x += (target_x - self._scroll_x)

				# Advance the index past anything scrolled off the left edge
				while (
					self.overlayEventIndex < len(self.dumb_staffEvent)
					and self.dumb_staffEvent[self.overlayEventIndex].get("x_position", 0) + self._scroll_x < -self.note_width
				):
					self.overlayEventIndex += 1

				# scrollingCanvas owns all note/bar shapes and scrolls via _scroll_x.
				# _canvas is a fixed overlay — nothing from dumb_staffEvent goes here.
				
				self.processUserEvents(midi_notes, changedMidi, trueTime=trueTime)
				self._draw_press_window(trueTime)
			case 1:  # Proper Staff Time — variable-speed scroll driven by BPM + fractions
				if not self._pt_map:
					return

				self._pt_elapsed += deltaTime
				trueTime = self._pt_elapsed

				# ── Locate current segment ────────────────────────────────────────
				# Binary search: find the last chord whose pt_time <= _pt_elapsed.
				pt_times = [e['pt_time'] for e in self._pt_map]
				idx = bisect.bisect_right(pt_times, self._pt_elapsed) - 1
				idx = max(0, min(idx, len(self._pt_map) - 1))

				entry = self._pt_map[idx]

				# ── Interpolate scroll_x within the segment ───────────────────────
				# Between chord[idx] and chord[idx+1] we linearly move _scroll_x
				# from entry['scroll_x'] to next['scroll_x'] over entry['hold_sec']
				# seconds.  This is the variable-speed magic: a long note (large
				# hold_sec) scrolls slowly; a short note scrolls quickly.
				if idx + 1 < len(self._pt_map):
					next_entry  = self._pt_map[idx + 1]
					t_into      = self._pt_elapsed - entry['pt_time']
					frac        = min(1.0, t_into / max(entry['hold_sec'], 1e-9))
					self._scroll_x = (
						entry['scroll_x']
						+ frac * (next_entry['scroll_x'] - entry['scroll_x'])
					)
				else:
					# Past the last chord — freeze at its target position.
					self._scroll_x = entry['scroll_x']

				# ── Show user notes + press-window highlight ──────────────────────
				self.processUserEvents(midi_notes, changedMidi, trueTime=trueTime)

				# Advance gate past chords that are fully behind the press window.
				while (
					self.overlayEventIndex < len(self.dumb_staffEvent)
					and (self.dumb_staffEvent[self.overlayEventIndex].get('pt_time') or 0.0)
						< self._pt_elapsed - self.press_window_sec
				):
					self.overlayEventIndex += 1

				self._draw_press_window_pt(trueTime)
				events_to_spawn = []


			case 2:  # Per Press
				events_to_spawn = []

				if not self.dumb_staffEvent:
					return []

				if midi_notes:
					noteCount = sum(1 for v in midi_notes if v != 0)

					# If notes are being released, the chord is shrinking — remember that.
					if noteCount < self._prev_note_count:
						self._chord_was_shrinking = True

					# Advance only when a note is being PRESSED (count going up), and only
					# if it's a genuinely new chord — either coming from silence or after
					# the previous chord started shrinking (notes were released).
					# Releases set _chord_was_shrinking but must NOT advance by themselves.
					note_count_increased = noteCount > self._prev_note_count
					has_active_notes = (
						note_count_increased
						and (self._prev_note_count == 0 or self._chord_was_shrinking)
					)

					self._prev_note_count = noteCount

					if changedMidi and has_active_notes:
						self._chord_was_shrinking = False  # consumed — reset for next chord

						# Skip bar events — only snap to chords
						while (
							self.snap_index < len(self.dumb_staffEvent)
							and self.dumb_staffEvent[self.snap_index].get("type") != "chord"
						):
							self.snap_index += 1

						if self.snap_index >= len(self.dumb_staffEvent):
							self.processUserEvents(midi_notes, changedMidi, trueTime=None)
							return self.cachedShapes

						newNoteTime = self.dumb_staffEvent[self.snap_index]["start_sec"]
						self.snap_index += 1

						self._scroll_x = -(newNoteTime * self.layout_pps)
						self.logger.debug(f"[scroll x]: {self._scroll_x}")

						now = monotonic()
						countdown_time = self.staff_timer.remaining()
						trueTime = self.staffEvent[1] - countdown_time
						self.processUserEvents(midi_notes, changedMidi, trueTime=trueTime)

					else:
						now = monotonic()
						countdown_time = max(0.0, (self.staff_timer.end_time - now) * self.staff_timer.time_scale)
						trueTime = self.staffEvent[1] - countdown_time
						self.processUserEvents(midi_notes, changedMidi, trueTime=trueTime)

				else:
					# All notes released — next press starts a fresh chord from silence.
					self._prev_note_count = 0
					self._chord_was_shrinking = False
					now = monotonic()
					countdown_time = max(0.0, (self.staff_timer.end_time - now) * self.staff_timer.time_scale)
					trueTime = self.staffEvent[1] - countdown_time
					self.processUserEvents(midi_notes, changedMidi, trueTime=trueTime)



			case 3:  # None
				events_to_spawn = []
				now = monotonic()
				countdown_time = max(0.0, (self.staff_timer.end_time - now) * self.staff_timer.time_scale)
				trueTime = self.staffEvent[1] - countdown_time
				target_x = -(trueTime * self.layout_pps)
				smoothing = 2
				self._scroll_x += (target_x - self._scroll_x) * min(1.0, smoothing * deltaTime)
				self.processUserEvents(midi_notes, changedMidi, trueTime=trueTime)

		for event in events_to_spawn:
			if event.get("type") == "chord":
				temp_shape_list.extend(event['flat_shapes'])

		temp_shape_list.extend(self.user_note_shapes)
		self.draw_shapes(temp_shape_list, self._canvas)


	def on_destroy(self):
		if self._canvas is not None:
			del self._canvas
			self._canvas = None
		self._file_dialog = None
