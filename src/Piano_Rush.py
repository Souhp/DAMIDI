import flet as ft
from DefaultStructures import Default_Page, staff
import flet.canvas as cv
import time
from midiFuncs import midi_to_note


class App_Inst(Default_Page):





	def __init__(self, mainPage,width=1200, height=120, line_spacing=24):
		super().__init__()
		self.staff = staff(mainPage)
		self.name = "PRUSH"

		self.widgets=[self.staff]
		# Add the container to the page body
		self.body.controls[0].content = ft.Column(controls=[self.staff.Wbody],horizontal_alignment=ft.CrossAxisAlignment.CENTER)

		


		#add widget options TO SIDEBAR##
		self.sidebar.content.controls.append(self.staff.sidebar_content)




	async def note_update(self,e):
		start_time = time.time()

		#self.body.content = ft.Row(alignment=ft.MainAxisAlignment.CENTER,controls=[self.KD.body])
		

		        

		pl =[]
		print(f"self.ml.active_notes: {self.ml.active_notes.keys()}")
		for pitch in sorted(self.ml.active_notes.keys()):
			print(f"pitch: {pitch}")
			pl.append(pitch)

		await self.staff.update_func(pl)
		await self.staff.tick(updated_externally=True)
		self.staff.Wbody.update()



		

