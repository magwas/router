from demszky import Cell
from bistromatic import LogicFunction,DFlipFlop

def itoa(x, base=10):
	""" inverse of int(). should have been standard builtin or string function."""
	if 0 is x:
		return '0'
	isNegative = x < 0
	if isNegative:
		x = -x
	digits = []
	while x > 0:
		x, lastDigit = divmod(x, base)
		digits.append('0123456789abcdefghijklmnopqrstuvwxyz'[lastDigit])
	if isNegative:
		digits.append('-')
	digits.reverse()
	return ''.join(digits) 

def binary(n,l):
	s=itoa(n,2)
	assert len(s) <= l , "number is too big for width: %s %s %s"%(s,n,l)
	s=(l-len(s))*'0'+s
	return s

class Generator:
	"""
		The Generator class of the module automagically becomes the base class of EdifCell
		The role of the methods defined here is to implement the library
	"""
	def initobj(self):
		"""
			initializes the library object based on its properties
			this is called from the parser, and should prepare the cell for an eventual call of generate(),
			which returns a set of AbstractObject instances (see there)
			this fill in self.contents
		"""
		#print self.properties
		#print "parsing lpm_library/"+self.properties['lpm_type']
		lpm_type=self.properties['lpm_type'].lower()
		gener=getattr(self,lpm_type,None)
		assert gener , "No generator found for " + self.properties['lpm_type']
		gener()
		#for c in self.contents:
		#	print c

	def generate(self,name):
		"""
			this is called in sight of the edif construct (instance ...)
			it should return a set of AbstractObject instances made unique using name
		"""
		c=Cell(name,(None))
		objs=[]
		for (k,v) in self.contents.items():
			for o in v:
				i=o.instantiate(name)
				objs.append(i)
		return objs

	
	def getprop(self,name,defval=None):
		"""
			gets the named property, returns default or raises exception if not found
		"""
		if self.properties.has_key(name):
			return self.properties[name]
		assert defval is not None, name+ " is required parameter"
		return defval


	@staticmethod
	def makebus(namepattern,width,nochop=False):
		"""
			makes a list of signal names in a bus
		"""
		bus=[]
		if (width == 1) and (not nochop):
			return [(namepattern%0)[:-1]]
		for i in range(width):
			bus.append(namepattern%i)
		bus.reverse()
		return bus

	def lpm_constant(self):
		"""
			LPM_CONSTANT megafunction
		"""
		width=self.getprop('lpm_width')
		value=self.getprop('lpm_cvalue')
		matrix=binary(value,width)
		pins=[]
		pins=self.makebus('result%u',width)
		self.contents["constant"]=[LogicFunction([matrix],pins,0)]

	def lpm_mux(self):
		"""
			LPM_MUX megafunction
		"""
		width=self.getprop('lpm_width')
		size=self.getprop('lpm_size')
		ws=width*size
		swidth=self.getprop('lpm_widths')
		assert (2 ** swidth) >= size, "selector is too narrow for number of buses"
		pipeline=self.getprop('lpm_pipeline',0)
		assert pipeline == 0, "lpm_pipeline not yet implemented"
		inputs=[]
		outputs=self.makebus('result%u',width)
		for i in range(size):
			for j in range(width):
				inputs.append("data%ux%u"%(i,j))
		sels=self.makebus("sel%u",swidth)
		vars=inputs+sels+outputs
		numinputs=swidth+ws
		matrix=[]
		for i in range(2**width):
			out=binary(i,width)
			for s in range(size):
				sel=binary(s,swidth)
				input="-"*(width*s)+out+"-"*(width*(size-s-1))
				matrix.append(input+sel+out)
		self.contents['mux']=[LogicFunction(matrix,vars,numinputs)]

	def lpm_or(self):
		"""
			lpm_or megafunction
		"""
		width=self.getprop('lpm_width')
		size=self.getprop('lpm_size')
		ws=width*size
		pipeline=self.getprop('lpm_pipeline',0)
		assert pipeline == 0, "lpm_pipeline not yet implemented"
		inputs=[]
		outputs=self.makebus('result%u',width,nochop=1)
		for i in range(size):
			for j in range(width):
				inputs.append("data%ux%u"%(i,j))
		vars=inputs+outputs
		matrix=[]
		inf=2**width
		for j in range(2**ws):
			out=0
			for i in range(size):
				l=j/(inf ** i)%inf
				out |= l
			line=binary(j*inf+out,ws+width)
			matrix.append(line)
		#for i in matrix:
		#	print i
		#print vars,ws
		self.contents['or']=[LogicFunction(matrix,vars,ws)]
		#print self.contents['or']
			
	def lpm_inv(self):
		"""
			inverter
		"""
		width=self.getprop('lpm_width')
		matrix=[]
		inf=2 ** width
		for i in range(inf):
			line=binary(i,width)+binary((inf-1)^i,width)
			matrix.append(line)
		vars=self.makebus("data%u",width)+self.makebus("result%u",width)
		self.contents['inv']=[LogicFunction(matrix,vars,width)]
			
	def lpm_ff(self):
		"""
			LPM_FF megafunction
			implement lpm_width number of D flip-flops,
			and the necessary switching logic
		"""
		rd={}
		#FIXME should have been called the device's generator for flip-flop instead of constructing it here
		width=self.getprop('lpm_width')
		have_enable=self.hasportwithname("enable")
		have_sset=self.hasportwithname("sset")
		have_sclr=self.hasportwithname("sclr")
		have_testenab=self.hasportwithname("testenab")
		have_testin=self.hasportwithname("testin")
		have_testout=self.hasportwithname("testout")
		assert not (have_testenab or have_testin or have_testout), "Test port not yet implemented"
		fftype=self.getprop('lpm_fftype','DFF')
		assert fftype=='DFF', "only D flip-flop is implemented yet"
		pvalue=self.getprop('lpm_pvalue',0)
		contents=[]
		for bit in range(width):
			RD={"D":"data%u"%bit, "clock":"inclock", "Q":"q%u"%bit,"/Q":"/q%u"%bit}
			c=DFlipFlop(renamedict=RD,initial=int((pvalue&(2 ** bit))>0))
			contents.append(c)
		funcs=[]
		andtable=[ "000", "010", "100", "111"]
		onetable=[ "00", "11"]
		if have_enable:
			clk=LogicFunction(andtable,["enable","clock","inclock"],2)
		else:
			clk=LogicFunction(onetable,["clock","inclock"],2)
		
		if have_sset:
			f=LogicFunction(andtable,["sset","inclock","aset"],2)
			clk=clk.mold(f)
		if have_sclr:
			f=LogicFunction(andtable,["sclr","inclock","aclr"],2)
			clk=clk.mold(f)
		#print clk
		contents.append(clk)
		self.contents['ff']=contents
		
		
	def lpm_add_sub(self):
		"""
			LPM_ADD_SUB megafunction
		"""
		width=self.getprop('lpm_width')
		representation=self.getprop('lpm_represenTation',"signed")
		assert (representation == 'signed') or (representation == 'unsigned'), "Wrong representation " + representation
		direction=self.getprop('lpm_direction',"default")
		if 'unused' == direction:
			direction = 'default'
		assert (direction == 'add') or (direction == 'sub') or (direction == 'default'), "Wrong lpm_direction " + direction
		pipeline=self.getprop('lpm_pipeline',0)
		assert pipeline == 0, "lpm_pipeline not yet implemented"
		inputs = self.makebus("dataa%u",width)
		inputs += self.makebus("datab%u",width)
		outputs=self.makebus("result%u",width)
		if self.hasportwithname("cin"):
			inputs.append("cin")
			has_cin=True
			cins=[0,1]
		else:
			has_cin=False
			cins=[0]
		if self.hasportwithname("cout"):
			outputs.append("cout")
			has_cout=True
		else:
			has_cout=False
		if direction == 'default':
			inputs.append("add_sub")
			has_add_sub=True
			addsubs=[0,1]
		else:
			has_add_sub=False
			if direction=="add":
				addsubs=[1]
			else:
				addsubs=[0]
		if self.hasportwithname("owerflow"):
			outputs.append("overflow")
			has_overflow=True
		else:
			has_overflow=False
		inf=2 ** width
		zero=2 ** (width-1)
		matrix=[]
		vars=inputs+outputs
		for a in range(inf):
			s_a=binary(a,width)
			if representation=='signed':
				if a >= zero:
					a=a-inf
			for b in range(inf):
				s_b=binary(b,width)
				if representation == 'signed':
					if b >= zero:
						b=b-inf
				for cin in cins:
					for add_sub in addsubs:
						#print 'a=%s'%a
						#print 'b=%s'%b
						#print 'zero=%s'%zero
						cout=0
						overflow=0
						if ((a+b+cin)%inf) > zero:
							cout=1
						if add_sub:
							result=a+b+cin
						else:
							result=a-b+cin-1
						negative=0
						#print 'result=%s'%result
						if representation == 'signed':
							negative = (result < 0)
							if (result >= zero) or (result < -zero):
								overflow = 1
								result=result%zero
							#print 'result1=%s'%result
							if result == (-zero):
								result=0
							else:
								result %= zero
							#print 'result2=%s'%result
							if negative:
								result=result + negative * zero
							#print 'result3=%s'%result
						else:
							if (result < 0) or (result >= inf):
								overflow = 1
							result=result%inf
						line=s_a+s_b
						if has_cin:
							line += "%u"%cin
						if has_add_sub:
							line += "%u"%add_sub
						line+=binary(result,width)
						if has_cout:
							line += "%u"%cout
						if has_overflow:
							line += "%u"%overflow
						#print 'result=%s'%result
						#print 'cin=%s'%cin
						#print 'cout=%s'%cout
						#print 'overflow=%s\n'%overflow
						#print 'negative=%s\n'%negative


						#checkline(line,vars)
						matrix.append(line)
		f=LogicFunction(matrix,vars,len(inputs))
		f.simplify()
		self.contents['add_sub']=[f]

