import flet as ft
import flet.canvas as cv
import math
#
# This notelnie when drawn wll be at some point left in the staff,
# more importantly is that is noteline spans exactly the y of the stafflines. from the top staffline to the nottom.
#
#	self.noteline = cv.Line(
#			(canvas_width - right_margin)/7, (canvas_height),
#			(canvas_width - right_margin)/7, top_margin,
#			paint=self.semi_transparent_paint
#			)
#
	
def make_flag(stem_top_x, stem_top_y, shape_width, shape_height, paint, length_scale=1):
    flag = cv.Path(
        elements=[
            cv.Path.MoveTo(x=stem_top_x, y=stem_top_y),
            cv.Path.CubicTo(
                cp1x=stem_top_x + shape_width * 0.5,  cp1y=stem_top_y + shape_height * 0.3 * length_scale,
                cp2x=stem_top_x + shape_width * 0.5,  cp2y=stem_top_y + shape_height * 0.8 * length_scale,
                x=stem_top_x + shape_width * 0.5,     y=stem_top_y + shape_height * 0.8 * length_scale,
            ),
        ],
        paint=ft.Paint(
            color=paint.color,
            stroke_width=shape_width * 0.15,
            style=ft.PaintingStyle.STROKE,
            stroke_cap=ft.StrokeCap.ROUND,
            stroke_join=ft.StrokeJoin.ROUND,
        ),
    )
    return flag


def make_stem(x1,y1,x2,y2,shape_width,paint):


	stem = cv.Line(
		x1=x1,
		y1=y1,
		x2=x2,
		y2=y2,
		paint=ft.Paint(
			color=paint.color,
			stroke_width=shape_width * 0.15,   # thick — scales with note size
			style=ft.PaintingStyle.STROKE,
			stroke_cap=ft.StrokeCap.ROUND,	   # rounded tip at the end
			stroke_join=ft.StrokeJoin.ROUND,
		),
	)
	return stem



class Notehead:
	"""
	A rotated ellipse notehead built from 4 rational quadratic bezier arcs.
	Exact ellipse geometry via w = cos(π/4).

	Usage:
		head = Notehead(cx=100, cy=200, width=20, height=13, theta=-math.pi/6)
		head = Notehead(cx=100, cy=200, width=20, height=13, hollow=True)
		shapes = head.shapes
		stem_up_point	= head.stem_up_attach	 # P0 — right
		stem_down_point = head.stem_down_attach  # P2 — left
	"""
	W = math.cos(math.pi / 4)  # ≈ 0.7071 — exact ellipse quarter

	def __init__(
		self,
		cx: float,
		cy: float,
		width: float = 20,
		height: float = 13,
		theta: float = -math.pi / 6,
		paint: ft.Paint = None,
		hollow: bool = False,

	):
		self.cx = cx
		self.cy = cy
		self.width = width
		self.height = height
		self.theta = theta
		self.hollow = hollow

		if paint is None:
			paint = ft.Paint(
				color=ft.Colors.BLACK,
				style=ft.PaintingStyle.FILL,
			)

		if hollow:
			self.paint = ft.Paint(
				color=paint.color,
				style=ft.PaintingStyle.STROKE,
				stroke_width=(width)*0.30,
				stroke_join=ft.StrokeJoin.ROUND,
			)
		else:
			self.paint = paint

		self._compute_geometry()
		self._build_shapes()




	def _compute_geometry(self):
		a = self.width / 2
		b = self.height / 2
		cx, cy = self.cx, self.cy
		cos_t = math.cos(self.theta)
		sin_t = math.sin(self.theta)

		self.P0   = (cx + a*cos_t,			  cy + a*sin_t)
		self.P1   = (cx - b*sin_t,			  cy + b*cos_t)
		self.P2   = (cx - a*cos_t,			  cy - a*sin_t)
		self.P3   = (cx + b*sin_t,			  cy - b*cos_t)

		self.CP01 = (cx + a*cos_t - b*sin_t,  cy + a*sin_t + b*cos_t)
		self.CP12 = (cx - a*cos_t - b*sin_t,  cy - a*sin_t + b*cos_t)
		self.CP23 = (cx - a*cos_t + b*sin_t,  cy - a*sin_t - b*cos_t)
		self.CP30 = (cx + a*cos_t + b*sin_t,  cy + a*sin_t - b*cos_t)

	def _build_shapes(self):
		P0, P1, P2, P3 = self.P0, self.P1, self.P2, self.P3
		CP01, CP12, CP23, CP30 = self.CP01, self.CP12, self.CP23, self.CP30
		w = self.W

		self.path = cv.Path(
			elements=[
				cv.Path.MoveTo(x=P0[0],   y=P0[1]),
				cv.Path.QuadraticTo(cp1x=CP01[0], cp1y=CP01[1], x=P1[0], y=P1[1], w=w),
				cv.Path.QuadraticTo(cp1x=CP12[0], cp1y=CP12[1], x=P2[0], y=P2[1], w=w),
				cv.Path.QuadraticTo(cp1x=CP23[0], cp1y=CP23[1], x=P3[0], y=P3[1], w=w),
				cv.Path.QuadraticTo(cp1x=CP30[0], cp1y=CP30[1], x=P0[0], y=P0[1], w=w),
				cv.Path.Close(),
			],
			paint=self.paint,
		)

	@property
	def shapes(self) -> list:
		return [self.path]

	@property
	def stem_up_attach(self) -> tuple:
		return self.P0

	@property
	def stem_down_attach(self) -> tuple:
		return self.P2



def shape_constructor(
		shape_x=None,
		shape_y=None,
		shape_width=None,
		shape_height=None,
		type=None,
		paint=None,
		canvas_width=None,
		canvas_height=None,
		top_margin=None,
		left_margin=None,
		right_margin=None,
		dotted=False
		):
	# x and y are the coords of the note
	# width and height are the same
	return_list = []
	
	if not paint:
		paint = ft.Paint(
			color=ft.Colors.BLACK,
			style=ft.PaintingStyle.FILL
		)
	
	white_paint = ft.Paint(
		color=ft.Colors.WHITE,
		style=ft.PaintingStyle.FILL
	)
	

	if not type:
		return None
	
	match type:
		case 'quarter':
			import math
			if not all([shape_x, shape_y, shape_width, shape_height]):
				return None

			notehead = Notehead(shape_x, shape_y, shape_width, shape_height, -math.pi/6, paint)
			offsetX, offsetY = notehead.stem_down_attach
			stem_x, stem_y = notehead.stem_up_attach
			stem_height = shape_height * 2.5
			stem_top_x = stem_x
			stem_top_y = stem_y - stem_height

			# STEM
			stem_x1 = stem_x + ((offsetX - stem_x) * .05)
			stem_y1 = stem_y + ((offsetY - stem_y) * .3)
			stem_x2 = stem_x + ((offsetX - stem_x) * .05)
			stem_y2 = stem_top_y
			stem = make_stem(stem_x1, stem_y1, stem_x2, stem_y2, shape_width, paint)

			return_list.append(([notehead.shapes[0], stem], 'quarter'))		

		case '32nd':
			import math
			if not all([shape_x, shape_y, shape_width, shape_height]):
				return None

			notehead = Notehead(shape_x, shape_y, shape_width, shape_height, -math.pi/6, paint)
			offsetX, offsetY = notehead.stem_down_attach
			stem_x, stem_y = notehead.stem_up_attach
			stem_height = shape_height * 2.5
			stem_top_x = stem_x
			stem_top_y = stem_y - stem_height

			# STEM
			stem_x1 = stem_x + ((offsetX - stem_x) * .05)
			stem_y1 = stem_y + ((offsetY - stem_y) * .3)
			stem_x2 = stem_x + ((offsetX - stem_x) * .05)
			stem_y2 = stem_top_y
			stem = make_stem(stem_x1, stem_y1, stem_x2, stem_y2, shape_width, paint)

			# FLAGS — two straight leaning lines
			flag_dx = shape_width * 0.6   # how far right they lean
			flag_dy = shape_height * 0.8  # how far down they drop
			flag_gap = shape_height * 0.4 # vertical gap between the two flags

			flag = make_stem(
				stem_top_x,            stem_top_y,
				stem_top_x + flag_dx,  stem_top_y + flag_dy,
				shape_width, paint
			)

			flag_dy = shape_height * 0.75  # how far down they drop
			flag_dx = shape_width * 0.5   # how far right they lean
			flag2 = make_stem(
				stem_top_x,            stem_top_y + flag_gap,
				stem_top_x + flag_dx,  stem_top_y + flag_gap + flag_dy,
				shape_width, paint
			)
			flag_dx = shape_width * 0.45   # how far right they lean
			
			flag_gap = shape_height * 0.45 # vertical gap between the two flags
			flag3 = make_stem(
				stem_top_x,            stem_top_y + flag_gap*2,
				stem_top_x + flag_dx,  stem_top_y + flag_gap*2 + flag_dy,
				shape_width, paint
			)
			return_list.append(([notehead.shapes[0], stem, flag, flag2,flag3], 'thirtysecond'))		
		case '16th':

			import math
			if not all([shape_x, shape_y, shape_width, shape_height]):
				return None

			notehead = Notehead(shape_x+ shape_width/2, shape_y, shape_width, shape_height, -math.pi/6, paint)
			offsetX, offsetY = notehead.stem_down_attach
			stem_x, stem_y = notehead.stem_up_attach
			stem_height = shape_height * 2.5
			stem_top_x = stem_x
			stem_top_y = stem_y - stem_height

			# STEM
			stem_x1 = stem_x + ((offsetX - stem_x) * .05)
			stem_y1 = stem_y + ((offsetY - stem_y) * .3)
			stem_x2 = stem_x + ((offsetX - stem_x) * .05)
			stem_y2 = stem_top_y
			stem = make_stem(stem_x1, stem_y1, stem_x2, stem_y2, shape_width, paint)

			# FLAGS — two straight leaning lines
			flag_dx = shape_width * 0.6   # how far right they lean
			flag_dy = shape_height * 0.8  # how far down they drop
			flag_gap = shape_height * 0.6 # vertical gap between the two flags

			flag = make_stem(
				stem_top_x,            stem_top_y,
				stem_top_x + flag_dx,  stem_top_y + flag_dy,
				shape_width, paint
			)

			flag_dx = shape_width * 0.5   # how far right they lean
			flag2 = make_stem(
				stem_top_x,            stem_top_y + flag_gap,
				stem_top_x + flag_dx,  stem_top_y + flag_gap + flag_dy,
				shape_width, paint
			)

			return_list.append(([notehead.shapes[0], stem, flag, flag2], 'sixteenth'))		






		case 'eighth':
			import math
			if not all([shape_x, shape_y, shape_width, shape_height]):
				return None

			# shape_x, shape_y	= center of the notehead
			# shape_width		 = full extent along major axis  (e.g. 20)
			# shape_height		 = full extent along minor axis  (e.g. 13)
			# Tilt: noteheads conventionally lean ~30° counter-clockwise from horizontal
			


			notehead=Notehead(shape_x,shape_y,shape_width,shape_height,-math.pi/6,paint)
			# Stem: rises from the right attach point upward
			offsetX,offsetY=notehead.stem_down_attach
			stem_x, stem_y = notehead.stem_up_attach
			stem_height = shape_height * 2.5
			stem_top_x = stem_x
			stem_top_y = stem_y - stem_height

			#STEM

			stem_x1=stem_x+((offsetX-stem_x)*.05)
			stem_y1=stem_y+((offsetY-stem_y)*.3)
			stem_x2=stem_x+((offsetX-stem_x)*.05)
			stem_y2=stem_top_y
			stem=make_stem(stem_x1,stem_y1,stem_x2,stem_y2,shape_width,paint)
			
			#FLAG
			flag=make_flag(stem_top_x,stem_top_y,shape_width,shape_height,paint) 
			# Flag: swoops from the top of the stem down and to the right
	
			return_list.append(([notehead.shapes[0], stem, flag], 'eighth'))
		



		case 'half':
			import math
			if not all([shape_x, shape_y, shape_width, shape_height]):
				return None

			# shape_x, shape_y	= center of the notehead
			# shape_width		 = full extent along major axis  (e.g. 20)
			# shape_height		 = full extent along minor axis  (e.g. 13)
			# Tilt: noteheads conventionally lean ~30° counter-clockwise from horizontal
			


			notehead=Notehead(shape_x,shape_y,shape_width*0.8,shape_height*0.7 ,-math.pi/6,paint,hollow=True)
			# Stem: rises from the right attach point upward
			offsetX,offsetY=notehead.stem_down_attach
			stem_x, stem_y = notehead.stem_up_attach
			stem_height = shape_height * 2.5
			stem_top_x = stem_x
			stem_top_y = stem_y - stem_height

			#STEM

			stem_x1=stem_x-((offsetX-stem_x)*.069)
			stem_y1=stem_y+((offsetY-stem_y)*.3)
			stem_x2=stem_x-((offsetX-stem_x)*.069)
			stem_y2=stem_top_y
			stem=make_stem(stem_x1,stem_y1,stem_x2,stem_y2,shape_width,paint)
			
			#FLAG
			flag=make_flag(
				stem_x-((offsetX-stem_x)*.069),
				stem_top_y,
				shape_width,
				shape_height,
				paint
				) 
			# Flag: swoops from the top of the stem down and to the right
	
			return_list.append(([notehead.shapes[0], stem, flag], 'half'))
		










		case 'whole':
			# Check required variables
			if not all([shape_x, shape_y, shape_width, shape_height]):
				return None
			
			b_dot = cv.Oval(
				x=shape_x,
				y=shape_y - (shape_height/2),
				width=shape_width,
				height=shape_height,
				paint=paint
			)
			
			w_dot = cv.Oval(
				x=shape_x + shape_height/2.3,
				y=shape_y - shape_width/4,
				width=shape_height/2.2,
				height=shape_width/2,
				paint=white_paint
			)
			
			return_list.append(([b_dot, w_dot], 'whole'))
		case "#":
			# Check required variables
			if not all([shape_x, shape_y, shape_width, shape_height, paint]):
				return None
			
			accidental_type = '#'
			print("case FOUND sharp")
			
			sharp_line1 = cv.Line(
				shape_x + (shape_width/3), shape_y + ((shape_height/4) - shape_height/7),
				shape_x - (shape_width/3), shape_y + (shape_height/4),
				paint=paint,
			)

			sharp_line2 = cv.Line(
				shape_x + (shape_width/3), shape_y - ((shape_height/4) + shape_height/7),
				shape_x - (shape_width/3), shape_y - (shape_height/4),
				paint=paint,
			)

			sharp_vert1 = cv.Line(
				shape_x + (shape_width/7), shape_y - (shape_width - (shape_width/3)),
				shape_x + (shape_width/7), shape_y + (shape_width - (shape_width/3)),
				paint=paint,
			)

			sharp_vert2 = cv.Line(
				shape_x - (shape_width/7), shape_y - (shape_width - (shape_width/3)),
				shape_x - (shape_width/7), shape_y + (shape_width - (shape_width/3)),
				paint=paint,
			)

			return_list.append(([sharp_line1, sharp_line2, sharp_vert1, sharp_vert2], accidental_type))

		case "b":
			# Check required variables
			if not all([shape_x, shape_y, shape_width, paint]):
				return None
			
			accidental_type = 'b'
			print("case FOUND flat")
			
			flat_vert1 = cv.Line(
				shape_x - (shape_width/20), shape_y - (shape_width - (shape_width/4)),
				shape_x - (shape_width/20), shape_y + (shape_width - (shape_width/1.4)),
				paint=paint,
			)

			flat_curve = cv.Path(
				[
					cv.Path.MoveTo(shape_x - (shape_width/20), shape_y + (shape_width - (shape_width/1.3))),
					cv.Path.QuadraticTo(
						shape_x + (shape_width*0.6), shape_y - (shape_width*0.2),
						(shape_x - (shape_width/20)), shape_y + (shape_width - (shape_width*1.2)),
						1
					),
					cv.Path.Close(),
				],
				paint=paint,
			)

			return_list.append(([flat_vert1, flat_curve], accidental_type))

		case "N":
			# Check required variables
			if not all([shape_x, shape_y, shape_width, paint]):
				return None
			
			accidental_type = 'N'
			print("case FOUND natural")
			
			nat_vert1 = cv.Line(
				shape_x + (shape_width/5), shape_y - (shape_width - (shape_width/2)),
				shape_x + (shape_width/5), shape_y + (shape_width - (shape_width/2)),
				paint=paint,
			)

			nat_vert2 = cv.Line(
				shape_x - (shape_width/5), shape_y - (shape_width - (shape_width/2)),
				shape_x - (shape_width/5), shape_y + (shape_width - (shape_width/2)),
				paint=paint,
			)

			cross_line = cv.Line(
				shape_x - (shape_width/5), shape_y - (shape_width - (shape_width/2)),
				shape_x + (shape_width/5), shape_y + (shape_width - (shape_width/2)),
				paint=paint,
			)

			return_list.append(([nat_vert1, nat_vert2, cross_line], accidental_type))


		case 0:
			import math
			if not all([shape_x, shape_y, shape_width, shape_height]):
				return None

			# shape_x, shape_y	= center of the notehead
			# shape_width		 = full extent along major axis  (e.g. 20)
			# shape_height		 = full extent along minor axis  (e.g. 13)
			# Tilt: noteheads conventionally lean ~30° counter-clockwise from horizontal
			

			notehead=Notehead(shape_x,shape_y,shape_width,shape_height,-math.pi/6,paint)
			# Stem: rises from the right attach point upward
			offsetX,offsetY=notehead.stem_down_attach
			stem_x, stem_y = notehead.stem_up_attach
			stem_height = shape_height * 2.5
			stem_top_x = stem_x
			stem_top_y = stem_y - stem_height

			#STEM

			stem_x1=stem_x+((offsetX-stem_x)*.05)
			stem_y1=stem_y+((offsetY-stem_y)*.3)
			stem_x2=stem_x+((offsetX-stem_x)*.05)
			stem_y2=stem_top_y
			stem=make_stem(stem_x1,stem_y1,stem_x2,stem_y2,shape_width,paint)
			
			#FLAG
			flag=make_flag(stem_top_x,stem_top_y,shape_width,shape_height,paint) 
			# Flag: swoops from the top of the stem down and to the right


			# SLASH (grace note slash)
			slash_length = shape_height * 0.9
			slash_offset_down = shape_height * 0.4  # move slightly below stem top

			slash = cv.Line(
				x1=stem_x2 - shape_width * 0.4,
				y1=stem_top_y + slash_offset_down,
				x2=stem_x2 + shape_width * 0.4,
				y2=stem_top_y + slash_offset_down + slash_length * 0.3,
				paint=ft.Paint(
					color=paint.color,
					stroke_width=shape_width * 0.12,  # slightly thinner than stem
					style=ft.PaintingStyle.STROKE,
					stroke_cap=ft.StrokeCap.ROUND,
				)
			)



			return_list.append(([notehead.shapes[0], stem, flag,slash], 'grace'))
		


		case "##":
			# Check required variables
			if not all([shape_x, shape_y, shape_width, paint]):
				return None
			
			accidental_type = '##'
			print("case FOUND double sharp")
			
			cross_line1 = cv.Line(
				shape_x - (shape_width/5), shape_y - (shape_width - (shape_width/2)),
				shape_x + (shape_width/5), shape_y + (shape_width - (shape_width/2)),
				paint=paint,
			)
			
			cross_line2 = cv.Line(
				shape_x + (shape_width/5), shape_y - (shape_width - (shape_width/2)),
				shape_x - (shape_width/5), shape_y + (shape_width - (shape_width/2)),
				paint=paint,
			)
			
			return_list.append(([cross_line1, cross_line2], accidental_type))

		case "bb":
			# Check required variables
			if not all([shape_x, shape_y, shape_width, paint]):
				return None
			
			accidental_type = 'bb'
			print("case FOUND double flat")
			
			flat_vert1 = cv.Line(
				shape_x - (shape_width/2.3), shape_y - (shape_width - (shape_width/4)),
				shape_x - (shape_width/2.3), shape_y + (shape_width - (shape_width/1.4)),
				paint=paint,
			)

			flat_curve1 = cv.Path(
				[
					cv.Path.MoveTo(shape_x - (shape_width/2.3), shape_y + (shape_width - (shape_width/1.3))),
					cv.Path.QuadraticTo(
						shape_x + (shape_width*0.27), shape_y - (shape_width*0.2),
						(shape_x - (shape_width/2.3)), shape_y + (shape_width - (shape_width*1.2)),
						1
					),
					cv.Path.Close(),
				],
				paint=paint,
			)
			
			flat_vert2 = cv.Line(
				shape_x - (shape_width/10), shape_y - (shape_width - (shape_width/4)),
				shape_x - (shape_width/10), shape_y + (shape_width - (shape_width/1.4)),
				paint=paint,
			)

			flat_curve2 = cv.Path(
				[
					cv.Path.MoveTo(shape_x - (shape_width/10), shape_y + (shape_width - (shape_width/1.3))),
					cv.Path.QuadraticTo(
						shape_x + (shape_width*0.5), shape_y - (shape_width*0.2),
						(shape_x - (shape_width/10)), shape_y + (shape_width - (shape_width*1.2)),
						1
					),
					cv.Path.Close(),
				],
				paint=paint,
			)
			
			return_list.append(([flat_vert1, flat_curve1, flat_vert2, flat_curve2], accidental_type))
		
		case "bar":
			# Check required variables
			if	all([shape_x, canvas_height, top_margin, paint])==None:
				return None
			
			accidental_type = 'bar'
			print("case FOUND bar")
			
			# Bar line spans exactly from top staffline to bottom staffline
			# Only needs x position - y span is always the same (stafflines)
			bar_line = cv.Line(
				shape_x, canvas_height -top_margin*1.2,
				shape_x, top_margin,
				paint=paint,
			)
			
			return_list.append(([bar_line], accidental_type))
		case _:
			print(f"unknown time of {type}")

# after all your cases, before returning
	if dotted:
		# position dot to the right of the notehead
		dot = cv.Circle(
			x=shape_x + shape_width * 0.75,
			y=shape_y,
			radius=shape_width * 0.1,
			paint=paint
		)
		return_list[0][0].append(dot)


	return return_list		


	

