"""
staff_widget.py
───────────────
A ChildWidget that owns a pygame.Surface canvas for drawing music notation.

Design
──────
The canvas uses an IMMEDIATE-DRAW model:

	staff.clear()			   — fill canvas with background colour
	staff.draw_shape(shape)    — draw one PygameShape directly onto the canvas
	staff.draw_shapes(shapes)  — draw a list of PygameShapes in one call

Each call draws immediately onto the internal Surface.	There is no stored
shape list — the canvas pixel data IS the state.  When the WidgetScene calls
widget.draw() the canvas is blitted to the screen in one operation.

This keeps the hot loop as:
	clear → draw N shapes → (next frame) blit

Which scales to hundreds of redraws per second because:
  1. Shapes have their geometry pre-computed at construction time.
  2. clear() is a single Surface.fill() call.
  3. draw() is a single Surface.blit() call.
  4. No Python-side list iteration happens during blit.

Usage
─────
	from staff_widget import StaffWidget
	from pygame_note_shapes import pygame_shape_constructor

	class MyPage(WidgetScene):
		def setup_widgets(self):
			self.staff = StaffWidget(bg_color=(255, 255, 255))
			self.add_widget(self.staff, col=0, row=0)

		def update(self, dt):
			self.staff.clear()
			shapes = pygame_shape_constructor(
				shape_x=100, shape_y=50,
				shape_width=20, shape_height=13,
				type='quarter',
			)
			if shapes:
				for shape_list, _ in shapes:
					self.staff.draw_shapes(shape_list)
"""

from modules.pygame_note_shapes import pygame_shape_constructor
import pygame
import pygame_gui
from modules.childWidget import ChildWidget
from time import monotonic
import math

_VISIBLE_16 = {6, 8, 10, 12, 14}
_VISIBLE_32 = {6, 8, 10, 12, 14, 18, 20, 22, 24, 26}

_MEDIA_BAR_H_BASE = 44	 # design-space pixels, will be scaled

class StaffWidget(ChildWidget):
	"""
	A ChildWidget that provides a pygame Surface canvas for music notation.

	Parameters
	──────────
	bg_color   — RGBA tuple (0-255) used by clear().  Default opaque white.
	border	   — pixel width of the border drawn around the canvas.
				 0 disables the border.
	border_color — RGBA colour for the border.

	Canvas coordinate space
	───────────────────────
	(0, 0) is the top-left corner of the widget's allocated rect.
	canvas_width / canvas_height are available after build() is called.

	When the window is resized the widget is rebuilt: a new canvas Surface is
	created at the new size and clear() is called so the first frame is blank.
	"""


	class Timer:
		__slots__ = (
			"duration",
			"end_time",
			"time_scale",
			"_paused_remaining",
		)

		def __init__(self, duration_seconds, scale=2):
			self.duration = float(duration_seconds)
			self.time_scale = float(scale)
			self.end_time = None
			self._paused_remaining = None

		# -------------------------
		# Core Controls
		# -------------------------
		def play(self):
			"""Start fresh or resume from pause — whichever is appropriate."""
			if self._paused_remaining is not None:
				self.resume()
			else:
				self.start()

		def set_position(self, seconds):
			"""Seek to a position without starting playback."""
			if self.running():
				self.end_time = monotonic() + float(seconds) / self.time_scale
			else:
				self._paused_remaining = float(seconds)
		
		def start(self):
			"""Start from full duration."""
			self.end_time = monotonic() + self.duration / self.time_scale
			self._paused_remaining = None

		def restart(self,staff_widget):
			staff_widget.staffEventIterGate=0	
			self.start()

		def stop(self):
			"""Stop and reset."""
			self.end_time = None
			self._paused_remaining = None

		def pause(self):
			"""Pause without resetting."""
			if self.running():
				self._paused_remaining = self.remaining()
				self.end_time = None

		def resume(self):
			"""Resume from paused state."""
			if self._paused_remaining is not None:
				self.end_time = monotonic() + self._paused_remaining
				self._paused_remaining = None

		# -------------------------
		# Time Manipulation
		# -------------------------

		def skip(self, seconds):
			"""
			Skip forward (+) or backward (-).
			"""
			if not self.running():
				return

			self.end_time -= seconds / self.time_scale

		def set_scale(self, scale):
			"""
			Change playback speed.
			2.0 = twice as fast
			0.5 = half speed
			"""
			if scale <= 0:
				raise ValueError("Scale must be > 0")

			if self.running():
				remaining = self.remaining()
				self.time_scale = float(scale)
				self.end_time = monotonic() + remaining / self.time_scale
			else:
				self.time_scale = float(scale)

		# -------------------------
		# State
		# -------------------------

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
				return max(0.0, self.end_time - now)
			elif self._paused_remaining is not None:
				return self._paused_remaining
			return self.duration

		def running(self):
			return self.end_time is not None

		# -------------------------
		# Callback
		# -------------------------

		def on_finish(self):
			print("Timer finished")


	def __init__(
		self,
		bg_color:	  tuple = (0, 0, 0, 0),
		border:		  int	= 1,
		border_color: tuple = (180, 180, 200, 255),
		showBass=True,
		injected_note_staff_division= None
	):
		super().__init__()
		self._bg_color	   = bg_color
		self._border	   = border
		self._border_color = border_color

		#staff variable setup
		self.injected_note_staff_division=injected_note_staff_division		
		self.numIndexes = 32 if showBass else 18  # was 16 — needs room for C4 at idx 16
		self.showBass = showBass
		self._file_dialog = None 
		self.staffEvent=None
		self.dumb_staffEvent=None
		
		if showBass==True:
			self.note_range= [2,6]
		else:
			self.note_range= [4,6]


		self.note_dic={}
		self.set_note_dic()
		self.accidentals		= {}
		self.accidental_state	= {}
		self.pl					= []
		self.new_scale_note		= ''
		self.jumped				= False
		self.last_played_index	= float('inf')
		self.staffEventIterGate=0 #this will be the count iteration over the entire events
									#will gate from going farther than needed
		self.pixels_per_second   = 120          # scroll "feel" — lower = slower, smoother
		self.note_spacing_scale  = 6.0 
		self.press_window_sec	= 0.2
		self.current_pressed_midi = {}
		self.staff_timer=None


		# Set after build()

		self.scrollingCanvas:		pygame.Surface | None = None
		self._canvas:		pygame.Surface | None = None
		self._canvas_rect:	pygame.Rect    | None = None
		self.canvas_width:	int = 0
		self.canvas_height: int = 0
		
		#for specifically scroll canvas
		self._scroll_x_f=0





	def _compute_line_ys(self) -> list[float]:
		n	 = self.numIndexes			# 16 or 32
		pad  = self.canvas_height * 0.1
		step = (self.canvas_height - pad * 2) / (n - 1)
		return [pad + i * step for i in range(n)]

	
	def precompute_sizes(self):
		
		self._line_ys= self._compute_line_ys()

		self.note_height = (self._line_ys[1] - self._line_ys[0])
		self.note_width  = self.note_height * 1.3
		self.default_note_position= self.canvas_width // 7.5 if self.injected_note_staff_division is None else (self.canvas_width // self.injected_note_staff_division)

		self.default_note_position = self.canvas_width // (
			self.injected_note_staff_division or 7.5
		)

		self.look_ahead_sec = self.compute_lookahead_seconds(
			self.canvas_width, self.pixels_per_second * self.note_spacing_scale
		)




	def scrollingStaffSetup(self):

		
		scrolling=False
		temp_shape_list = []
		scroll_width=self.canvas_width
		if self.dumb_staffEvent:
			scrolling=True
			layout_pps  = self.pixels_per_second * self.note_spacing_scale
			scroll_width = self.staffEvent[1] * layout_pps + self.canvas_width



			events_to_spawn = self.get_events_lookahead_and_place(
				total_time     = self.staffEvent[1],
				countdown_time = self.staffEvent[1],      
				look_ahead_sec = self.staffEvent[1],
				check_index=False,
			)
			for event in events_to_spawn:
				event_type = event.get("type")
				if event_type == "bar":
					for shape_tuple in event['shapes']:
						shapes_list, _ = shape_tuple
						temp_shape_list.extend(shapes_list)
				elif event_type == "chord":
					temp_shape_list.extend(event['flat_shapes'])
		

		self.scrollingCanvas = pygame.Surface((scroll_width, self.canvas_height))
		




		self.scrollingCanvas.fill((255, 255, 255))
		visible  = _VISIBLE_32 if self.numIndexes == 32 else _VISIBLE_16
		color	 = (0, 0, 0, 255)
		line_w	 = max(1, self.canvas_height // 200)
		x0		 = int(self.canvas_width * 0.02)
		x1		 = self.canvas_width - x0
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


    # hide until XML is loaded
	def _build_widget_ui(self, rect: pygame.Rect):
		if self._canvas is not None:
			del self._canvas

		totalHeight=rect.height

		if self.dumb_staffEvent:

			media_bar_h = int(_MEDIA_BAR_H_BASE * (totalHeight / 600))
			self.media_bar_height = max(32, min(media_bar_h, 900))
		else:
			self.media_bar_height=0

		self._canvas_rect  = rect.copy()
		self.canvas_width  = rect.width
		self.canvas_height = rect.height-self.media_bar_height
		self._canvas = pygame.Surface((self.canvas_width, self.canvas_height),pygame.SRCALPHA)
		self.precompute_sizes()
		self.clear()

		#mediabar setup
		self.mediaBarSetup()	


		if self.dumb_staffEvent:
			self.dumb_staffEvent= self.create_dumb_events(self.staffEvent[0])

		self.scrollingStaffSetup()

	def clear(self):
		if self._canvas is not None:
			self._canvas.fill(self._bg_color)

	def line_y(self, index: int) -> float:
		return self._line_ys[index]



	#mediabar logic
	def _on_play_btn(self, event):
		if self.staff_timer is None:
			return
		if self.staff_timer.running():
			self.staff_timer.pause()
			self._play_btn.set_text("▶ Play")
		else:
			self.staff_timer.play()
			self._play_btn.set_text("⏸ Pause")
	


	# ── Note-To-Staff Construction and Positioning Logic────────────────────────────────────────────────────────────


	def set_note_dic(self):
		
		note_names = ['C', 'D','E', 'F','G', 'A', 'B']


		#so if the range was 2,6 C6 would have a line index of -4
		#so if both trebel and bass are showing it would be 29 keys
		#or 15() keys if only trebel
		#so it would 
		if self.showBass==True:
			start_line_index=30

		else:
			start_line_index=16

		for i in range(int(self.note_range[0]), int(self.note_range[1])):
			for x in note_names:
				self.note_dic[x + str(i)] = start_line_index
				start_line_index -= 1

		self.note_dic["C" + str(self.note_range[1])] = start_line_index

		for i,x in self.note_dic.items():
			print(f"key:{i},   item{x}:")




	def assign_positions(self,row, index,prev_positions=None, width=5):
		"""
		Compute column positions for a single `row`, avoiding vertical stacking.

		Automatically determines whether to stagger the first row based on the global `rows` list:
		- If `prev_positions` is empty (first row) and `rows` has more than one row, use a step of 2 (staggered).
		- Otherwise, use a step of 1 (contiguous).
		- Single-item first rows always place at [0].

		Parameters:
		- row: list of items for the current row
		- prev_positions: set of column indices used by the previous row (None for first row)
		- width: total number of columns (indices 0..width-1)

		Returns:
		- curr_positions: list of column indices assigned to this row
		"""
		curr_positions = []
		prev_positions = prev_positions or set()
		#print(f"prevous positions: {prev_positions}")
		if not prev_positions:
			# determine step based on global rows context
			if len(row) == 1:
				step = 1
			else:
				# stagger if multiple rows exist
				if (index-1 in self.accidentals): 
					step = 2 
					print("stepping 2 AAAAA")
				else:
					print("steppa only 1 AAAAAA")
					step=1

			col = 0
			for _ in row:
				if col >= width:
					raise ValueError("Not enough columns for first row spacing")
				curr_positions.append(col)
				col += step
		else:
			# avoid vertical stacking for subsequent rows
			free_cols = [c for c in range(width) if c not in prev_positions]
			if len(free_cols) < len(row):
				raise ValueError("Not enough columns to avoid stacking")
			curr_positions = free_cols[:len(row)]

		return curr_positions



	def make_accidentals(self, accidentals_list, width=5):
		note_height = self.note_height	
		note_width = self.note_width
		default_note_position = self.default_note_position
		return_list = []
		width = 8
		prev_positions = None

		for i in accidentals_list:
			row = accidentals_list[i]
			#print(f"DEBUG: Processing index {i}, row: {row}")
			if (i+1 not in accidentals_list):
				prev_positions = None

			curr = self.assign_positions(row, i, prev_positions, width)
			#print(f"DEBUG: Positions assigned: {curr}")
			prev_positions = set(curr)

			count = 0
			y = self.line_y(i)
			
			for x in row:
				# ← UNPACK TUPLE OR USE STRING
				if isinstance(x, tuple):
					accidental_char, note_x = x
					#print(f"DEBUG: Unpacked tuple - accidental={accidental_char}, note_x={note_x}")
				else:
					accidental_char = x
					note_x = default_note_position
					#print(f"DEBUG: Using string - accidental={accidental_char}, note_x={note_x}")
				
				position_mult = curr[count] + 1
				count += 1
				
				accidental_x = (note_x + note_width/2) - ((note_width*0.9)*int(position_mult))
				#print(f"DEBUG: accidental_x for {accidental_char} = {accidental_x}, note_x={note_x}, default_note_position={default_note_position}")

				# Use shape_constructor for accidentals
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

		#print(f"DEBUG: make_accidentals returning {len(return_list)} accidentals")
		return return_list



	def accidental_type(self,note,always_accidental=False):

		#note should be anything like c# or gb

		"""
		Returns:
		 - None			   if `note` is in the major scale of `key`
		 - "sharp"		   if it's an out-of-scale sharp (e.g. F# in C major)
		 - "flat"		   if it's an out-of-scale flat  (e.g. Bb in C major)
		 - "natural"	   if it's a natural accidental,
						  i.e. neither # nor b (e.g. E in F# major)
		"""

		if always_accidental:


			#find the accidentals, if there is none it is a natural
			length=len(note)

			if length>2:
				return (note[1]+note[2])


			elif length>1:
				
				return note[1]
				
				#if "#" == note[1]:
				#	return note[1]
				#elif "b" in note[1]:
				#	return "flat"
			else:
				return "N"





		else:
				#if it is not a normal key shitty check tho gonna be honest
			if note not in self.manager.non_chromatic_music_scale:


				# sanity check: must still be in chromatic
				#if note not in all_scales.chromatic_major_scales[self.manager.scale_name]:
				#	raise ValueError(f"{note!r} isn’t even in the chromatic of {key!r}")


				##gets the position of key in all notes in chromatic scale,

				#index= all_scales.chromatic_major_scales[self.manager.scale_name].index(note)
				

				length=len(note)

				if length>2:
					return note[1]+note[2]


				elif length>1:
					
					return note[1]
					
					#if "#" == note[1]:
					#	return note[1]
					#elif "b" in note[1]:
					#	return "flat"
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
		note_type='quarter',   # ← was duration=None
		dotted=False,
	):
		


		return_list=[]
		
		note_height=self.note_height	
		note_width=self.note_width
		
		# ← Don't overwrite position!
		if position is None:
			position = self.default_note_position
		

		is_xml_mode = (accidentals_list is not None)

		if accidentals_list==None:
			accidentals=self.accidentals
		else:
			accidentals= accidentals_list
		
		if new_scale_note==None:
			new_scale_note=self.new_scale_note

		if pitch_list==None:
			pitch_list=self.pl
		
		default_jump=False
		if jumped==None:
			default_jump=True	
			jumped=self.jumped

		default_last_played=False
		if last_played_index==None:
			default_last_played=True
			last_played_index=self.last_played_index

		#print(f"Index is: {index}")
		
		y = self.line_y(index)			# ← replaces top_margin arithmetic
		
		# ← Calculate FINAL position
		final_position = position
		
		#logic for notes to appear ONTOP AND to the side if the notes are one note apart
		if (last_played_index-1 == index and not jumped):
			final_position = position + (note_width*0.8)
			jumped = True
		#logic for notes to appear to the side of the same note if the notes are the same but different suffix ie: C and C#
		elif (last_played_index == index) and not jumped:
			final_position = position + note_width
			jumped = True
		else:
			jumped = False

		x = final_position
		
		#print(f"DEBUG make_note: final_position={final_position}, position={position}, self.default_note_position={self.default_note_position}")
		


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
		
		##basically managing all the accidentals 
		accidental=self.accidental_type(new_scale_note,always_accidental=False)

		if accidental==None:
			#case: when   #@[@]<-new note
			if index in accidentals:
				t_accidental =self.accidental_type(new_scale_note,always_accidental=True)
				t_list=accidentals[index]
				
				if is_xml_mode:
					t_list.append((t_accidental, final_position))  # ← Use final_position
				else:
					t_list.append(t_accidental)
				
				accidentals[index]=t_list

			else:
				ranged_list =range(3)

				index_to_change=index
				for i in ranged_list:
					index_to_change+=7
					if index_to_change in accidentals:
						t_accidental =self.accidental_type(new_scale_note,always_accidental=True)
						
						if index in accidentals:
							t_list=accidentals[index]
						else:
							t_list=[]
						
						if is_xml_mode:
							t_list.append((t_accidental, final_position))
						else:
							t_list.append(t_accidental)
						
						accidentals[index]=t_list
						del accidentals[index_to_change]

				index_to_change=index
				for i in ranged_list:
					index_to_change-=7
					if index_to_change in accidentals:
						t_accidental =self.accidental_type(new_scale_note,always_accidental=True)
						t_list=accidentals[index]
						
						if is_xml_mode:
							t_list.append((t_accidental, final_position))
						else:
							t_list.append(t_accidental)
						
						accidentals[index]=t_list
						del accidentals[index_to_change]

		else:
			#if accidental == "#":
				#print("found accidental sharp")
			#elif accidental == "b":
				#print("found accidental flat")
			#elif accidental == "N":
				#print("found accidental Natural")

			if index in accidentals:
				t_list=accidentals[index]
				
				if is_xml_mode:
					t_list.append((accidental, final_position))
				else:
					t_list.append(accidental)
				
				accidentals[index]=t_list
			else:
				if last_played_index == index:
					if pl_index >= 2:
						old_note=self.midi_to_scale_note(pitch_list[pl_index-2])
						print(f"old note {old_note}")
						
						old_accidental=self.accidental_type(old_note[:-1],always_accidental=True)
						
						if is_xml_mode:
							accidentals[index]=[(old_accidental, final_position), (accidental, final_position)]
						else:
							accidentals[index]=[old_accidental, accidental]
					else:
						if is_xml_mode:
							accidentals[index]=[(accidental, final_position)]
						else:
							accidentals[index]=[accidental]
				else:
					if is_xml_mode:
						accidentals[index]=[(accidental, final_position)]
					else:
						accidentals[index]=[accidental]

		if accidentals_list==None:
			self.accidentals=accidentals
		else:
			accidentals_list=accidentals

		if default_jump == True:
			self.jumped=jumped

		if default_last_played == True:
			self.last_played_index=last_played_index

		try:
			self.last_played_index=index
			#print("setting index for next time!!")
		except UnboundLocalError:
			print("error 1647 ds")
			pass

		return_list.append([*shapes,note_type])	
		
		if accidentals_list != None:
			# ← RETURN final_position too!
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
					shape_x = self.default_note_position + self.note_width / 2,
					shape_y		 = bar_top,
					shape_height = bar_bottom - bar_top,
					shape_width  = max(1, self.canvas_height // 200),  # line width
					type		 = "bar",
				)
				dumb_events.append({
					"type"	   : event_type,
					"shapes"   : bar_shapes,
					"start_sec": bar_start_sec,
				})

			elif event_type == "chord":
				pl			   = []
				notes		   = i.get("notes", [])
				accidentals_list = {}
				jumped			= False
				last_played_index = float('inf')
				note_shapes_list  = []
				current_position  = self.default_note_position

				for note in notes:
					pl.append(note.get('pitch'))

				for pl_index, note in enumerate(notes, start=1):
					global_note_counter += 1
					pitch		 = note.get('pitch')
					tscale_note  = str(self.manager.midi_to_scale_note(pitch))
					note_name	 = tscale_note[0]
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
								position		= current_position,
								index			= idx,
								accidentals_list= accidentals_list,
								new_scale_note	= new_scale_note,
								pitch_list		= pl,
								jumped			= jumped,
								last_played_index = last_played_index,
								note_type		= note.get('note_type', 'quarter'),
								dotted			= note.get('dots', 0) > 0,
							)
						note_shapes_list.append(note_shapes)

				make_accidentals_result = self.make_accidentals(
					accidentals_list,
				)

				flat  = [s for nw in note_shapes_list for ni in nw for s in ni[:-1]]
				flat += [s for acc in make_accidentals_result	for s in acc[0]]

				dumb_events.append({
					"type"		 : event_type,
					"shapes"	 : [note_shapes_list, make_accidentals_result],
					"flat_shapes": flat,
					"start_sec"  : i.get('start_sec'),
					"pitch_list" : pl,
				})
				last_playable_shape = i

		return dumb_events
	def _find_next_note_time(self, events, current_div):
		"""Helper function to find the time of the next note after current_div"""
		for event in events:
			if event.get("type") == "chord" and event.get("start_div") > current_div:
				return event.get("start_sec")
		return None

	# REALTIME CANVAS SHAPE MOVEMENT
	def _shift_drawable_x(self, shape, dx):
		"""Shift a PygameShape horizontally by dx."""
		from modules.pygame_note_shapes import PygameShape
		if isinstance(shape, PygameShape):
			shape.shift_x(dx)


	def edit_shape(self, shape_to_resize, color=None):
		event_type = shape_to_resize.get("type")
		x_target   = shape_to_resize.get("x_position")

		if x_target is None:
			return

		previous_x = shape_to_resize.get("current_x", self.canvas_width)
		dx		   = -(x_target - previous_x)
		shape_to_resize["current_x"] = x_target

		# ── bar ──────────────────────────────────────────────────────────
		if event_type == "bar":
			for shape_group in shape_to_resize.get("shapes", []):
				if isinstance(shape_group, tuple):
					shape_list, _ = shape_group
					for shape in shape_list:
						self._shift_drawable_x(shape, dx)
			return

		if event_type != "chord":
			return

		# ── chord ─────────────────────────────────────────────────────────
		note_shapes, accidental_shapes = shape_to_resize["shapes"]

		_GREEN = (0, 200, 0, 255)

		def _shift_and_color(shape,color=None):
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
							_shift_and_color(shape,color=color)
			for acc_block in accidental_shapes:
				for shape in acc_block[0]:
					_shift_and_color(shape,color=color)


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
		window_end	 = current_time + look_ahead_sec

		if events is None:
			events = self.dumb_staffEvent  # ← renamed from current_event

		if events is None:
			return []

		result	 = []
		n		 = len(events)
		i		 = self.staffEventIterGate if check_index else 0  # ← renamed from event_index
		commit_i = i

		while i < n:
			event = events[i]
			start = event.get("start_sec")
			if start is None:
				i += 1
				continue

			start = float(start)

			# kill off events that are well behind the playhead
			if current_time > start + 1.6:
				commit_i = i + 1
				i += 1
				continue

			if start >= window_end:
				break

			# get_events_lookahead_and_place
			layout_pps = self.pixels_per_second * self.note_spacing_scale
			event['x_position'] = (
				self.canvas_width - ((start - current_time) * layout_pps)
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
							self.edit_shape(event,color=color)

					elif pitch_list[0] in temp_midi:
						self.edit_shape(event, color=_GREEN)
						del temp_midi[pitch_list[0]]
						self.current_pressed_midi = temp_midi
					else:
						self.edit_shape(event)
				else:
					self.edit_shape(event,color=color)
			else:
				self.edit_shape(event,color=color)

			result.append(event)
			i += 1

		if check_index:
			self.staffEventIterGate = commit_i	# ← renamed from event_index

		return result

	# ── Canvas API ────────────────────────────────────────────────────────────

	def clear(self):
		"""
		Fill the canvas with the background colour.

		Call this at the start of each update cycle before drawing new shapes.
		This is a single Surface.fill() — O(1) GPU blit.
		"""
		if self._canvas is not None:
			self._canvas.fill(self._bg_color)

		

	def draw_shape(self, shape,canvas):
		"""
		Draw a single PygameShape onto the canvas immediately.

		shape.draw() is called with the canvas Surface, not the screen.
		Coordinates in the shape should be relative to the canvas origin
		(i.e. the widget's top-left corner).
		"""
		if canvas is not None:
			shape.draw(canvas)

	def draw_shapes(self, shapes,canvas):
		"""
		Draw a list of PygameShapes onto the canvas in one call.

		shapes may be any iterable of PygameShape instances.
		"""
		if canvas is not None:
			for shape in shapes:
				shape.draw(canvas)

	# ── ChildWidget draw (called by WidgetScene every frame) ──────────────────

	def draw(self):
		if self._canvas is None or self._canvas_rect is None:
			return

		# 1. scroll the background canvas into screen
		if self.scrollingCanvas is not None:
			src_x = max(0, min(
				int(-self._scroll_x_f),   # truncate, not floor — same thing for positive values
				self.scrollingCanvas.get_width() - self.canvas_width
			))
			self.screen.blit(
				self.scrollingCanvas,
				self._canvas_rect.topleft,
				pygame.Rect(src_x, 0, self.canvas_width, self.canvas_height)
			)

		# 2. overlay _canvas on top (transparent except for highlights etc.)
		self.screen.blit(self._canvas, self._canvas_rect.topleft)

		if self._border:
			pygame.draw.rect(self.screen, self._border_color, self._canvas_rect, self._border)
	# ── coordinate helpers ────────────────────────────────────────────────────

	def canvas_rect(self) -> pygame.Rect | None:
		"""Return the screen-space Rect that this canvas occupies."""
		return self._canvas_rect.copy() if self._canvas_rect else None

	def to_canvas(self, screen_x: float, screen_y: float) -> tuple[float, float]:
		"""Convert a screen-space coordinate to canvas-local coordinates."""
		if self._canvas_rect is None:
			return screen_x, screen_y
		return (screen_x - self._canvas_rect.x,
				screen_y - self._canvas_rect.y)

	def to_screen(self, canvas_x: float, canvas_y: float) -> tuple[float, float]:
		"""Convert a canvas-local coordinate to screen-space."""
		if self._canvas_rect is None:
			return canvas_x, canvas_y
		return (canvas_x + self._canvas_rect.x,
				canvas_y + self._canvas_rect.y)
	

	


	def sidebar_options(self):
		return [("Load XML", self._open_file_dialog)]

	def _open_file_dialog(self):
		# only open one at a time
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

	async def _load_xml(self,path):
		from modules.mxmlParser import parse_musicxml_chords
		print(path)

		self.staffEvent = parse_musicxml_chords(path)
		print("done parsing recieved on main runner")
		self.staff_timer=self.Timer(self.staffEvent[1])
		self.dumb_staffEvent= self.create_dumb_events(self.staffEvent[0])
		self.staff_timer.start()
	
		self._build_widget_ui(self._rect)
	
	def on_non_generic_pygame_event(self,event):
		#print(f"recieved: {event}")
		pass



	def update(self, deltaTime):
		if not (self.staff_timer and self.staff_timer.running()):
			return

		now = monotonic()
		wall_countdown = max(0.0, self.staff_timer.end_time - now)
		current_time   = self.staffEvent[1] - (wall_countdown * self.staff_timer.time_scale)

		# Direct — no lerp, no floor
		self._scroll_x_f = -(current_time * self.pixels_per_second)

		if now >= self.staff_timer.end_time:
			self.staff_timer.end_time = None
			self.staff_timer.on_finish()
			return

		# clear _canvas for overlays only (highlights, cursor line, etc.)
		self.clear()

		debug=False
		if debug:
				
			# ── ONE time snapshot for the entire frame ────────────────────────
			# Calling monotonic() twice (once in tick(), once in remaining())
			# lets OS scheduling jitter sneak in between calls and cause jumps.


			
			events_to_spawn = self.get_events_lookahead_and_place(
				total_time     = self.staffEvent[1],
				countdown_time = wall_countdown	 ,      # ← frozen snapshot, not a fresh call
				look_ahead_sec = self.look_ahead_sec,
				color='blue'
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

			#self.staffSetup()
			self.draw_shapes(temp_shape_list,self._canvas)

		def on_destroy(self):
			if self._canvas is not None:
				del self._canvas
				self._canvas = None
			self._file_dialog = none
