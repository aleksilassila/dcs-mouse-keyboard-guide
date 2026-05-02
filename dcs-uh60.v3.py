# init
if starting:
	centreX = 0.015
	centreY = 0.03
	centrePedal = 0.02
	sensX = 13
	sensY = 13
	sensZ = 200
	sensPedal = 400
	viewSensX = 10
	viewSensY = 10
	system.setThreadTiming(TimingTypes.HighresSystemTimer)
	system.threadExecutionInterval = 20
	x = 0
	y = 0
	z = float(vJoy[0].axisMax)
	rx = 0
	ry = 0
	pedal = 0
	trimY = 0
	freelook = False
	viewLatch = False
	moveLatch = False

# mouse axis
if mouse.deltaX:
	if freelook:
		rx += mouse.deltaX * viewSensX
	else:
		moveLatch = True
		x_ratio = abs(x) / float(vJoy[0].axisMax)
		x_mult = 1.0 - (0.5 * (x_ratio ** 2)) # Exponential falloff: 1.0x at center, dropping to 0.5x at max
		x += mouse.deltaX * sensX * x_mult
		if abs(x) > vJoy[0].axisMax:
			x = vJoy[0].axisMax * x / abs(x)
x /= (1.0 + centreX)

if mouse.deltaY:
	if freelook:
		ry += mouse.deltaY * viewSensY
	else:
		moveLatch = True
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

# recenter
if (not freelook and viewLatch):
	rx = 0
	ry = 0
	viewLatch = False

#keyboard override mouse
if (moveLatch and keyboard.getPressed(Key.Space) or keyboard.getPressed(Key.Z)):
	x = 0
	y = 0
	moveLatch = False

# throttle control
if keyboard.getKeyDown(Key.W):
	z -= sensZ
	if z < -vJoy[0].axisMax:
		z = -vJoy[0].axisMax
if keyboard.getKeyDown(Key.S):
	z += sensZ
	if z > vJoy[0].axisMax:
		z = vJoy[0].axisMax

# pedal control
pedal_pressed = False
if keyboard.getKeyDown(Key.Q):
	pedal -= sensPedal
	if pedal < -vJoy[1].axisMax:
		pedal = -vJoy[1].axisMax
	pedal_pressed = True
if keyboard.getKeyDown(Key.E):
	pedal += sensPedal
	if pedal > vJoy[1].axisMax:
		pedal = vJoy[1].axisMax
	pedal_pressed = True

if not pedal_pressed:
	pedal /= (1.0 + centrePedal)

#code for hold freelock
freelook = mouse.getButton(3) or mouse.middleButton
if (mouse.getPressed(3)):
	viewLatch = True
	
#code for toggle freelook
#toggle = keyboard.getPressed(Key.CapsLock)
#if (toggle):
#	freelook = not freelook


# vJoy axis mapping
vJoy[0].rx = rx
vJoy[0].ry = ry
vJoy[0].x = x
vJoy[0].y = y
vJoy[0].z = z
vJoy[1].y = pedal

diagnostics.watch(vJoy[0].x)
diagnostics.watch(vJoy[0].y)
diagnostics.watch(vJoy[0].z)
diagnostics.watch(vJoy[1].y)
diagnostics.watch(vJoy[0].rx)
diagnostics.watch(vJoy[0].ry)
diagnostics.watch(freelook)
diagnostics.watch(moveLatch)
diagnostics.watch(mouse.getButton(3))
diagnostics.watch(trimY)