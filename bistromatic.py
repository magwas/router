"""
	logic optimization of switches
	the espresso-mv algoritm is described in http://www.eecs.berkeley.edu/Pubs/TechRpts/1986/ERL-86-65.pdf
	I do not understand it, so I have implemented what I figured out, which may or may not resembles to espresso.
"""

class AbstractObject:
	"""
		AbstractObject is describing some object (logic switch, counter, lut, flip-flop, etc), in an abstract manner.
		AbstractObjects can be simplified, joined, and meld if they can agree on how to do that.
		After they amended with device-specific knowledge, they can place themselves.
	"""
	def __init__(self,vars,ilen=0,iolen=0,objtype=None):
		"""
			vars is a list of strings naming the inputs and outputs of the object
			ilen is the number of inputs
			iolen is the number of bidirectional interfaces
			the set of inputs is vars[:ilen]
			the set of outputs is vars[ilen-iolen:]
		"""
		self.vars=vars
		self.funcdict={}
		self.fixvars()
		self.ilen=ilen
		self.iolen=iolen
		self.objtype=objtype

	def copy(self):
		"""
			copy constructor
		"""
		n=AbstractObject([]+self.vars,self.ilen,self.iolen,self.objtype)
		return n

	def renamevar(self,fromname,toname):
		"""
			renames a variable
		"""
		#print "renaming %s to %s"%(fromname,toname)
		#print self.vars
		p=self.vars.index(fromname)
		self.vars[p]=toname
		for (k,v) in self.funcdict.items():
			if v==fromname:
				self.funcdict[k]=toname
		#print self.vars
	def instantiate(self,name):
		n=self.copy()
		for i in self.vars:
			n.renamevar(i,"%s:%s"%(name,i))
		return n

	def check(self):
		"""
			check if there is no inconsistency
			should be implemented by the derived classes
		"""
		raise NotImplementedError

	def simplify(self,check=None):
		"""
			makes optimizations within the object if possible
			should be implemented by the derived classes
		"""
		raise NotImplementedError

	def getDomain(self):
		"""
			gets the domain ([:self.ilen])
		"""
		return self.filter(range(self.ilen))

	def getOutputs(self):
		"""
		"""
		return self.vars[self.ilen-self.iolen:]
	def createmapping(self,other):
		"""
			creates the mapping other.vars->self.vars, but only on inputs
			e.g. [0,3,1] means ABCD -> ADB
		"""
		mapping=[]
		for i in range(other.ilen):
			pos=None
			for j in range(self.ilen):
				if other.vars[i] == self.vars[j]:
					pos=j
			assert pos is not None, "cannot map"
			mapping.append(pos)
		#print "mapping",other,self,mapping
		return mapping

	def fixvars(self):
		"""
			A convenience function initializing self.funcdict,
			which holds function:varname pairs
			initially each function equals its var name
		"""
		for i in self.vars:
			self.funcdict[i]=i

	def __str__(self):
		return "%s(%s,%s,%s)"%(self.objtype,self.funcdict,self.ilen,self.iolen)
			
	def join(self,myoutput,other,otherinput):
		"""
		returns a abstract object created by joining self and other through
		self.myoutput=other.otherinput
		if it is impossible, return None
		implemented by derived classes knowing each other
		"""
		raise NotImplementedError

	def mold(self,other):
		"""
		molds two abstract objects into one if it is possible
		returns None if impossible
		"""
		raise NotImplementedError

class DFlipFlop(AbstractObject):
	"""
		A D Flip-Flop have
			an input (D)
			a clock input (clock)
			a asynchronous set input (aset)
			a asynchronous clear input (aclr)
			an output (Q)
			an inverting output (/Q)
	"""
	def __init__(self,initial=0,renamedict=None):
		"""
			renamedict is a dictionary of function:newname items
		"""
		vars=["D","clock","aset","aclr","Q","/Q"]
		AbstractObject.__init__(self,vars,4,objtype="DFlipFlop")
		if renamedict:
			for (k,v) in renamedict.items():
				self.renamevar(k,v)
		self.initial=initial
	def copy(self):
		n=DFlipFlop(self.initial,renamedict=self.funcdict)
		return n
		

class LogicFunction(AbstractObject):
	"""
	A logic function contains a set of inputs, a set of outputs, and the truth table.
	"""
	def __init__(self,table,vars,ilen=None):
		"""
			table is the truth table
			ilen is the number of input variables, if appicable
			vars is a list of variable names. If applicable, inputs first.
			iolen is always zero
		"""
		AbstractObject.__init__(self,vars,ilen,objtype="LogicFunction")
		self.table=table
		self.check()
	def copy(self):
		n=LogicFunction([]+self.table,[]+self.vars,self.ilen)
		return n

	def __str__(self):
		return "%s([\n'%s'],%s,%s,%s)"%(self.objtype,"',\n'".join(self.table),self.vars,self.funcdict,self.ilen)
	def resultfor(self,input):
		"""
			returns the result for a given input
		"""
		for line in self.table:
			if self.rowIsEqual(line,input,len(input)):
				return line[len(input):]
		return "-"*(len(self.vars)-self.ilen)

	def rowIsEqual(self,A,B,len):
		"""
			whether A[:len] == B[:len]
			- is equal to anything
			FIXME: can be optimized
		"""
		for i in range(len):
			a=A[i]
			b=B[i]
			if (a != b) and (a != '-') and (b != '-'):
				return False
		return True
			
	def check(self):
		"""
			check if there is no inconsistency in the table
		"""
		if not self.ilen:
			return
		for rowa in range(len(self.table)-1):
			for rowb in range(rowa+1,len(self.table)):
				A=self.table[rowa]
				B=self.table[rowb]
				assert not (self.rowIsEqual(A,B,self.ilen) and (A[self.ilen+1:] != B[self.ilen+1:])), "inconsistency"

	def _simplifyrows(self,rowa,rowb):
		"""
		returns None or res
			None means no optimization done
			res is the two molded rows
		"""
		if rowa==rowb:
			return rowa
		for p in range(self.ilen):
			if rowa[p] == rowb[p]:
				continue
			if rowa[p+1:] == rowb[p+1:]:
				#print "---",p,rowa,rowb
				A=list(rowa)
				A[p]='-'
				#print "".join(A)
				return "".join(A)
			else:
				return None
					
				
	def simplify(self,check=None):
		"""
			AB+/AB=B
			where n<=ilen
			if we can found two rows where everything is the same but the nth position, we can reduce it
			to one row with '-' in the nth position
		"""
		#print "before:",self
		optimized=True
		while optimized:
			optimized=False
			for rowa in range(len(self.table)-1):
				a=self.table[rowa]
				if a:
					for rowb in range(rowa+1,len(self.table)):
						b=self.table[rowb]
						if not b:
							continue
						res=self._simplifyrows(a,b)
						if res:
							#print self.table
							optimized=True
							self.table[rowa]=None
							self.table[rowb]=res
							#print self.table
			while None in self.table:
					self.table.remove(None)
		#print "after:",self
		if True or check:
			self.check()

	def expand(self,line):
		"""
		"""
		pos=line.find('-')
		if -1 == pos:
			return [line]
		l0=list(line)
		l1=list(line)
		l0[pos]='0'
		l1[pos]='1'
		return self.expand("".join(l0))+self.expand("".join(l1))
	def permutate(self,other):
		"""
			permutates the domain of self and other
			expands '-'
			returns the permutated function
		"""
		newdom=[]
		len1=self.ilen
		len2=other.ilen
		for line1 in self.table:
			for line2 in other.table:
				line=line1[:len1]+line2[:len2]
				lines=self.expand(line)
				newdom+=lines
		newvars=self.vars[:len1]+other.vars[:len2]
		return LogicFunction(newdom,newvars,len(newvars))

	def computeresult(self,other):
		"""
			computes the result columns over domain of other
		"""
		#print "computeresult",self,other
		#print "mapping=",other.createmapping(self)
		dom2=other.filter(other.createmapping(self))
		#print "dom2",dom2
		result=[]
		for line in dom2.table:
			result.append(self.resultfor(line))
		dom2.table=result
		dom2.vars=self.getOutputs()
		dom2.ilen=0
		return dom2
			
	def filter(self,filterlist):
		"""
			rearranges columns in dom according to filterlist
		"""
		newdom=[]
		newinputs=[]
		#print "filter",self,filterlist
		for line in self.table:
			row=[]
			for i in filterlist:
				row.append(line[i])
			newdom.append("".join(row))
		for i in filterlist:
			newinputs.append(self.vars[i])
		#print "filter",newdom,newinputs
		f=LogicFunction(newdom,newinputs,len(newinputs))
		return f

	def reduceinputs(self):
		"""
			inputlist is a list of input names
			we filter out duplicate inputs, and then filter the domain accordingly
			return new inputlist and new domain
		"""
		newinputs=[]
		filterlist=[]
		for i in range(self.ilen-1):
			reduce=0
			for j in range(i+1,self.ilen):
				if self.vars[i] == self.vars [j]:
					#print i,"=",j
					reduce=1
					break
			if not reduce:
				newinputs.append(self.vars[i])
				filterlist.append(i)
		i=i+1
		newinputs.append(self.vars[i])
		filterlist.append(i)
		return self.filter(filterlist)

	def addcols(self,other):
		"""
			adds the columns of other function to ourselves
			the other function's output is appended to self's output
		"""
		assert len(self.table) == len(other.table), "incompatible columns to add"
		res=[]
		for i in range(len(self.table)):
			self.table[i]=self.table[i]+other.table[i]
		self.vars=self.vars+other.vars
			
	def join(self,myoutput,other,otherinput):
		"""
		returns a function created by the equation
		self.myoutput=other.otherinput
		F:= (a) -> (b0,b) //self
		G:= (c0,c) -> (d) //other
		d:=F|b //other.otherinput=self.myoutput
		H:= (a,c0) -> (b0,b,d) where F and and F(a)=b (=c)
		// we return H
		first we create the domain a x (c0,c)
		than we compute F(a)|b0,F(a)|b and G(c0,F(a)|b) on domain
		than we reduce it.
		"""
		if other.objtype != 'LogicFunction':
			return None
		# create domain
		domain=self.permutate(other)
		domain=domain.reduceinputs()
		# compute F over the domain
		Fout=self.computeresult(domain)
		# join Fout to the domain
		domain.addcols(Fout)
		# now we can compute G(c0,F(a)|b) over the domain
		#print "domain=",domain
		cindex=domain.vars.index(myoutput)
		bindex=domain.vars.index(otherinput)
		domain.vars[bindex]=myoutput
		domain.vars[cindex]=otherinput
		ilen=domain.ilen
		domain.ilen=cindex+1
		Gout=other.computeresult(domain)
		# join Gout to the domain
		domain.addcols(Gout)
		domain.check()
		# drop column for b and c
		vlist=range(len(domain.vars))
		vlist[bindex]=None
		vlist[cindex]=None
		vlist.remove(None)
		vlist.remove(None)
		#ilen=domain.ilen-1
		domain=domain.filter(vlist)
		domain.ilen=ilen-1
		domain.check()
		domain.simplify()
		domain.check()
		return domain

	def mold(self,other):
		"""
		molds two functions into one
		F:= (a) -> (b) //self
		G:= (c) -> (d) //other
		H:= (a,b) -> (c,d) 
		// we return H
		first we create the domain a x c
		than we compute F(a) G(c) on domain
		than we reduce it.
		"""
		if other.objtype != 'LogicFunction':
			return None
		# create domain
		domain=self.permutate(other)
		domain=domain.reduceinputs()
		# compute F over the domain
		Fout=self.computeresult(domain)
		Gout=other.computeresult(domain)
		# join Fout to the domain
		domain.addcols(Fout)
		# join Gout to the domain
		domain.addcols(Gout)
		domain.simplify()
		domain.check()
		return domain

