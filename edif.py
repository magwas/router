#!/usr/bin/python

import re
from libs import externals
from bistromatic import LogicFunction,IOPin, directions, INPUT,OUTPUT
from sexpr import str2sexpr

class Port:
	"""
		A port as defined by the EDIF (port ...) construct
		it have a direction a name and an alias
	"""
	def __init__(self,repr):
		"""
			repr is the representation of the port. examples:
			("Data1x1" ("direction" "INPUT"))
			(("rename" "PORT0" "P[0]") ("direction" "INOUT"))
		"""
		self.inverted=False
		for tag in repr:
			if type(tag) is str:
				#name of the port
				self.name=tag
				self.alias=tag
			elif type(tag) is list:
				if tag[0] == "direction":
					self.direction=directions[tag[1]]
				elif tag[0] == "rename":
					self.name=tag[1]
					self.alias=tag[2]
				elif tag[0] == "property":
					if tag[1] == "lpm_polarity":
						if (tag[2][0] == 'string') and (tag[2][1].lower() == 'invert'):
							self.inverted=True
						else:
							raise NotImplementedError, tag[2]
					else:
						raise NotImplementedError, tag[1]
				else:
					raise NotImplementedError, tag
			else:
				raise NotImplementedError, tag
	def __str__(self):
		return "PIN %s (%s) %s"%(self.name,self.alias,dirs[self.direction])


class Cell:
	"""
		a cell have a name, ports, and content
		name is a string
		ports is a hash of IOPin objects, keyed by port name
		content is a list of all objects contained in the cell
	"""
	def __init__(self,name):
		self.name=name
		self.ports={}
		self.content=[]

	def getDirectionOfPort(self,name):
		"""
			Gets direction of named port
		"""
		return self.ports[name].direction
		
	def hasportwithname(self,name):
		"""
			do we have a port named name?
		"""
		for p in self.ports.values():
			#print "port "+p.name
			if p.name == name:
				return True
		return False

	def __str__(self):
		"""
			written representation
		"""
		s="Cell %s:\n\tports:\n"%self.name
		for port in self.ports:
			s+="\t %s\n"%port
		s += "\tcontent:\n"
		for c in self.content:
			s+="\t %s (%s)\n"%(c,c.connections)
		return s

	def copy(self,prefix="?"):
		"""
			copies itself:
				name will be prefix:name
				ports are copied
				content is copied
				connections are transformed
		"""
		n=Cell(prefix+':'+self.name)
		#print "copying",self
		for ob in self.content:
			cob=ob.copy()
			cob.name=prefix+':'+cob.name
			for v in cob.vars:
				cob.renamevar(v,prefix+':'+v)
			n.content.append(cob)
		for (nam,val) in self.ports.items():
			i=self.content.index(val)
			n.ports[nam]=n.content[i]
		for ob in self.content:
			i=self.content.index(ob)
			nob=n.content[i]
			#print " ob=",ob,ob.connections
			#print "nob=",nob,nob.connections
			for (pin,d,ob2,pin2) in ob.connections:
				i2=self.content.index(ob2)
				nob2=n.content[i2]
				nob.connections.add((prefix+':'+pin,d,nob2,prefix+':'+pin2))
		#print n
		return n

	def enumobjs(self):
		"""
		returns all objects contained in self 
		"""
		ol=self.content
		return ol
		

class EdifCell(Cell):
	"""
		EdifCell is a cell constructed from an edif file
		a cell have a name, ports, instances and content
		name is a string
		ports is a hash of IOPin objects, keyed by port name
		instances is a hash of EdifCell objects, keyed by instance name
		content is a list of all objects contained in the cell
		It is is a piece of logic, e.g. a gate array, a flip-flop, a LUT or a processor.
		Cells have name and ports, and maybe contents.
		Contents are AbstractObjects.
	"""
	def __init__(self,name,definition,libname=None,libs=None,device=None):
		"""
			definition is a preparsed EDIF cell declaration
			libname is the name of the lib
			libs is a dictionary of libs
		"""
		Cell.__init__(self,name)
		self.instances={}
		self.device=device

		self.properties={}
		self.invertpins=[]
		self.libs=libs
		#print self.libs
		if libname:
			self.islib=True
		else:
			self.islib=False
		#print "islib",self.islib
		self.parsecell(definition)
		if self.islib:
			generator=externals[libname].Generator
			self.__class__.__bases__+=(generator,)
			self.initobj()
		self.doinversion()

	def enumobjs(self):
		"""
		returns all objects contained in self and its instances
		"""
		ol=self.content
		for i in self.instances.values():
			ol.extend(i.enumobjs())
		return ol
	
	def __str__(self):
		s=Cell.__str__(self)
		s+="\tproperties:\n"
		for name,value in self.properties.items():
			s+="\t %s=%s\n"%(name,value)
		return s


	def doinversion(self):
		"""
			fror each outbound connections of the pin:
				-disconnect connection.
				-add an inverter function
				-connect the pin to the inverter, and the inverter to the original connection
		"""
		#print "inverted pins:",self.invertpins
		for pname in self.invertpins:
			p=self.ports[pname]
			for (pin,d,ob,opin) in p.connections:
				if d==OUTPUT:
					inv=self.device.LogicFunction(["10","01"],[p+"_inv_input",p+"_inv_output"],name=p+"_inv")
					self.content.append(inv)
					p.disconnectfrom(pin,ob,opin)
					p.connectto(pin,inv,p+"_inv_input")
					inv.connectto(p+"_inv_output",ob,opin)
				
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
			we connect pins of devices here
		"""
		plist=[]
		for port in contents:
			portname=port[1]
			if len(port) >2:
				devname=port[2][1]
				plist.append(self.instances[devname].ports[portname])
			else:
				plist.append(self.ports[portname])
		for p1 in plist:
			for p2 in plist:
				 p1.connectto(p1.vars[0],p2,p2.vars[0])
		
				
	def _extractcontents(self,contents):
		"""
			extracts contents 
			FIXME: this is cheap and dirty
			FIXME: instantiate somehow
		"""
		for c in contents:
			if c[0] == "instance":
				instname=c[1]
				cellname=c[2][2][1]
				library=c[2][2][2][1]
				cell=self.libs[library][cellname]
				self.instances[instname]=cell.copy(instname)
			if c[0] == "net":
				self._extractnet(c[1],c[2][1:])

	def _extractports(self,interface):
		"""
			extract ports from the interface
			FIXME property LPM_Polarity (string "INVERT")
		"""
		for i in interface:
			if i[0] == "port":
				p=Port(i[1:]) #FIXME: should we get rid of Port? It is used just for parsing.
				#print "\n\n",i[1:]
				pin=self.device.IOPin(p.direction,p.name,eliminable=self.islib)
				pin.name=p.name
				self.ports[p.name]=pin
				self.content.append(pin)
				if p.inverted:
					self.invertpins.append(p.name)
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
	def __init__(self,device,content):
		"""
			deviceclass is the name of the device we are using
			content is the content of the EDIF file
		"""
		self.device=device
		edif=str2sexpr(content)[0]
		#print edif
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
				lib[cell[1]]=EdifCell(cell[1],cell[2:],libname,libs,device=self.device)
			elif cell[0] == "ediflevel":
				assert cell[1] == '0', "we know only edif level 0"
			elif cell[0] == "technology":
				pass
			else:
				print cell
				raise "unparsed"
	


