"""
	logic optimization of switches
	the espresso-mv algoritm is described in http://www.eecs.berkeley.edu/Pubs/TechRpts/1986/ERL-86-65.pdf
	I do not understand it, so I have implemented what I figured out, which may or may not resembles to espresso.
"""

from itoa import binary

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
		#print "eliminating",self
		#print "disconnected:",dis
		#print "connected:",con
		#print "remaining connections: %s"%(self.connections)
		#print "\n"
		for (pin1,d1,ob1,opin1) in self.connections:
			print "\t",ob1.connections
		return ([],[self])
	def joined(self,myinput,other,otheroutput):
		if not self.eliminable:
			return None
		return self.join(myinput,other,otheroutput)

class LogicFunction(AbstractObject):
	"""
	A logic function contains a set of inputs, a set of outputs, and the truth table.
	"""
	def __init__(self,terms=None,vars=None,ilen=0,name="",matrix=None):
		"""
			terms is a dictionary of (name: table) items, where 
				name is the name of output
				table is the truth table of that output (true plan)
			ilen is the number of input variables, if appicable
			vars is a list of variable names. If applicable, inputs first.
			example:
				{not=^a,and= a&b,or = a | b} is constructed as:
				LogicFunction(["a","b","not","and","or"],
					{"not":["0-1"],
					"and":["111"],
					"or":["-11"],["1-1"},2)
		"""
		if vars==None:
			vars=[]
		AbstractObject.__init__(self,vars,ilen,objtype="LogicFunction",name=name)
		if (terms is None):
			self.terms={}
			if (matrix is not None):
				self.loadmatrix(matrix)
		else:
			self.terms=terms
		self.check()
	def loadmatrix(self,matrix):
		"""
			loads a matrix into terms
		"""
		outvars=self.vars[self.ilen:]
		for v in outvars:
			self.terms[v]=[]
		for line in matrix:
			base=line[:self.ilen]
			for v in outvars:
				p=self.vars.index(v)
				l=base+line[p]
				self.terms[v].append(l)
	def copy(self):
		n=LogicFunction(self.terms.copy(),[]+self.vars,self.ilen,name=self.name)
		return n

	def value(self,inputs,inputbuses=None,outputbuses=None):
		"""
			return the logic function's value for the given inputs
			inputbuses is a list of input variables or a list of thereof
			outputbuses is the same for output variables
			inputs is a list of values for output buses
		"""
		if inputbuses is None:
			inputbuses=self.vars[self.ilen:]
		if outputbuses is None:
			outputbuses=self.vars[:self.ilen]
		inputval=['0']*self.ilen
		for i in range(len(inputbuses)):
			ival=inputs[i]
			if type(ival) != str:
				ival=int(ival)
			else:
				ival=int(ival,2)

			bus=inputbuses[i]
			if type(bus) == list:
				ival=binary(ival,len(bus))
				for j in range(len(bus)):
					line=bus[j]
					pos=self.vars.index(line)
					inputval[pos]=ival[j]
			else:
				pos=self.vars.index(bus)
				inputval[pos]=binary(ival,1)
		input="".join(inputval)
		outputvars=self.vars[self.ilen:]
		outputs=[None]*len(outputvars)
		#print input,outputvars
		res=[]
		for i in range(len(outputs)):
			#print "term",outputvars[i]
			outputs[i]=self.resultfor(input,outputvars[i])
		#print "outputs=",outputs
		for i in range(len(outputbuses)):
			bus=outputbuses[i]
			if type(bus) == list:
				r=0
				for v in bus:
					pos=outputvars.index(v)
					r= r <<1
					r=r+int(outputs[pos])
				res.append(r)
			else:
				pos=outputvars.index(bus)
				res.append(outputs[pos])
		return(res)
	def renamevar(self,fromname,toname):
		"""
			renames a variable
		"""
		AbstractObject.renamevar(self,fromname,toname)
		if fromname in self.terms:
			self.terms[toname]=self.terms[fromname]
			del(self.terms[fromname])

	def _print(self):
		return "%s([\n'%s'],%s,%s,%s,%s)"%(self.objtype,self.terms,self.vars,self.funcdict,self.ilen,self.connections)
	def resultfor(self,input,output):
		"""
			returns the result for a given input on output
		"""
		for line in self.terms[output]:
			#print line
			if self.rowIsEqual(line,input,len(input)):
				return line[-1]
		return '0'

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
			check if there is no inconsistency in the terms
		"""
		if not self.ilen:
			return
		for var in self.vars[self.ilen:]:
			table=self.terms[var]
			for rowa in range(len(table)-1):
				for rowb in range(rowa+1,len(table)):
					A=table[rowa]
					B=table[rowb]
					assert not (self.rowIsEqual(A,B,self.ilen) and (A[self.ilen:] != B[self.ilen:])), "inconsistency: %s %s len=%u"%(A,B,self.ilen)

	def simplify(self,check=None):
		#print "before:",self,self.terms
		for (key,table) in self.terms.items():
			self.terms[key]=self._simplify(table)
		#print "after:",self,self.terms
		if True or check:
			self.check()
	def _simplify(self,table):
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
			#print "table",table
			for row in range(len(table)-1):
				a=table[row]
				#print a
				if a is None:
					continue
				if a in table[row+1:]:
					optimized=True
					x=row
					while a in table[x+1:]:
						x=table[x+1:].index(a)+x+1
						table[x]=None
					#print table,nt
				for p in range(self.ilen):
					#print a,p
					if '0' == a[p]:
						target=a[:p]+'1'+a[p+1:]
					elif '1' == a[p]:
						target=a[:p]+'0'+a[p+1:]
					else:
						continue
					#print "target=",target
					if target in table[row+1:]:
						table[row]=None
						nt.append(a[:p]+'-'+a[p+1:])
						optimized=True
						x=row
						while target in table[x+1:]:
							x=table[x+1:].index(target)+x+1
							table[x]=None
						#print self.table,nt
						break
					for r in range(self.ilen):
						if a[r] != '-':
							continue
						t1=target[:r]+'1'+target[r+1:]
						t2=target[:r]+'0'+target[r+1:]
						if (t1 in table[row+1:]) and ( t2 in table[row+1:]):
							#print "t1,t2",t1,t2
							optimized=True
							opt=True
							#table[row]=None
							#print "r,target",r,target
							newrow=target[:r]+'-'+target[r+1:]
							#print "newrow",newrow
							nt.append(newrow)
							x=row
							while t1 in table[x+1:]:
								x=table[x+1:].index(t1)+x+1
								table[x]=None
							x=row
							while t2 in table[x+1:]:
								x=table[x+1:].index(t2)+x+1
								table[x]=None
							#print table,nt
			while None in table:
					table.remove(None)
			table=nt+table
			#print table
		return table

	def expand(self,line):
		"""
			FIXME: it is not needed
		"""
		pos=line.find('-')
		if -1 == pos:
			return [line]
		l0=list(line)
		l1=list(line)
		l0[pos]='0'
		l1[pos]='1'
		return self.expand("".join(l0))+self.expand("".join(l1))

	def permutate(self,selfterm,otherterm,locks):
		"""
			permutates the domain of self and other
			for outputs selfout and otherout
			output of self should be equal to input in locked positions
			expands '-'
			returns the permutated function
		"""
		#print "permutate",selfterm,otherterm
		newdom=[]
		len1=len(selfterm[0])
		len2=len(otherterm[0])
		for line1 in selfterm:
			for line2 in otherterm:
				okay=True
				line=line1+line2
				for (l1,l2) in locks:
					p1=line[l1]
					p2=line[l2]
					if (p1 == p2 ):
						pass
					elif p1 == '-':
						line=line[:l1]+p2+line[l1+1:]
					elif p2 == '-':
						line=line[:l2]+p1+line[l2+1:]
					else:
						okay=False
						break
				if okay:
					#print line
					#lines=self.expand(line)
					newdom.append(line)
		#print newdom
		return newdom

	def filter(self,table,mapping):
		"""
			rearranges columns in table according to filterlist
			and adds result
		"""
		newdom=[]
		newinputs=[]
		for line in table:
			row=[]
			for i in mapping:
				row.append(line[i])
			row.append(line[-1])
			newdom.append("".join(row))
		return newdom

	def prepare_join(self,myoutput,other,otherinput):
		"""
			prepares join/mold operation
			creates a new logic function which can be filled up with the terms necessary
			creates mapping for filtering operation
			creates lock list for permutation
		"""
		# create domain
		result=LogicFunction(name=self.name+'+'+other.name)

		# create a consolidated variable list
		# newinputs are the union of two inputs, minus otherinput
		# newoutputs are the union of two outputs minus myoutput
		# inputs might be common, outputs should not
		# common domain will be generated by permutating rows of terms of self and other
		# so we need a mapping which maps other.vars[:ilen] to
		# myinputs+[otherinput]+other[vars]
		# 
		selfinputs=self.vars[:self.ilen]
		otherinputs=other.vars[:other.ilen]
		selfoutputs=self.vars[self.ilen:]
		otheroutputs=other.vars[other.ilen:]

		for i in selfinputs:
			if i in otherinputs:
				otherinputs.remove(i)
		if otherinput is not None:
			otherinputs.remove(otherinput)
		for v in selfoutputs:
			if v in otheroutputs:
				otheroutputs.remove(v)
		#assert set()==set(selfoutputs).intersection(set(otheroutputs)), "output collision between %s(%s) and %s(%s)"%(self,selfoutputs,other,otheroutputs)
		if myoutput is not None:
			selfoutputs.remove(myoutput)
		result.vars=selfinputs+otherinputs+selfoutputs+otheroutputs
		result.ilen=len(selfinputs)+len(otherinputs)
		mapping=[]
		mapbase=selfinputs+[otherinput]+other.vars[:other.ilen]
		for v in result.vars[:result.ilen]:
			mapping.append(mapbase.index(v))
		locks=[]
		# locks are the position pairs where the same value should be when permutating
		#print "selfinputs",selfinputs
		#print "otherinput",otherinput
		#print "other.vars",other.vars
		#print "mapbase",mapbase
		for x in set(mapbase):
			p1=mapbase.index(x)+1
			if x in mapbase[p1:]:
				#print p1,x
				p2=mapbase[p1:].index(x)+p1
				locks.append((p1-1,p2))
		#print "locks",locks
		#print "mapping=",mapping

		for ou in selfoutputs:
			result.terms[ou]=[]
			for line in self.terms[ou]:
				result.terms[ou].append(line[:self.ilen]+'-'*len(otherinputs)+line[-1:])
			#print "self term",ou,result.terms[ou]
			
		return (result,mapping,locks)

	def join(self,	myoutput,other,otherinput):
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
		for outputs of self (-myoutput), the term is the same, just '-'-s inserted for new variables
		for outputs of other, the term is on the new domain, and it is FoG
		"""
		r = other.joined(otherinput,self,myoutput)
		if None != r:
			return r
		#print "joining %s(%s):%s -> %s(%s):%s"%(self,self._print(),myoutput,other,other._print(),otherinput)
		if other.objtype != 'LogicFunction':
			return None
		#print "joining",self._print(),other._print()
		(result,mapping,locks)=self.prepare_join(myoutput,other,otherinput)

		for ou in other.vars[other.ilen:]:
			#print "ou=",ou
			#print "myoutput=",myoutput
			#print "myterms=",self.terms[myoutput]
			#print "otherterms=",other.terms[ou]
			#print "locks=",locks
			#print "mapping=",mapping
			permutated=self.permutate(self.terms[myoutput],other.terms[ou],locks)
			#print "permutated=",permutated
			result.terms[ou]=self.filter(permutated,mapping)
			#print "other term",ou,result.terms[ou]
		#print result._print()

		result.check()
		result.simplify()
		result.check()

		disc=set()
		con=set()
		for (pin,d,ob,opin) in self.connections:
			if d == INPUT:
				disc.add((ob,opin,self,pin))
				con.add((ob,opin,result,pin))
			elif d == OUTPUT:
				disc.add((self,pin,ob,opin))
				if pin != myoutput:
					con.add((result,pin,ob,opin))
		for (pin,d,ob,opin) in other.connections:
			if d == INPUT:
				disc.add((ob,opin,other,pin))
				if pin != otherinput:
					con.add((ob,opin,result,pin))
			elif d == OUTPUT:
				disc.add((other,pin,ob,opin))
				con.add((result,pin,ob,opin))

		for (o1,pin1,o2,pin2) in disc:
			o1.disconnectfrom(pin1,o2,pin2)
		for (o1,pin1,o2,pin2) in con:
			o1.connectto(pin1,o2,pin2)

		rl=[other]
		if not self.hasoutputs():
			rl.append(self)
		#print "result",result
		return ([result],rl)

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
		(result,mapping,locks)=self.prepare_join(None,other,None)

		myterm=['-'*(self.ilen+1)]
		for ou in other.vars[other.ilen:]:
			permutated=self.permutate(myterm,other.terms[ou],locks)
			result.terms[ou]=self.filter(permutated,mapping)
			#print "other term",ou,result.terms[ou]
		#print result._print()

		result.check()
		result.simplify()
		result.check()

		disc=set()
		con=set()
		for (pin,d,ob,opin) in self.connections:
			if d == INPUT:
				disc.add((ob,opin,self,pin))
				con.add((ob,opin,result,pin))
			elif d == OUTPUT:
				disc.add((self,pin,ob,opin))
				con.add((result,pin,ob,opin))
		for (pin,d,ob,opin) in other.connections:
			if d == INPUT:
				disc.add((ob,opin,other,pin))
				con.add((ob,opin,result,pin))
			elif d == OUTPUT:
				disc.add((other,pin,ob,opin))
				con.add((result,pin,ob,opin))

		for (o1,pin1,o2,pin2) in disc:
			o1.disconnectfrom(pin1,o2,pin2)
		for (o1,pin1,o2,pin2) in con:
			o1.connectto(pin1,o2,pin2)

		rl=[other]
		if not self.hasoutputs():
			rl.append(self)
		#print "result",result
		return ([result],[self,other])


