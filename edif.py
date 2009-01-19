#!/usr/bin/python

import re
from libs import externals
from demszky import Cell,Port,directions,INPUT,OUTPUT
from bistromatic import LogicFunction,IOPin

class EdifCell(Cell):
	"""
		EdifCell is a Cell, which is constructed from an edif file
	"""
	def __init__(self,name,definition,libname=None,libs=None):
		"""
			name is a string
			definition is a preparsed EDIF cell declaration
			libname is the name of the lib
			libs is a dictionary of libs
		"""
		Cell.__init__(self,name)
		print "cell %s"%name
		self.properties={}
		self.libs=libs
		#print self.libs
		if libname:
			self.islib=True
		else:
			self.islib=False
		print "islib",self.islib
		self.parsecell(definition)
		if self.islib:
			generator=externals[libname].Generator
			self.__class__.__bases__+=(generator,)
			self.initobj()
		#self.init(name,self.properties)
		#assert getattr(self,"type",None), "object without type"
	def parsecell(self,construct):
		"""
			parses a cell edif construct
		"""
		for i in construct:
			if i[0] == "view":
				assert i[1] == "net", "we can parse only net view"
				#print "<<<"
				#pprint.pprint(i[2:],depth=10)
				#print ">>>"
				for j in i[2:]:
					#pprint.pprint(j)
					if j[0] == "viewtype":
						assert j[1] == "netlist", "We now only netlist viewtype"
					elif j[0] == "interface":
						self._extractports(j[1:])
					elif j[0] == "contents":
						self._extractcontents(j[1:])
					else:
						print "unparsed :", j[0]
			elif i[0] == "celltype":
				assert i[1] == "generic", "we know only generic cell type"
			elif i[0] == None:
				pass
			else:
				print "unknown:",i[0]
	def _extractnet(self,name,contents):
		"""
			A net is a logic function where all the outputs are the OR
			function of all the outputs
		"""
		plist=[]
		for port in contents:
			portname=port[1]
			if len(port) >2:
				devname=port[2][1]
				portname="%s:%s"%(devname,portname)
				for ao in self.contents[devname]:
					d=ao.getDirectionOfPort(portname)
					#print portname,d
					plist.append((portname,d,ao))
			else:
				plist.append((portname,self.getDirectionOfPort(portname),self.contents[portname][0]))	
		inputs=[]
		outputs=[]
		print plist
		for (n,d,o) in plist:
			if d & INPUT:
				inputs.append((n,o))
			if d & OUTPUT:
				outputs.append((n,o))
		inputs=list(set(inputs))
		outputs=list(set(outputs))
		li=len(inputs)
		lo=len(outputs)
		if ( 0 == (li * lo)) or ( li == 1 and (inputs == outputs )):
			return
		for (iname,i) in inputs:
			for (oname,o) in outputs:
				#print "connecting",iname,i,oname,o
				o.connectsto(oname,i,iname)
				#print i._print(),o._print()
		
				
	def _extractcontents(self,contents):
		"""
			extracts contents from the interface
		"""
		for c in contents:
			if c[0] == "instance":
				#print "FIXME instance",c[1],c[2][2][1],c[2][2][2][1]
				instname=c[1]
				cellname=c[2][2][1]
				library=c[2][2][2][1]
				cell=self.libs[library][cellname]
				n=cell.generate(instname)
				self.contents[instname]=n
			if c[0] == "net":
				self._extractnet(c[1],c[2][1:])
				#print "FIXME net",c[1]
				#for i in c[2][1:]:
					#if len (i) >2:
						#print i
						#print " ",i[1],i[2][1]
					#else:
						#print " ",i[1]
	def _extractports(self,interface):
		"""
			extract ports from the interface
			FIXME property LPM_Polarity (string "INVERT")
		"""
		for i in interface:
			if i[0] == "port":
				p=Port(i[1:]) #FIXME: we can get rid of Port
				pin=IOPin(p.direction,p.name)
				self.ports.append(Port(i[1:]))
				if not self.islib:
					self.contents[p.name]=[pin]
				#FIXME property LPM_Polarity (string "INVERT")
				#if Port.inverted:
				# oldnam=pin.name
				# tmpnam=pin.name+'_t'
				# f=LogicFunction(["10","01",[oldnam,tmpnam],1)
				# pin.name=tmpnam
				# self.contents[oldnam].append(f)
			elif i[0] == "property":
				if i[2][0] == "string":
					self.properties[i[1]]=i[2][1]
				elif i[2][0] == "integer":
					self.properties[i[1]]=int(i[2][1])
			else:
				print "unparsed:",i[0]
	
		
		

class Edif:
	"""
		EDIF parser
	"""
	def __init__(self,content):
		"""
			content is the content of the EDIF file
		"""
		edif=self.pythonify(content)
		assert edif[0] == "edif", "is it really an EDIF file?"
		self.designname=edif[1]
		#print "design name is", self.designname
		self.libs={}
		for construct in edif[2:]:
			if (construct[0]=="external"):
				lib={}
				self.parselib(lib,construct,external=True)
				self.libs[construct[1]]=lib

			elif (construct[0]=="library"):
				lib={}
				self.parselib(lib,construct)
				self.libs[construct[1]]=lib
	def __str__(self):
		s=""
		for v in self.libs.values():
			for cell in v:
				s+="%s"%cell
		return s

	def pythonify(self,lisp):
		"""
			turns a string containing LISP into a list
			it is quick&dirty string massage and eval
		"""
		lisp=lisp.lower()
		l2=re.sub('\n','',lisp)
		l3=re.sub('([^() \t]+)','"\\1",',l2)
		l4=re.sub('""','"',l3)
		l5=re.sub("\)[ \t]*\(","), (",l4)
		return eval(l5)

	def parselib(self,lib,construct,external=None):
		libname=construct[1]
		for cell in construct[2:]:
			if cell[0] == "cell":
				#print "cell",cell[1]
				if external:
					libs=None
				else:
					libs=self.libs
					libname=None
				lib[cell[1]]=EdifCell(cell[1],cell[2:],libname,libs)
			elif cell[0] == "ediflevel":
				assert cell[1] == '0', "we know only edif level 0"
			elif cell[0] == "technology":
				pass
			else:
				print cell
				raise "unparsed"
	


