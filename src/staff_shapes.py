import flet as ft
import flet.canvas as cv
#
# This notelnie when drawn wll be at some point left in the staff,
# more importantly is that is noteline spans exactly the y of the stafflines. from the top staffline to the nottom.
#
#	self.noteline = cv.Line(
#			(canvas_width - right_margin)/7, (canvas_height),
#			(canvas_width - right_margin)/7, top_margin,
#			paint=self.semi_transparent_paint
#			)
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
			if  all([shape_x, canvas_height, top_margin, paint])==None:
				return None
			
			accidental_type = 'bar'
			print("case FOUND bar")
			
			# Bar line spans exactly from top staffline to bottom staffline
			# Only needs x position - y span is always the same (stafflines)
			bar_line = cv.Line(
				shape_x, canvas_height,
				shape_x, top_margin,
				paint=paint,
			)
			
			return_list.append(([bar_line], accidental_type))


		
	
	return return_list		


	

