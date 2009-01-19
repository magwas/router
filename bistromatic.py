"""
	logic optimization of switches
	the espresso-mv algoritm is described in http://www.eecs.berkeley.edu/Pubs/TechRpts/1986/ERL-86-65.pdf
	I do not understand it, so I have implemented what I figured out, which may or may not resembles to espresso.
"""

from demszky import directions,INPUT,OUTPUT

class AbstractObject:
	"""
		AbstractObject is describing some object (logic switch, counter, lut, flip-flop, etc), in an abstract manner.
		AbstractObjects can be simplified, joined, and meld if they can agree on how to do that.
		After they amended with device-specific knowledge, they can place themselves.
	"""
	def __init__(self,vars,ilen=0,iolen=0,objtype=None,name=None):
		"""
			vars is a list of strings naming the inputs and outputs of the object
			ilen is the number of inputs
			iolen is the number of bidirectional interfaces
			the set of inputs is vars[:ilen]
			the set of outputs is vars[ilen-iolen:]
		"""
		self.name=name
		self.vars=vars
		self.funcdict={}
		self.fixvars()
		self.ilen=ilen
		self.iolen=iolen
		self.objtype=objtype
		self.outputsto={}
		self.inputsfrom={}

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
		n.name=name
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

	def _print(self):
		return "%s(%s,%s,%s,%s,%s)"%(self.objtype,self.funcdict,self.ilen,self.iolen,self.inputsfrom,self.outputsto)
	def __repr__(self):
		return "%s(%s)"%(self.objtype,self.name)
			
	def join(self,myoutput,other,otherinput):
		"""
		returns a abstract object created by joining self and other through
		self.myoutput=other.otherinput
		if it is impossible, return None
		implemented by derived classes knowing each other
		"""
		return None

	def mold(self,other):
		"""
		molds two abstract objects into one if it is possible
		returns None if impossible
		"""
		raise NotImplementedError

	def connectsto(self,pin,other,otherpin):
		"""
			The topology is described through two hashes,
			inputsfrom and outputsto
			the hashes are indexed by pin, and contain sets of (object,pinname) pairs
			connectsto() declares that an object connects to another.
			it sets the necessary things both in itself and the other object
		"""
		if self==other:
			return
		mydir=self.getDirectionOfPort(pin)
		otherdir=other.getDirectionOfPort(otherpin)
		#print self,mydir,self.vars,self.ilen,self.iolen
		#print other,otherdir,other.vars,other.ilen,other.iolen
		if (OUTPUT & mydir) and (INPUT & otherdir):
			#print "i->o"
			if not self.outputsto.has_key(pin):
				self.outputsto[pin]=set()
			if not other.inputsfrom.has_key(otherpin):
				other.inputsfrom[otherpin]=set()
			self.outputsto[pin].add((other,otherpin))
			other.inputsfrom[otherpin].add((self,pin))
		if (INPUT & mydir) and (OUTPUT & otherdir):
			#print "o->i"
			if not self.inputsfrom.has_key(pin):
				self.inputsfrom[pin]=set()
			if not other.outputsto.has_key(otherpin):
				other.outputsto[otherpin]=set()
			other.outputsto[otherpin].add((self,pin))
			self.inputsfrom[pin].add((other,otherpin))
	def unconnect(self,pin,other,otherpin):
		"""
			eliminate the connection
		"""
		if self.inputsfrom.has_key(pin):
			self.inputsfrom[pin] -= set([(other,otherpin)])
		if self.outputsto.has_key(pin):
			self.outputsto[pin] -= set([(other,otherpin)])
	def replaceconn(self,oldie,newie,addinputs=False):
		"""
		replaces oldie with newie in all connections
		replaces the connected side as well
		"""
		#print "replacing",self,oldie,newie,addinputs
		#print self.inputsfrom,self.outputsto
		for (pin,oset) in self.outputsto.items():
			l=[]
			for (ob,opin) in oset:
				#print ob,opin
				if ob==oldie:
					#print "hit"
					l.append((newie,opin))
					if addinputs:
						l.append((ob,opin))
				else:
					l.append((ob,opin))
			self.outputsto[pin]=set(l)
		if addinputs:
			#print self.inputsfrom,self.outputsto
			return
		#print "inputs"
		for (pin,oset) in self.inputsfrom.items():
			l=[]
			for (ob,opin) in oset:
				#print ob,opin
				if ob==oldie:
					#print "hit"
					l.append((newie,opin))
				else:
					l.append((ob,opin))
			self.inputsfrom[pin]=set(l)
		#print self.inputsfrom,self.outputsto

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
	def __init__(self,initial=0,renamedict=None,name=None):
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
		n=DFlipFlop(self.initial,renamedict=self.funcdict)
		return n
		
class IOPin(AbstractObject):
	"""
		An I/O pin have one port with direction, and no logic
	"""
	def __init__(self,direction,name):
		self.direction=direction
		if direction & INPUT:
			ilen=1
		else:
			ilen=0
		if direction & OUTPUT:
			iolen=ilen
		else:
			iolen=0
		AbstractObject.__init__(self,[name],objtype="IOPin",ilen=ilen,iolen=iolen,name=name)
	def _print(self):
		return "%s(%s,%s,%s,%s)"%(self.objtype,self.direction,self.vars[0],self.inputsfrom,self.outputsto)

class LogicFunction(AbstractObject):
	"""
	A logic function contains a set of inputs, a set of outputs, and the truth table.
	"""
	def __init__(self,table,vars,ilen=None,name=None):
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
		n=LogicFunction([]+self.table,[]+self.vars,self.ilen)
		return n

	def _print(self):
		return "%s([\n'%s'],%s,%s,%s,%s,%s)"%(self.objtype,"',\n'".join(self.table),self.vars,self.funcdict,self.ilen,self.inputsfrom,self.outputsto)
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
			FIXME: len = self.ilen
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

	
	def _simplifyrows(self,rowa,rowb,round=1):
		"""
		returns None or res
			None means no optimization done
			if round=1
				res is the two molded rows
			if round=0
				res is a list of rows
		"""
		#print rowa,rowb
		nrow=""
		diff=0
		sa=0
		sb=0
		for p in range(self.ilen):
			if rowa[p] == rowb[p]:
				nrow += rowa[p]
			elif rowa[p] == '-':
				sa+=1
				nrow += '-'
			elif rowb[p] == '-':
				sb+=1
				nrow += '-'
			else:
				diff+=1
				nrow += '-'
		for p in range(self.ilen,len(rowa)):
			if rowa[p] == '-':
				nrow += rowb[p]
			elif rowb[p] == '-':
				nrow += rowa[p]
			elif rowa[p] == rowb[p]:
				nrow += rowa[p]
			else:
				return None
		#print nrow,diff,sa,sb
		"""
A  B   diff  	sa sb 	res
00 00  0	0  0	00
00 01  1	0  0	0-
00 0-  0	0  1	0-
00 10  1	0  0	_0
00 11  2	0  0    None
00 1-  1	0  1    None
00 -0  0	0  1    -0
00 -1  1	0  1    None ([00,01,11],[0-,11],[00,-1])
00 --  0	0  2	--
01 00  1	0  0	0_
01 01  0	0  0 	01
01 0-  0	0  1    0-
01 10  2	0  0	None
01 11  1	0  0	0_
01 1-  1	0  1	None ([01,10,11],[01,1-],[10,-1])
01 -0  1        0  1    None ([01,10,00],[10,1-],[01,-1])
01 -1  0	0  1	-1
01 --  0	0  2    --
0- 00  0	1  0	0-
0- 01  0	1  0	0-
0- 0-  0	0  0	0-
0- 10  1	1  0	None
0- 11  1	1  0	01 00 11
0- 1-  1	0  0    --   R
0- -0  0        1  1    None
0- -1  0	1  1    00 01 11
0- --  0        0  1    --

there is no way to find multi-DC solutions from two rows, so
either DC solutions have to be added, and not replace in first runs,
or at least three lines should be used for optimization.

"""
		if (diff > 1) or (diff*(sa+sb)) or (sa*sb):
			return None
		if (not round):
			if diff:
				return nrow
			return None
		return nrow
	
	def _simplifyrowsold(self,rowa,rowb):
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

	def simplifyold(self,check=None):
		"""
			AB+/AB=B
			where n<=ilen
			if we can found two rows where everything is the same but the nth position, we can reduce it
			to one row with '-' in the nth position
		"""
		print "before:",self
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
		print "after:",self
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

