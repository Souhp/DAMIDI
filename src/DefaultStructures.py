import flet as ft
from Event_Dispatch_Bus import trigger_event
import PageMemory
from midiFuncs import midi_listener,midi_to_note,strip_octave
import asyncio
from mingus.core import notes, chords
from pychord import find_chords_from_notes, Chord, notes_to_positions
import flet.canvas as cv
from typing import List
class SearchField:
	def __init__(self,align: ft.MainAxisAlignment):

		SearchField.TextInput = ft.TextField(hint_text="type here")
		SearchField.SearchButton = ft.FloatingActionButton(text="Search")
		SearchField.Row = ft.Row(

			controls=[SearchField.TextInput,SearchField.SearchButton],
			alignment=align,

			)



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

		self.ml = None
		self.listener=None
		self.sidebar = Sidebar()
		self.sidebar.visible=False

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



class chord_display:
	def __init__(self):
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




class interval_display:
	def __init__(self):
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
		
		



class visual_piano:
	def __init__(self, num_keys=88):
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
			

class staff():
	def __init__(self, width=1200, height=120, line_spacing=24,stroke_width=6,show_bass=True):
		super().__init__()
		self.width = width
		self.height = height
		self.line_spacing = line_spacing
		self.num_lines = 5
		self.left_margin = 20
		self.right_margin = 20
		self.top_margin = 20
		self.show_bass=show_bass

		self.Wbody = ft.Container(
			#bgcolor=ft.Colors.AMBER_500,
			alignment=ft.alignment.center,
			#expand=True,
		)
		semi_transparent_paint = ft.Paint(
			style=ft.PaintingStyle.FILL,
			color="#8C008DFF",  # full hex with alpha
			stroke_width=8
		)
		stroke_paint = ft.Paint(
			stroke_width=6,
			style=ft.PaintingStyle.STROKE,
			color=ft.Colors.BLACK
		)

		# Generate the staff lines
		staff_lines = []
		for i in range(self.num_lines):
			y = self.top_margin + i * self.line_spacing
			staff_lines.append(cv.Line(
				self.left_margin, y,
				self.width - self.right_margin, y,
				paint=stroke_paint
			))

		# Choose which line to place the dot on (e.g., 3rd line = index 2)
		line_index = 3
		y = self.top_margin + line_index * self.line_spacing
		x = self.width // 2  # Center of the canvas

		# Create the dot as a small red filled circle
		dot = cv.Circle(
			x=x,
			y=y,
			radius=5,
			paint=ft.Paint(
				color=ft.Colors.RED,
				style=ft.PaintingStyle.FILL
			)
		)


		noteline = cv.Line(
				(self.width - self.right_margin)/7, self.height+self.top_margin,
				(self.width - self.right_margin)/7, 0,
				paint=semi_transparent_paint
				)

		# Create the canvas with staff lines + dot
		canvas = cv.Canvas(
			staff_lines + [dot] +[noteline],
			width=(self.width+20),
			height=(self.height+20),
			expand=True
		)

		# Add the canvas to a container and center it


		t_row=ft.Row(

			controls=[
				ft.Container(
					content=canvas,
					#alignment=ft.alignment.center,
					bgcolor=ft.Colors.WHITE
					),
				ft.Container(
					content=ft.Image(
						src="treb.PNG",
						fit=ft.ImageFit.SCALE_DOWN,
						height=(self.height*1.8),
						),
					padding=ft.padding.only(bottom=7)

					)
				],
			#alignment=ft.MainAxisAlignment.CENTER,
			spacing=(-self.width)

			)

		b_row=ft.Row(

			controls=[
				ft.Container(
					content=canvas,
					#alignment=ft.alignment.center,
					bgcolor=ft.Colors.WHITE
					),
				ft.Container(
					content=ft.Image(
						src="bass.PNG",
						fit=ft.ImageFit.SCALE_DOWN,
						height=(self.height/1.3),
						),
					padding=ft.padding.only(bottom=12)

					)
				],
			#alignment=ft.MainAxisAlignment.CENTER,
			spacing=(-self.width/1.03)

			)






		# Add the container to the page body
		self.Wbody.content = ft.Column(controls=[ctrl for ctrl in [t_row,self.show_bass and b_row] if ctrl])




class Sidebar(ft.Container):

	def __init__(self,items=[],):

		itemlist=[

			ft.Row(
				[
					ft.Text("SETTINGS",size=30,weight=ft.FontWeight.BOLD),
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
