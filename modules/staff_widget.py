"""
working version


staff_widget.py
───────────────
A ChildWidget that owns a pygame.Surface canvas for drawing music notation.
"""

from modules.pygame_note_shapes import pygame_shape_constructor
import pygame
import pygame_gui
from modules.childWidget import ChildWidget
from time import monotonic

_VISIBLE_16 = {6, 8, 10, 12, 14}
_VISIBLE_32 = {6, 8, 10, 12, 14, 18, 20, 22, 24, 26}

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
		self.pixels_per_second	= 75
		self.midiCache=None
		# CHANGE 1: note_spacing_scale decouples visual spacing from scroll speed.
		# Increase to spread notes further apart without changing how fast they scroll.
		# layout_pps = pixels_per_second * note_spacing_scale is used everywhere
		# notes are placed or measured, so the two stay in sync automatically.
		self.note_spacing_scale = 12.0
		self.press_window_sec	= 0.05
		self.current_allowed_pressed_midi = {}
		self.staff_timer = None


		self.canvas_width:	int = 0
		self.canvas_height: int = 0
		self._scroll_x = 0


	# CHANGE 2: single property so every consumer is guaranteed to agree.
	@property
	def layout_pps(self) -> float:
		"""Pixels per music-second for note layout AND scroll offset."""
		return self.pixels_per_second * self.note_spacing_scale


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

		if self.staffEvent:            # ← was: if self.dumb_staffEvent
			media_bar_h = int(_MEDIA_BAR_H_BASE * (totalHeight / 600))
			self.media_bar_height = max(32, min(media_bar_h, 900))
		else:
			self.media_bar_height = 0

		self._canvas_rect  = self._rect.copy()
		self.canvas_width  = self._rect.width
		self.canvas_height = self._rect.height - self.media_bar_height
		self._canvas = pygame.Surface((self.canvas_width, self.canvas_height),pygame.SRCALPHA)

	


	def scrollingStaffSetup(self):
		scrolling = False
		temp_shape_list = []
		scroll_width = self.canvas_width
		if self.dumb_staffEvent:
			scrolling = True
			# CHANGE 3b: wide canvas sized by layout_pps so notes land correctly
			scroll_width = self.staffEvent[1] * self.layout_pps + self.canvas_width

			events_to_spawn = self.get_events_lookahead_and_place(
				total_time	   = self.staffEvent[1],
				countdown_time = self.staffEvent[1],	  
				look_ahead_sec = self.staffEvent[1],
				check_index    = False,
			)
			for event in events_to_spawn:
				event_type = event.get("type")
				if event_type == "bar":
					for shape_tuple in event['shapes']:
						shapes_list, _ = shape_tuple
						temp_shape_list.extend(shapes_list)
				elif event_type == "chord":
					temp_shape_list.extend(event['flat_shapes'])

		self.scrollingCanvas = pygame.Surface((int(scroll_width), self.canvas_height))
		self.scrollingCanvas.fill((255, 255, 255))

		visible = _VISIBLE_32 if self.numIndexes == 32 else _VISIBLE_16
		color	= (0, 0, 0, 255)
		line_w	= max(1, self.canvas_height // 200)
		x0		= int(self.canvas_width * 0.02)
		x1		= scroll_width - x0
		for i in visible:
			y = int(self._line_ys[i])
			pygame.draw.line(self.scrollingCanvas, color, (x0, y), (x1, y), line_w)

		if scrolling:
			self.draw_shapes(temp_shape_list, self.scrollingCanvas)


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

		pygame.draw.line(self._debug_overlay, (255, 255, 255, 255),
						(int(hit_x), 0), (int(hit_x), self.canvas_height), 2)

		band_surf = pygame.Surface((int(press_window_px * 2), self.canvas_height), pygame.SRCALPHA)
		band_surf.fill((0, 255, 0, 100))
		self._debug_overlay.blit(band_surf, (int(hit_x - press_window_px), 0))

		txt = self._debug_font.render(
			f"hit_x:{hit_x:.0f}  lead:{lead_sec:.3f}s  win:±{self.press_window_sec:.3f}s  ({press_window_px:.0f}px)",
			True, (255, 255, 0)
		)
		self._debug_overlay.blit(txt, (4, 4))


	def buildCanvasElements(self, refresh=None):
		self.staffElementGroup="staffElementGroup"
		self.register_group(self.staffElementGroup, self.buildCanvasElements)
		self.clear()
		self.overlayStaffSetup()
		self.precompute_sizes()
		if self.staffEvent:            # ← guard both together
			self.mediaBarSetup()
			self.dumb_staffEvent = self.create_dumb_events(self.staffEvent[0])
		self.scrollingStaffSetup()
		self._build_debug_overlay()



	def _build_widget_ui(self, rect: pygame.Rect):
		self.buildCanvasElements(refresh=True)
		



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
		note_height           = self.note_height
		note_width            = self.note_width
		default_note_position = self.default_note_position
		return_list           = []
		width                 = 8
		prev_positions        = None

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
		
		if (last_played_index - 1 == index and not jumped):
			final_position = position + (note_width * 0.8)
			jumped = True
		elif (last_played_index == index) and not jumped:
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
			else:
				ranged_list = range(3)

				index_to_change = index
				for i in ranged_list:
					index_to_change += 7
					if index_to_change in accidentals:
						t_accidental = self.accidental_type(new_scale_note, always_accidental=True)
						if index in accidentals:
							t_list = accidentals[index]
						else:
							t_list = []
						if is_xml_mode:
							t_list.append((t_accidental, accidental_ref_x))
						else:
							t_list.append(t_accidental)
						accidentals[index] = t_list
						del accidentals[index_to_change]

				index_to_change = index
				for i in ranged_list:
					index_to_change -= 7
					if index_to_change in accidentals:
						t_accidental = self.accidental_type(new_scale_note, always_accidental=True)
						if index in accidentals:        # ← add this guard
							t_list = accidentals[index]
						else:
							t_list = []
						if is_xml_mode:
							t_list.append((t_accidental, accidental_ref_x))
						else:
							t_list.append(t_accidental)
						accidentals[index] = t_list
						del accidentals[index_to_change]
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

			last_played_index=index
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
					"color"      : None
				})

			elif event_type == "chord":
				pl				  = []
				notes			  = i.get("notes", [])
				accidentals_list  = {}
				jumped			  = False
				last_played_index = float('inf')
				note_shapes_list  = []
				current_position  = self.default_note_position

				for note in notes:
					pl.append(note.get('pitch'))

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
					"color"      : None
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
		include_bars=True,
		events=None,
		check_index=True,
		color=None,
		true_time=None,
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

			if current_time > start + 1.6:
				commit_i = i + 1
				i += 1
				continue

			if start >= window_end:
				break

			event['x_position'] = round(
				self.canvas_width - ((start - current_time) * self.layout_pps)
			)

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
		if self.scrollingCanvas is not None:
			self.screen.blit(
				self.scrollingCanvas,
				(self._canvas_rect.x + self._scroll_x, self._canvas_rect.y)
			)
		self.screen.blit(self._canvas, self._canvas_rect.topleft)
		if self._border:
			pygame.draw.rect(self.screen, self._border_color, self._canvas_rect, self._border)


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


	def sidebar_options(self):
		return [("Load XML", self._open_file_dialog)]

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
		self.dumb_staffEvent = None          # ← prevent stale shapes showing if refresh is deferred
		self.refresh_group(self.staffElementGroup)   # buildCanvasElements now owns create_dumb_events
		self.staff_timer.start()         # ← AFTER rebuild is done
				

	def on_non_generic_pygame_event(self, event):
		pass


			
		
	
	def processUserEvents(self, midi, changedMidi, trueTime=None):
		if not changedMidi:
			if self.changedBuffer:
				return self.user_note_shapes
			else:
				self.changedBuffer = True
		else:
			self.changedBuffer = False
		#print(f"pitches list: {pl}")

		#used in make note for staff notation
		accidentals={}
		accidental_state={}


		last_played_index=float('inf')#default int so that it never triggers first note


		jumped=False#if the note was pushed to the side due to them being right next to each other
		#for staff im saving the pitch list because i need to for ingame size change
		old_pressed_midi=self.current_allowed_pressed_midi
		self.current_allowed_pressed_midi={}
		pl_count=0

		self.user_note_shapes=[]
		if midi:
			old_pressed_midi.keys()

			pitch_list = list(midi.keys())   # e.g. [60, 64, 67]
			for pitch, velocity in midi.items():


				if velocity == 0:
					continue
				#print(f"midi is {pitch, velocity}")

				pl_count += 1

				tscale_note = str(self.manager.midi_to_scale_note(pitch))

				note_name = tscale_note[0]
				note_octave = tscale_note[-1]

				new_scale_note = tscale_note[0]
				for ch in tscale_note[1:]:
					if ch in ('#', 'b'):
						new_scale_note += ch
					else:
						break  # hit the octave number (or '-'), s

				if str(note_name + note_octave) in self.note_dic:

					if self.staff_timer and trueTime:

						#keeping the timestamp
						if pitch in old_pressed_midi:

							timestamp,pressedTooLong = old_pressed_midi[pitch]
							if not pressedTooLong:
								self.current_allowed_pressed_midi[pitch] = (timestamp, True)

							else:
								self.current_allowed_pressed_midi[pitch] = old_pressed_midi[pitch]
						else:
							self.current_allowed_pressed_midi[pitch] = (trueTime,False)


		
					if new_scale_note == "B#":
						index = self.note_dic[str(note_name + str(int(note_octave)-1))]
					else:
						index = self.note_dic[str(note_name + note_octave)]

					note_result, accidentals, jumped, last_played_index, _ = self.make_note(
						pl_count,
						position=None,
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

					accidental_state[str(index)] = [s for note_block in note_result for s in note_block[:-1]]		#accidentals are added after because the
			#y change space retroactively on future accidentals
			#the accidentals gets added in thesame order as notes get added
			canvas_art=self.make_accidentals(accidentals)
			#print("adding_art")
			for i in canvas_art:

				if i[-1] in {'#','b','N','##','bb'}:
					i=i[:-1]
				#print(f"items in canvas art/accidental list = {i}")
				for e in i:
					#print(f'items are: {e}')
					if type(e)== list:
						for x in e:
							self.user_note_shapes.append(x)
					else:
						self.user_note_shapes.append(e)

		return self.user_note_shapes
	
	


	def update(self, deltaTime, midi_notes,changedMidi):
		if self._canvas is None:  # ← add this guard
			return
		if not (self.staff_timer and self.staff_timer.running()):
			temp_shape_list = []
			self.processUserEvents(midi_notes,changedMidi,trueTime=None)
			temp_shape_list.extend(self.user_note_shapes)

			self.clear()  
			self.draw_shapes(temp_shape_list, self._canvas)
			self._canvas.blit(self._debug_overlay, (0, 0))
			return



		now = monotonic()
		countdown_time = max(0.0, (self.staff_timer.end_time - now) * self.staff_timer.time_scale)
		trueTime = self.staffEvent[1] - countdown_time   # metronome-accurate, never smoothed

		# --- scroll smoothing (purely visual) ---
		target_x = -(trueTime * self.layout_pps)
		smoothing = 12
		self._scroll_x += (target_x - self._scroll_x) * min(1.0, smoothing * deltaTime)

		# visual_time: what the scrolling canvas is actually showing right now
		visual_time     = -self._scroll_x / self.layout_pps
		visual_countdown = self.staffEvent[1] - visual_time
		
		#sets self.user_note_shapes
		self.processUserEvents(midi_notes,changedMidi,trueTime=trueTime)
		

		debug=True
		if debug:

			if now >= self.staff_timer.end_time:
				self.staff_timer.end_time = None
				self.staff_timer.on_finish()
				return

			self.clear()

			events_to_spawn = self.get_events_lookahead_and_place(
				total_time     = self.staffEvent[1],
				countdown_time = visual_countdown,    # ← positions notes via visual_time
				look_ahead_sec = self.look_ahead_sec,
				color          = 'blue',
				true_time      = trueTime,           # ← MIDI window uses real clock
			)

			temp_shape_list = []
			for event in events_to_spawn:
				event_type = event.get("type")
				#if event_type == "bar":
				#	for shape_tuple in event['shapes']:
				#		shapes_list, _ = shape_tuple
				#		temp_shape_list.extend(shapes_list)
				if event_type == "chord":
					temp_shape_list.extend(event['flat_shapes'])

			
			temp_shape_list.extend(self.user_note_shapes)

			self.draw_shapes(temp_shape_list, self._canvas)
			self._canvas.blit(self._debug_overlay, (0, 0))


	def on_destroy(self):
		if self._canvas is not None:
			del self._canvas
			self._canvas = None
		self._file_dialog = None
