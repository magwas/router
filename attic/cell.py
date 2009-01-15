"""
	A macrocell may contain a flip-flop, may have some simple logic, and may drives an output.
	We separate it to two entities: a flip-flop, and output logic.
"""

INPUT=0
OUTPUT=1

Class Pad:
	"""
		A pad of a cell.
		A pad can be input or output.
		P+R is done by connecting pads to each other
	"""
	def __init__(direction=INPUT,name=""):
		"""
			A pad have a direction, and may have a name.
		"""
		self.type="pad"
		self.cell=None
		self.function=None
		self.name=name
		self.direction=direction
		self.connections=[]
	def isOutput(self):
		return self.direction
	def _connectObject(self,cell,function):
		"""
			At initialization the pad is attached to a function of a device
			The function is device-specific, maybe just a string like "clk".
			This should only be called by Cell.attachPad
		"""
		if self.cell:
			raise "Already connected"
		self.cell=cell
		self.function=function
	def connectPad(self,pad):
		"""
			When virtual nets are eliminated, cells are connected through pads.
			An input pad can be connected to one output pad.
			An output pad can be connected to multiple input pads.
			Connection is done by adding the pads to each other.
		"""
		if self.direction:
			if cell.connection:
				raise "output-output conflict"
			else:
				self.connections.append(pad)
				pad.connections.append(self)
		else:
			if pad.connection:
				pad.connections.append(self)
				self.connections.append(pad)
			else:
				raise "input-input conflict"
	def optimize(self):
		"""
			Tries to optimize out the pad in the optimization stage.
			Calls its cell's optimizator with all the connections, and the function.
		"""
		if not self.cell:
			raise "stale pad"
		self.cell.optimize(self.function,self.connections)
	
	def eliminate(self):
		"""
			Eliminates the pad, unlinks references.
		"""
		for i in self.connections:
			i.remove(self)
		self.cell.removePad(self.function)

Class Librarycell:
	"""
		A library cell, like LPM_ADD_SUB.
	"""
	def __init__(self,properties):
		"""
			Initialization is specific to the object.
			properties is a dictionary of keyvord-value pairs given at the config.
		"""
		self.processProperties(properties)
	def processProperties(self,properties):
		"""
			Properties are specific to the library part.
			This method is defined by the library part definition.
		"""
		raise NotImplementedError
	def instantiate(self,name):
		"""
			Instantiate the library cell.
			This step is part-specific.
			This returns two sets:
				a set of objects which is either implemented by the device or
					can be eliminated with the device specific optimizator.
				a set of pads
			The returned sets are dictionaries, the keywords are in name+'_'+identifier form.
		"""
		raise NotImplementedError

Class SwitchPad(Pad):
	"""
		A SwitchPad is a pad which can be allocated to a slot (row or column).
	"""
	def __init__(direction=INPUT,name=""):
		"""
			we do not have allocated slot in the beginning
		"""
		Pad.__init__(direction,name)
		self.allocatedslot=None

	def _connectObject(self,cell,function):
		"""
			When connected we ask for the slots available for us
		"""
		self.availableslots=cell.slotsForFunction(function)
		Pad._connectObject(self,cell,function)
	def availableSlots(self,slotlist):
		"""
			The optimizel tells the pad which slots are available
                        if the set of rows could be made smaller, it return true
		"""
		if not self.availableslots:
			raise "No available slots"
		olen=len(self.availableslots)
		self.availableslots=self.availableslots-set(slotlist)
		nlen=len(self.availableslots)
		if not nlen:
			raise "Ran out of slots"
		return len<olen
		
Class Cell:
	"""
		An instantiated cell.
		It is part specific, and contains the optimizer and p+r logic.
	"""
	def __init__(self,name,device,properties=None):
		"""
			Well, the initialization is specific to the cell type.
			It must create the pads, and place it into a dictionary called paddict.
			The keywords are the function names.
			we have a device containing the cell, so all device-specific functions can be implemented there
			do not forget to put device type into self.type
		"""
		self.device=device
		self.name=name
		self.properties=properties
		raise NotImplementedError

	def getType(self):
		"""
			returns the type of the cell
		"""
		return self.type
	def getPads(self):
		"""
			Return the pads in the form of a dictionary.
		"""
		return self.paddict

	def getPadFor(self,function):
		return self.paddict[function]

	def getConnectedPadsFor(self,function):
		"""
			returns the list of pads connected to the function
		"""
		return self.paddict[function].connections

	def optimize(self,function,connectedpads):
		"""
			The optimizer function.
			It tries to simplify and place the cell.
			Returns (optimized,relocate,eliminate)
			optimized is boolean, telling if we could optimize anything
			relocate is a dictionary containing the pins to be relocated.
				the keyword is the pin, the value is (cell,function) pair describing the target
			eliminate is a list of pins and cells to  be eliminated
		"""
		Raise NotImplementedError
	def place(self):
		"""
			places the cell, and sets its configuration variables
		"""
		raise NotImplementedError
	def eliminate(self):
		"""
			Eliminates the cell, unlinks references.
		"""
		Raise NotImplementedError

	def removePad(self,function):
		"""
			Removes the pad attached to function
		"""
		del(self.paddict[function])
	def attachPad(self,function,pad):
		"""
			Attaches a pad to a device
		"""
		self.paddict[function]=pad
		pad._connectObject(self,function)
	

Class PhysicalPin(Pad):
	"""
		A physical pin of a silicon device
	"""
	def __init__(self,direction,name,pinno):
		self.type="PIN"
		self.pinno=pinno
		Pad.__init__(self,direction,name)

	def eliminate(self):
		"""
			We do not have a software-only implementation of ESR's Ultimate Firewall
		"""
		raise NotImplementedError

Class Device(Cell):
	"""
		A physical device made of silicon or whatever.
	"""

	def __init__(self,interface,cells):
		"""
			interface is a list of physical pins, cells is a list of cells
		"""
		self.type="device"
		self.pins={}
		self.cells={}
		for pin in interface:
			self.attachPad(pin.name,pin)
		self.checkPins()
		for cell in cells:
			self.cells[cell.name]=cell
	def checkPins(self):
		"""
			check if the pinout is correct
		"""
		raise NotImplementedError
	def writeJedec(self):
		"""
			returns a string containing the contents of a JEDEC file
		"""
		raise NotImplementedError
	def removePad(self,function):
		"""
			We do not have a software-only implementation of ESR's Ultimate Firewall
		"""
		raise NotImplementedError

	def eliminate(self):
		"""
			We do not have a software-only implementation of ESR's Ultimate Firewall
		"""
		raise NotImplementedError

	def route(self):
		"""
			Place and route.
		"""
		raise NotImplementedError

