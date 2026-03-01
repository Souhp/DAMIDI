
import flet as ft
from Event_Dispatch_Bus import trigger_event, register_event
import PageMemory
from midiFuncs import midi_listener,midi_to_note,strip_octave,get_note_verisons
import asyncio
from mingus.core import notes, chords
from pychord import find_chords_from_notes, Chord, notes_to_positions
import flet.canvas as cv
#from typing import List
from pychord.constants import all_scales
from collections import namedtuple
default_scale={"C":  ["C", "D", "E", "F", "G", "A", "B"]}
import math
import copy
from parser import parse_musicxml_chords
import time
from staff_shapes import shape_constructor


def uni_toggle(x):
	x=not x
	return x


class SizeAwareControl(cv.Canvas):
	def __init__(self, content=None, resize_interval=100, on_resize=None, **kwargs):
		super().__init__(**kwargs)
		self.content = content
		self.resize_interval = resize_interval
		self.resize_callback = on_resize

		self.size = namedtuple("size", field_names=["width", "height"], defaults=[0, 0])
		# self.on_resize = self.__handle_canvas_resize



class SearchField:
	def __init__(self,align: ft.MainAxisAlignment):

		SearchField.TextInput = ft.TextField(hint_text="type here")
		SearchField.SearchButton = ft.FloatingActionButton(text="Search")
		SearchField.Row = ft.Row(

			controls=[SearchField.TextInput,SearchField.SearchButton],
			alignment=align,
			)


class Default_Widget():


	async def tick(self):
		pass


	def __init__(self):

		self.sidebar_content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
		self.scale=default_scale["C"]
		#scale name always for major
		self.scale_name = "C"
		self.page_size = {"x":1600,"y":400}

	async def resize(self):
		print("timetoresize")


	def midi_to_scale_note(self,pitch):

		print()

		note_names = all_scales.chromatic_major_scales[self.scale_name]
		if 0 <= pitch <= 127:
			note = note_names[pitch % 12]
			octave = (pitch // 12) - 1
			return f"{note}{octave}"
		else:
			raise ValueError("MIDI pitch must be between 0 and 127")






class Default_Page():

	####ALLL VISUALS DONE HERE

	#this function is basically how the inividual app executes code on note press, not a tick, only upates on press
	async def note_update(e,self):


		print("OK READY TO FUCK HARD")
		print(str(e))




	async def child_tick(self):
		##This is where the child app does its visual updates
		pass


	async def click_sidebar_button(self,*x):


		self.sidebar.visible = not self.sidebar.visible
		self.sidebar.update()
		#await trigger_event("total_update")


	async def click_bb(self,*x):
		#if x != None:

		#print(x)
				##stops midi connection
		if self.ml != None:

			self.ml.stop=True
		await trigger_event("change_page", PageMemory.Past_Page)





	async def tick(self,name):
		while True:

			for i in self.widgets:
				await i.tick()
			#print(f"tick update")

			if self.ml.updated == True:
				await self.note_update(self)
				self.ml.updated = False


			#else:
				#print("aaa")

			self.child_tick
			await asyncio.sleep(0.01)


	async def tickmidi(self,name):
		while True:
			await self.ml.listen()

			#await asyncio.sleep(1)
		#await asyncio.sleep(1)









	async def async_init(self,midi_input=None,tick_time=0.1):
		


		##CONTAINER OF ALL NOTES
		self.Active_Note_Dict={}
		self.tick_time = tick_time
		self.ml = midi_listener(midi_input)
		



		####
		if midi_input==None:
			raise ValueError("GAY No MIDI INPUT")

		else:
			#await asyncio.sleep(5)
			asyncio.create_task(self.ml.listen())

			#self.listener= await midi_listener(midi_input)
			print("walahi")
			#while True:
			#    midi_data = await asyncio.wait_for(midi_queue.get(),timeout=0.01)
			#    for i,k in midi_data:
			#        print("NOTE LIST FOR APP: ",i)
		
		asyncio.create_task(self.tick("fuk1"))

	def __init__(self):

		self.scale="CMajor"
		self.ml = None
		self.listener=None
		self.sidebar = Sidebar()
		self.sidebar.visible=False
		self.name = "DefPage"


		##WARNING THIS MUST BE FILLED SO THAT MY FUNCTIONS CAN AUTO UPDATE SCALE ON SCALE CHANGE IN SETTINGS DROPDOWN!## ^_^
		self.widgets=[]

		self.Back_Button = ft.FloatingActionButton( 
	
			icon=ft.Icons.ARROW_BACK,
			on_click=self.click_bb

			)

		self.side_menu_button=ft.FloatingActionButton(
			on_click=self.click_sidebar_button,
			icon=ft.Icons.MENU

			)

		self.Header = ft.Container(ft.Row(controls=[self.Back_Button,ft.Container(expand=True),self.side_menu_button]),bgcolor=ft.Colors.GREEN_50)
		global globHeader
		globHeader = self.Header
		


		self.body=ft.Stack(
			[
			ft.Container(content=ft.Text("CONTENT HERE"),alignment=ft.alignment.center,expand=True,bgcolor=ft.Colors.BLUE_50),
			ft.Row(controls=[self.sidebar],alignment=ft.MainAxisAlignment.END)

			]
		)





		self.All_Content=ft.Container(



			content=ft.Column(


				controls=[


					self.Header,


					self.body,

					]


				),

			bgcolor=ft.Colors.PINK_100,

			alignment=ft.alignment.center,

			expand=True


			)

	##update new scale scale
	def scale_update(self,x):
		print("starting scale update")
		self.scale=x
		nl=[]
		if x.endswith("Major"):
			y = x[:-5]  # remove the last 5 characters ("Major")
		else:
			raise ValueError("line 235 default strctures does not start with major fuc  fuckf cufkc fuck aaa")
		for i in self.widgets:
			i.scale_name = y
			print(f"NEW SCALE NAME:{y}")
			i.scale=all_scales.major_scales[y]

	async def size_update(self,cords: dict):
		for i in self.widgets:
			print(str(cords))
			i.page_size=cords
			await i.resize()




class chord_display(Default_Widget):
	def __init__(self,scale=1):
		super().__init__()
		self.current_root = None
		self.current_chord = None
		self.nlo_c = []
		self.nl_c = []
		self.textScale=scale


		self.Chord_Body = ft.Container(
			content=ft.Row(
				controls=[
					ft.Container(
						ft.Row(
							alignment=ft.MainAxisAlignment.CENTER
							),
						bgcolor=ft.Colors.GREEN_ACCENT_400,
						expand=True,


						),

					ft.Container(
						ft.Column(
							alignment=ft.MainAxisAlignment.START,
							horizontal_alignment=ft.CrossAxisAlignment.END,
							),


						bgcolor=ft.Colors.GREEN,
						#expand=True,
						),

					],
				alignment=ft.MainAxisAlignment.CENTER,
				#spacing=50
				),
				

			expand=True,


			bgcolor=ft.Colors.GREEN_ACCENT_700,
			alignment=ft.alignment.center,

		)

		self.Wbody = ft.Container(
			ft.Column(
				horizontal_alignment=ft.CrossAxisAlignment.CENTER,
				alignment=ft.MainAxisAlignment.CENTER,
				controls=[self.Chord_Body],
			),
			bgcolor=ft.Colors.BLACK,
			alignment=ft.alignment.center,
			expand=True,
		)

	def update_func(self, nl, nlo, chordList, parts_list):

		if chordList:
			self.textMult = ((min(self.page_size["y"], self.page_size["x"])) * self.textScale)/100

			self.nlo_c = nlo
			self.nl_c = nl

			self.Chord_Body.content.controls[0].content.controls.clear()
			self.Chord_Body.content.controls[1].content.controls.clear()


			self.current_chord = chordList[0]
			self.current_root = parts_list[0]["temp_root"]

			self.Chord_Body.content.controls[0].content.controls.append(
				ft.Text(self.current_root, size=20*self.textMult, weight=ft.FontWeight.BOLD)
			)
			self.Chord_Body.content.controls[0].content.controls.append(
				ft.Text(parts_list[0]["quality"], size=15*self.textMult, italic=True)
			)
			if parts_list[0]["root"] != self.current_root:
				self.Chord_Body.content.controls[0].content.controls.append(
					ft.Text(f"/{parts_list[0]['root']}", size=170*self.textMult)
				)

			for i in parts_list[1:]:
				extra_chord_row=ft.Row(alignment=ft.MainAxisAlignment.END)
				self.Chord_Body.content.controls[1].content.controls.append(extra_chord_row)
				extra_chord_row.controls.append(
					ft.Text((i["temp_root"]), size=5*self.textMult, weight=ft.FontWeight.BOLD)
				)
				extra_chord_row.controls.append(
					ft.Text((i["quality"]), size=4*self.textMult, italic=True)
				)
				if i["root"] != i["temp_root"]:
					extra_chord_row.controls.append(
						ft.Text(f"/{i['root']}", size=4.5*self.textMult)
					)

	async def resize(self):

		print("timetoresizeCD")
		self.textMult = ((min(self.page_size["y"], self.page_size["x"])) * self.textScale) / 100
		bListLen=len(self.Chord_Body.content.controls[0].content.controls)

		if bListLen>0:
			self.Chord_Body.content.controls[0].content.controls[0].size=20*self.textMult
			self.Chord_Body.content.controls[0].content.controls[1].size = 15 * self.textMult
			if bListLen>2:
				self.Chord_Body.content.controls[0].content.controls[2].size = 5* self.textMult

		for i in self.Chord_Body.content.controls[1].content.controls:
			bListLen2=len(i.controls)
			i.controls[0].size=5*self.textMult
			i.controls[1].size=4*self.textMult
			if bListLen2>2:
				i.controls[2].size=4.5*self.textMult

		self.Wbody.update()



class interval_display(Default_Widget):
	def __init__(self):
		super().__init__()
		self.current_root = None
		self.current_chord = None
		self.nlo_c = []
		self.nl_c = []
		self.ntp = []

		self.QL = [
			["1P", "8P"], ["2m", "9m"], ["2M", "9M"], ["3m", "10m"],
			["3M", "10M"], ["4P", "11P"], ["5d", "12d"], ["5P", "12P"],
			["6m", "13m"], ["6M", "13M"], ["7m", "14m"], ["7M", "14M"]
		]

		self.interval_body = ft.Container(
			ft.Row(alignment=ft.MainAxisAlignment.CENTER),
			bgcolor=ft.Colors.PURPLE_400,
			alignment=ft.alignment.center,
		)

		for i in self.QL:
			self.interval_body.content.controls.append(
				ft.Container(
					ft.Column(
						controls=[
							ft.Text(i[0], size=20, color=ft.Colors.WHITE),
							ft.Text(i[1], size=20, color=ft.Colors.WHITE)
						],
						horizontal_alignment=ft.CrossAxisAlignment.CENTER,
						alignment=ft.MainAxisAlignment.CENTER
					),
					bgcolor=ft.Colors.GREY,
				)
			)

		self.Wbody = ft.Container(
			ft.Column(
				horizontal_alignment=ft.CrossAxisAlignment.CENTER,
				alignment=ft.MainAxisAlignment.CENTER,
				controls=[self.interval_body]
			),
			bgcolor=ft.Colors.AMBER_500,
			alignment=ft.alignment.center
		)

	def update_func(self, nl,nlo,chordList, parts_list,c_nl,c_nl_o,outcast_nlo,ntp,last_root):
		
		if chordList:
			self.current_chord = chordList[0]
			self.current_root = parts_list[0]["temp_root"]
			for idx, container in enumerate(self.interval_body.content.controls):
				if idx in ntp or (idx + 12) in ntp:
					container.bgcolor = ft.Colors.BLUE
				else:
					container.bgcolor = ft.Colors.GREY

		elif self.current_chord is not None:

			for idx, container in enumerate(self.interval_body.content.controls):
				if idx in ntp:
					container.bgcolor = ft.Colors.GREEN

			for container in self.interval_body.content.controls:
				if container.bgcolor == ft.Colors.GREEN:
					container.bgcolor = ft.Colors.BLUE
				elif container.bgcolor == ft.Colors.RED:
					container.bgcolor = ft.Colors.GREY

			for note in outcast_nlo:
				stripped = strip_octave(note)
				pos_list = notes_to_positions([stripped], last_root)
				if pos_list:
					pos = pos_list[0]
					if stripped in c_nl:
						self.interval_body.content.controls[pos].bgcolor = ft.Colors.GREEN
					else:
						self.interval_body.content.controls[pos].bgcolor = ft.Colors.RED
		
		



class visual_piano(Default_Widget):
	def __init__(self, num_keys=88):
		super().__init__()
		self.num_keys = num_keys
		self.key_map = {}
		self.current_chord = ''

		self.page_size["x"]

		self.whiteKeyWidthScale=0.0125
		self.whiteKeyHeightScale=0.078
		self.blackKeyWidthScale=0.0083
		self.blackKeyHeightScale=0.0459
		black_key_positions = {1, 3, 6, 8, 10}

		if num_keys > 88 or num_keys < 1:
			raise ValueError("Number of keys must be between 1 and 88")

		if num_keys == 88:
			start_midi = 21
		elif num_keys == 76:
			start_midi = 28
		elif num_keys in (61, 49):
			start_midi = 36
		else:
			start_midi = 21 + ((88 - num_keys) // 2)

		white_keys = []
		black_keys = []
		white_index = 0

		Bwidth=self.page_size["x"] * self.blackKeyWidthScale
		Bheight=self.page_size["y"] * self.blackKeyHeightScale
		Wwidth=self.page_size["x"] * self.whiteKeyWidthScale
		Wheight=self.page_size["y"] * self.whiteKeyHeightScale
			
		for i in range(num_keys):
			midi_num = start_midi + i
			note_index = midi_num % 12
			full_note = midi_to_note(midi_num)
			is_black = note_index in black_key_positions

			if is_black:
				key = ft.Container(
					width=Bwidth,
					height=Bheight,
					bgcolor=ft.Colors.BLACK,
					left=white_index * Wwidth - (Bwidth // 2),
					top=0,
					border_radius=2,
					data={"note": full_note, "is_white": False},
				)
				black_keys.append(key)
			else:
				key = ft.Container(
					width=Wwidth,
					height=Wheight,
					bgcolor=ft.Colors.WHITE,
					border=ft.border.all(1, ft.Colors.BLACK),
					content=ft.Text(full_note, size=8, color=ft.Colors.BLACK),
					alignment=ft.alignment.bottom_center,
					data={"note": full_note, "is_white": True},
				)
				white_keys.append(key)
				white_index += 1

			self.key_map[full_note] = key
		self.numOfWhiteKeys=len(white_keys)
		white_key_row = ft.Row(controls=white_keys, spacing=0)

		self.black_key_stack = ft.Stack(
			controls=[
				ft.Container(
					content=white_key_row,
					width=Wwidth * self.numOfWhiteKeys,
					height=Wheight,
					
				),
				*black_keys
			],
			width=Wwidth * self.numOfWhiteKeys,
			height=Wheight,
		)

		self.Wbody = ft.Container(
			content=self.black_key_stack,
			alignment=ft.alignment.bottom_center,
			bgcolor=ft.Colors.GREEN,	
			#height=Wheight*1.2,
		)
		



	def update_func(self, nl, nlo, chordList, parts_list, last_chord_notes, last_chord_notes_0, new_nlo, ntp, last_root,last_keys):
		

		nlast_keys= last_keys    
		print("=== DEBUG ===")
		print("chordList:", chordList)
		print("parts_list:", parts_list)

		# Determine if there's any usable chord info
		no_chord_info = not chordList or not parts_list or len(str(self.current_chord)) < 1

		# Use full note names with octaves for precise chord tone tracking
		chord_notes_full = last_chord_notes_0 if not no_chord_info and last_chord_notes_0 else nl

		# Use newly pressed notes if available, otherwise fallback to last stat

		# Update chord/root state if valid data is present
		if not no_chord_info:
			self.current_chord = last_chord_notes_0 if last_chord_notes_0 else chordList[0]
			current_root = last_root if last_root else parts_list[0]["temp_root"]




		# --- Resizes and Resets all keys first ---
		
		for note, key in self.key_map.items():
			key.bgcolor = ft.Colors.WHITE if key.data["is_white"] else ft.Colors.BLACK

		# --- Highlight logic ---


		for note in nlo:

			self.key_map[note].bgcolor=ft.Colors.BLUE

		

	

		#SIDEBAR OPTIONS##
		#self.sidebar_content.controls.append(self.staff.sidebar_content)

	async def resize(self):
		print("RESIZING PIANO")
		Bwidth=self.page_size["x"] * self.blackKeyWidthScale
		Bheight=self.page_size["y"] * self.blackKeyHeightScale
		Wwidth=self.page_size["x"] * self.whiteKeyWidthScale
		Wheight=self.page_size["y"] * self.whiteKeyHeightScale
		
		white_index=0
		for note, key in self.key_map.items():
			if key.data["is_white"]:
				key.width=Wwidth
				key.height=Wheight
				white_index+=1

			else:
				key.left=white_index * Wwidth - (Bwidth // 2)
				key.width=Bwidth
				key.height=Bheight


		self.black_key_stack.controls[0].width=Wwidth * self.numOfWhiteKeys

		self.black_key_stack.controls[0].height=Wheight

		self.black_key_stack.width=Wwidth * self.numOfWhiteKeys

		self.black_key_stack.height=Wheight
		#self.Wbody.height=Wheight*1.2
		self.Wbody.update()

class staff(Default_Widget):



	class Timer:
		__slots__ = (
			"duration",
			"end_time",
			"scale",
			"_paused_remaining",
		)

		def __init__(self, duration_seconds, scale=1.0):
			self.duration = float(duration_seconds)
			self.scale = float(scale)
			self.end_time = None
			self._paused_remaining = None

		# -------------------------
		# Core Controls
		# -------------------------

		def start(self):
			"""Start from full duration."""
			self.end_time = time.monotonic() + self.duration / self.scale
			self._paused_remaining = None

		def restart(self,staff):
			staff.event_index=0	
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
				self.end_time = time.monotonic() + self._paused_remaining
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

			self.end_time -= seconds / self.scale

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
				self.scale = float(scale)
				self.end_time = time.monotonic() + remaining / self.scale
			else:
				self.scale = float(scale)

		# -------------------------
		# State
		# -------------------------

		def tick(self):
			if self.running() and time.monotonic() >= self.end_time:
				self.end_time = None
				self.on_finish()

		def remaining(self):
			if self.running():
				return max(0.0, self.end_time - time.monotonic())
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
	def toggle_playback(self, button):
		"""Toggle between play and pause"""
		if not self.score_timer:
			return
		
		if button.data["playing"]:
			# Currently playing → pause
			self.paused_time_remaining = self.score_timer.remaining()
			self.score_timer.stop()
			button.icon = ft.Icons.PLAY_ARROW
			button.tooltip = "Play"
			button.data["playing"] = False
		else:
			# Currently paused → play
			# ← ADD THESE 2 LINES:
			if hasattr(self, 'paused_time_remaining') and self.paused_time_remaining is not None:
				self.score_timer.duration = self.paused_time_remaining
			self.score_timer.start()
			button.icon = ft.Icons.PAUSE
			button.tooltip = "Pause"
			button.data["playing"] = True
		
		button.update()

	def _shift_drawable_x(self, shape, dx):
		t = type(shape)
		if t is cv.Path:
			for el in shape.elements:
				for attr in ('x', 'cp1x', 'cp2x'):
					v = getattr(el, attr, None)
					if v is not None:
						setattr(el, attr, v + dx)
		elif hasattr(shape, 'x1'):  # Line
			shape.x1 += dx
			shape.x2 += dx
		else:
			shape.x += dx

	def edit_shape(self, shape_to_resize, color=None):
		event_type = shape_to_resize.get("type")
		x_target = shape_to_resize.get("x_position")
		
		if x_target is None:
			return
		
		previous_x = shape_to_resize.get("current_x", self.canvas.width)
		dx = x_target - previous_x
		
		# NEGATE dx to reverse direction
		dx = -dx
		
		shape_to_resize["current_x"] = x_target
		
		# ---------- HANDLE BARS ----------
		if event_type == "bar":
			shapes = shape_to_resize.get("shapes", [])
			for shape_group in shapes:
				if isinstance(shape_group, tuple):
					shape_list, shape_type = shape_group
					for shape in shape_list:
						self._shift_drawable_x(shape, dx)

			return
		
		# ---------- HANDLE CHORDS ----------
		if event_type != "chord":
			return



		note_shapes, accidental_shapes = shape_to_resize["shapes"]  
		
		if color is None:
			# Fast path - just move shapes
			for note_group in note_shapes:
				for note_block in note_group:
					if isinstance(note_block, list):
						for shape in note_block[:-1]:  # Skip type string
							self._shift_drawable_x(shape, dx)
			
			for acc_block in accidental_shapes:
				for shape in acc_block[0]:  # Direct tuple access
					self._shift_drawable_x(shape, dx)
		else:
			# Slow path - move and color
			for note_group in note_shapes:
				for note_block in note_group:
					if isinstance(note_block, list):
						for shape in note_block[:-1]:
							self._shift_drawable_x(shape, dx)
							shape.paint = copy.copy(shape.paint)
							shape.paint.color = color
			
			for acc_block in accidental_shapes:
				for shape in acc_block[0]:
					self._shift_drawable_x(shape, dx)
					shape.paint = copy.copy(shape.paint)
					shape.paint.color = color
	def compute_lookahead_seconds(
		self,
		screen_length_px,
		pixels_per_second,
		buffer_seconds=0.1
	):
		"""
		Returns how many seconds ahead we should look.
		"""

		visible_seconds = screen_length_px / pixels_per_second
		return visible_seconds + buffer_seconds

	def get_events_lookahead_and_place(
		self,
		total_time,
		countdown_time,
		look_ahead_sec,
		include_bars=True,
		events=None
	):
		"""
		Amortized O(1) lookahead.
		"""
		screen_width = self.canvas.width
		pixels_per_second = self.pixels_per_second
		
		current_time = total_time - countdown_time
		window_end = current_time + look_ahead_sec
		#temp_midi_dict = self.current_pressed_midi.copy()
		
		if events is None:
			events = self.current_event
		
		result = []
		n = len(events)
		i = self.event_index
		commit_i = i
		
		while i < n:
			event = events[i]
			start = event.get("start_sec")
			if start is None:
				i += 1
				continue
			
			start = float(start) * 5


			##kill off
			if current_time > start + 1.6:
				commit_i = i + 1
				i += 1
				continue
			

			if start >= window_end:
				break
			
			event['x_position'] = screen_width - ((start - current_time) * pixels_per_second)
			press_window = self.press_window_sec
			
			if current_time >= start - press_window and current_time <= start + press_window:
				temp_midi_dict = self.current_pressed_midi
				
				if "pitch_list" in event:
					pitch_list = event["pitch_list"]  
					
					if len(pitch_list) > 1 and len(pitch_list)==len(temp_midi_dict):
								
						if set(pitch_list).issubset(temp_midi_dict):  #  Use temp_midi_dict
							self.edit_shape(event, color=ft.Colors.GREEN)

							for pitch in pitch_list:
								del temp_midi_dict[pitch]
							self.current_pressed_midi = temp_midi_dict
						else:
							self.edit_shape(event)
					

					elif pitch_list[0] in temp_midi_dict:
						self.edit_shape(event, color=ft.Colors.GREEN)
						del temp_midi_dict[pitch_list[0]]
						self.current_pressed_midi = temp_midi_dict
					else:
						self.edit_shape(event)
				else:
					self.edit_shape(event)
			else:
				self.edit_shape(event)
			
			result.append(event)
			i += 1  
		
		self.event_index = commit_i
		return result

	def create_dumb_events(self, events):
		dumb_events = []
		global_note_counter = 0
		last_playable_shape = None  # ← initialize here

		for index, i in enumerate(events):
			event_type = i.get("type")

			if event_type == "bar":
								# midpoint between last chord and this bar
				bar_start_sec = i.get('start_sec')
				if last_playable_shape is not None:
					prev_start = last_playable_shape.get('start_sec', bar_start_sec)
					bar_start_sec = (prev_start + bar_start_sec) / 2

				bar_shapes = shape_constructor(
					shape_x=self.og_position + self.d_width / 2,  # center, matching Notehead anchor
					canvas_height=self.canvas.height,
					top_margin=self.top_margin,
					paint=self.stroke_paint,
					type="bar"
				)
				dumb_events.append({
					"type": event_type,
					"shapes": bar_shapes,
					"start_sec": bar_start_sec,  # ← use midpoint
				})

					
			elif event_type == "chord":
				pl = []
				notes = i.get("notes", [])
				accidentals_list = {}
				jumped = False
				last_played_index = float('inf')
				note_shapes_list = []
				
				# Initialize current_position for this chord
				current_position = self.position
				
				# First, build the pitch list
				for note in notes:
					pitch = note.get('pitch')
					pl.append(pitch)
				
				for pl_index, note in enumerate(notes, start=1):
					global_note_counter += 1
					
					pitch = note.get('pitch')
					
					print(f"\n=== Processing pitch {pitch} (note #{global_note_counter}, chord position #{pl_index}) ===")
					
					tscale_note = str(self.midi_to_scale_note(pitch))
					print(f"tscale_note: {tscale_note}")
					
					note_name = tscale_note[0]
					note_octave = tscale_note[-1]
					
					# Extract accidental
					new_scale_note = tscale_note[0]
					tlen = len(tscale_note)
					
					if tlen > 3:
						new_scale_note = new_scale_note + tscale_note[1] + tscale_note[2]
					elif tlen > 2:
						new_scale_note = new_scale_note + tscale_note[1]
					
					print(f"note_name: {note_name}")
					print(f"note_octave: {note_octave}")
					print(f"new_scale_note: {new_scale_note}")
					print(f"accidentals_list BEFORE: {accidentals_list}")
					
					# Handle B# edge case
					if new_scale_note == "B#":
						lookup_key = str(note_name + str(int(note_octave) - 1))
					else:
						lookup_key = str(note_name + note_octave)
					
					if lookup_key in self.note_dic:
						index = self.note_dic[lookup_key]
						print(f"index for {lookup_key}: {index}")
						
						note_shapes, accidentals_list, jumped, last_played_index, current_position = self.make_note(
							pl_index,
							position=current_position,
							index=index,
							accidentals_list=accidentals_list,
							new_scale_note=new_scale_note,
							pitch_list=pl,
							jumped=jumped,
							last_played_index=last_played_index,
							note_type=note.get('note_type', 'quarter'),
							dotted=note.get('dots', 0) > 0,
)
						
						print(f"accidentals_list AFTER: {accidentals_list}")
						note_shapes_list.append(note_shapes)
					else:
						print(f"SKIPPED: {lookup_key} not in note_dic")
				make_accidentals_result=self.make_accidentals(accidentals_list)
				flat = [s for nw in note_shapes_list for ni in nw for s in ni[:-1]]
				flat += [s for acc in make_accidentals_result for s in acc[0]]
				dumb_events.append({
					"type": event_type,
					"shapes": [note_shapes_list, make_accidentals_result],
					"flat_shapes":flat,
					"start_sec": i.get('start_sec'),
					"pitch_list": pl
				})
				last_playable_shape=i
			
		return dumb_events	

	def _find_next_note_time(self, events, current_div):
		"""Helper function to find the time of the next note after current_div"""
		for event in events:
			if event.get("type") == "chord" and event.get("start_div") > current_div:
				return event.get("start_sec")
		return None


	def change_octave_field(self,x,y,z,param):
		print("ss")
		if param=="up":
			self.note_range[0]=y.value
			x.value=int(y.value)+(4 if self.show_bass ==True else 2)
			self.note_range[1]=x.value

		else:
			self.note_range[1]=y.value
			x.value=int(y.value)-(4 if self.show_bass ==True else 2)
			self.note_range[0]=x.value

		self.sidebar_content.update()


		##this is how everything is mapped##
		self.set_note_dic()

	def handle_file_result(self, e: ft.FilePickerResultEvent, filesButton,media_container=None):
		if e.files:

			self.currentFile = e.files[0].path
			print(self.currentFile)
			textforbutton = self.currentFile if len(self.currentFile) < 15 else self.currentFile[:15]+"..."
			if filesButton:
				filesButton.content.controls[0].controls[0].value = textforbutton
				filesButton.update()
			
			##parse music xml
			events,self.total_score_time_sec = parse_musicxml_chords(self.currentFile)
			self.total_score_time_sec
			self.paused_time_remaining=self.total_score_time_sec	

			self.current_event=self.create_dumb_events(events)
			self.event_index = 0  
			print(f"{len(self.current_event)} is dumb vs {len(events)} ")
			self.score_timer= self.Timer(self.total_score_time_sec)

			if media_container:
				play_pause_button = ft.IconButton(
					icon=ft.Icons.PLAY_ARROW,
					tooltip="Play",
					data={"playing": False},  # track state
					on_click=lambda e: self.toggle_playback(e.control)
				)

				restart_button = ft.IconButton(
					icon=ft.Icons.RESTART_ALT,
					tooltip="Restart",
					on_click=lambda _: self.score_timer.restart(self)
				)

				# Add them to the layout
				controls_row = ft.Row(
					controls=[play_pause_button, restart_button],
					spacing=5
				)

				media_container.content=(controls_row)
				media_container.update()
		else:
			if filesButton:

				filesButton.content.controls[0].controls[0].value = "NONE"
				filesButton.update()
			self.currentFile= None

	def _toggle_step_playing(self, e):
		self.step_playing = not self.step_playing
		if self.step_playing:
			self.step_toggle_real.bgcolor = ft.Colors.GREY_600
			self.step_toggle_step.bgcolor = ft.Colors.GREEN
			self.play_settings_container.content = self.step_settings
		else:
			self.step_toggle_real.bgcolor = ft.Colors.GREEN
			self.step_toggle_step.bgcolor = ft.Colors.GREY_600
			self.play_settings_container.content = self.realtime_settings
		self.sidebar_content.update()

	def _on_pps_change(self, e):
		self.pixels_per_second = e.control.value
		self.look_ahead_sec = self.compute_lookahead_seconds(self.canvas.width, self.pixels_per_second)
		self.shouldTickUpdate=True
		print("moved")

	def __init__(self, mainPage,width_scale=1, height_scale=1,stroke_scale=1,show_bass=True,show_line=True,step_playing=False):
		super().__init__()

		self.canvas = cv.Canvas()
		self.show_bass=show_bass
		self.note_dic={}
		self.pl=[]
		self.stroke_scale=stroke_scale
		self.user_note_shapes=[]
		self.mainPage=mainPage
		#for mxml
		self.next_canvas_step=float('inf')

		self.event_index=0
		self.currentFile=None
		self.current_event=None
		self.total_score_time_sec=0
		self.score_timer=self.Timer(0)	
		self.step_playing=step_playing
		BASE_WIDTH = 1600
		self.pixels_per_second = 120 * (self.page_size["x"] / BASE_WIDTH)
		self.press_window_sec=0.2
		self.current_pressed_midi={}
		self.paused_time_remaining = None
		self.timed_notes=True
		self.correct_played_notes=True	
		#this is because some items have call backs that arent made in a synchronus event or other shit
		#Only really used for visual purposes, once a change is made it should have ticked once
		self.shouldTickUpdate=False



		if show_bass==True:
			self.num_lines = 11
			self.note_range= [2,6]
		else:
			self.note_range= [4,6]
			self.num_lines = 5

		self.set_note_dic()




		self.width_scale = width_scale
		self.height_scale = height_scale


		self.width = self.page_size["x"]*self.width_scale
		self.height = (self.page_size["y"]/1.3)*self.height_scale
		#self.width = 1600
		#self.height = 400	
		self.line_spacing = self.height/self.num_lines
		self.top_margin=self.height*0.18
		self.left_margin = self.width*0.18
		self.right_margin = self.width*0.18


		self.show_line=show_line


		self.Wbody = ft.Container(
			bgcolor=ft.Colors.BLACK,
			alignment=ft.alignment.center,
			#on_resized=lambda: print("resized"),
			#expand=True,
		)
		self.semi_transparent_paint = ft.Paint(
			style=ft.PaintingStyle.FILL,
			color="#8C008DFF",  # full hex with alpha
			stroke_width=11
		)
		self.stroke_paint = ft.Paint(
			stroke_width=(((self.page_size["y"]*0.01)-(self.height*0.007))*self.stroke_scale)
,
			style=ft.PaintingStyle.STROKE,
			color=ft.Colors.BLACK
		)

		# Generate the staff lines
		self.staff_lines = []
		l_count = 0
		for i in range(self.num_lines):
			l_count+= 1
			if l_count != 6:

				y = self.top_margin + i * self.line_spacing
				self.staff_lines.append(cv.Line(
					self.left_margin, y,
					self.width - self.right_margin, y,
					paint=self.stroke_paint
			))

		# Choose which line to place the dot on (e.g., 3rd line = index 2)
		d_width=30  # Width of the oval
		d_height=20
		line_index = 2
		y = self.top_margin + line_index/2 * self.line_spacing
		x = self.width // 2  # Center of the canvas

		
		original_center_y = 765/3 #ths assumes the original height was this
		desired_center_y = self.top_margin + line_index * self.line_spacing ##50 is the coordinates

		treb_x, treb_y = 1,1
		treb_oy = desired_center_y - (original_center_y * treb_y)
		#resulting_center = original_center_x * treb_x + treb_ox
		

		#treb_x, treb_y = 2, 2  # for example, half size
		treb_ox = 0

		self.trebel_shapes=[

			cv.Path([
			# Start at bottom swirl

		],

				

			)


		]

		self.noteline = cv.Line(
				(self.width - self.right_margin)/7, (self.height),
				(self.width - self.right_margin)/7, self.top_margin,
				paint=self.semi_transparent_paint
				)


		#ddd
		# Create the canvas with staff lines + dot
		self.canvas = cv.Canvas(
			self.staff_lines+([self.noteline] if self.show_line else []),
			width=self.width,
			height=self.height,
		#	expand=True
		)

		self.active_canvas = cv.Canvas(
			width=self.width,
			height=self.height,
		#	expand=True
		)
		self.active_canvas2 = cv.Canvas(
			width=self.width,
			height=self.height,
		#	expand=True
		)



		# Add the canvas' to a container and center it
	

		
		self.active_canvas_container=ft.Container(
			width=self.width,
			height=self.height,
			left=0,
			content=self.active_canvas,
			alignment=ft.alignment.center_right,
			bgcolor=ft.Colors.with_opacity(0.8,"red"),
			animate_position=ft.Animation(3000, ft.AnimationCurve.LINEAR),
			)

		self.active_canvas_container2=ft.Container(
			width=self.width,
			height=self.height,
			left=self.width,
			content=self.active_canvas2,
			alignment=ft.alignment.center_right,
			bgcolor=ft.Colors.with_opacity(0.8,"blue"),
			animate_position=ft.Animation(3000, ft.AnimationCurve.LINEAR),
			)





		self.canvas_stack=ft.Stack(controls=[self.active_canvas_container,self.active_canvas_container2,self.canvas])
		
		self.t_row = ft.Row(
			controls=[
				ft.Container(
					expand=True,
					content=self.canvas_stack,
					alignment=ft.alignment.center_right,
					bgcolor=ft.Colors.WHITE,
				),
			],
			alignment=ft.MainAxisAlignment.CENTER,
			#spacing=(-self.width),

		)


		# Add the container to the page body
		self.Wbody.content = ft.Row(
								controls=
									[

									ft.Column(
										controls=[self.t_row,ft.Container()],
										#horizontal_alignment=ft.CrossAxisAlignment.START
										alignment=ft.MainAxisAlignment.CENTER
										),


									],
								alignment=ft.MainAxisAlignment.END,
								)







		f_options=[2,6]
		f2_options=[3,6]

		#######################sidebar options########################

		self.from_field = ft.TextField(
			value=f_options[0] if self.show_bass==True else f2_options[0],
			input_filter=ft.InputFilter(regex_string=r"[0-9]*", replacement_string="")
		)

		self.to_field = ft.TextField(
			value=f_options[1] if self.show_bass==True else f2_options[1] ,
			input_filter=ft.InputFilter(regex_string=r"[0-9]*", replacement_string="")
		)

		range_row = ft.Row(
			controls=[
				ft.Container(content=self.from_field, alignment=ft.alignment.center, width=50),
				ft.Text("-TO-"),
				ft.Container(content=self.to_field, alignment=ft.alignment.center, width=50)
			],
			wrap=True,
			alignment=ft.MainAxisAlignment.CENTER

		)


		filesButton=ft.ElevatedButton(
			content=ft.Column(controls=[ft.Row(controls=[ft.Text(self.currentFile or "NONE",overflow=ft.TextOverflow.ELLIPSIS,expand_loose=True)],wrap=True)],wrap=True),
			on_click=lambda _: pick_files_dialog.pick_files(allow_multiple=False, allowed_extensions=["mxl","xml"]),
		)

		#           row-column.32
		
		pick_files_dialog = ft.FilePicker(
			on_result=lambda e: self.handle_file_result(e, filesButton,media_container=self.Wbody.content.controls[0].controls[1])
		)

		fileSelectRow=ft.Row(
			alignment=ft.MainAxisAlignment.CENTER,

			controls=[
				pick_files_dialog,
				ft.Text("MXML to read: ",weight=ft.FontWeight.BOLD),
				filesButton,
				]
		)

				# --- Real Time settings ---
		self.pps_slider = ft.Slider(
			min=30,
			max=400,
			value=self.pixels_per_second,
			divisions=37,
			label="{value} px/s",
			on_change=self._on_pps_change,
		)


			# In __init__, after fileSelectRow:

		self.step_toggle_real = ft.Container(
			content=ft.Text("Real Time", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
			bgcolor=ft.Colors.GREEN if not self.step_playing else ft.Colors.GREY_600,
			padding=ft.padding.symmetric(horizontal=10, vertical=6),
			border_radius=ft.border_radius.only(top_left=8, bottom_left=8),
		)

		self.step_toggle_step = ft.Container(
			content=ft.Text("Step by Step", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
			bgcolor=ft.Colors.GREY_600 if not self.step_playing else ft.Colors.GREEN,
			padding=ft.padding.symmetric(horizontal=10, vertical=6),
			border_radius=ft.border_radius.only(top_right=8, bottom_right=8),
		)

		self.step_toggle_btn = ft.ElevatedButton(
			content=ft.Row(
				controls=[self.step_toggle_real, self.step_toggle_step],
				spacing=0,
				tight=True,
			),
			on_click=self._toggle_step_playing,
			style=ft.ButtonStyle(
				padding=ft.padding.all(0),
				shape=ft.RoundedRectangleBorder(radius=8),
				overlay_color=ft.Colors.TRANSPARENT,
				bgcolor=ft.Colors.TRANSPARENT,
				shadow_color=ft.Colors.TRANSPARENT,
				elevation=0,
			),
		)

		# --- Real Time settings ---
		self.realtime_settings = ft.Column(
			controls=[
				ft.Text("Real Time Settings", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE70),
				ft.Text("(your real time options here)", size=10, color=ft.Colors.WHITE54),
			],
			horizontal_alignment=ft.CrossAxisAlignment.CENTER,
			spacing=4,
		)

		# --- Step by Step settings ---
		self.step_settings = ft.Column(
			controls=[
				ft.Text("Step Settings", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE70),
				ft.Text("(your step options here)", size=10, color=ft.Colors.WHITE54),
			],
			horizontal_alignment=ft.CrossAxisAlignment.CENTER,
			spacing=4,
		)

		self.play_settings_container = ft.Container(
			content=self.step_settings if self.step_playing else self.realtime_settings,
			padding=ft.padding.symmetric(vertical=6),
			bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.GREY)
		)
		
		timed_notes_checkbox=ft.Checkbox(value=True,on_change=lambda e:uni_toggle(self.timed_notes))
		correct_played_notes_checkbox=ft.Checkbox(value=True,on_change=lambda e:uni_toggle(self.correct_played_notes))

		notes_settings_container = ft.Container(
			content=ft.Row(
				controls=[
					ft.Column(
						controls=[
							ft.Row(
								controls=[
									ft.Text("Timed Notes", size=17),
									timed_notes_checkbox
								]
							),
							ft.Row(
								controls=[
									ft.Text("Correct Midi input", size=15),
									correct_played_notes_checkbox
								]
							),
						]
					),
				],
				alignment=ft.MainAxisAlignment.CENTER,
			)
		)
		

		###ACCURATE TIMED NOTEs
		
		
		
		self.sidebar_content.controls.append(notes_settings_container)
		self.sidebar_content.controls.append(fileSelectRow)
		self.sidebar_content.controls.append(self.pps_slider)
		self.sidebar_content.controls.append(self.step_toggle_btn)
		self.sidebar_content.controls.append(self.play_settings_container)
		#lambda makes me do this after i think
		self.from_field.on_change = lambda e: self.change_octave_field(self.to_field,self.from_field,self,"up")
		self.to_field.on_change = lambda e: self.change_octave_field(self.from_field,self.to_field,self,"down")


		self.mainPage.update()

	async def update_func(self,pl):


	
		self.user_note_shapes=[]

		#print(f"pitches list: {pl}")

		#used in make note for staff notation
		self.accidentals={}
		self.accidental_state={}


		self.last_played_index=float('inf')#default int so that it never triggers first note


		self.jumped=False#if the note was pushed to the side due to them being right next to each other
		self.jump_start=False
		#for staff im saving the pitch list because i need to for ingame size change
		self.pl=pl

		#print(f"list of shapes:  {self.canvas.shapes}")
		
		old_pressed_midi=self.current_pressed_midi
		self.current_pressed_midi={}
		pl_count=0
		for i in self.pl:
			pl_count+=1

		#	takes pitch get scale note 
			tscale_note=str(self.midi_to_scale_note(i))
		
			note_name = tscale_note[0]
			note_octave = tscale_note[-1]
			print(f"t scale note: {(note_name+note_octave)}")

			self.new_scale_note=tscale_note[0]
			tlen=len(tscale_note)
			


			#adds the note and remove the octave at the end
			if tlen>3:
				self.new_scale_note=self.new_scale_note+tscale_note[1]+tscale_note[2]

			elif tlen>2:
				self.new_scale_note=self.new_scale_note+tscale_note[1]






			print(f"pitchaaa: {i}")
		#	#self.not_dic has all the keys in the specified range and their position in the canvas
		#	##if not in range it will not appear in the staff bc i dont have space it would look crazy
			if str(note_name+note_octave) in self.note_dic:
				

				#scales like F# will have C## so to not have c,c#,c## we make c to b#.
				#but my systems is crude and does not work like that. it just takes in an index and note
				#so I have to switch it back for this function to let the staff know that this is the first appeance of B and not the last B in the scale
				if self.new_scale_note=="B#":
					index =self.note_dic[str(note_name+str(int(note_octave)-1))]	
				else:
					index =self.note_dic[str(note_name+note_octave)]

				note_shapes=self.make_note(pl_count,position=None,index=index)
				

				##lets me know if and when the user pressed keys and to remember it
				if self.score_timer:
					if i in old_pressed_midi:
						pass
					else:
						self.current_pressed_midi[i]=self.score_timer.remaining()


				###what the fuck does this do???????? 
				#i mean actuslly what the fuck did i do?
				#i know like mechanically what ot does but like 
				#i dont know why note_shapes[-1] is like that
				#what the fuck is at the end that i dont want???
				###wait its not even doing anythng cause its a list with one item im pretty sure, we are in the loop(:
				## funny but im scared to touch rn im doing something else atm

				# i do i[-1] because the last item is the note type, i need it for mxml parsing so i need to dodge it here
				for i in note_shapes[-1][:-1]:

					self.user_note_shapes.append(i)

				temp_list=[]
				for i in note_shapes[:-1]:
					temp_list.append(i)

				self.accidental_state[str(index)]=temp_list	

		#accidentals are added after because the
		#y change space retroactively on future accidentals
		#the accidentals gets added in thesame order as notes get added
		canvas_art=self.make_accidentals(self.accidentals)
		print("adding_art")
		for i in canvas_art:

			if i[-1] in {'#','b','N','##','bb'}:
				i=i[:-1]
			#print(f"items in canvas art/accidental list = {i}")
			for e in i:
				print(f'items are: {e}')
				if type(e)== list:
					for x in e:
						self.user_note_shapes.append(x)
				else:
					self.user_note_shapes.append(e)
	

	def accidental_type(self,note,always_accidental=False):

		#note should be anything like c# or gb

		"""
		Returns:
		 - None            if `note` is in the major scale of `key`
		 - "sharp"         if it's an out-of-scale sharp (e.g. F# in C major)
		 - "flat"          if it's an out-of-scale flat  (e.g. Bb in C major)
		 - "natural"       if it's a natural accidental,
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
				#if ykyk
			if note not in self.scale:


				# sanity check: must still be in chromatic
				#if note not in all_scales.chromatic_major_scales[self.scale_name]:
				#	raise ValueError(f"{note!r} isn’t even in the chromatic of {key!r}")


				##gets the position of key in all notes in chromatic scale,

				#index= all_scales.chromatic_major_scales[self.scale_name].index(note)
				

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






	def set_note_dic(self):
		
		note_names = ['C', 'D','E', 'F','G', 'A', 'B']


		#so if the range was 2,6 C6 would have a line index of -4
		#so if both trebel and bass are showing it would be 29 keys
		#or 15() keys if only trebel
		#so it would 
		if self.show_bass==True:
			start_line_index=24

		else:
			start_line_index=10

		for i in range(int(self.note_range[0]),int(self.note_range[1])):
				for x in note_names:
					self.note_dic[x+str(i)]=start_line_index
					start_line_index -=1


		self.note_dic["C"+str(self.note_range[1])]=start_line_index

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
		print(f"prevous positions: {prev_positions}")
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
		d_height = self.d_height	
		d_width = self.d_width
		position = self.position
		og_position = self.og_position
		return_list = []
		width = 8
		prev_positions = None
		accidental_type = None

		for i in accidentals_list:
			row = accidentals_list[i]
			print(f"DEBUG: Processing index {i}, row: {row}")
			if (i+1 not in accidentals_list):
				prev_positions = None

			curr = self.assign_positions(row, i, prev_positions, width)
			print(f"DEBUG: Positions assigned: {curr}")
			prev_positions = set(curr)

			count = 0
			y = self.top_margin + i/2 * self.line_spacing
			
			for x in row:
				# ← UNPACK TUPLE OR USE STRING
				if isinstance(x, tuple):
					accidental_char, note_x = x
					print(f"DEBUG: Unpacked tuple - accidental={accidental_char}, note_x={note_x}")
				else:
					accidental_char = x
					note_x = og_position
					print(f"DEBUG: Using string - accidental={accidental_char}, note_x={note_x}")
				
				position_mult = curr[count] + 1
				count += 1
				
				accidental_x = (note_x + d_width/2) - ((d_width*0.9)*int(position_mult))
				print(f"DEBUG: accidental_x for {accidental_char} = {accidental_x}, note_x={note_x}, og_position={og_position}")

				# Use shape_constructor for accidentals
				accidental_shapes = shape_constructor(
					shape_x=accidental_x,
					shape_y=y,
					shape_width=d_width,
					shape_height=d_height,
					type=accidental_char,
					paint=self.stroke_paint
				)
				
				if accidental_shapes is None:
					raise ValueError(f"shape_constructor returned None for accidental '{accidental_char}' at x={accidental_x}, y={y}, width={d_width}, height={d_height}")
				
				return_list.extend(accidental_shapes)

		print(f"DEBUG: make_accidentals returning {len(return_list)} accidentals")
		return return_list






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
		dotted=False,          # ← add this
	):

		return_list=[]
		
		d_height=self.d_height	
		d_width=self.d_width
		
		# ← Don't overwrite position!
		if position is None:
			position = self.position
		
		og_position=self.og_position
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

		print(f"Index is: {index}")
		
		y = self.top_margin + index/2 * self.line_spacing
		
		# ← Calculate FINAL position
		final_position = position
		
		#logic for notes to appear ONTOP AND to the side if the notes are one note apart
		if (last_played_index-1 == index and not jumped):
			final_position = position + (d_width*0.8)
			jumped = True
		#logic for notes to appear to the side of the same note if the notes are the same but different suffix ie: C and C#
		elif (last_played_index == index) and not jumped:
			final_position = position + d_width
			jumped = True
		else:
			jumped = False

		x = final_position
		
		print(f"DEBUG make_note: final_position={final_position}, position={position}, self.position={self.position}")
		


		# Use shape_constructor for whole note
		note_shapes = shape_constructor(
			shape_x=x,
			shape_y=y,
			shape_width=d_width,
			shape_height=d_height,
			type=note_type,
			paint=None,  # Will use default black fill
			dotted=dotted
		)
		
		if note_shapes is None:
			raise ValueError(f"shape_constructor returned None for whole note at x={x}, y={y}, width={d_width}, height={d_height}")
		
		shapes, note_type = note_shapes[0]
		d_line= cv.Line()
		
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
			if accidental == "#":
				print("found accidental sharp")
			elif accidental == "b":
				print("found accidental flat")
			elif accidental == "N":
				print("found accidental Natural")

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
			print("setting index for next time!!")
		except UnboundLocalError:
			print("error 1647 ds")
			pass

		return_list.append([*shapes,note_type])	
		
		if accidentals_list != None:
			# ← RETURN final_position too!
			return return_list, accidentals_list, jumped, last_played_index, final_position
		else:
			return return_list


	def canvasStepper(self, remaining):
		if remaining <= self.next_canvas_step:
			self.next_canvas_step = remaining - 3
			# Slide active canvas left by one 3-second window worth of pixels
			current_left = self.active_canvas_container.left or 0
			current_left2=self.active_canvas_container2.left or 0

			self.active_canvas_container.left = current_left - (self.pixels_per_second * 3)
			self.active_canvas_container2.left=current_left2-(self.pixels_per_second*3)
			self.active_canvas_container.update()
			self.active_canvas_container2.update()
			return True
		return False

	async def tick(self, updated_externally=False):
		"""
		Update canvas with user notes and spawned events from the score timer.
		"""
		events_to_spawn = []
		updated_externally=updated_externally	
		active_canvas_update = updated_externally

		if  self.score_timer.running():

			self.score_timer.tick()
			remaining = self.score_timer.remaining()
			
			self.current_pressed_midi = {
				pitch: timestamp 
				for pitch, timestamp in self.current_pressed_midi.items()
				if timestamp <= remaining + 0.1
			}
			if self.canvasStepper(remaining):


				#print(remaining)
				events_to_spawn = self.get_events_lookahead_and_place(
					total_time=self.total_score_time_sec,
					countdown_time=self.score_timer.remaining(),
					look_ahead_sec=self.look_ahead_sec,
				)
				#print(len(events_to_spawn))

				active_canvas_update = True

		elif self.shouldTickUpdate:
			print("faketick")
			self.shouldTickUpdate=False

			remaining = self.score_timer.remaining()
						
			events_to_spawn = self.get_events_lookahead_and_place(
				total_time=self.total_score_time_sec,
				countdown_time=self.score_timer.remaining(),
				look_ahead_sec=self.look_ahead_sec,
			)
			#print(len(events_to_spawn))
			active_canvas_update = True
			updated_externally=True

			



		if active_canvas_update:
			#print(f"the number of items in user shapes is {len(self.user_note_shapes)}")
			
			# Keep only the staff lines, remove any previous note/event shapes

			self.active_canvas.shapes = []
			
			# Add user's note shapes
			self.active_canvas.shapes.extend(self.user_note_shapes)
			
			# Add spawned event shapes from the score
			#print(f"shapes:{len(events_to_spawn)}")
			for event in events_to_spawn:
				event_type = event.get("type")
				
				if event_type == "bar":
					# Bar shapes come directly from shape_constructor: [([bar_line], 'bar')]
					bar_shapes = event['shapes']
					for shape_tuple in bar_shapes:
						shapes_list, shape_type = shape_tuple
						for shape in shapes_list:
							self.active_canvas.shapes.append(shape)
				
				elif event_type == "chord":
					self.active_canvas.shapes.extend(event['flat_shapes']) 
			self.active_canvas.update()
			self.active_canvas2.update()
		

		if updated_externally:
			self.canvas.update()



	async def resize(self):
		print("timetoresizestaff")

		
		self.height=((self.page_size["y"]/1.7)*self.width_scale)
		self.width=(self.page_size["x"]*self.width_scale)
		self.top_margin=self.height*0.18



		self.active_canvas_container.width = self.width
		self.active_canvas_container.height = self.height + self.top_margin  # ← match canvas
		self.active_canvas_container2.width = self.width
		self.active_canvas_container2.height = self.height + self.top_margin  #
		self.active_canvas_container2.left=self.width
		self.active_canvas_container2.animate_position=None


		self.active_canvas2.width=self.canvas.width= self.active_canvas.width=self.width
		BASE_WIDTH = 1600  # your reference/design resolution width
		self.pixels_per_second = 120 * (self.canvas.width / BASE_WIDTH)
		self.look_ahead_sec = self.compute_lookahead_seconds(self.canvas.width, self.pixels_per_second)
		self.look_ahead_sec=self.compute_lookahead_seconds(self.canvas.width,self.pixels_per_second)
		self.canvas.height=self.active_canvas.height=self.active_canvas2.height=self.height+self.top_margin
		self.line_spacing = (self.height/self.num_lines)-(self.height*0.013)
		self.stroke_paint.stroke_width=(((self.page_size["y"]*0.01)-(self.height*0.007))*self.stroke_scale)
		self.left_margin = self.width*0.01
		self.right_margin = self.width*0.02



		self.semi_transparent_paint.stroke_width=((self.page_size["y"]*0.03)-(self.height*0.007))*self.stroke_scale
		self.noteline = cv.Line(
				(self.width - self.right_margin)/7, self.height+self.top_margin/2,
				(self.width - self.right_margin)/7, self.top_margin/3,
				paint=self.semi_transparent_paint
				)




		self.d_height=((self.top_margin + 1 * self.line_spacing)-(self.top_margin))*0.7
		self.d_width=self.d_height*1.3  # Width of the oval
		




		if self.show_bass:

			self.position=self.width // 7.5 
			self.og_position=self.width // 7.5

		else:
			self.position=self.width // 2
			self.og_position=self.width // 2










		self.staff_lines=[]
		l_count=0
		for i in range(self.num_lines):
			l_count+= 1
			if l_count != 6:

				y = self.top_margin + i * self.line_spacing
				self.staff_lines.append(cv.Line(
					self.left_margin, y,
					self.width - self.right_margin, y,
					paint=self.stroke_paint
			))
		#self.canvas.shapes=self.canvas.shapes[:(self.num_lines-1)]

		#resets notelines and clears past notes   
		self.canvas.shapes=[]
		for i in self.staff_lines:
			self.canvas.shapes.insert(0,i)  #<---- can be optimised to be added on creation instead of looping twice over staff lines
		self.canvas.shapes.append(self.noteline)



				##FOR XML NOTES
		if self.current_event:
			current_time = None
			if self.score_timer.running():
				current_time = self.score_timer.remaining()
				self.score_timer.stop()

				try:
					play_button = self.Wbody.content.controls[0].controls[1].content.controls[0]
					play_button.icon = ft.Icons.PLAY_ARROW
					play_button.tooltip = "Play"
					play_button.data["playing"] = False
					play_button.update()
				except (IndexError, AttributeError, TypeError):
					pass  # button might not exist yet
			elif self.paused_time_remaining is not None:
				current_time = self.paused_time_remaining  # ← was paused, grab saved position

			makeshift_result = type("Dummy", (), {})()
			file_obj = type("Dummy", (), {})()
			file_obj.path = self.currentFile
			makeshift_result.files = [file_obj]

			self.handle_file_result(makeshift_result, None)

			if current_time is not None:
				self.score_timer.duration = current_time
				self.paused_time_remaining = current_time

			self.score_timer.start()

		await self.update_func(self.pl)
		await self.tick(updated_externally=True)

		if self.score_timer:
			self.score_timer.stop()
		self.Wbody.update()

class Sidebar(ft.Container):



	async def dropdown_changed(self,e):
		await trigger_event("change_scale",e.control.value.split('/')[0])


	def gen_scale_options(self):
		from pychord.constants import all_scales


		scale_options = [f"{maj}Major/{min}Minor" for maj, min in zip(all_scales.major_scales, all_scales.minor_scales)]
		return scale_options

	def __init__(self,items=[],):



		#self.scale=
		

		itemlist=[

			ft.Row(
				[
					ft.Text("SETTINGS",size=30,weight=ft.FontWeight.BOLD),
						],
						wrap=True,
						alignment=ft.MainAxisAlignment.CENTER

					),

			ft.Row(
				controls=[
					ft.Dropdown(
						label="Scale",
						value="CMajor/AMinor",
						options=[
							ft.dropdown.Option(f"{maj}Major/{min}Minor")
							for maj, min in zip(all_scales.major_scales, all_scales.minor_scales)
						],
						width=200,
						on_change=self.dropdown_changed,
					)
				],
				alignment=ft.MainAxisAlignment.CENTER,
			),




			# divider
			ft.Container(
				bgcolor=ft.Colors.BLACK26,
				border_radius=ft.border_radius.all(30),
				height=1,
				alignment=ft.alignment.center_right,
				width=220,
				#expand=True,
			),


		]
		for i in items:
			itemlist.append(i)




		super().__init__(

			content=ft.Column(
				itemlist,
				#tight=True,

			horizontal_alignment=ft.CrossAxisAlignment.CENTER,
			),

			padding=ft.padding.all(15),
			margin=ft.margin.all(0),
			width=300,
			bgcolor=ft.Colors.BLUE_GREY,
			#visible=self.nav_rail_visible,

		)
		#self.visible=False

	def top_nav_change(self, e):
		self.top_nav_rail.selected_index = e.control.selected_index
		self.update()

