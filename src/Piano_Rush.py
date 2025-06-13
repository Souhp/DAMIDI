import flet as ft
from DefaultStructures import Default_Page, staff
import flet.canvas as cv


class App_Inst(Default_Page):





	def __init__(self, width=1200, height=120, line_spacing=24):
		super().__init__()
		self.staff = staff()
		# Add the container to the page body
		self.body.controls[0].content = ft.Column(controls=[self.staff.Wbody])

		self.from_field = ft.TextField(
		    value="2",
		    input_filter=ft.InputFilter(regex_string=r"[0-9]*", replacement_string="")
		)

		self.to_field = ft.TextField(
		    value="6",
		    input_filter=ft.InputFilter(regex_string=r"[0-9]*", replacement_string="")
		)

		range_row = ft.Row(
		    controls=[
		        ft.Container(content=self.from_field, alignment=ft.alignment.center, width=50),
		        ft.Text("-TO-"),
		        ft.Container(content=self.to_field, alignment=ft.alignment.center, width=50)
		    ],
		    wrap=True
		)


		self.sidebar.content.controls.append(range_row)

		self.from_field.on_change = lambda e: change_octave_field(self.to_field,self.from_field,self,"up")
		self.to_field.on_change = lambda e: change_octave_field(self.from_field,self.to_field,self,"down")

def change_octave_field(x,y,z,param):

	if param=="up":
		x.value=int(y.value)+4

	else:
		x.value=int(y.value)-4

	z.sidebar.update()
