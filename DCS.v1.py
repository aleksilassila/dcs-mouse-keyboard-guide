if starting:
	system.setThreadTiming(TimingTypes.HighresSystemTimer)
	system.threadExecutionInterval = 20

	freelook_toggle = False
	k_toggle = False
	axis_max = float(vJoy[0].axisMax)
	
	class VirtualAxis:
		def __init__(self, axis_max, sensitivity, center_rate=0.0, linear_centering=False, use_falloff=False, always_center=False):
			self.value = 0.0
			self.trim_value = 0.0
			self.axis_max = float(axis_max)
			self.sensitivity = sensitivity
			self.center_rate = center_rate
			self.linear_centering = linear_centering
			self.use_falloff = use_falloff
			self.always_center = always_center
			self.did_move = False

		def move(self, delta):
			self.did_move = True
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
			if self.center_rate > 0 and (self.always_center or not self.did_move):
				# if self.linear_centering:
				self.value = self.trim_value + (self.value - self.trim_value) * (1.0 - self.center_rate)
				# else:
				# 	self.value = self.trim_value + (self.value - self.trim_value) / (1.0 + self.center_rate)

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

		def post_update(self):
			self.apply_centering()
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
			self.roll_sensitivity = 8
			self.pitch_sensitivity = 15
			self.roll_center_rate = 0.015
			self.pitch_center_rate = 0.3
			self.brakes_multiplier = 1

		def setup(self):
			self.axis_roll = VirtualAxis(axis_max, sensitivity=self.roll_sensitivity, center_rate=self.roll_center_rate, linear_centering=True, use_falloff=True, always_center=True)
			self.axis_pitch = VirtualAxis(axis_max, sensitivity=self.pitch_sensitivity, center_rate=self.pitch_center_rate, linear_centering=True, use_falloff=True, always_center=True)
			
			self.pedal_speed = VirtualAxis(1.0, sensitivity=0.1, center_rate=0.1)
			self.axis_pedal = VirtualAxis(axis_max, sensitivity=200, center_rate=0.1, use_falloff=False)
			
			self.axis_throttle = VirtualAxis(axis_max, sensitivity=200)
			self.axis_throttle.set_val(axis_max)
			
			self.axis_brake_left = VirtualAxis(axis_max * self.brakes_multiplier, sensitivity=400, center_rate=0.05)
			self.axis_brake_left.set_val(-axis_max * self.brakes_multiplier)
			self.axis_brake_left.set_trim(-axis_max * self.brakes_multiplier)
			
			self.axis_brake_right = VirtualAxis(axis_max * self.brakes_multiplier, sensitivity=400, center_rate=0.05)
			self.axis_brake_right.set_val(-axis_max * self.brakes_multiplier)
			self.axis_brake_right.set_trim(-axis_max * self.brakes_multiplier)

			self.axis_zoom = VirtualAxis(axis_max, sensitivity=-20, use_falloff=False)
			# self.axis_manual_zoom = VirtualButtonAxis(decay=20, max_val=1000)
			self.axis_manual_zoom = VirtualAxis(axis_max, sensitivity=20, use_falloff=False)
			
			self.axis = [self.axis_roll, self.axis_pitch, self.pedal_speed, self.axis_pedal, self.axis_throttle, self.axis_brake_left, self.axis_brake_right, self.axis_zoom, self.axis_manual_zoom]

		def update(self, freelook=False, alt_pressed=False, shift_pressed=False):
			deltaX = mouse.deltaX
			deltaY = mouse.deltaY

			if not freelook:
				# mouse axis
				if deltaX:
					self.axis_roll.move(deltaX)

				if deltaY:
					self.axis_pitch.move(-deltaY)

				# Y axis trim logic
				self.axis_pitch.set_trim()
				if mouse.getButton(4):  # MOUSE 4
				# if mouse.getButton(3):  # MOUSE 3
					self.axis_pitch.set_trim(0)
				
				if mouse.wheel != 0:
					if keyboard.getKeyDown(Key.LeftShift):
						self.axis_manual_zoom.move(mouse.wheel)
					else:
						self.axis_zoom.move(mouse.wheel)

				if keyboard.getKeyDown(Key.Z):
					vJoy[0].setButton(11, keyboard.getKeyDown(Key.W))
					vJoy[0].setButton(12, keyboard.getKeyDown(Key.S))
					vJoy[0].setButton(13, keyboard.getKeyDown(Key.A))
					vJoy[0].setButton(14, keyboard.getKeyDown(Key.D))
					vJoy[0].setButton(15, keyboard.getKeyDown(Key.Q))
					vJoy[0].setButton(16, keyboard.getKeyDown(Key.E))
				elif keyboard.getKeyDown(Key.X):
					vJoy[0].setButton(17, keyboard.getKeyDown(Key.W))
					vJoy[0].setButton(18, keyboard.getKeyDown(Key.S))
					vJoy[0].setButton(19, keyboard.getKeyDown(Key.A))
					vJoy[0].setButton(20, keyboard.getKeyDown(Key.D))
					vJoy[0].setButton(21, keyboard.getKeyDown(Key.Q))
					vJoy[0].setButton(22, keyboard.getKeyDown(Key.E))
				elif keyboard.getKeyDown(Key.C):
					vJoy[0].setButton(23, keyboard.getKeyDown(Key.W))
					vJoy[0].setButton(24, keyboard.getKeyDown(Key.S))
					vJoy[0].setButton(25, keyboard.getKeyDown(Key.A))
					vJoy[0].setButton(26, keyboard.getKeyDown(Key.D))
					vJoy[0].setButton(27, keyboard.getKeyDown(Key.Q))
					vJoy[0].setButton(28, keyboard.getKeyDown(Key.E))
				elif keyboard.getKeyDown(Key.V):
					vJoy[1].setButton(0, keyboard.getKeyDown(Key.W))
					vJoy[1].setButton(1, keyboard.getKeyDown(Key.S))
					vJoy[1].setButton(2, keyboard.getKeyDown(Key.A))
					vJoy[1].setButton(3, keyboard.getKeyDown(Key.D))
					vJoy[1].setButton(4, keyboard.getKeyDown(Key.Q))
					vJoy[1].setButton(5, keyboard.getKeyDown(Key.E))
				else:
					vJoy[0].setButton(11, False)
					vJoy[0].setButton(12, False)
					vJoy[0].setButton(13, False)
					vJoy[0].setButton(14, False)
					vJoy[0].setButton(15, False)
					vJoy[0].setButton(16, False)
					vJoy[0].setButton(17, False)
					vJoy[0].setButton(18, False)
					vJoy[0].setButton(19, False)
					vJoy[0].setButton(20, False)
					vJoy[0].setButton(21, False)
					vJoy[0].setButton(22, False)
					vJoy[0].setButton(23, False)
					vJoy[0].setButton(24, False)
					vJoy[0].setButton(25, False)
					vJoy[0].setButton(26, False)
					vJoy[0].setButton(27, False)
					vJoy[0].setButton(28, False)
					vJoy[1].setButton(0, False)
					vJoy[1].setButton(1, False)
					vJoy[1].setButton(2, False)
					vJoy[1].setButton(3, False)
					vJoy[1].setButton(4, False)
					vJoy[1].setButton(5, False)

					# throttle control
					if keyboard.getKeyDown(Key.W):
						self.axis_throttle.move(-1)
					if keyboard.getKeyDown(Key.S):
						self.axis_throttle.move(1)
					
					# pedal control
					if keyboard.getKeyDown(Key.Q):
						self.axis_pedal.move(-1)
						self.axis_brake_left.move(self.brakes_multiplier)
					if keyboard.getKeyDown(Key.E):
						self.axis_pedal.move(1)
						self.axis_brake_right.move(self.brakes_multiplier)
					
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

			# vJoy axis mapping
			vJoy[0].x = self.axis_roll.value
			vJoy[0].y = self.axis_pitch.value
			vJoy[0].z = self.axis_throttle.value
			vJoy[0].rx = self.axis_brake_left.value
			vJoy[0].ry = self.axis_brake_right.value
			vJoy[0].rz = self.axis_pedal.value
			vJoy[0].slider = self.axis_zoom.value
			vJoy[1].slider = self.axis_manual_zoom.value
			# vJoy[0].setButton(29, self.axis_manual_zoom.increment)
			# vJoy[0].setButton(30, self.axis_manual_zoom.decrement)

			# diagnostics.watch(self.axis_manual_zoom.value)
			# diagnostics.watch(self.axis_manual_zoom.increment)
			# diagnostics.watch(self.axis_manual_zoom.decrement)

			self.post_update()

	class F16CProfile(AirplaneProfile):
		def __init__(self):
			super(F16CProfile, self).__init__()
			self.pitch_sensitivity = 8
			self.pitch_center_rate = 0.3
			self.roll_sensitivity = 8
			self.roll_center_rate = 0.015
			self.brakes_multiplier = 1

	class A4ECProfile(AirplaneProfile):
		def __init__(self):
			super(A4ECProfile, self).__init__()
			self.pitch_sensitivity = 13
			self.pitch_center_rate = 0.03
			self.roll_sensitivity = 4
			self.roll_center_rate = 0.015
			self.brakes_multiplier = -1

	class HelicopterProfile(DCSProfile):
		def __init__(self):
			self.pedal_sensitivity = 200

		def setup(self):
			# self.axis_roll = VirtualAxis(axis_max, sensitivity=6, center_rate=0.015, use_falloff=True, always_center=True)
			# self.axis_pitch = VirtualAxis(axis_max, sensitivity=6, center_rate=0.06, use_falloff=True, always_center=True)
			self.axis_roll = VirtualAxis(axis_max, sensitivity=3, center_rate=0.0075, use_falloff=True, always_center=True)
			self.axis_pitch = VirtualAxis(axis_max, sensitivity=3, center_rate=0.03, use_falloff=True, always_center=True)
			self.axis_pedal = VirtualAxis(axis_max, sensitivity=self.pedal_sensitivity, center_rate=0.02, use_falloff=False)
			
			self.throttle_speed = VirtualAxis(1.0, sensitivity=0.025, center_rate=0.07)
			self.throttle_speed.set_trim(0.5)
			self.throttle_speed.set_val(0.5)
			self.axis_throttle1 = VirtualAxis(axis_max, sensitivity=200)
			self.axis_throttle1.set_val(axis_max)

			self.axis_throttle2 = VirtualAxis(axis_max, sensitivity=200, center_rate=1, always_center=True)
			self.axis_throttle2.set_val(axis_max)
			
			self.axis = [self.axis_roll, self.axis_pitch, self.axis_pedal, self.throttle_speed, self.axis_throttle1, self.axis_throttle2]

		def update(self, freelook=False, alt_pressed=False, shift_pressed=False):
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

	profiles = dict([
		("F-16C", F16CProfile()),
		("A-4E-C", A4ECProfile()),
		("UH-60L", UH60Profile()),
		("OH-6A", OH6AProfile()),
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
	freelook_toggle = False

if k_toggle:
	# K Binds
	if keyboard.getKeyDown(Key.D1):
		active_profile = profiles["UH-60L"]

	if keyboard.getPressed(Key.D2):
		active_profile = profiles["OH-6A"]

	if keyboard.getKeyDown(Key.D4):
		active_profile = profiles["A-4E-C"]

	if keyboard.getKeyDown(Key.D5):
		active_profile = profiles["F-16C"]

	for key in Key.__dict__:
		#diagnostics.debug(key)
		#diagnostics.debug(isinstance(Key.__dict__[key], Key))
		
		if not isinstance(Key.__dict__[key], Key):
			continue

		if keyboard.getPressed(Key.__dict__[key]):
			diagnostics.debug(Key.__dict__[key])
			k_toggle = False
			break
else:
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

if keyboard.getPressed(Key.K):
	k_toggle = not k_toggle

diagnostics.watch(k_toggle)
diagnostics.watch(active_profile.__class__.__name__ if active_profile else None)

if active_profile is not None:
	active_profile.update(freelook=(alt_pressed or freelook_toggle), alt_pressed=alt_pressed, shift_pressed=shift_pressed)
