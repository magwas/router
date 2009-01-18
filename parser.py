#!/usr/bin/python

from edif import Edif
from demszky import directions

f=open("example.edif")
lisp=f.read()
edif=Edif(lisp)

objlist=edif.libs['design']['device'].enumobsj()
"""
now we have a list of objects
let's try to merge logic functions
first we determine
	lvars: set of vars of the logic functions
	ovars: set of vars of the other objects
	evars = lvars - ovars: may be eliminable
		which is not: is either a i/o pin (maybe have to have objects for them), or an errorr
at the end we will have one or more logic cells, which we can mold into one,
and a set of other objects, which we have to place somehow
"""

lfs=[]
objs=[]
lvars=[]
ovars=[]
for ac in objlist:
	if ac.objtype=='LogicFunction':
		lfs.append(ac)
		lvars.extend(ac.vars)
	else:
		objs.append(ac)
		ovars.extend(ac.vars)

print "*************** Logic Functions *****************"
for lf in lfs:
	print lf

print "*************** Other Objects *******************"
for ob in objs:
	print ob

for lf in lfs:
	print "connections of", lf
	print lf.inputsfrom, lf.outputsto
	miss=0
	for (pin,oset) in lf.outputsto.items():
		for (oob,opin) in oset:
			print "joining",lf,pin,oob,opin
			r=lf.join(pin,oob,opin)
			if r is None:
				miss += 1
			else:
				#FIXME the set of AOs in r should replace oob
				print "succesful optimization step",r

