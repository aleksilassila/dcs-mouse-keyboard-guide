if starting:
	class VirtualAxis:
		def __init__(self, axis_max, sensitivity, center_rate=0.0, use_falloff=False):
			self.value = 0.0
			self.trim_value = 0.0
			self.axis_max = float(axis_max)
			self.sensitivity = sensitivity
			self.center_rate = center_rate
			self.use_falloff = use_falloff

		def move(self, delta):
			if self.use_falloff:
				ratio = abs(self.value) / self.axis_max
				mult = 1.0 - (0.5 * (ratio ** 2))
				self.value += delta * self.sensitivity * mult
			else:
				self.value += delta * self.sensitivity
			self.clamp()

		def set_trim(self, new_trim=None):
			if new_trim is None:
				self.trim_value = self.value
			else:
				self.trim_value = new_trim
			self.clamp()

		def offset_trim(self, delta):
			self.trim_value += delta
			self.value += delta
			self.clamp()

		def apply_centering(self):
			if self.center_rate > 0:
				self.value = self.trim_value + (self.value - self.trim_value) / (1.0 + self.center_rate)

		def set_val(self, val):
			self.value = val
			self.clamp()

		def clamp(self):
			if self.value > self.axis_max:
				self.value = self.axis_max
			elif self.value < -self.axis_max:
				self.value = -self.axis_max
			
			if self.trim_value > self.axis_max:
				self.trim_value = self.axis_max
			elif self.trim_value < -self.axis_max:
				self.trim_value = -self.axis_max

	system.setThreadTiming(TimingTypes.HighresSystemTimer)
	system.threadExecutionInterval = 20

	axis_max = float(vJoy[0].axisMax)
	
	# Cyclic
	axis_x = VirtualAxis(axis_max, sensitivity=13, center_rate=0.015, use_falloff=True)
	axis_y = VirtualAxis(axis_max, sensitivity=13, center_rate=0.03, use_falloff=True)
	
	# Pedals
	axis_pedal = VirtualAxis(axis_max, sensitivity=200, center_rate=0.02, use_falloff=False)
	
	# Throttles (start at max)
	axis_throttle1 = VirtualAxis(axis_max, sensitivity=200)
	axis_throttle1.set_val(axis_max)
	axis_throttle2 = VirtualAxis(axis_max, sensitivity=200)
	axis_throttle2.set_val(axis_max)

	# View
	axis_view_x = VirtualAxis(axis_max, sensitivity=2)
	axis_view_y = VirtualAxis(axis_max, sensitivity=2)
	
	freelook = False


# mouse axis
if mouse.deltaX:
	if freelook:
		axis_view_x.move(mouse.deltaX)
	else:
		axis_x.move(mouse.deltaX)

if mouse.deltaY:
	if freelook:
		axis_view_y.move(mouse.deltaY)
	else:
		axis_y.move(-mouse.deltaY)

# Y axis trim logic
if mouse.getButton(4):  # MOUSE 4
	axis_y.set_trim()
if mouse.getButton(3):  # MOUSE 3
	axis_y.set_trim(0)

# throttle control
if keyboard.getKeyDown(Key.W):
	axis_throttle1.move(-1)
if keyboard.getKeyDown(Key.S):
	axis_throttle1.move(1)

# secondary throttle control
if keyboard.getKeyDown(Key.X):
	axis_throttle2.move(-1)
if keyboard.getKeyDown(Key.Z):
	axis_throttle2.move(1)

# pedal control
pedal_pressed = False
if keyboard.getKeyDown(Key.Q):
	axis_pedal.move(-1)
	pedal_pressed = True
if keyboard.getKeyDown(Key.E):
	axis_pedal.move(1)
	pedal_pressed = True

alt_pressed = keyboard.getKeyDown(Key.LeftAlt) or keyboard.getKeyDown(Key.RightAlt)

# X/Pedal trim logic
if keyboard.getKeyDown(Key.A):
	if alt_pressed:
		axis_x.offset_trim(-50)
	else:
		axis_pedal.offset_trim(-axis_pedal.sensitivity)
if keyboard.getKeyDown(Key.D):
	if alt_pressed:
		axis_x.offset_trim(50)
	else:
		axis_pedal.offset_trim(axis_pedal.sensitivity)
if keyboard.getKeyDown(Key.F):
	if alt_pressed:
		axis_x.set_trim(0)
	else:
		axis_pedal.set_trim(0)

# Apply continuous centering where needed
axis_x.apply_centering()
axis_y.apply_centering()
if not pedal_pressed:
	axis_pedal.apply_centering()

# freelook hold
freelook2 = keyboard.getKeyDown(Key.LeftAlt) or keyboard.getKeyDown(Key.RightAlt)
if (freelook and not freelook2) or (not freelook and freelook2):
	axis_view_x.set_val(0)
	axis_view_y.set_val(0)
	freelook = freelook2

# vJoy axis mapping
vJoy[1].x = axis_view_x.value
vJoy[1].y = axis_view_y.value
vJoy[0].x = axis_x.value
vJoy[0].y = axis_y.value
vJoy[0].rx = axis_throttle1.value
vJoy[0].ry = axis_throttle2.value
vJoy[0].rz = axis_pedal.value

diagnostics.watch(vJoy[0].x)
diagnostics.watch(vJoy[0].y)
diagnostics.watch(vJoy[0].rx)
diagnostics.watch(vJoy[0].ry)
diagnostics.watch(vJoy[0].rz)
diagnostics.watch(vJoy[1].x)
diagnostics.watch(vJoy[1].y)
diagnostics.watch(freelook)
diagnostics.watch(mouse.getButton(3))
diagnostics.watch(axis_x.trim_value)
diagnostics.watch(axis_y.trim_value)
diagnostics.watch(axis_pedal.trim_value)