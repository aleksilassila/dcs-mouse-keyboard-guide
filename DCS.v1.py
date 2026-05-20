if starting:
	system.setThreadTiming(TimingTypes.HighresSystemTimer)
	system.threadExecutionInterval = 20

	freelook_toggle = True
	k_toggle = False
	control_mode = 1
	axis_max = float(vJoy[0].axisMax)

	def linear_map(value, x_min, x_max, y_min, y_max):
		return y_min + (value - x_min) * (y_max - y_min) / (x_max - x_min)
	
	class VirtualAxis:
		def __init__(self, axis_max, sensitivity=1.0, trim_value=None, linear_rate=0.0, constant_rate=0.0):
			self.value = 0.0
			self.trim_value = trim_value
			self.axis_max = float(axis_max)
			self.sensitivity = sensitivity
			self.linear_rate = linear_rate
			self.constant_rate = constant_rate
			self.did_move = False

		def move(self, delta):
			trim_diff = (self.trim_value - self.value) if self.trim_value is not None else 0

			constant_component = self.constant_rate * (1 if trim_diff > 0 else -1) if self.constant_rate != 0 else 0
			linear_component = trim_diff * self.linear_rate

			self.value = self.value + delta * self.sensitivity + min(abs(trim_diff), max(-abs(trim_diff), linear_component + constant_component))
			self.did_move = True

			self.clamp()

		def set_trim(self, new_trim=None):
			self.trim_value = new_trim
			self.clamp()

		def offset_trim(self, delta):
			if self.trim_value is None:
				self.trim_value = 0.0
			self.trim_value += delta
			self.value += delta
			self.clamp()

		def set_val(self, val):
			self.value = val
			self.clamp()

		def clamp(self):
			if self.value > self.axis_max:
				self.value = self.axis_max
			elif self.value < -self.axis_max:
				self.value = -self.axis_max

			if self.trim_value is not None and self.trim_value > self.axis_max:
				self.trim_value = self.axis_max
			elif self.trim_value is not None and self.trim_value < -self.axis_max:
				self.trim_value = -self.axis_max

		def post_update(self):
			if not self.did_move:
				self.move(0)
			self.did_move = False

	class VirtualButtonAxis:
		def __init__(self, decay=1, max_val=15):
			self.decay = decay
			self.value = 0.0
			self.max_val = max_val

		def clamp(self):
			if self.value > self.max_val:
				self.value = self.max_val
			elif self.value < -self.max_val:
				self.value = -self.max_val

		def move(self, delta):
			self.value += delta
			self.clamp()
				
		@property
		def increment(self):
			return self.value > 0
		
		@property
		def decrement(self):
			return self.value < 0

		def post_update(self):
			if self.value > 0:
				self.value = max(0, self.value - self.decay)
			elif self.value < 0:
				self.value = min(0, self.value + self.decay)

	class DCSProfile(object):
		def __init__(self):
			self.axis = []

		def post_update(self):
			for axis in self.axis:
				axis.post_update()

			diagnostics.watch(vJoy[0].x)
			diagnostics.watch(vJoy[0].y)
			diagnostics.watch(vJoy[0].z)
			diagnostics.watch(vJoy[0].rx)
			diagnostics.watch(vJoy[0].ry)
			diagnostics.watch(vJoy[0].rz)
			diagnostics.watch(vJoy[1].x)
			diagnostics.watch(vJoy[1].y)
			diagnostics.watch(vJoy[1].z)
			diagnostics.watch(vJoy[1].rx)
			diagnostics.watch(vJoy[1].ry)
			diagnostics.watch(vJoy[1].rz)


	class AirplaneProfile(DCSProfile):
		def __init__(self):
			self.pitch_sensitivity = 8
			self.pitch_linear_rate = 0.015
			self.pitch_constant_rate = 25
			self.roll_sensitivity = 8
			self.roll_linear_rate = 0.015
			self.roll_constant_rate = 25
			self.brakes_multiplier = 1

		def setup(self):
			self.axis_pitch = VirtualAxis(axis_max, sensitivity=8, linear_rate=0.015, constant_rate=15)
			self.axis_roll = VirtualAxis(axis_max, sensitivity=8, linear_rate=0.015, constant_rate=15, trim_value=0.0)
			
			self.pedal_speed = VirtualAxis(1.0, sensitivity=0.1, constant_rate=0.1)
			self.axis_pedal = VirtualAxis(axis_max, sensitivity=200, linear_rate=0.015, constant_rate=20)
			
			self.axis_throttle = VirtualAxis(axis_max, sensitivity=200)
			self.axis_throttle.set_val(axis_max)
			
			self.axis_brake_left = VirtualAxis(axis_max * self.brakes_multiplier, sensitivity=600, constant_rate=600)
			self.axis_brake_left.set_val(-axis_max * self.brakes_multiplier)
			self.axis_brake_left.set_trim(-axis_max * self.brakes_multiplier)
			
			self.axis_brake_right = VirtualAxis(axis_max * self.brakes_multiplier, sensitivity=600, constant_rate=600)
			self.axis_brake_right.set_val(-axis_max * self.brakes_multiplier)
			self.axis_brake_right.set_trim(-axis_max * self.brakes_multiplier)

			self.axis_zoom = VirtualAxis(axis_max, sensitivity=-20)
			self.axis_zoom_out = VirtualAxis(axis_max, constant_rate=400, linear_rate=0.5, trim_value=self.axis_zoom.value)
			# self.axis_manual_zoom = VirtualButtonAxis(decay=20, max_val=1000)
			self.axis_manual_zoom = VirtualAxis(axis_max, sensitivity=20)
			
			self.axis = [self.axis_roll, self.axis_pitch, self.pedal_speed, self.axis_pedal, self.axis_throttle, self.axis_brake_left, self.axis_brake_right, self.axis_zoom, self.axis_zoom_out, self.axis_manual_zoom]

		def update(self, freelook=False, control_layer=False, alt_pressed=False, shift_pressed=False, control_mode=1):
			deltaX = mouse.deltaX
			deltaY = mouse.deltaY

			if not freelook:
				# mouse axis
				if control_mode == 1:
					self.axis_pitch.set_trim(0 if mouse.getButton(4) else None)
					self.axis_roll.move(deltaX)
					self.axis_pitch.move(-deltaY)
				elif control_mode == 2:
					self.axis_pitch.set_trim(0)
					self.axis_pedal.set_trim(0 if mouse.getButton(4) else None)
					self.axis_pedal.move(deltaX / 50)

				# Y axis trim logic
				# if mouse.getButton(4):  # MOUSE 4
				# # if mouse.getButton(3):  # MOUSE 3
				# 	self.axis_pitch.set_trim(0)

				if mouse.getPressed(2): # MOUSE 3
					if self.axis_zoom.value < 6000 and self.axis_zoom.value > 2000:
						self.axis_zoom.set_val(-11000)
					else:
						self.axis_zoom.set_val(5000)
				elif mouse.wheel != 0:
					if keyboard.getKeyDown(Key.LeftShift):
						self.axis_manual_zoom.move(mouse.wheel)
					else:
						self.axis_zoom.move(mouse.wheel)

				if control_layer:
					# throttle control
					if keyboard.getKeyDown(Key.W):
						self.axis_throttle.move(-1)
					if keyboard.getKeyDown(Key.S):
						self.axis_throttle.move(1)
					
					# pedal control
					if keyboard.getKeyDown(Key.Q):
						if not keyboard.getKeyDown(Key.E):
							self.axis_pedal.move(-2)
						self.axis_brake_left.move(self.brakes_multiplier * 2)
					if keyboard.getKeyDown(Key.E):
						if not keyboard.getKeyDown(Key.Q):
							self.axis_pedal.move(2)
						self.axis_brake_right.move(self.brakes_multiplier * 2)
					
					if keyboard.getKeyDown(Key.A):
						if shift_pressed:
							self.axis_roll.offset_trim(-10)
						else:
							self.axis_pedal.offset_trim(-self.axis_pedal.sensitivity * self.pedal_speed.value)
							self.pedal_speed.move(1)
					if keyboard.getKeyDown(Key.D):
						if shift_pressed:
							self.axis_roll.offset_trim(10)
						else:
							self.axis_pedal.offset_trim(self.axis_pedal.sensitivity * self.pedal_speed.value)
							self.pedal_speed.move(1)
					if keyboard.getKeyDown(Key.F):
						if shift_pressed:
							self.axis_roll.set_trim(0)
						else:
							self.axis_pedal.set_trim(0)

			self.axis_zoom_out.trim_value = self.axis_zoom.value

			# vJoy axis mapping
			vJoy[0].x = self.axis_roll.value
			vJoy[0].y = self.axis_pitch.value
			vJoy[0].z = self.axis_throttle.value
			vJoy[0].rx = self.axis_brake_left.value
			vJoy[0].ry = self.axis_brake_right.value
			vJoy[0].rz = self.axis_pedal.value
			vJoy[0].slider = linear_map(self.axis_zoom_out.value, -axis_max, axis_max, -axis_max, 11000)
			vJoy[1].slider = self.axis_manual_zoom.value
			# vJoy[0].setButton(29, self.axis_manual_zoom.increment)
			# vJoy[0].setButton(30, self.axis_manual_zoom.decrement)

			# diagnostics.watch(self.axis_manual_zoom.value)
			# diagnostics.watch(self.axis_manual_zoom.increment)
			# diagnostics.watch(self.axis_manual_zoom.decrement)

			diagnostics.watch(vJoy[0].slider)
			diagnostics.watch(self.axis_pitch.value)
			diagnostics.watch(self.axis_pitch.trim_value)
			diagnostics.watch(self.pedal_speed.value)

			self.post_update()

	class F16CProfile(AirplaneProfile):
		def __init__(self):
			super(F16CProfile, self).__init__()
			self.pitch_sensitivity = 8
			self.pitch_linear_rate = 100
			self.roll_sensitivity = 8
			self.roll_linear_rate = 100
			self.brakes_multiplier = 1

	class A4ECProfile(AirplaneProfile):
		def __init__(self):
			super(A4ECProfile, self).__init__()
			self.pitch_sensitivity = 13
			self.pitch_linear_rate = 0.03
			self.roll_sensitivity = 4
			self.roll_linear_rate = 0.015
			self.brakes_multiplier = -1

	class HelicopterProfile(DCSProfile):
		def __init__(self):
			self.pedal_sensitivity = 200
			self.pitch_linear_rate = 0.03
			self.roll_linear_rate = 0.0075
			self.always_trim_pitch = True

		def setup(self):
			self.axis_pitch = VirtualAxis(axis_max, sensitivity=3, linear_rate=self.pitch_linear_rate, trim_value=0.0)
			self.axis_roll = VirtualAxis(axis_max, sensitivity=3, linear_rate=self.roll_linear_rate, trim_value=0.0)
			self.axis_pedal = VirtualAxis(axis_max, sensitivity=self.pedal_sensitivity, linear_rate=0.02)
			
			self.throttle_speed = VirtualAxis(1.0, sensitivity=0.025, linear_rate=0.07)
			self.throttle_speed.set_trim(0.5)
			self.throttle_speed.set_val(0.5)
			self.axis_throttle1 = VirtualAxis(axis_max, sensitivity=200)
			self.axis_throttle1.set_val(axis_max)

			self.axis_throttle2 = VirtualAxis(axis_max, sensitivity=200, linear_rate=1)
			self.axis_throttle2.set_val(axis_max)
			
			self.axis = [self.axis_roll, self.axis_pitch, self.axis_pedal, self.throttle_speed, self.axis_throttle1, self.axis_throttle2]

		def update(self, freelook=False, control_layer=False, alt_pressed=False, shift_pressed=False, control_mode=1):
			deltaX = mouse.deltaX
			deltaY = mouse.deltaY

			if not freelook:
				# mouse axis
				if deltaX:
					self.axis_roll.move(deltaX)

				if deltaY:
					self.axis_pitch.move(-deltaY)

				if mouse.wheel != 0:
					self.axis_pedal.offset_trim(mouse.wheel * self.axis_pedal.sensitivity / 60)

				# Y axis trim logic
				if self.always_trim_pitch:
					self.axis_pitch.set_trim()
				if mouse.getButton(4):  # MOUSE 4
				# if mouse.getButton(3):  # MOUSE 3
					self.axis_pitch.set_trim(0)
				
				if keyboard.getKeyDown(Key.Z):
					# secondary throttle control
					if keyboard.getKeyDown(Key.W):
						self.axis_throttle2.set_trim(-axis_max)
					if keyboard.getKeyDown(Key.S):
						self.axis_throttle2.set_trim(axis_max)

					vJoy[0].setButton(11, keyboard.getKeyDown(Key.A))
					vJoy[0].setButton(12, keyboard.getKeyDown(Key.D))
					vJoy[0].setButton(13, keyboard.getKeyDown(Key.Q))
					vJoy[0].setButton(14, keyboard.getKeyDown(Key.E))
				else:
					vJoy[0].setButton(11, False)
					vJoy[0].setButton(12, False)
					vJoy[0].setButton(13, False)
					vJoy[0].setButton(14, False)

					# throttle control
					if keyboard.getKeyDown(Key.W):
						self.axis_throttle1.move(-1 * self.throttle_speed.value)
						self.throttle_speed.move(1)
					if keyboard.getKeyDown(Key.S):
						self.axis_throttle1.move(1 * self.throttle_speed.value)
						self.throttle_speed.move(1)
					
					# # secondary throttle control
					# if keyboard.getKeyDown(Key.X):
					# 	self.axis_throttle2.move(-1)
					# if keyboard.getKeyDown(Key.Z):
					# 	self.axis_throttle2.move(1)
					
					# pedal control
					if keyboard.getKeyDown(Key.Q):
						self.axis_pedal.move(-1)
					if keyboard.getKeyDown(Key.E):
						self.axis_pedal.move(1)

					# X/Pedal trim logic
					if keyboard.getKeyDown(Key.A):
						if shift_pressed:
							self.axis_roll.offset_trim(-50)
						else:
							self.axis_pedal.offset_trim(-self.axis_pedal.sensitivity)
					if keyboard.getKeyDown(Key.D):
						if shift_pressed:
							self.axis_roll.offset_trim(50)
						else:
							self.axis_pedal.offset_trim(self.axis_pedal.sensitivity)
					if keyboard.getKeyDown(Key.F):
						if shift_pressed:
							self.axis_roll.set_trim(0)
						else:
							self.axis_pedal.set_trim(0)

			# vJoy axis mapping
			vJoy[0].x = self.axis_roll.value
			vJoy[0].y = self.axis_pitch.value
			vJoy[0].rx = self.axis_throttle1.value
			vJoy[0].ry = self.axis_throttle2.value
			vJoy[0].rz = self.axis_pedal.value

			self.post_update()

	class UH60Profile(HelicopterProfile):
		def __init__(self):
			super(UH60Profile, self).__init__()

	class OH6AProfile(HelicopterProfile):
		def __init__(self):
			super(OH6AProfile, self).__init__()
			self.pedal_sensitivity = 350

	class UH1HProfile(HelicopterProfile):
		def __init__(self):
			super(UH1HProfile, self).__init__()
			self.always_trim_pitch = True
			self.roll_linear_rate = 0
			self.pedal_sensitivity = 350

	profiles = dict([
		("F-16C", F16CProfile()),
		("A-4E-C", A4ECProfile()),
		("UH-60L", UH60Profile()),
		("OH-6A", OH6AProfile()),
		("UH-1H", UH1HProfile()),
	])

	for profile in profiles.values():
		profile.setup()

	active_profile = None

# Alt
alt_pressed = keyboard.getKeyDown(Key.LeftAlt) or keyboard.getKeyDown(Key.RightAlt)
shift_pressed = keyboard.getKeyDown(Key.LeftShift) or keyboard.getKeyDown(Key.RightShift)

# Alt toggle
if mouse.getPressed(3):
	if not freelook_toggle:
		vJoy[0].setPressed(29)
	freelook_toggle = True
elif keyboard.getPressed(Key.Grave):
	if freelook_toggle:
		vJoy[0].setPressed(29)
	else:
		control_mode = 1
	freelook_toggle = False
elif keyboard.getPressed(Key.T) and not freelook_toggle:
	control_mode = 2

control_layer = not keyboard.getKeyDown(Key.Z) and not keyboard.getKeyDown(Key.X) and not keyboard.getKeyDown(Key.C) and not keyboard.getKeyDown(Key.V)
freelook = alt_pressed or freelook_toggle

if k_toggle:
	# K Binds
	if keyboard.getKeyDown(Key.D1):
		active_profile = profiles["UH-60L"]

	if keyboard.getPressed(Key.D2):
		active_profile = profiles["OH-6A"]

	if keyboard.getKeyDown(Key.D3):
		active_profile = profiles["UH-1H"]

	if keyboard.getKeyDown(Key.D4):
		active_profile = profiles["A-4E-C"]

	if keyboard.getKeyDown(Key.D5):
		active_profile = profiles["F-16C"]

	# Match any keypress
	for key in Key.__dict__:
		#diagnostics.debug(key)
		#diagnostics.debug(isinstance(Key.__dict__[key], Key))
		
		if not isinstance(Key.__dict__[key], Key):
			continue

		if keyboard.getPressed(Key.__dict__[key]):
			diagnostics.debug(Key.__dict__[key])
			k_toggle = False
			break

if not k_toggle and not freelook:
	if keyboard.getKeyDown(Key.Z): # 40-
		vJoy[0].setButton(40, keyboard.getKeyDown(Key.W))
		vJoy[0].setButton(41, keyboard.getKeyDown(Key.S))
		vJoy[0].setButton(42, keyboard.getKeyDown(Key.A))
		vJoy[0].setButton(43, keyboard.getKeyDown(Key.D))
		vJoy[0].setButton(44, keyboard.getKeyDown(Key.Q))
		vJoy[0].setButton(45, keyboard.getKeyDown(Key.E))
		vJoy[0].setButton(46, keyboard.getKeyDown(Key.F))
		vJoy[0].setButton(47, keyboard.getKeyDown(Key.R))
		# vJoy[0].setButton(48, keyboard.getKeyDown(Key.G))
		# vJoy[0].setButton(49, keyboard.getKeyDown(Key.T))
		vJoy[0].setButton(50, keyboard.getKeyDown(Key.D1))
		vJoy[0].setButton(51, keyboard.getKeyDown(Key.D2))
		vJoy[0].setButton(52, keyboard.getKeyDown(Key.D3))
		vJoy[0].setButton(53, keyboard.getKeyDown(Key.D4))
		# vJoy[0].setButton(54, keyboard.getKeyDown(Key.D5))
	elif keyboard.getKeyDown(Key.X): # 60-
		vJoy[0].setButton(60, keyboard.getKeyDown(Key.W))
		vJoy[0].setButton(61, keyboard.getKeyDown(Key.S))
		vJoy[0].setButton(62, keyboard.getKeyDown(Key.A))
		vJoy[0].setButton(63, keyboard.getKeyDown(Key.D))
		vJoy[0].setButton(64, keyboard.getKeyDown(Key.Q))
		vJoy[0].setButton(65, keyboard.getKeyDown(Key.E))
		vJoy[0].setButton(66, keyboard.getKeyDown(Key.F))
		vJoy[0].setButton(67, keyboard.getKeyDown(Key.R))
		# vJoy[0].setButton(68, keyboard.getKeyDown(Key.G))
		# vJoy[0].setButton(69, keyboard.getKeyDown(Key.T))
		vJoy[0].setButton(70, keyboard.getKeyDown(Key.D1))
		vJoy[0].setButton(71, keyboard.getKeyDown(Key.D2))
		vJoy[0].setButton(72, keyboard.getKeyDown(Key.D3))
		vJoy[0].setButton(73, keyboard.getKeyDown(Key.D4))
		# vJoy[0].setButton(74, keyboard.getKeyDown(Key.D5))
	elif keyboard.getKeyDown(Key.C): # 80-
		vJoy[0].setButton(80, keyboard.getKeyDown(Key.W))
		vJoy[0].setButton(81, keyboard.getKeyDown(Key.S))
		vJoy[0].setButton(82, keyboard.getKeyDown(Key.A))
		vJoy[0].setButton(83, keyboard.getKeyDown(Key.D))
		vJoy[0].setButton(84, keyboard.getKeyDown(Key.Q))
		vJoy[0].setButton(85, keyboard.getKeyDown(Key.E))
		vJoy[0].setButton(86, keyboard.getKeyDown(Key.F))
		vJoy[0].setButton(87, keyboard.getKeyDown(Key.R))
		# vJoy[0].setButton(88, keyboard.getKeyDown(Key.G))
		# vJoy[0].setButton(89, keyboard.getKeyDown(Key.T))
		vJoy[0].setButton(90, keyboard.getKeyDown(Key.D1))
		vJoy[0].setButton(91, keyboard.getKeyDown(Key.D2))
		vJoy[0].setButton(92, keyboard.getKeyDown(Key.D3))
		vJoy[0].setButton(93, keyboard.getKeyDown(Key.D4))
		# vJoy[0].setButton(94, keyboard.getKeyDown(Key.D5))
	elif keyboard.getKeyDown(Key.V): # 100-
		vJoy[0].setButton(100, keyboard.getKeyDown(Key.W))
		vJoy[0].setButton(101, keyboard.getKeyDown(Key.S))
		vJoy[0].setButton(102, keyboard.getKeyDown(Key.A))
		vJoy[0].setButton(103, keyboard.getKeyDown(Key.D))
		vJoy[0].setButton(104, keyboard.getKeyDown(Key.Q))
		vJoy[0].setButton(105, keyboard.getKeyDown(Key.E))
		vJoy[0].setButton(106, keyboard.getKeyDown(Key.F))
		vJoy[0].setButton(107, keyboard.getKeyDown(Key.R))
		# vJoy[0].setButton(108, keyboard.getKeyDown(Key.G))
		# vJoy[0].setButton(109, keyboard.getKeyDown(Key.T))
		vJoy[0].setButton(110, keyboard.getKeyDown(Key.D1))
		vJoy[0].setButton(111, keyboard.getKeyDown(Key.D2))
		vJoy[0].setButton(112, keyboard.getKeyDown(Key.D3))
		vJoy[0].setButton(113, keyboard.getKeyDown(Key.D4))
		# vJoy[0].setButton(114, keyboard.getKeyDown(Key.D5))

if control_layer or k_toggle or freelook:
	for i in range(40, 128):
		vJoy[0].setButton(i, False)

# Default layer
if control_layer and not k_toggle and not freelook:
	vJoy[0].setButton(0, keyboard.getKeyDown(Key.D0))
	vJoy[0].setButton(1, keyboard.getKeyDown(Key.D1))
	vJoy[0].setButton(2, keyboard.getKeyDown(Key.D2))
	vJoy[0].setButton(3, keyboard.getKeyDown(Key.D3))
	vJoy[0].setButton(4, keyboard.getKeyDown(Key.D4))
	vJoy[0].setButton(5, keyboard.getKeyDown(Key.D5))
	vJoy[0].setButton(6, keyboard.getKeyDown(Key.D6))
	vJoy[0].setButton(7, keyboard.getKeyDown(Key.D7))
	vJoy[0].setButton(8, keyboard.getKeyDown(Key.D8))
	vJoy[0].setButton(9, keyboard.getKeyDown(Key.D9))
	vJoy[0].setButton(10, mouse.getButton(3))
else:
	for i in range(0, 10):
		vJoy[0].setButton(i, False)
	vJoy[0].setButton(10, False)

if keyboard.getPressed(Key.K):
	k_toggle = not k_toggle

diagnostics.watch(k_toggle)
diagnostics.watch(freelook)
diagnostics.watch(control_layer)
diagnostics.watch(active_profile.__class__.__name__ if active_profile else None)

if active_profile is not None:
	active_profile.update(freelook=freelook, alt_pressed=alt_pressed, shift_pressed=shift_pressed, control_layer=control_layer, control_mode=control_mode)
