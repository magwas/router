def itoa(x, base=10):
	""" inverse of int(). should have been standard builtin or string function."""
	if 0 is x:
		return '0'
	isNegative = x < 0
	if isNegative:
		x = -x
	digits = []
	while x > 0:
		x, lastDigit = divmod(x, base)
		digits.append('0123456789abcdefghijklmnopqrstuvwxyz'[lastDigit])
	if isNegative:
		digits.append('-')
	digits.reverse()
	return ''.join(digits) 

def binary(n,l):
	s=itoa(n,2)
	assert len(s) <= l , "number is too big for width: %s %s %s"%(s,n,l)
	s=(l-len(s))*'0'+s
	return s

