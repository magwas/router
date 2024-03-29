from edif import EdifCell
from bistromatic import LogicFunction,DFlipFlop, INPUT, OUTPUT
from itoa import itoa,binary

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
			this fill in self.content
		"""
		#print self.properties
		#print "parsing lpm_library/"+self.properties['lpm_type']
		lpm_type=self.properties['lpm_type'].lower()
		gener=getattr(self,lpm_type,None)
		assert gener , "No generator found for " + self.properties['lpm_type']
		gener()
		#print "generating pins for",self.name,self.ports.items()
		for (name,pin) in self.ports.items():
			pdir = pin.direction
			for ob in self.content:
				#print "ob=",ob
				if ob == pin:
					continue
				if name in ob.vars:
					odir = ob.getDirectionOfPort(name)
					if (odir & INPUT) and ( pdir & INPUT):
						pin.connectto(name,ob,name)
					if (odir & OUTPUT) and ( pdir & OUTPUT):
						ob.connectto(name,pin,name)
					assert odir & pdir , "problem with directions: %s %s"%(pin._print(),ob._print())
					#print ob.connections,pin.connections
			#print pin,pin.connections
		#for c in self.content:
		#	print c

	
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
		pins=self.makebus('result%u',width,nochop=True)
		self.content.append(self.device.LogicFunction(matrix=[matrix],vars=pins,ilen=0,name="lpm_const%s"%value))

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
		outputs=self.makebus('result%u',width,nochop=True)
		for i in range(size):
			for j in range(width):
				inputs.append("data%ux%u"%(i,j))
		sels=self.makebus("sel%u",swidth,nochop=True)
		vars=inputs+sels+outputs
		numinputs=swidth+ws
		matrix=[]
		for i in range(2**width):
			out=binary(i,width)
			for s in range(size):
				sel=binary(s,swidth)
				input="-"*(width*s)+out+"-"*(width*(size-s-1))
				matrix.append(input+sel+out)
		self.content.append(self.device.LogicFunction(matrix=matrix,vars=vars,ilen=numinputs,name="mux %ux%u"%(width,size)))

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
		self.content.append(self.device.LogicFunction(matrix=matrix,vars=vars,ilen=ws,name="or"))
			
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
		self.content.append(self.device.LogicFunction(matrix=matrix,vars=vars,ilen=width,name="inv"))
			
	def lpm_ff(self):
		"""
			LPM_FF megafunction
			implement lpm_width number of D flip-flops,
			and the necessary switching logic
			calls device's createFlipFlops to do the job
			there are so many configuration options, that we just throw self in
		"""
		#width=self.getprop('lpm_width')
		#fftype=self.getprop('lpm_fftype','DFF')
		#avalue=self.getprop('lpm_avalue','1'*width)
		#pvalue=self.getprop('lpm_pvalue',0)
		#svalue=self.getprop('lpm_svalue','1'*width)
		#have_enable=self.hasportwithname("enable")
		#have_sset=self.hasportwithname("sset")
		#have_sclr=self.hasportwithname("sclr")
		#have_aset=self.hasportwithname("aset")
		#have_aclr=self.hasportwithname("aclr")
		have_sload=self.hasportwithname("sload")
		have_aload=self.hasportwithname("aload")
		have_testenab=self.hasportwithname("testenab")
		have_testin=self.hasportwithname("testin")
		have_testout=self.hasportwithname("testout")
		assert (not (have_aload or have_sload)) or (fftype != 'DFF'), "have aload or sload while fftype is DFF"
		assert (not (have_testenab or have_testin or have_testout)) or (have_testenab and have_testin and have_testout), "test ports are present, but not all of them"
		self.content.extend(self.device.createFlipFlops("FF",self))
		
		
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
		direction=direction.lower()
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
		f=self.device.LogicFunction(matrix=matrix,vars=vars,ilen=len(inputs),name="adder")
		f.simplify()
		self.content.append(f)

