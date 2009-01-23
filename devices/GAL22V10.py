"""
	cells and optimisations specific to 22V10 GAL
"""

from bistromatic import IOPin, LogicFunction, AbstractObject

dRows= {
	23: range(44/44+1,396/44+1),
	22: range(440/44+1,880/44+1),
	21: range(924/44+1,1452/44+1),
	20: range(1496/44+1,2112/44+1),
	19: range(2156/44+1,2860/44+1),
	18: range(2904/44+1,3608/44+1),
	17: range(3652/44+1,4268/44+1),
	16: range(4312/44+1,4840/44+1),
	15: range(4884/44+1,5324/44+1),
	14: range(5368/44+1,5720/44+1)
}

oeRows={
	23: [44/44],
	22: [440/44],
	21: [924/44],
	20: [1496/44],
	19: [2156/44],
	18: [2904/44],
	17: [3652/44],
	16: [4312/44],
	15: [4884/44],
	14: [5368/44],
	}

class Technology:
	"""
		mix-in class of Cell describing a GAL22V10
		22V10 have
			10 input pins
			10 I/O pins
			10 OLMC-s attached to I/O pins
			a 132x44 and-array
	"""
	def __init__(self):
		"""
		initializing our structures
		"""
		self.LogicFunction=LogicFunction
		self.IOPin=IOPin
		self.partname="GAL22V10"
		self.OLMCs={}
		self.dRows=dRows
		self.oeRows=oeRows

	def createFlipFlops(self,name,width,fftype,pvalue,have_enable,have_sset,have_sclr,have_testenab,have_testin,have_testout):
		"""
		creates an array of flip-flops
		"""
		content=[]
                for bit in range(width):
                        RD={"D":"data%u"%bit, "Q":"q%u"%bit}
                        #c=OLMC(renamedict=RD,initial=int((pvalue&(2 ** bit))>0),name="flipflop%u"%bit)
                        c=OLMC("%s%u"%(name,bit),self,haveflipflop=True)
			for (orig,newname) in RD.items():
				c.renamevar(orig,newname)
			
                        content.append(c)
		print "FIXME: this is buggy!"
		print content
		return content
                funcs=[]
                andtable=[ "000", "010", "100", "111"]
                onetable=[ "00", "11"]
                if have_enable:
                        clk=self.LogicFunction(andtable,["enable","clock","inclock"],2)
                else:
                        clk=self.LogicFunction(onetable,["clock","inclock"],2)

                if have_sset:
                        f=self.LogicFunction(andtable,["sset","inclock","aset"],2)
                        clk=clk.mold(f)
                if have_sclr:
                        f=self.LogicFunction(andtable,["sclr","inclock","aclr"],2)
                        clk=clk.mold(f)
                #print clk
                clk.name="clk"
                content.append(clk)
		return(content)

	def checkPins(self):
		"""
			Checks whether pins are okay.
		"""
		portlist=self.ports.keys()
		for i in range(24):
			pname="PORT%d"%i
			if i == 12:
				assert not ((pname in portlist) and (self.ports[pname].connections)), "illegal pin connected: %s"%pname
			assert pname in portlist, "port %s is missing"%pname
			portlist.remove(pname)
		for pname in portlist:
			assert not (self.ports[pname].connections), "illegal pin connected: %s"%pname
	def registerOlmc(self,pinno,olmc):
		if pinno < 14:
			raise "Illegal pin"
		if self.OLMCs.has_key(pinno):
			raise "multiple OLMCs in one slot"
		self.OLMCs[pinno]=olmc

class OLMC(AbstractObject):
	"""
		An OLMC
		It drives a pin, and can contain a flip-flop.
		if S0=0, then there is a D flip-flop, and its input is driven by pin1
		if S1=0, then the pin is inverted
		it have an enable input: if it is false, then the pin is input pin
		functions:
		 D:	flip-flop input
		 PIN:	pin tristate
		 OE:	output enable input
		 Q:     flip-flop output
                 /Q:	flip-flop output inverted
	"""
	def __init__(self,name, device, haveflipflop=None,inverted=None,input=None):
		"""
			haveflipflop: (0: no, 1: yes, None: undecided)
			inverted: (0: no, 1: yes, None: undecided)
			input: (0: no, 1: yes, None: undecided)
		"""
		vars=["D","OE","PIN","Q"]
		AbstractObject.__init__(self,vars,ilen=3,iolen=1,objtype="OLMC",name=name)
		self.device=device
		self.name=name
		self.haveflipflop=haveflipflop
		self.inverted=inverted
		self.input=input
		self.OlmcSlot=None

	def copy(self):
		"""
		copy constructor
		"""
		n=OLMC(self.name,self.device,self.haveflipflop,self.inverted,self.input)
		return n

	def optimize(self,function,connectedpads):
		"""
			on the PIN function we can place ourselves into a slot, and look for inverter state
			FIXME: maybe the logic should be very different: all outputs are initially connected to Q, and relocated to PIN or /Q if needed
			if placed in a slot:
				on the D and OE function we can designate switch rows to the output pads of the connected terms,
				on the Q and /Q function also, and can contribute to the logical term
		"""
		optimized=0
		relocate={}
		eliminate=[]
		if function=="PIN":
			for pad in connectedpads:
				if not pad.cell:
					raise "Stale pad"
				if pad.type == "PIN":
					if not self.OlmcSlot:
						self.device.registerOlmc(pad.pinno,self)
						self.OlmcSlot=pad.pinno
						optimized=1
					else:
						# not necessarily an error: if more pins are driven from the same OLMC, we should drive it through the switch.
						raise NotImplementedError
				elif pad.cell.type == "INV":
					#we optimize out inverters
					invotherside=pad.cell.getConnectedPortsFor("Result")
					if (len(invotherside)==1) and (invotherside[0].type=="PIN"):
						self.inverted= not self.inverted
						eliminate.append(pad.cell)
						relocate[(self,"PIN")]=pad.cell.getPortFor("Result")
						optimized=1
		elif function=="D":
			if self.OlmcSlot:
				if pad.cell.type == "switch":
					#FIXME switch pads have to have a availableSlots function, which tells which rows are available
					# if the set of rows could be made smaller, it should return true
					optimized=pad.availableSlots(self.device.dRows[self.OlmcSlot])
		elif function == "OE":
			if self.OlmcSlot:
				if pad.cell.type == "switch":
					optimized=pad.availableSlots(self.device.oeRows[self.OlmcSlot])
		elif function == "Q" or function=="/Q":
			# in slot allocation we do not distinguish between direct and inverted output
			# we leave the choice for the switch's term optimization 
			if self.OlmcSlot:
				if pad.cell.type == "switch":
					optimized=pad.availableSlots(self.device.qRows[self.OlmcSlot])
	
		return (optimized,relocate,eliminate)

	def place(self):
		"""
			We should place ourselves.
		"""
		if not self.OlmcSlot:
			#buried cell
			self.OlmcSlot=self.device.getUnusedOlmc()

class Switch:
	"""
		Switch matrix.
		Initially a switch matrix is a logic expression. It have inputs, outputs, and a truth table.
		In the beginning there are more switches.
		In the optimization stage we mold 'em into one.
		When placing, we assign slots to inputs and outputs, and values to fuses.
	"""
	def __init__(self,name,device,inputs,outputs,table,properties=None):
		"""
			A switch is defined by its inputs and outputs and truth table.
			inputs and outputs are list of strings describing the connection names
			table is a string containing of rows separated by newlines, containing
			"1","0", and "-" for each input and output in sequence. space and "|" characters
			may be used to group them. Empty lines are ignored.
			Only the ON cover have to be defined.
		"""
		self.type="switch"
		self.type="OLMC"
		self.device=device
		self.name=name
		self.inputs=[]
		self.outputs=[]
		for iname in self.inputs:
			function=name+"_"+iname
			self.attachPort(function,SwitchPort(INPUT,iname))
			self.inputs.attach(function)
		for oname in self.outputs:
			function=name+"_"+iname
			self.attachPort(function,SwitchPort(OUTPUT,iname))
			self.outputs.attach(function)
		self.table=[]
		width=len(inputs)+len(outputs)
		tablerows=table.replace(" ","").replace("|","").split()
		for row in tablerows:
			if row=='':
				continue
			if len(row) != width:
				raise "Row length is not equal to sum of inputs and outputs"
			else:
				table.append(list(row))
	def optimize(self,funtion,connectedpads):
		"""
			We optimize on output pads.
			For each connected switches we incorporate their all outputs and all inputs minus the one we connected to.
			The table is permutated with the tables of incorporated switches.
			If there are no other cells than switches connected, we eliminate the output.
		"""
		if not self.getPortFor(function).isOutput():
			return 0
		hasotherobjects=0
		for pad in connectedpads:
			if pad.cell.type != "switch":
				hasotherobjects=1
				continue
			newinputs=pad.cell.inputs
			newoutputs=pad.cell.outputs
			FIXME
		
