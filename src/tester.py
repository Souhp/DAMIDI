import flet as ft
import flet.canvas as cv




def main(page: ft.Page):
	t = ft.Text(value="Hello, world!", color="green")


	treb_x = 1
	treb_y = 1

	treb_ox = 0
	treb_oy = 0


	trebel_shapes=[

		cv.Path(


			[
		# Start at bottom swirl
	cv.Path.MoveTo(57.9375* treb_x + treb_ox, 421.875 * treb_y + treb_oy),
	cv.Path.QuadraticTo(50.3438 * treb_x + treb_ox, 421.875 * treb_y + treb_oy, 44.7188 * treb_x + treb_ox, 418.2188 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(39.0938 * treb_x + treb_ox, 414.5625 * treb_y + treb_oy, 36.2812 * treb_x + treb_ox, 407.6719 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(33.4688 * treb_x + treb_ox, 400.7812 * treb_y + treb_oy, 33.4688 * treb_x + treb_ox, 393.75 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(33.4688 * treb_x + treb_ox, 387.2812 * treb_y + treb_oy, 35.7188 * treb_x + treb_ox, 381.7969 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(37.9688 * treb_x + treb_ox, 376.3125 * treb_y + treb_oy, 42.75 * treb_x + treb_ox, 373.2188 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(47.5312 * treb_x + treb_ox , 370.125 * treb_y + treb_oy, 53.7188 * treb_x + treb_ox, 370.125 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(59.625 * treb_x + treb_ox, 370.4062 * treb_y + treb_oy, 63.8438 * treb_x + treb_ox, 372.5156 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(68.0625 * treb_x + treb_ox, 374.625 * treb_y + treb_oy, 70.7344 * treb_x + treb_ox, 378.7031 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(73.4062 * treb_x + treb_ox, 382.7812 * treb_y + treb_oy, 73.4062 * treb_x + treb_ox, 389.8125 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(73.4062 * treb_x + treb_ox, 397.125 * treb_y + treb_oy, 70.7344 * treb_x + treb_ox, 401.2031 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(68.0625 * treb_x + treb_ox, 405.2812 * treb_y + treb_oy, 64.2656 * treb_x + treb_ox, 407.3906 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(60.4688 * treb_x + treb_ox, 409.5 * treb_y + treb_oy, 54.8438 * treb_x + treb_ox, 409.5 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(52.0312 * treb_x + treb_ox, 409.5 * treb_y + treb_oy, 50.0625 * treb_x + treb_ox, 408.6562 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(48.0938 * treb_x + treb_ox, 407.8125 * treb_y + treb_oy, 45.8438 * treb_x + treb_ox, 405.5625 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(46.9688 * treb_x + treb_ox, 409.7812 * treb_y + treb_oy, 50.2031 * treb_x + treb_ox, 412.1719 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(53.4375 * treb_x + treb_ox, 414.5625 * treb_y + treb_oy, 57.9375 * treb_x + treb_ox, 414.5625 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(65.3906 * treb_x + treb_ox, 414.5625 * treb_y + treb_oy, 71.0859 * treb_x + treb_ox, 409.6406 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(76.7812 * treb_x + treb_ox, 404.7188 * treb_y + treb_oy, 80.3672 * treb_x + treb_ox, 391.5 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(83.9531 * treb_x + treb_ox, 378.2812 * treb_y + treb_oy, 84.7969 * treb_x + treb_ox, 360 * treb_y + treb_oy, 1),
	cv.Path.LineTo(81 * treb_x + treb_ox, 360 * treb_y + treb_oy),
	cv.Path.QuadraticTo(60.1875 * treb_x + treb_ox, 360 * treb_y + treb_oy, 46.4062 * treb_x + treb_ox, 355.7812 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(32.625 * treb_x + treb_ox, 351.5625 * treb_y + treb_oy, 24.1875 * treb_x + treb_ox, 339.4688 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(15.75 * treb_x + treb_ox, 327.375 * treb_y + treb_oy, 15.75 * treb_x + treb_ox, 309.9375 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(15.75 * treb_x + treb_ox, 296.4375 * treb_y + treb_oy, 20.8125 * treb_x + treb_ox, 279 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(27 * treb_x + treb_ox, 264.375 * treb_y + treb_oy, 36.2812 * treb_x + treb_ox, 252 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(45.5625 * treb_x + treb_ox, 239.625 * treb_y + treb_oy, 59.625 * treb_x + treb_ox, 226.6875 * treb_y + treb_oy, 1),
	cv.Path.LineTo(67.9219 * treb_x + treb_ox, 217.9688 * treb_y + treb_oy),
	cv.Path.LineTo(64.125 * treb_x + treb_ox, 204.1875 * treb_y + treb_oy),
	cv.Path.QuadraticTo(57.9375 * treb_x + treb_ox, 182.25 * treb_y + treb_oy, 55.9688 * treb_x + treb_ox, 172.9688 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(54 * treb_x + treb_ox, 163.6875 * treb_y + treb_oy, 54 * treb_x + treb_ox, 157.5 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(54 * treb_x + treb_ox, 149.625 * treb_y + treb_oy, 56.5312 * treb_x + treb_ox, 139.2188 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(59.0625 * treb_x + treb_ox, 128.8125 * treb_y + treb_oy, 66.9375 * treb_x + treb_ox, 124.0312 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(74.8125 * treb_x + treb_ox, 119.25 * treb_y + treb_oy, 80.4375 * treb_x + treb_ox, 119.25 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(87.1875 * treb_x + treb_ox, 119.25 * treb_y + treb_oy, 93.6562 * treb_x + treb_ox, 125.1562 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(100.125 * treb_x + treb_ox, 131.0625 * treb_y + treb_oy, 103.2188 * treb_x + treb_ox, 142.5938 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(106.3125 * treb_x + treb_ox, 154.125 * treb_y + treb_oy, 106.3125 * treb_x + treb_ox, 165.375 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(106.3125 * treb_x + treb_ox, 174.375 * treb_y + treb_oy, 104.625 * treb_x + treb_ox, 184.7812 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(102.9375 * treb_x + treb_ox, 195.1875 * treb_y + treb_oy, 98.0156 * treb_x + treb_ox, 205.0312 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(93.0938 * treb_x + treb_ox, 214.875 * treb_y + treb_oy, 85.7812 * treb_x + treb_ox, 223.3125 * treb_y + treb_oy, 1),
	cv.Path.LineTo(83.5312 * treb_x + treb_ox, 225.9844 * treb_y + treb_oy),
	cv.Path.QuadraticTo(86.0625 * treb_x + treb_ox, 241.1719 * treb_y + treb_oy, 88.875 * treb_x + treb_ox, 258.75 * treb_y + treb_oy, 1),
	cv.Path.LineTo(90.8438 * treb_x + treb_ox, 272.9531 * treb_y + treb_oy),
	cv.Path.LineTo(95.0625 * treb_x + treb_ox, 272.8125 * treb_y + treb_oy),
	cv.Path.QuadraticTo(105.1875 * treb_x + treb_ox, 272.8125 * treb_y + treb_oy, 113.3438 * treb_x + treb_ox, 277.6641 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(121.5 * treb_x + treb_ox, 282.5156 * treb_y + treb_oy, 125.4375 * treb_x + treb_ox, 292.0078 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(129.375 * treb_x + treb_ox, 301.5 * treb_y + treb_oy, 129.375 * treb_x + treb_ox, 314.4375 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(129.375 * treb_x + treb_ox, 327.9375 * treb_y + treb_oy, 126.2812 * treb_x + treb_ox, 336.5156 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(123.1875 * treb_x + treb_ox, 345.0938 * treb_y + treb_oy, 115.6641 * treb_x + treb_ox, 351 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(108.1406 * treb_x + treb_ox, 356.9062 * treb_y + treb_oy, 96.0469 * treb_x + treb_ox, 358.875 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(94.9219 * treb_x + treb_ox, 378.8438 * treb_y + treb_oy, 90.2812 * treb_x + treb_ox, 394.1719 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(85.6406 * treb_x + treb_ox, 409.5 * treb_y + treb_oy, 77.4141 * treb_x + treb_ox, 415.6875 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(69.1875 * treb_x + treb_ox, 421.875 * treb_y + treb_oy, 57.9375 * treb_x + treb_ox, 421.875 * treb_y + treb_oy, 1),
	cv.Path.Close(),
	# Next sub-path:
	cv.Path.MoveTo(80.4375 * treb_x + treb_ox, 344.8125 * treb_y + treb_oy),
	cv.Path.LineTo(84.9375 * treb_x + treb_ox, 344.6719 * treb_y + treb_oy),
	cv.Path.LineTo(84.9375 * treb_x + treb_ox, 336.0938 * treb_y + treb_oy),
	cv.Path.QuadraticTo(84.9375 * treb_x + treb_ox, 327.2344 * treb_y + treb_oy, 84.0234 * treb_x + treb_ox, 316.3359 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(83.1094 * treb_x + treb_ox, 305.4375 * treb_y + treb_oy, 80.8594 * treb_x + treb_ox, 288.8438 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(77.3438 * treb_x + treb_ox, 290.25 * treb_y + treb_oy, 74.25 * treb_x + treb_ox, 293.4141 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(71.1562 * treb_x + treb_ox, 296.5781 * treb_y + treb_oy, 69.3281 * treb_x + treb_ox, 300.5859 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(67.5 * treb_x + treb_ox, 304.5938 * treb_y + treb_oy, 67.5 * treb_x + treb_ox, 307.9688 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(67.5 * treb_x + treb_ox, 317.5312 * treb_y + treb_oy, 69.6094 * treb_x + treb_ox, 323.5781 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(71.7188 * treb_x + treb_ox, 329.625 * treb_y + treb_oy, 77.625 * treb_x + treb_ox, 335.25 * treb_y + treb_oy, 1),
	cv.Path.LineTo(73.125 * treb_x + treb_ox, 336.9375* treb_y + treb_oy),
	cv.Path.QuadraticTo(67.2188 * treb_x + treb_ox, 333.8438 * treb_y + treb_oy, 63.7031 * treb_x + treb_ox, 330.0469 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(60.1875 * treb_x + treb_ox, 326.25 * treb_y + treb_oy, 58.5 * treb_x + treb_ox, 320.7656 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(56.8125 * treb_x + treb_ox, 315.2812 * treb_y + treb_oy , 56.8125 * treb_x + treb_ox, 306.5625 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(56.8125 * treb_x + treb_ox, 300.0938 * treb_y + treb_oy , 59.5547 * treb_x + treb_ox, 293.625 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(62.2969 * treb_x + treb_ox, 287.1562 * treb_y + treb_oy , 66.9375 * treb_x + treb_ox, 282.375 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(71.5781 * treb_x + treb_ox, 277.5938 * treb_y + treb_oy , 78.8906 * treb_x + treb_ox, 275.2031 * treb_y + treb_oy, 1),
	cv.Path.LineTo(77.0625 * treb_x + treb_ox, 264.375 * treb_y + treb_oy),
	cv.Path.QuadraticTo(74.5312 * treb_x + treb_ox, 249.0469 * treb_y + treb_oy, 72.7031 * treb_x + treb_ox, 239.4844 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(63.2812 * treb_x + treb_ox, 251.0156 * treb_y + treb_oy, 56.8125 * treb_x + treb_ox, 260.1562 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(52.3125 * treb_x + treb_ox, 267.1875 * treb_y + treb_oy, 48.6562 * treb_x + treb_ox, 275.625 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(45 * treb_x + treb_ox, 284.0625 * treb_y + treb_oy, 43.875 * treb_x + treb_ox, 292.2188 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(42.75 * treb_x + treb_ox, 300.375 * treb_y + treb_oy, 42.75 * treb_x + treb_ox, 308.8125 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(42.75 * treb_x + treb_ox, 318.9375 * treb_y + treb_oy, 46.9688 * treb_x + treb_ox, 328.5 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(51.1875 * treb_x + treb_ox, 338.0625 * treb_y + treb_oy, 60.1875 * treb_x + treb_ox, 341.4375 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(69.1875 * treb_x + treb_ox, 344.8125 * treb_y + treb_oy, 80.4375 * treb_x + treb_ox, 344.8125 * treb_y + treb_oy, 1),
	cv.Path.Close(),
	# Third sub-path:
	cv.Path.MoveTo(96.1875 * treb_x + treb_ox, 343.125 * treb_y + treb_oy),
	cv.Path.QuadraticTo(103.5 * treb_x + treb_ox, 340.5938 * treb_y + treb_oy, 106.875 * treb_x + treb_ox, 336.2344 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(110.25 * treb_x + treb_ox, 331.875 * treb_y + treb_oy, 111.6562 * treb_x + treb_ox, 326.4609 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(113.0625 * treb_x + treb_ox, 321.0469 * treb_y + treb_oy, 113.0625 * treb_x + treb_ox, 314.4375 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(113.0625 * treb_x + treb_ox, 307.125 * treb_y + treb_oy, 111.0938 * treb_x + treb_ox, 300.375 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(109.125 * treb_x + treb_ox, 293.625 * treb_y + treb_oy, 104.7656 * treb_x + treb_ox, 290.25 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(100.4062 * treb_x + treb_ox, 286.875 * treb_y + treb_oy, 92.8125 * treb_x + treb_ox, 286.875 * treb_y + treb_oy, 1),
	cv.Path.LineTo(92.5312 * treb_x + treb_ox, 286.875 * treb_y + treb_oy),
	cv.Path.QuadraticTo(94.5 * treb_x + treb_ox, 302.4844 * treb_y + treb_oy, 95.3438 * treb_x + treb_ox, 313.9453 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(96.1875 * treb_x + treb_ox, 325.4062 * treb_y + treb_oy, 96.1875 * treb_x + treb_ox, 334.6875 * treb_y + treb_oy, 1),
	cv.Path.LineTo(96.1875 * treb_x + treb_ox, 343.125 * treb_y + treb_oy),
	cv.Path.Close(),
	# Fourth sub-path:
	cv.Path.MoveTo(79.4531 * treb_x + treb_ox, 206.4375 * treb_y + treb_oy),
	cv.Path.QuadraticTo(86.9062 * treb_x + treb_ox, 198.9844 * treb_y + treb_oy, 90.7031 * treb_x + treb_ox, 192.9375 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(94.5 * treb_x + treb_ox, 186.8906 * treb_y + treb_oy, 96.75 * treb_x + treb_ox, 179.3672 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(99 * treb_x + treb_ox, 171.8438 * treb_y + treb_oy, 99 * treb_x + treb_ox, 165.375 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(99 * treb_x + treb_ox, 157.5 * treb_y + treb_oy, 97.5938 * treb_x + treb_ox, 152.4375 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(96.1875 * treb_x + treb_ox, 147.375 * treb_y + treb_oy, 92.8125 * treb_x + treb_ox, 143.1562 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(89.4375 * treb_x + treb_ox, 138.9375 * treb_y + treb_oy, 84.9375 * treb_x + treb_ox, 138.9375 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(81.5625 * treb_x + treb_ox, 139.2188 * treb_y + treb_oy, 78.1875 * treb_x + treb_ox, 141.6094 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(74.8125 * treb_x + treb_ox, 144 * treb_y + treb_oy, 73.2656 * treb_x + treb_ox, 147.7969 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(71.7188 * treb_x + treb_ox, 151.5938 * treb_y + treb_oy, 71.7188 * treb_x + treb_ox, 154.9688 * treb_y + treb_oy, 1),
	
	cv.Path.QuadraticTo(71.7188 * treb_x + treb_ox, 159.4688 * treb_y + treb_oy, 72.5625 * treb_x + treb_ox, 169.7344 * treb_y + treb_oy, 1),
	cv.Path.QuadraticTo(73.4062 * treb_x + treb_ox, 180 * treb_y + treb_oy, 77.625 * treb_x + treb_ox, 198.5625 * treb_y + treb_oy, 1),
	
	cv.Path.LineTo(79.4531 * treb_x + treb_ox, 206.4375 * treb_y + treb_oy),
	cv.Path.Close()
	])
]








	canvas = cv.Canvas(trebel_shapes,width=treb_x,height=treb_y,)


	page.controls.append(canvas)
	page.update()

ft.app(main)