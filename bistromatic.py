"""
	logic optimization of switches
	the espresso-mv algoritm is described in http://www.eecs.berkeley.edu/Pubs/TechRpts/1986/ERL-86-65.pdf
	I do not understand it, so I have implemented what I figured out, which may or may not resembles to espresso.
"""


dirs = [
"notconnected",
"input",
"output",
"inout"]
directions={}
for i in range(len(dirs)):
	directions[dirs[i]]=i
INPUT=directions['input']
OUTPUT=directions['output']
INOUT=directions['inout']


class AbstractObject:
	"""
		AbstractObject is describing some object (logic switch, counter, lut, flip-flop, etc), in an abstract manner.
		AbstractObjects can be simplified, joined, and meld if they can agree on how to do that.
		After they amended with device-specific knowledge, they can place themselves.
	"""
	def __init__(self,vars,ilen=0,iolen=0,objtype=None,name=""):
		"""
			vars is a list of strings naming the inputs and outputs of the object
			ilen is the number of inputs
			iolen is the number of bidirectional interfaces
			the set of inputs is vars[:ilen]
			the set of outputs is vars[ilen-iolen:]
			connections is a set of (pin,direction,object,otherpin) tuples.
			Direction is either INPUT or OUTPUT, for bidirectional connections two tuples have to be added.
		"""
		self.name=name
		self.vars=vars
		self.funcdict={}
		self.fixvars()
		self.ilen=ilen
		self.iolen=iolen
		self.objtype=objtype
		self.connections=set()

	def getDirectionOfPort(self,name):
		"""
			Gets direction of named port
		"""
		if name in self.vars:
			dir=0
			index=self.vars.index(name)
			if index < self.ilen:
				dir = dir | directions ["input"]
			if index >= self.ilen-self.iolen:
				dir = dir | directions ["output"]
			#print name,dir
			return dir
		return directions["notconnected"]

	def copy(self):
		"""
			copy constructor
		"""
		raise NotImplementedError, "%s.copy()"%self.__class__

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

	def _print(self):
		return "%s(%s,%s,%s,%s)"%(self.objtype,self.funcdict,self.ilen,self.iolen,self.connections)
	def __repr__(self):
		return "%s(%s)"%(self.objtype,self.name)
			
	def join(self,myoutput,other,otherinput):
		"""
		returns a abstract object created by joining self and other through
		self.myoutput=other.otherinput
		if it is impossible, return None
		implemented by derived classes knowing each other
		"""
		r = other.joined(otherinput,self,myoutput)
		if None != r:
			return r
		return None
	def joined(self,myinput,other,otheroutput):
		"""
		same as join, but we are connected at our input
		"""
		return None

	def mold(self,other):
		"""
		molds two abstract objects into one if it is possible
		returns None if impossible
		"""
		raise NotImplementedError

	def connectto_old(self,pin,other,otherpin):
		"""
			adds a connection
		"""
		if self==other:
			return
		mydir=self.getDirectionOfPort(pin)
		otherdir=other.getDirectionOfPort(otherpin)
		#print "connectto(%s,%s,%s,%s) (%s,%s)"%(self,pin,other,otherpin,mydir,otherdir)
		if (OUTPUT & mydir) and (INPUT & otherdir):
			self.connections.add((pin,OUTPUT,other,otherpin))
			other.connections.add((otherpin,INPUT,self,pin))
		elif (INPUT & mydir) and (OUTPUT & otherdir):
			self.connections.add((pin,INPUT,other,otherpin))
			other.connections.add((otherpin,OUTPUT,self,pin))
		else:
			assert False, "missed connectto(%s(%s),%s,%s(%s),%s) (%s,%s)"%(self,self.vars,pin,other,other.vars,otherpin,mydir,otherdir)

	def connectto(self,pin,other,otherpin):
		"""
			adds a connection
		"""
		#print "connectto",self,pin,other,otherpin
		if self==other:
			#print "self=other"
			return
		self.connections.add((pin,OUTPUT,other,otherpin))
		other.connections.add((otherpin,INPUT,self,pin))

	def disconnectfrom(self,pin,other,otherpin):
		"""
			inverse of connectto
		"""
		if self==other:
			return
		#print " disconnectfrom(%s,%s,%s,%s) "%(self,pin,other,otherpin)
		assert (pin,OUTPUT,other,otherpin) in self.connections, "missed discard (%s,%s,%s,%s) in %s(%s)"%(pin,OUTPUT,other,otherpin,self,self.connections)
		assert (otherpin,INPUT,self,pin) in other.connections, "missed discard (%s,%s,%s,%s) in %s(%s)"%(otherpin,INPUT,self,pin,other,other.connections)
		self.connections.discard((pin,OUTPUT,other,otherpin))
		other.connections.discard((otherpin,INPUT,self,pin))

	def replaceconn(self,oldie,newie):
		"""
		replaces oldie with newie in all connections
		replaces in the connected side as well
		"""
		inputs=[]
		outputs=[]
		for (pin,d,ob,opin) in self.connections:
			if ob == oldie:
				if d == OUTPUT:
					outputs.append((pin,opin))
				else:
					inputs.append((opin,pin))
		for (pin,opin) in outputs:
			self.disconnectfrom(pin,oldie,opin)
			self.connectto(pin,newie,opin)
			#print (pin,opin),"output moved from",oldie,"to",newie,"in",self._print()
		for (opin,pin) in inputs:
			oldie.disconnectfrom(opin,self,pin)
			newie.connectto(opin,self,pin)
			#print (opin,pin),"input moved from",oldie,"to",newie,"in",self._print()

	def connectionswith(self,other,direction=None):
		"""
			list connections between self and other
			if direction is given, then only connections in that direction are listed
		"""
		l=[]
		for (pin,d,ob,opin) in self.connections:
			if (ob == other) and ((direction==None) or (direction==d)): 
				l.append((pin,d,opin))
		return l
	def hasoutputs(self):
		"""
			Do we have otputs yet?
		"""
		for (pin,d,ob,opin) in self.connections:
			if d==OUTPUT:
				return True
		return False
	def cloneoutput(self,oldie,newie):
		"""
			Clones connections to oldie to newie
		"""
		cons=[]
		for (pin,d,ob,opin) in self.connections:
			if (ob == oldie) and ( d == OUTPUT):
				cons.append((pin,newie,opin))
		for (pin,newie,opin) in cons:
			#print "cloning",oldie,opin,"to",newie, "in",self
			self.connectto(pin,newie,opin)

	def _forgetobj(self,oldie):
		"""
			forget about object oldie
		"""
		cons=[]
		for (pin,d,ob,opin) in self.connections:
			if ob == oldie:
				cons.append((pin,d,opin))
		for (pin,d,opin) in cons:
				self.connections.discard((pin,d,oldie,opin))
	def forget(self):
		"""
			forget about myself: delete our connections
		"""
		for (pin,d,ob,opin) in self.connections:
			#print "%s still have connection (%s,%s,%s,%s)"%(self,pin,d,ob,opin)
			ob._forgetobj(self)
		

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
	def __init__(self,initial=0,renamedict=None,name=""):
		"""
			renamedict is a dictionary of function:newname items
		"""
		vars=["D","clock","aset","aclr","Q","/Q"]
		AbstractObject.__init__(self,vars,4,objtype="DFlipFlop",name=name)
		if renamedict:
			for (k,v) in renamedict.items():
				self.renamevar(k,v)
		self.initial=initial
	def copy(self):
		n=DFlipFlop(self.initial,renamedict=self.funcdict,name=self.name)
		return n
		
class IOPin(AbstractObject):
	"""
		An I/O pin have one port with direction, and no logic
	"""
	def __init__(self,direction,name="",eliminable=True):
		self.direction=direction
		self.eliminable=eliminable
		if direction & INPUT:
			ilen=1
		else:
			ilen=0
		if direction & OUTPUT:
			iolen=ilen
		else:
			iolen=0
		AbstractObject.__init__(self,[name],objtype="IOPin",ilen=ilen,iolen=iolen,name=name)
	
	def copy(self):
		n=IOPin(self.direction,self.name,self.eliminable)
		return n

	def getDirectionOfPort(self,name):
		"""
			PIN ports are treated as bidirectional
		"""
		return INOUT
	def _print(self):
		return "%s(%s,%s,%s)"%(self.objtype,self.direction,self.vars[0],self.connections)

	def join(self,myoutput,other,otherinput):
		"""
			We connect all our connections with each other, and commit suicide

		"""
		if not self.eliminable:
			r = other.joined(otherinput,self,myoutput)
			return r
		dis=set()
		con=set()
		#print self.connections
		for (pin1,d1,ob1,opin1) in self.connections:
			for (pin2,d2,ob2,opin2) in self.connections:
				#print (pin1,d1,ob1,opin1),(pin2,d2,ob2,opin2) 
				if (d1==INPUT) and (d2 == OUTPUT):
					#print "ez:",(ob1,opin1,self,pin1)
					dis.add((ob1,opin1,self,pin1))
					dis.add((self,pin1,ob2,opin2))
					con.add((ob1,opin1,ob2,opin2))
		#print dis
		for (o1,p1,o2,p2) in dis:
			o1.disconnectfrom(p1,o2,p2)
		for (o1,p1,o2,p2) in con:
			o1.connectto(p1,o2,p2)
		#print dis,self.connections
		return ([],[self])
	def joined(self,myinput,other,otheroutput):
		if not self.eliminable:
			return None
		return self.join(myinput,other,otheroutput)

class LogicFunction(AbstractObject):
	"""
	A logic function contains a set of inputs, a set of outputs, and the truth table.
	"""
	def __init__(self,table,vars,ilen=None,name=""):
		"""
			table is the truth table
			ilen is the number of input variables, if appicable
			vars is a list of variable names. If applicable, inputs first.
			iolen is always zero
		"""
		AbstractObject.__init__(self,vars,ilen,objtype="LogicFunction",name=name)
		self.table=table
		self.check()
	def copy(self):
		n=LogicFunction([]+self.table,[]+self.vars,self.ilen,name=self.name)
		return n

	def _print(self):
		return "%s([\n'%s'],%s,%s,%s,%s)"%(self.objtype,"',\n'".join(self.table),self.vars,self.funcdict,self.ilen,self.connections)
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
				assert not (self.rowIsEqual(A,B,self.ilen) and (A[self.ilen:] != B[self.ilen:])), "inconsistency: %s %s len=%u"%(A,B,self.ilen)

	def simplify(self,check=None):
		"""
			AB+/AB=B
			where n<=ilen
                        for each row ex 10-1:
				target is '1' or '0' (:=p) changed to -. it is done for each non-dc digits, eg -0-1 
				and we look for
					row in table
					^p in table
					then (^p and - -> 1) and (^p and - -> 0) in table, eg 0001 and 0011
		"""
		#print "before:",self
		optimized=True
		while optimized:
			optimized=False
			nt=[]
			for row in range(len(self.table)-1):
				a=self.table[row]
				#print a
				if a is None:
					continue
				if a in self.table[row+1:]:
					optimized=True
					x=row
					while a in self.table[x+1:]:
						x=self.table[x+1:].index(a)+x+1
						self.table[x]=None
					#print self.table,nt
				for p in range(self.ilen):
					#print a,p
					if '0' == a[p]:
						target=a[:p]+'1'+a[p+1:]
					elif '1' == a[p]:
						target=a[:p]+'0'+a[p+1:]
					else:
						continue
					if target in self.table[row+1:]:
						self.table[row]=None
						nt.append(a[:p]+'-'+a[p+1:])
						optimized=True
						x=row
						while target in self.table[x+1:]:
							x=self.table[x+1:].index(target)+x+1
							self.table[x]=None
						#print self.table,nt
						break
					for r in range(self.ilen):
						if a[r] != '-':
							continue
						t1=target[:r]+'1'+target[r+1:]
						t2=target[:r]+'0'+target[r+1:]
						if (t1 in self.table[row+1:]) and ( t2 in self.table[row+1:]):
							optimized=True
							opt=True
							self.table[row]=None
							nt.append(target[:r]+'-'+target[r+1:])
							x=row
							while t1 in self.table[x+1:]:
								x=self.table[x+1:].index(t1)+x+1
								self.table[x]=None
							x=row
							while t2 in self.table[x+1:]:
								x=self.table[x+1:].index(t2)+x+1
								self.table[x]=None
							#print self.table,nt
			while None in self.table:
					self.table.remove(None)
			self.table=nt+self.table
			#print self.table
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
		r = other.joined(otherinput,self,myoutput)
		if None != r:
			return r
		#print "joining %s:%s -> %s:%s"%(self,myoutput,other,otherinput)
		if other.objtype != 'LogicFunction':
			return None
		#print "joining",self._print(),other._print()
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
		#print domain._print()
		domain.check()
		domain.simplify()
		domain.check()
		domain.name=self.name+'+'+other.name

		disc=set()
		con=set()
		for (pin,d,ob,opin) in self.connections:
			if d == INPUT:
				disc.add((ob,opin,self,pin))
				con.add((ob,opin,domain,pin))
			elif d == OUTPUT:
				disc.add((self,pin,ob,opin))
				if pin != myoutput:
					con.add((domain,pin,ob,opin))
		for (pin,d,ob,opin) in other.connections:
			if d == INPUT:
				disc.add((ob,opin,other,pin))
				if pin != otherinput:
					con.add((ob,opin,domain,pin))
			elif d == OUTPUT:
				disc.add((other,pin,ob,opin))
				con.add((domain,pin,ob,opin))

		for (o1,pin1,o2,pin2) in disc:
			o1.disconnectfrom(pin1,o2,pin2)
		for (o1,pin1,o2,pin2) in con:
			o1.connectto(pin1,o2,pin2)

		rl=[other]
		if not self.hasoutputs():
			rl.append(self)
		#print "result",domain
		return ([domain],rl)

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

