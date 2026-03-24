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
				self.end_time = monotonic() + self._paused_remaining / self.time_scale  # was: no division
				self._paused_remaining = None

		def skip(self, seconds):
			if not self.running():
				return
			self.end_time -= seconds / self.time_scale  # was: no division

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
		self._canvas:         pygame.Surface | None = None
		self._canvas_rect:    pygame.Rect    | None = None
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
		
		if showBass:
			self.note_range = [2, 6]
		else:
			self.note_range = [4, 6]

		self.note_dic = {}
		self.set_note_dic()
		self.accidentals      = {}
		self.accidental_state = {}
		self.pl               = []
		self.new_scale_note   = ''
		self.jumped           = False
		self.last_played_index = float('inf')
		self.staffEventIterGate = 0
		self.pixels_per_second  = 75
		# CHANGE 1: note_spacing_scale decouples visual spacing from scroll speed.
		# Increase to spread notes further apart without changing how fast they scroll.
		# layout_pps = pixels_per_second * note_spacing_scale is used everywhere
		# notes are placed or measured, so the two stay in sync automatically.
		self.note_spacing_scale = 12.0
		self.press_window_sec   = 0.2
		self.current_pressed_midi = {}
		self.staff_timer = None


		self.canvas_width:  int = 0
		self.canvas_height: int = 0
		self._scroll_x = 0


	# CHANGE 2: single property so every consumer is guaranteed to agree.
	@property
	def layout_pps(self) -> float:
		"""Pixels per music-second for note layout AND scroll offset."""
		return self.pixels_per_second * self.note_spacing_scale


	def _compute_line_ys(self) -> list[float]:
		n    = self.numIndexes
		pad  = self.canvas_height * 0.1
		step = (self.canvas_height - pad * 2) / (n - 1)
		return [pad + i * step for i in range(n)]

	
	def precompute_sizes(self):
		self._line_ys = self._compute_line_ys()
		self.note_height = self._line_ys[1] - self._line_ys[0]
		self.note_width  = self.note_height * 1.3
		self.default_note_position = self.canvas_width // (
			self.injected_note_staff_division or 7.5
		)
		self.look_ahead_sec = self.compute_lookahead_seconds(
			self.canvas_width, self.layout_pps  # CHANGE 3a: use layout_pps
		)


	def scrollingStaffSetup(self):
		scrolling = False
		temp_shape_list = []
		scroll_width = self.canvas_width
		if self.dumb_staffEvent:
			scrolling = True
			# CHANGE 3b: wide canvas sized by layout_pps so notes land correctly
			scroll_width = self.staffEvent[1] * self.layout_pps + self.canvas_width

			events_to_spawn = self.get_events_lookahead_and_place(
				total_time     = self.staffEvent[1],
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
		color   = (0, 0, 0, 255)
		line_w  = max(1, self.canvas_height // 200)
		x0      = int(self.canvas_width * 0.02)
		x1      = self.canvas_width - x0
		for i in visible:
			y = int(self._line_ys[i])
			pygame.draw.line(self.scrollingCanvas, color, (x0, y), (x1, y), line_w)

		if scrolling:
			self.draw_shapes(temp_shape_list, self.scrollingCanvas)


	def mediaBarSetup(self):
		if self.dumb_staffEvent:
			media_rect = pygame.Rect(
				self._rect.x,
				self._rect.bottom - self.media_bar_height,
				self._rect.width,
				self.media_bar_height,
			)
			self._media_panel = self._add(pygame_gui.elements.UIPanel(
				relative_rect=media_rect,
				manager=self.ui,
			))
			btn_h = self.media_bar_height - 8
			self._play_btn = self._add(pygame_gui.elements.UIButton(
				relative_rect=pygame.Rect(4, 4, 80, btn_h),
				text="▶ Play",
				manager=self.ui,
				container=self._media_panel,
			))
			self.on_event(pygame_gui.UI_BUTTON_PRESSED, self._on_play_btn, element=self._play_btn)


	def _build_widget_ui(self, rect: pygame.Rect):
		if self._canvas is not None:
			del self._canvas

		totalHeight = rect.height

		if self.dumb_staffEvent:
			media_bar_h = int(_MEDIA_BAR_H_BASE * (totalHeight / 600))
			self.media_bar_height = max(32, min(media_bar_h, 900))
		else:
			self.media_bar_height = 0

		self._canvas_rect  = rect.copy()
		self.canvas_width  = rect.width
		self.canvas_height = rect.height - self.media_bar_height
		self._canvas = pygame.Surface((self.canvas_width, self.canvas_height),pygame.SRCALPHA)
		self.precompute_sizes()
		self.clear()

		self.mediaBarSetup()

		if self.dumb_staffEvent:
			self.dumb_staffEvent = self.create_dumb_events(self.staffEvent[0])

		self.scrollingStaffSetup()


	def clear(self):
		if self._canvas is not None:
			self._canvas.fill(self._bg_color)


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


	def assign_positions(self, row, index, prev_positions=None, width=5):
		curr_positions = []
		prev_positions = prev_positions or set()
		if not prev_positions:
			if len(row) == 1:
				step = 1
			else:
				if (index - 1 in self.accidentals): 
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

		for i in accidentals_list:
			row = accidentals_list[i]
			if (i + 1 not in accidentals_list):
				prev_positions = None

			curr = self.assign_positions(row, i, prev_positions, width)
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
		note_type='quarter',
		dotted=False,
	):
		return_list = []
		note_height = self.note_height
		note_width  = self.note_width
		
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
					t_list.append((t_accidental, final_position))
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
							t_list.append((t_accidental, final_position))
						else:
							t_list.append(t_accidental)
						accidentals[index] = t_list
						del accidentals[index_to_change]

				index_to_change = index
				for i in ranged_list:
					index_to_change -= 7
					if index_to_change in accidentals:
						t_accidental = self.accidental_type(new_scale_note, always_accidental=True)
						t_list = accidentals[index]
						if is_xml_mode:
							t_list.append((t_accidental, final_position))
						else:
							t_list.append(t_accidental)
						accidentals[index] = t_list
						del accidentals[index_to_change]
		else:
			if index in accidentals:
				t_list = accidentals[index]
				if is_xml_mode:
					t_list.append((accidental, final_position))
				else:
					t_list.append(accidental)
				accidentals[index] = t_list
			else:
				if last_played_index == index:
					if pl_index >= 2:
						old_note = self.midi_to_scale_note(pitch_list[pl_index - 2])
						print(f"old note {old_note}")
						old_accidental = self.accidental_type(old_note[:-1], always_accidental=True)
						if is_xml_mode:
							accidentals[index] = [(old_accidental, final_position), (accidental, final_position)]
						else:
							accidentals[index] = [old_accidental, accidental]
					else:
						if is_xml_mode:
							accidentals[index] = [(accidental, final_position)]
						else:
							accidentals[index] = [accidental]
				else:
					if is_xml_mode:
						accidentals[index] = [(accidental, final_position)]
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
		dumb_events         = []
		global_note_counter = 0
		last_playable_shape = None

		for index, i in enumerate(events):
			event_type = i.get("type")

			if event_type == "bar":
				bar_start_sec = i.get('start_sec')
				if last_playable_shape is not None:
					prev_start    = last_playable_shape.get('start_sec', bar_start_sec)
					bar_start_sec = (prev_start + bar_start_sec) / 2

				bar_top    = self._line_ys[0]
				bar_bottom = self._line_ys[-1]
				bar_shapes = pygame_shape_constructor(
					shape_x      = self.default_note_position + self.note_width / 2,
					shape_y      = bar_top,
					shape_height = bar_bottom - bar_top,
					shape_width  = max(1, self.canvas_height // 200),
					type         = "bar",
				)
				dumb_events.append({
					"type"     : event_type,
					"shapes"   : bar_shapes,
					"start_sec": bar_start_sec,
				})

			elif event_type == "chord":
				pl                = []
				notes             = i.get("notes", [])
				accidentals_list  = {}
				jumped            = False
				last_played_index = float('inf')
				note_shapes_list  = []
				current_position  = self.default_note_position

				for note in notes:
					pl.append(note.get('pitch'))

				for pl_index, note in enumerate(notes, start=1):
					global_note_counter += 1
					pitch        = note.get('pitch')
					tscale_note  = str(self.manager.midi_to_scale_note(pitch))
					note_name    = tscale_note[0]
					note_octave  = tscale_note[-1]
					new_scale_note = tscale_note[0]
					tlen = len(tscale_note)
					if tlen > 3:
						new_scale_note = new_scale_note + tscale_note[1] + tscale_note[2]
					elif tlen > 2:
						new_scale_note = new_scale_note + tscale_note[1]

					if new_scale_note == "B#":
						lookup_key = str(note_name + str(int(note_octave) - 1))
					else:
						lookup_key = str(note_name + note_octave)

					if lookup_key in self.note_dic:
						idx = self.note_dic[lookup_key]
						note_shapes, accidentals_list, jumped, last_played_index, current_position = \
							self.make_note(
								pl_index,
								position          = current_position,
								index             = idx,
								accidentals_list  = accidentals_list,
								new_scale_note    = new_scale_note,
								pitch_list        = pl,
								jumped            = jumped,
								last_played_index = last_played_index,
								note_type         = note.get('note_type', 'quarter'),
								dotted            = note.get('dots', 0) > 0,
							)
						note_shapes_list.append(note_shapes)

				make_accidentals_result = self.make_accidentals(accidentals_list)

				flat  = [s for nw in note_shapes_list for ni in nw for s in ni[:-1]]
				flat += [s for acc in make_accidentals_result for s in acc[0]]

				dumb_events.append({
					"type"       : event_type,
					"shapes"     : [note_shapes_list, make_accidentals_result],
					"flat_shapes": flat,
					"start_sec"  : i.get('start_sec'),
					"pitch_list" : pl,
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
		dx         = -(x_target - previous_x)
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
		color=None
	):
		"""Amortized O(1) lookahead."""
		_GREEN = (0, 200, 0, 255)

		current_time = total_time - countdown_time
		window_end   = current_time + look_ahead_sec

		if events is None:
			events = self.dumb_staffEvent

		if events is None:
			return []

		result   = []
		n        = len(events)
		i        = self.staffEventIterGate if check_index else 0
		commit_i = i

		while i < n:
			event = events[i]
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

			# CHANGE 3c: use layout_pps so x_position matches scroll offset
			event['x_position'] = round(
				self.canvas_width - ((start - current_time) * self.layout_pps)
			)

			press_window = self.press_window_sec
			in_press_window = (current_time >= start - press_window and
								current_time <= start + press_window)

			if in_press_window:
				temp_midi = self.current_pressed_midi
				if "pitch_list" in event:
					pitch_list = event["pitch_list"]
					if len(pitch_list) > 1 and len(pitch_list) == len(temp_midi):
						if set(pitch_list).issubset(temp_midi):
							self.edit_shape(event, color=_GREEN)
							for pitch in pitch_list:
								del temp_midi[pitch]
							self.current_pressed_midi = temp_midi
						else:
							self.edit_shape(event, color=color)
					elif pitch_list[0] in temp_midi:
						self.edit_shape(event, color=_GREEN)
						del temp_midi[pitch_list[0]]
						self.current_pressed_midi = temp_midi
					else:
						self.edit_shape(event)
				else:
					self.edit_shape(event, color=color)
			else:
				self.edit_shape(event, color=color)

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
		self.on_event(pygame_gui.UI_WINDOW_CLOSE,            self._on_dialog_close, element=self._file_dialog)

	def _on_path_picked(self, event):
		self.run_task(self._load_xml(event.text))
		self._file_dialog = None

	def _on_dialog_close(self, event):
		self._file_dialog = None

	async def _load_xml(self, path):
		from modules.mxmlParser import parse_musicxml_chords
		print(path)
		self.staffEvent = parse_musicxml_chords(path)
		print("done parsing recieved on main runner")
		self.staff_timer     = self.Timer(self.staffEvent[1])
		self.dumb_staffEvent = self.create_dumb_events(self.staffEvent[0])
		self.staff_timer.start()
		self._build_widget_ui(self._rect)

	def on_non_generic_pygame_event(self, event):
		pass


	def update(self, deltaTime):
		if not (self.staff_timer and self.staff_timer.running()):
			return

		now = monotonic()
		countdown_time = max(0.0, (self.staff_timer.end_time - now) * self.staff_timer.time_scale)
		current_time = self.staffEvent[1] - countdown_time

		target_x = -(current_time * self.layout_pps)

		smoothing = 1   # higher = snappier
		self._scroll_x += (target_x - self._scroll_x) * min(1, smoothing * deltaTime)		
		debug = False
		if debug:
			if now >= self.staff_timer.end_time:
				self.staff_timer.end_time = None
				self.staff_timer.on_finish()
				return

			self.clear()
			if self.scrollingCanvas is not None:
				self._canvas.blit(self.scrollingCanvas, (self._scroll_x, 0))

			events_to_spawn = self.get_events_lookahead_and_place(
				total_time     = self.staffEvent[1],
				countdown_time = countdown_time,
				look_ahead_sec = self.look_ahead_sec,
				color          = 'blue'
			)

			temp_shape_list = []
			for event in events_to_spawn:
				event_type = event.get("type")
				if event_type == "bar":
					for shape_tuple in event['shapes']:
						shapes_list, _ = shape_tuple
						temp_shape_list.extend(shapes_list)
				elif event_type == "chord":
					temp_shape_list.extend(event['flat_shapes'])

			self.draw_shapes(temp_shape_list, self._canvas)


	def on_destroy(self):
		if self._canvas is not None:
			del self._canvas
			self._canvas = None
		self._file_dialog = None
