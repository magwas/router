#!/usr/bin/python

import libs,imp
from edif import Edif
from bistromatic import directions, OUTPUT
from time import clock
import sys


class DemszkysMom:
	"""
		When I hear the expression 'P+R', I can't stop thinking about
		the mother of the major of Budapest.
	"""
	def optimize(self):
		optimized=True
		while optimized:
			#print "optimizing step",self
			optimized=False
			for i in range(len(self.objlist)):
				lf=self.objlist[i]
				#print "optimizing",lf
				if lf is None:
					continue
				for (pin,d,oob,opin) in lf.connections:
					time=clock()
					#print "joining",lf,pin,oob,opin,d
					if d == OUTPUT:
						r=lf.join(pin,oob,opin)
					else:
						r=lf.joined(pin,oob,opin)
					if r is not None:
						#print "joined",lf,pin,oob,opin,d
						#print "result=",r
						#print "elapsed:",clock()-time
						(addend,minuend)=r
						for o in minuend:
							#print "removing",o
							if o.connections:
								o.forget()
								print "trying to remove %s with living connections %s"%(o,o.connections)
							j=self.objlist.index(o)
							self.objlist[j]=None
						self.objlist.extend(addend)
						#print clock()-time,"seconds"
						optimized=True
						break
				if optimized:
					break
		while None in self.objlist:
			self.objlist.remove(None)
	def __str__(self):
		str=""
		for i in self.objlist:
			if i is None:
				continue
			str+="%s: %s\n\n"%(i.name,i._print())
		return str
	def place(self):
		"""
			We have been trough minimization, now try to place our objects
		"""
		self.device.place(self)

class Demszky(DemszkysMom):
	"""
		Some say that the only thing we can be sure of is the direct
		inheritance relationship described above;)
	"""
	def __init__(self,devicename,file):
		"""
			If we are talking about the beginnings, it must be told that he
			did not start it as the corrupt incompetent politician like he is now.
			He did and stand a lot. But unfortunately he is not among the very few
			who could resist of adverse effects of law studies and being a political leader.
		"""
		devfile="devices/%s.py"%devicename
		m=open(devfile)
		module=imp.load_module(devicename,m,devfile,('.py','r',imp.PY_SOURCE))
		self.device=module.Technology()

		f=open(file)
		lisp=f.read()
		f.close()
		self.edif=Edif(self.device,lisp)
		self.objlist=self.edif.libs['design']['device'].enumobjs()+self.device.enumobjs()

if __name__ == "__main__":
	from time import clock
	(myself,devname,file)=sys.argv

	d=Demszky(devname,file)
	print "*********Begin**********"
	print d
	print "*********Optimizing**********"
	t=clock()
	d.optimize()
	print clock()-t,"secs elapsed"
	print "*********Result**********"
	print d
	print "*********Checks**********"
	d.place()

