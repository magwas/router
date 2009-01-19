#!/usr/bin/python

from edif import Edif
from demszky import directions
from time import clock
import sys

f=open(sys.argv[1])
lisp=f.read()
edif=Edif(lisp)

objlist=edif.libs['design']['device'].enumobsj()

optimized=True
while optimized:
	optimized=False
	for i in range(len(objlist)):
		lf=objlist[i]
		if lf is None:
			continue
		print "connections of", lf
		print lf.inputsfrom, lf.outputsto
		for (pin,oset) in lf.outputsto.items():
			for (oob,opin) in oset:
				time=clock()
				print "joining",lf,pin,oob,opin
				print lf._print(),oob._print()
				r=lf.join(pin,oob,opin)
				if r is not None:
					"""
					r is lf+oob
					lf should be unconnected from oob
					connect oob+lf connections to r
					oob should be replaced with r
					if lf have no more outputs, than it should be eliminated
					"""
					
					r.name=lf.name+'+'+oob.name
					print "result=",r._print()

					lf.unconnect(pin,oob,opin)

					hasouts=0
					for (pin,objs) in lf.outputsto.items():
						if len(objs):
							hasouts=1
							break
					if not hasouts:
						print "eliminating",lf
						objlist[i]=None
						for (pin,objs) in lf.inputsfrom.items():
							print pin,objs
							for (obj,opin) in objs:
								obj.unconnect(opin,lf,pin)

					for l in objlist:
						if l is None:
							continue
						l.replaceconn(oob,r)
						l.replaceconn(lf,r,addinputs=True)
					print "replacing",oob,"with",r
					j=objlist.index(oob)
					objlist[j]=r
					print "r=",r._print()
					print clock()-time,"seconds"
					optimized=True
					break
			if optimized:
				break
		if optimized:
			break

print "************************ Result **********************"
print objlist
for i in objlist:
	if i is None:
		continue
	print i.name,i._print()

