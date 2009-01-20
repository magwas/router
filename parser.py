#!/usr/bin/python

from edif import Edif
from demszky import directions, OUTPUT
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
		#print "connections of", lf
		#print lf.connections
		for (pin,d,oob,opin) in lf.connections:
			if d != OUTPUT:
				continue
			time=clock()
			#print "joining",lf,pin,oob,opin
			#print lf._print(),oob._print()
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
				#print "result=",r._print()

				for l in objlist:
					if l is None:
						continue
					l.replaceconn(oob,r)
					l.cloneoutput(lf,r)
				lf.disconnectfrom(pin,oob,opin)

				if not lf.hasoutputs():
					#print "eliminating",lf
					lf.forget()
					objlist[i]=None

				#print "replacing",oob,"with",r
				j=objlist.index(oob)
				objlist[j]=r
				#print "r=",r._print()
				#print clock()-time,"seconds"
				optimized=True
				break
		#if optimized:
		#	break

print "************************ Result **********************"
print objlist
for i in objlist:
	if i is None:
		continue
	print i.name,i._print()

