#!/usr/bin/python

from libs import externals
from demszky import Edif

f=open("example.edif")
lisp=f.read()
edif=Edif(lisp)

d=edif.libs['design']['device']
print d.contents
for (k,v) in d.contents.items():
	print "cell %s"%k
	for i in v:
		print i
