#!/usr/bin/python

class top:
	pass
class base(top):
	def __init__(self,otherclass):
		otherclass.amend(self)
		self.otherfunc()

class amender:
	@classmethod
	def amend(cls,self):
		print self.__class__.__bases__
		self.__class__.__bases__+=(cls,)
		print "Amended"
	def otherfunc(self):
		print self
		self.bela=True

	def thirdfunc(foo):
		print foo

a=base(amender)

