import flet as ft
from DefaultStructures import Default_Page, chord_display, interval_display,visual_piano,staff
from mingus.core import notes, chords
from Event_Dispatch_Bus import trigger_event 
from midiFuncs import midi_to_note, strip_octave
from pychord import find_chords_from_notes, Chord, notes_to_positions
import time



#from ListenToMidi import midi_listener

class App_Inst(Default_Page):
	

	def __init__(self):

		super().__init__()
		#self.body.update()
		self.body.expand=True


		##EVENTUALLY I WILL ADD A BETTER WAY TO ADD AND NOT ADD WIDGETS BUT FOR NOW ALL OF THEM WILL BE ADDED##
		self.last_chord_notes = []
		self.last_chord_notes_o = []
		self.last_root=''
		self.last_keys=[]
		self.cd = chord_display()
		self.id=interval_display()
		self.piano = visual_piano()
		self.staff = staff(0.3,1,0.4,False,False)
		self.name = "chordID"

		##WARINING
		self.widgets=[self.cd,self.id,self.piano,self.staff]

		#self.side_menu.items=[]
		self.body.expand=True
		self.body.controls[0].content = ft.Column(

			#alignment=ft.MainAxisAlignment.CENTER,
			horizontal_alignment=ft.CrossAxisAlignment.CENTER,
			controls=[

				ft.Container(
					self.cd.Wbody,
					bgcolor=ft.Colors.RED_50,
					alignment=ft.alignment.center,
					expand=True,

				),
				ft.Container(
					self.staff.Wbody,
					bgcolor=ft.Colors.RED_200,
					alignment=ft.alignment.center_right,
					# expand=True,
					#padding=ft.padding.only(right=100)
				),
					#spacer
				ft.Container(
					#expand=True


				),

				ft.Container(
					self.id.Wbody,
					bgcolor=ft.Colors.RED_50,
					alignment=ft.alignment.center),
				ft.Container(
					self.piano.Wbody,
					bgcolor=ft.Colors.RED_50,
					alignment=ft.alignment.bottom_center,
					#expand=True,
					),

				]

			)

		self.sidebar.content.controls.append(self.staff.sidebar_content)









		#self.All_Content.update()
 
	async def note_update(e,self):
		start_time = time.time()

		#self.body.content = ft.Row(alignment=ft.MainAxisAlignment.CENTER,controls=[self.KD.body])
		

		        
		nl = []
		nlo =[]
		chordList = []
		parts_list = []
		ntp = []
		for pitch in sorted(self.ml.active_notes.keys()):
			print(f"pitch: {pitch}")

			nl.append(strip_octave(str(midi_to_note(pitch))))
			nlo.append(str(midi_to_note(pitch)))
		



		try:
            
			chordList, parts_list = find_chords_from_notes(nl)

			if len(chordList) > 0:
				self.last_chord_notes=nl
				self.last_chord_notes_o=nlo
				self.last_root = parts_list[0]["temp_root"]
				ntp= notes_to_positions(nl, self.last_root)


		except Exception as e:

			print(f"Chord detection failed: {e}")




		new_nlo = [note for note in nlo if note not in self.last_chord_notes_o]
		

		elapsed = (time.time() - start_time) * 1000  # milliseconds
		print(f"update_func preTOTAL took {elapsed:.2f} ms")


		self.cd.update_func(nl,nlo,chordList, parts_list,)
		self.cd.Wbody.update()
		elapsed = (time.time() - start_time) * 1000  # milliseconds
		print(f"update_func after chord_display display took {elapsed:.2f} ms")
		#self.All_Content.update()
		
		self.id.update_func(nl,nlo,chordList, parts_list,self.last_chord_notes,self.last_chord_notes_o,new_nlo,ntp,self.last_root)
		self.id.Wbody.update()
		elapsed = (time.time() - start_time) * 1000  # milliseconds
		print(f"update_func after interval display took {elapsed:.2f} ms")



		self.piano.update_func(nl,nlo,chordList, parts_list,self.last_chord_notes,self.last_chord_notes_o,new_nlo,ntp,self.last_root,self.last_keys)
		self.piano.Wbody.update()
		
		elapsed = (time.time() - start_time) * 1000  # milliseconds
		print(f"update_func preTOTAL(after piano) took {elapsed:.2f} ms")

		##for staff
		pl =[]
		print(f"self.ml.active_notes: {self.ml.active_notes.keys()}")
		for pitch in sorted(self.ml.active_notes.keys()):
			print(f"pitch: {pitch}")
			pl.append(pitch)


		await self.staff.update_func(pl)
		await self.staff.tick(updated=True)
		self.staff.Wbody.update()


		#self.All_Content.update()
		self.last_keys=nlo





	



 
