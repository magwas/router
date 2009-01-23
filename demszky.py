#!/usr/bin/python

import libs,imp
from edif import Edif
from bistromatic import directions, OUTPUT
from time import clock
import sys

(myself,devname,file)=sys.argv

devfile="devices/%s.py"%devname
m=open(devfile)
module=imp.load_module(devname,m,devfile,('.py','r',imp.PY_SOURCE))
device=module.Technology()

f=open(file)
lisp=f.read()
edif=Edif(device,lisp)

objlist=edif.libs['design']['device'].enumobjs()

print "************************ Beginning with **********************"
print objlist
for i in objlist:
	if i is None:
		continue
	print i.name,i._print()

print "************************ OPTIMIZING **********************"
optimized=True
while optimized:
	optimized=False
	for i in range(len(objlist)):
		lf=objlist[i]
		#print "optimizing",lf
		if lf is None:
			continue
		for (pin,d,oob,opin) in lf.connections:
			time=clock()
			print "joining",lf,pin,oob,opin,d
			if d == OUTPUT:
				r=lf.join(pin,oob,opin)
			else:
				r=lf.joined(pin,oob,opin)
			if r is not None:
				print "joined",lf,pin,oob,opin,d
				print "result=",r
				print "elapsed:",clock()-time
				(addend,minuend)=r
				for o in minuend:
					#print "removing",o
					if o.connections:
						o.forget()
						print "trying to remove %s with living connections %s"%(o,o.connections)
					j=objlist.index(o)
					objlist[j]=None
				objlist.extend(addend)
				#print clock()-time,"seconds"
				optimized=True
				break
		if optimized:
			break

while None in objlist:
	objlist.remove(None)
print "************************ Result **********************"
print objlist
for i in objlist:
	print i.name,i._print()

