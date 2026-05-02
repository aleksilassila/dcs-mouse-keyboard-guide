# init
if starting:
	centreX = 0.015
	centreY = 0.03
	centrePedal = 0.02
	sensX = 4
	sensY = 13
	sensZ = 200
	sensPedal = 200
	viewSensX = 2
	viewSensY = 2
	system.setThreadTiming(TimingTypes.HighresSystemTimer)
	system.threadExecutionInterval = 20
	x = 0
	y = 0
	throttle = float(vJoy[0].axisMax)
	throttle2 = -float(vJoy[0].axisMax)
	rx = 0
	ry = 0
	pedal = 0
	trimX = 0
	trimY = 0
	trimPedal = 0
	freelook = False

# mouse axis
if mouse.deltaX:
	if freelook:
		rx += mouse.deltaX * viewSensX
	else:
		x_ratio = abs(x) / float(vJoy[0].axisMax)
		x_mult = 1.0 - (0.5 * (x_ratio ** 2)) # Exponential falloff: 1.0x at center, dropping to 0.5x at max
		x += mouse.deltaX * sensX * x_mult
		if abs(x) > vJoy[0].axisMax:
			x = vJoy[0].axisMax * x / abs(x)

x = trimX + (x - trimX) / (1.0 + centreX)

if mouse.deltaY:
	if freelook:
		ry += mouse.deltaY * viewSensY
	else:
		y_ratio = abs(y) / float(vJoy[0].axisMax)
		y_mult = 1.0 - (0.5 * (y_ratio ** 2)) # Exponential falloff: 1.0x at center, dropping to 0.5x at max
		y -= mouse.deltaY * sensY * y_mult
		if abs(y) > vJoy[0].axisMax:
			y = vJoy[0].axisMax * y / abs(y)

# Y axis trim logic
if mouse.getButton(4):  # MOUSE 4
	trimY = y
if mouse.getButton(3):  # MOUSE 3
	trimY = 0

y = trimY + (y - trimY) / (1.0 + centreY)

# throttle control
if keyboard.getKeyDown(Key.W):
	throttle -= sensZ
	if throttle < -vJoy[0].axisMax:
		throttle = -vJoy[0].axisMax
if keyboard.getKeyDown(Key.S):
	throttle += sensZ
	if throttle > vJoy[0].axisMax:
		throttle = vJoy[0].axisMax

# secondary throttle control
if keyboard.getKeyDown(Key.X):
	throttle2 -= sensZ
	if throttle2 < -vJoy[0].axisMax:
		throttle2 = -vJoy[0].axisMax
if keyboard.getKeyDown(Key.Z):
	throttle2 += sensZ
	if throttle2 > vJoy[0].axisMax:
		throttle2 = vJoy[0].axisMax

# pedal control
pedal_pressed = False
if keyboard.getKeyDown(Key.Q):
	pedal -= sensPedal
	if pedal < -vJoy[0].axisMax:
		pedal = -vJoy[0].axisMax
	pedal_pressed = True
if keyboard.getKeyDown(Key.E):
	pedal += sensPedal
	if pedal > vJoy[0].axisMax:
		pedal = vJoy[0].axisMax
	pedal_pressed = True

alt_pressed = keyboard.getKeyDown(Key.LeftAlt) or keyboard.getKeyDown(Key.RightAlt)

if keyboard.getKeyDown(Key.A):
	if alt_pressed:
		trimX -= 10
		x -= 10
		if trimX < -vJoy[0].axisMax:
			trimX = -vJoy[0].axisMax
		if x < -vJoy[0].axisMax:
			x = -vJoy[0].axisMax
	else:
		trimPedal -= sensPedal
		pedal -= sensPedal
		if trimPedal < -vJoy[0].axisMax:
			trimPedal = -vJoy[0].axisMax
		if pedal < -vJoy[0].axisMax:
			pedal = -vJoy[0].axisMax
if keyboard.getKeyDown(Key.D):
	if alt_pressed:
		trimX += 10
		x += 10
		if trimX > vJoy[0].axisMax:
			trimX = vJoy[0].axisMax
		if x > vJoy[0].axisMax:
			x = vJoy[0].axisMax
	else:
		trimPedal += sensPedal
		pedal += sensPedal
		if trimPedal > vJoy[0].axisMax:
			trimPedal = vJoy[0].axisMax
		if pedal > vJoy[0].axisMax:
			pedal = vJoy[0].axisMax
if keyboard.getKeyDown(Key.F):
	if alt_pressed:
		trimX = 0
	else:
		trimPedal = 0

if not pedal_pressed:
	pedal = trimPedal + (pedal - trimPedal) / (1.0 + centrePedal)

#code for hold freelock
freelook2 = keyboard.getKeyDown(Key.LeftAlt) or keyboard.getKeyDown(Key.RightAlt)
if (freelook and not freelook2) or (not freelook and freelook2):
	rx = 0
	ry = 0
	freelook = freelook2
	
#code for toggle freelook
#toggle = keyboard.getPressed(Key.CapsLock)
#if (toggle):
#	freelook = not freelook


# vJoy axis mapping
vJoy[1].x = rx
vJoy[1].y = ry
vJoy[0].x = x
vJoy[0].y = y

pedal_norm = pedal / float(vJoy[0].axisMax)
if pedal_norm < 0:
	right_brake = throttle2
	left_brake = throttle2 - (throttle2 + vJoy[0].axisMax) * (-pedal_norm)
else:
	left_brake = throttle2
	right_brake = throttle2 - (throttle2 + vJoy[0].axisMax) * pedal_norm

vJoy[0].z = throttle
vJoy[0].rx = left_brake
vJoy[0].ry = right_brake
vJoy[0].rz = pedal


diagnostics.watch(vJoy[0].x)
diagnostics.watch(vJoy[0].y)
diagnostics.watch(vJoy[0].rx)
diagnostics.watch(vJoy[0].ry)
diagnostics.watch(vJoy[0].rz)
diagnostics.watch(vJoy[1].x)
diagnostics.watch(vJoy[1].y)
diagnostics.watch(freelook)
diagnostics.watch(mouse.getButton(3))
diagnostics.watch(trimY)
diagnostics.watch(trimX)
diagnostics.watch(trimPedal)