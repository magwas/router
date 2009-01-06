#!/usr/bin/python
"""
	EDIF parser
	it turns an EDIF file into internal representation
"""

import re

def lisp2list(lisp):
	"""
		turns a string containing LISP into a list
	"""
	l2=re.sub('\n','',lisp)
	l3=re.sub('([^() \t]+)','"\\1",',l2)
	l4=re.sub('""','"',l3)
	l5=re.sub("\)[ \t]*\(","), (",l4)
	return eval(l5)

f=open("example.edif")
lisp=f.read()
print lisp2list(lisp)
