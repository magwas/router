#!/usr/bin/python

from types import StringType,TupleType

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
		for tag in repr:
			if type(tag) is StringType:
				#name of the port
				self.name=tag
				self.alias=tag
			elif type(tag) is TupleType:
				if tag[0] == "direction":
					self.direction=directions[tag[1]]
				elif tag[0] == "rename":
					self.name=tag[1]
					self.alias=tag[2]
	def __str__(self):
		return "PIN %s (%s) %s"%(self.name,self.alias,dirs[self.direction])


class Cell:
	"""
		Cell is a piece of logic, e.g. a gate array, a flip-flop, a LUT or a processor.
		Cells have name and ports, and maybe contents.
		Contents are AbstractObjects.
	"""
	def __init__(self,name,ports=None):
		self.name=name
		self.ports=[]
		if ports:
			for p in ports:
				self.ports.append(Port(p))
		self.contents={}

	def getDirectionOfPort(self,name):
		"""
			Gets direction of named port
		"""
		for p in self.ports:
			#print "port "+p.name
			if p.name == name:
				return p.direction
		return directions["notconnected"]
		
	def hasportwithname(self,name):
		for p in self.ports:
			#print "port "+p.name
			if p.name == name:
				return True
		return False
	def enumobsj(self):
		"""
			returns a flat list of objects in a cell
		"""
		obs=[]
		for (k,v) in self.contents.items():
			#print "cell %s"%k
			for i in v:
				obs.append(i)
		return obs


	def __str__(self):
		s="Cell %s:\n\tports:\n"%self.name
		for port in self.ports:
			s+="\t %s\n"%port
		s+="\tproperties:\n"
		for name,value in self.properties.items():
			s+="\t %s=%s\n"%(name,value)
		return s

