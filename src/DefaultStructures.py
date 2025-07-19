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

	def __init__(self):

		self.sidebar_content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
		self.scale=default_scale["C"]
		#scale name always for major
		self.scale_name = "C"
		self.page_size = {"x":1600,"y":400}

	def resize(self):
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


	async def note_update(e,self):


		print("OK READY TO FUCK HARD")
		print(str(e))




	async def child_tick():
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
			#print(f"tick update")

			if self.ml.updated == True:
				await self.note_update(self)
				self.ml.updated = False


			#else:
				#print("aaa")

			self.child_tick
			await asyncio.sleep(0.05)


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

		if midi_input==None:
			raise ValueError("GAY No MIDI INPUT")

		else:
			#await asyncio.sleep(5)
			asyncio.create_task(self.tick("fuk1"))
			asyncio.create_task(self.ml.listen())

			#self.listener= await midi_listener(midi_input)
			print("walahi")
			#while True:
			#    midi_data = await asyncio.wait_for(midi_queue.get(),timeout=0.01)
			#    for i,k in midi_data:
			#        print("NOTE LIST FOR APP: ",i)


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
	def __init__(self):
		super().__init__()
		self.current_root = None
		self.current_chord = None
		self.nlo_c = []
		self.nl_c = []



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
				controls=[self.Chord_Body,],
			),
			bgcolor=ft.Colors.AMBER_500,
			alignment=ft.alignment.center,
			expand=True,
		)

	def update_func(self, nl, nlo, chordList, parts_list):

		if chordList:
			self.nlo_c = nlo
			self.nl_c = nl

			self.Chord_Body.content.controls[0].content.controls.clear()
			self.Chord_Body.content.controls[1].content.controls.clear()


			self.current_chord = chordList[0]
			self.current_root = parts_list[0]["temp_root"]

			self.Chord_Body.content.controls[0].content.controls.append(
				ft.Text(self.current_root, size=200, weight=ft.FontWeight.BOLD)
			)
			self.Chord_Body.content.controls[0].content.controls.append(
				ft.Text(parts_list[0]["quality"], size=150, italic=True)
			)
			if parts_list[0]["root"] != self.current_root:
				self.Chord_Body.content.controls[0].content.controls.append(
					ft.Text(f"/{parts_list[0]['root']}", size=170)
				)

			for i in parts_list[1:]:
				extra_chord_row=ft.Row(alignment=ft.MainAxisAlignment.END)
				self.Chord_Body.content.controls[1].content.controls.append(extra_chord_row)
				extra_chord_row.controls.append(
					ft.Text((i["temp_root"]), size=50, weight=ft.FontWeight.BOLD)
				)
				extra_chord_row.controls.append(
					ft.Text((i["quality"]), size=40, italic=True)
				)
				if i["root"] != i["temp_root"]:
					extra_chord_row.controls.append(
						ft.Text(f"/{i['root']}", size=45)
					)




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

		white_key_width = 24
		white_key_height = 150
		black_key_width = 16
		black_key_height = 90
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

		for i in range(num_keys):
			midi_num = start_midi + i
			note_index = midi_num % 12
			full_note = midi_to_note(midi_num)
			is_black = note_index in black_key_positions

			if is_black:
				key = ft.Container(
					width=black_key_width,
					height=black_key_height,
					bgcolor=ft.Colors.BLACK,
					left=white_index * white_key_width - (black_key_width // 2),
					top=0,
					border_radius=2,
					data={"note": full_note, "is_white": False},
				)
				black_keys.append(key)
			else:
				key = ft.Container(
					width=white_key_width,
					height=white_key_height,
					bgcolor=ft.Colors.WHITE,
					border=ft.border.all(1, ft.Colors.BLACK),
					content=ft.Text(full_note, size=8, color=ft.Colors.BLACK),
					alignment=ft.alignment.bottom_center,
					data={"note": full_note, "is_white": True},
				)
				white_keys.append(key)
				white_index += 1

			self.key_map[full_note] = key

		white_key_row = ft.Row(controls=white_keys, spacing=0)

		black_key_stack = ft.Stack(
			controls=[
				ft.Container(
					content=white_key_row,
					width=white_key_width * len(white_keys),
					height=white_key_height,
				),
				*black_keys
			],
			width=white_key_width * len(white_keys),
			height=white_key_height,
		)

		self.Wbody = ft.Container(
			content=black_key_stack,
			alignment=ft.alignment.center,
			bgcolor=ft.Colors.AMBER_100,
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




		# --- Reset all keys first ---
		for note, key in self.key_map.items():
			key.bgcolor = ft.Colors.WHITE if key.data["is_white"] else ft.Colors.BLACK

		# --- Highlight logic ---


		for note in nlo:

			self.key_map[note].bgcolor=ft.Colors.BLUE

		



		#SIDEBAR OPTIONS##
		#self.sidebar_content.controls.append(self.staff.sidebar_content)

class staff(Default_Widget):






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




	def __init__(self, width_scale=1, height_scale=1,stroke_width=30,show_bass=True,show_line=True):
		super().__init__()

		
		self.canvas = cv.Canvas()
		self.show_bass=show_bass
		self.note_dic={}
		self.pl=[]
		
		









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
			bgcolor=ft.Colors.AMBER_500,
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
			stroke_width=6,
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
			width=(self.width if self.show_bass !=True else self.width),
			height=self.height,
		#	expand=True
		)

		# Add the canvas to a container and center it


		self.t_row = ft.Row(
			controls=[
				ft.Container(
					content=self.canvas,
					# alignment=ft.alignment.center,
					bgcolor=ft.Colors.WHITE,
				),
				
				ft.Column(
					controls=[
						ft.Container(
							content=ft.Image(
								src="x.PNG",
								#fit=ft.ImageFit.SCALE_DOWN,
								#height=(self.height * 0.5),
								#width=self.width*0.2
								),
							#padding=ft.padding.only(left=-self.width,bottom=-4 if self.show_bass == True else -85),

						),
						ft.Container(
							content=ft.Image(
								src="x.PNG",
								#fit=ft.ImageFit.SCALE_DOWN,
								#height=(self.height*1) if  self.show_bass== True else 0,
							),
				#			padding=ft.padding.only(bottom=87),
						),
					],

					spacing=0

				),
			
			],
			# alignment=ft.MainAxisAlignment.CENTER,
			#spacing=(-self.width),

		)


		# Add the container to the page body
		self.Wbody.content = ft.Row(
								controls=
									[

									ft.Column(
										controls=[self.t_row],
										#horizontal_alignment=ft.CrossAxisAlignment.START
										alignment=ft.MainAxisAlignment.CENTER
										),


									],
								alignment=ft.MainAxisAlignment.START,
								)







		f_options=[2,6]
		f2_options=[3,6]

		###sidebar options##

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


		self.sidebar_content.controls.append(range_row)




	

		self.from_field.on_change = lambda e: self.change_octave_field(self.to_field,self.from_field,self,"up")
		self.to_field.on_change = lambda e: self.change_octave_field(self.from_field,self.to_field,self,"down")

	async def update_func(self,pl):
		#print(f"pitches list: {pl}")

		#used in make note for staff notation
		self.accidentals={}
		self.accidental_state={}

		self.was_accidental=False
		self.last_played_index=float('inf')#default int so that it never triggers first note


		self.jumped=False#if the note was pushed to the side due to them being right next to each other
		self.accidental_to_jump=False
		self.accidental_jumped=False

		#for staff im saving the pitch list because i need to for ingame size change
		self.pl=pl

		#print(f"list of shapes:  {self.canvas.shapes}")
		
		self.canvas.shapes=self.canvas.shapes[:(self.num_lines)]
		print("updateing")



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



				for i in note_shapes[-1]:
					self.canvas.shapes.append(i)

				temp_list=[]
				for i in note_shapes[:-1]:
					temp_list.append(i)

				self.accidental_state[str(index)]=temp_list	

		#accidentals are added after because they change space retroactively on future accidentals
		#the accidentals gets added in thesame order as notes get added
		

		for i in self.accidental_state.values():
			
			#simple for loop ^_^
			for e in i:
				#oh no nested..but lists are short -_-
				#should be good
				#print(f"e= {e}")
				for x in e:
					##wtf have i done 0_0
					self.canvas.shapes.append(x)
		


	 

		self.canvas.update


		pass

	

	def accidental_type(self,note,always_accidental=False):
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

	def make_note(self,pl_index,position=None,index=6):
		return_list=[]
		
		d_height=((self.top_margin + 1 * self.line_spacing)-(self.top_margin))*0.7
		d_width=d_height*1.3  # Width of the oval
		



		if type(position)==type(None):
			
			if self.show_bass:

				position=self.width // 7.5 
				og_position=self.width // 7.5

			else:
				position=self.width // 2
				og_position=self.width // 2


		l_count=0


		

		print(f"Index is: {index}")




		y = self.top_margin + index/2 * self.line_spacing
		

		#logic for notes to appear ONTOP AND to the side if the notes are one note apart
		if (self.last_played_index-1 == index and not self.jumped):
			position=position+(d_width*0.8)
			self.jumped	=True
		#logic for notes to appear to the side of the same note if the notes are the same but different suffix ie: C and C#
		elif (self.last_played_index == index) and not self.jumped:
			position=position+d_width
			self.jumped =True

		else:
			self.jumped=False


		x =  position

		# Create the oval 
		b_dot = cv.Oval(
			x=x,
			y=y- (d_height/2),
			width=d_width,   # Width of the oval
			height=d_height,   # Height of the oval (change for desired oval shape)
			paint=ft.Paint(
				color=ft.Colors.BLACK,
				style=ft.PaintingStyle.FILL
			)
		)




		# Width of the oval



		w_dot = cv.Oval(
			x=x+d_height/2.3,
			y=y-d_width/4,
			width=d_height/2.2,   # Width of the oval
			height=d_width/2,   # Height of the oval (change for desired oval shape)
			paint=ft.Paint(
				color=ft.Colors.WHITE,
				style=ft.PaintingStyle.FILL
			)
		)

		d_line= cv.Line(
			)
		

		##basically managing all the accidentals 

		accidental=self.accidental_type(self.new_scale_note,always_accidental=False)

		if accidental==None:





			#case: when   #@[@]<-new note
			if index in self.accidentals:
				t_accidental =self.accidental_type(self.new_scale_note,always_accidental=True)
				t_list=self.accidentals[index]
				t_list.append(t_accidental)
				self.accidentals[index]=t_list

			else:

				ranged_list =range(3)


				#case: when #@ <-old note C#2
				#			 -
				#			[@]<-new note C#3
				index_to_change=index
				for i in ranged_list:
					index_to_change+=7
					if index_to_change in self.accidentals:
						t_accidental =self.accidental_type(self.new_scale_note,always_accidental=True)
						
						if index in self.accidentals:
							t_list=self.accidentals[index]

						else:
							t_list=[]
						t_list.append(t_accidental)
						self.accidentals[index]=t_list
						del self.accidentals[index_to_change]

				index_to_change=index
				for i in ranged_list:
					index_to_change-=7
					if index_to_change in self.accidentals:
						t_accidental =self.accidental_type(self.new_scale_note,always_accidental=True)
						t_list=self.accidentals[index]
						t_list.append(t_accidental)
						self.accidentals[index]=t_list
						del self.accidentals[index_to_change]

		else:


			if accidental == "#":
				print("found accidental sharp")
			elif accidental == "b":
				print("found accidental flat")

			elif accidental == "N":
				print("found accidental Natural")





			if index in self.accidentals:


				t_list=self.accidentals[index]
				t_list.append(accidental)
				self.accidentals[index]=t_list

			else:


				if self.last_played_index == index:
					#if an accidental gets added but theres a note before on the same index on same chord
					# there must be the "always accidental" sign from the note before
					old_note=self.midi_to_scale_note(self.pl[pl_index-2])
					print(f"old note {old_note}")
					
					#this makes sure that if a note is before an accidental it also shows its sign
					old_accidental=self.accidental_type(old_note[:-1],always_accidental=True)
					self.accidentals[index]=[old_accidental,accidental]

				else:

					self.accidentals[index]=[accidental]

		if index in self.accidentals:





			print(f"list of accidentals->  {(self.accidentals[index])}")


			side_count=0
			tlen=len(self.accidentals[index])


			for i in self.accidentals[index]:


				#this var controls accidentals on the same index before retroactive spacing
				inner_index=tlen-side_count


				#this var controls accidentals on the same index before retroactive spacing
				position_mult=inner_index
				side_count+=1

				
				print(f"current index: {index}")
				print(f"Last played index: {self.last_played_index}")
				print(f"inner index: {inner_index}")
				print(f"accidental: {i}")
				print(f"accidental should be jumped {self.accidental_to_jump}")
				if  (self.last_played_index-1)==index and self.was_accidental:

					#checks if an accidental is before it 
					print(f"FOUND ACCIDENTAL BEFORE position multiplier: {position_mult}")

					#i could make an addition for third accidentals on the same index but nah for now






					if inner_index==1:
						if self.accidental_to_jump==True:

							self.accidental_to_jump=False
							position_mult+=1

						else:
							self.accidental_to_jump=True
							print("aciidental should be jumpednext time")




				


				else:
					
					self.accidental_to_jump=True
					#self.accidental_to_jump2=False
					#self.accidental_jumped=False
				
				if inner_index>1:


					if self.accidental_to_jump==True:
						#position_mult+=1
						pass
					print(f"index-1:{(index-1)}")
					if (index-1) in self.accidentals:
						#could check for third accidental here
						#if len(self.accidentals[index+1]) > x ect...
						#but i assume only 2 for now
						print("has note ontop!!!!!!")
						position_mult+=1



				space_between=d_width/2
				accidental_x=(og_position+d_width/2)-((d_width*0.9)*position_mult)


				#---------------------------------------#
				#---------------------------------------#


				

				match i:
					case "#":
						print("case FOUND")
						#art for making sharps
						

						sharp_line1 = cv.Line(
							accidental_x+(d_width/3), y+((d_height/4)-d_height/7),
							accidental_x-(d_width/3), y+(d_height/4),
							paint=self.stroke_paint,

						)

						sharp_line2 = cv.Line(
							accidental_x+(d_width/3), y-((d_height/4)+d_height/7),
							accidental_x-(d_width/3), y-(d_height/4),
							paint=self.stroke_paint,

						)						

						sharp_vert1=cv.Line(
							accidental_x+(d_width/7), y-(d_width-(d_width/3)),
							accidental_x+(d_width/7), y+(d_width-(d_width/3)),
							paint=self.stroke_paint,

						)

						sharp_vert2=cv.Line(
							accidental_x-(d_width/7), y-(d_width-(d_width/3)),
							accidental_x-(d_width/7), y+(d_width-(d_width/3)),
							paint=self.stroke_paint,

						)



						return_list.append([sharp_line1,sharp_line2,sharp_vert1,sharp_vert2])

					case "b":

						#newcolor=copy.copy(self.stroke_paint)
						#newcolor.color=ft.Colors.GREEN_ACCENT_400
						
						flat_vert1=cv.Line(
							accidental_x-(d_width/20), y-(d_width-(d_width/5)),
							accidental_x-(d_width/20), y+(d_width-(d_width/1.2)),
							paint=self.stroke_paint,
							)

						flat_curve=cv.Path(
							[
								#starts here
								cv.Path.MoveTo(accidental_x-(d_width/20), y+(d_width-(d_width/1.1))),
								cv.Path.QuadraticTo(
									accidental_x+(d_width*0.5),y-(d_width*0.2),#curve towards this point			
									(accidental_x-(d_width/20 )),y+(d_width-(d_width*1.4)),#point to reach
									1 #WEIGHT
									),
								cv.Path.Close(),
							],
							paint=self.stroke_paint,
							)




						return_list.append([flat_vert1,flat_curve])
			

					case "N":

						nat_vert1=cv.Line(
							accidental_x+(d_width/5), y-(d_width-(d_width/3)),
							accidental_x+(d_width/5), y+(d_width-(d_width/3)),
							paint=self.stroke_paint,

						)

						nat_vert2=cv.Line(
							accidental_x-(d_width/5), y-(d_width-(d_width/3)),
							accidental_x-(d_width/5), y+(d_width-(d_width/3)),
							paint=self.stroke_paint,

						)

						cross_line=cv.Line(
							accidental_x-(d_width/5), y-(d_width-(d_width/3)),
							accidental_x+(d_width/5), y+(d_width-(d_width/3)),
							paint=self.stroke_paint,

						)

						return_list.append([nat_vert1,nat_vert2,cross_line])
						pass

					case "##":
						pass

					case "bb":
						pass



			self.was_accidental=True
		else:
			self.was_accidental=False
			self.accidental_to_jump=False

		try:



			self.last_played_index=index
			print("setting index for next time!!")

		except UnboundLocalError:
			print("error no pos mult")
			pass





		return_list.append([b_dot,w_dot])	
		
		return return_list






	async def resize(self):
		print("timetoresizestaff")

		
		self.height=((self.page_size["y"]/1.7)*self.width_scale)
		self.width=(self.page_size["x"]*self.width_scale)
		self.top_margin=self.height*0.18

		self.canvas.width=self.width
		self.canvas.height=self.height+self.top_margin
		self.line_spacing = (self.height/self.num_lines)-(self.height*0.013)
		self.stroke_paint.stroke_width=(self.page_size["y"]*0.01)-(self.height*0.007)
		self.left_margin = self.width*0.01
		self.right_margin = self.width*0.02



		self.semi_transparent_paint.stroke_width=(self.page_size["y"]*0.03)-(self.height*0.007)
		self.noteline = cv.Line(
				(self.width - self.right_margin)/7, self.height+self.top_margin/2,
				(self.width - self.right_margin)/7, self.top_margin/3,
				paint=self.semi_transparent_paint
				)



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

		await self.update_func(self.pl)
		self.Wbody.update()

		#await trigger_event("total_update")


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
				expand=True,
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


