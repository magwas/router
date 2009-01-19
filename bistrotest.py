#!/usr/bin/python

from bistromatic import LogicFunction
from time import clock

start=clock()


test1=LogicFunction([
'0000',
'0011',
'0101',
'0111',
'1001',
'1011',
'1101',
'1111'],['a','b','c'],3)
test1.simplify()
print test1._print()
test3= LogicFunction([
'0000',
'0100',
'1000',
'1100',
'1110',
'0011',
'0111',
'1011' ],['A0', 'B0', 'U0_10i0', 'U0_10'],3)
test3.simplify()
print """
'--00',
'-011',
'1110',
'0111'"""
test2= LogicFunction([
'001',
'001',
'011',
'011',
'101',
'101',
'110',
'110' ],['A0', 'B0', 'U0_11'],2)
test2.simplify()
print """
'-01',
'011',
'110'"""

test1=LogicFunction(['0001','0011','0101','0111','1001','1011','1101','1111'],['a','b','c'],3)
test1.simplify()
print """
'---1'
"""
print test1,'\n------------'

def andgate(name):
	return LogicFunction([ "000", "010", "100", "111"],["%si0"%(name),"%si1"%(name),"%s"%(name)],2)

def orgate(name):
	return LogicFunction([ "000", "011", "101", "111"],["%si0"%(name),"%si1"%(name),"%s"%(name)],2)

def notgate(name):
	return LogicFunction([ "01", "10"],["%si"%(name),"%s"%(name)],1)

x=andgate("x")
one=LogicFunction(["1"],["output"],0)
print x
print one
out=one.join("output",x,"xi0")
print out

#Adder:
U0_00=orgate("U0_00")
U0_00.renamevar("U0_00i0","A0")
U0_00.renamevar("U0_00i1","B0")
U0_01=andgate("U0_01")
U0_01.renamevar("U0_01i0","A0")
U0_01.renamevar("U0_01i1","B0")
U0_11=notgate("U0_11")
U0_10=andgate("U0_10")
U0_20=orgate("U0_20")
U0_20.renamevar("U0_20i1","H")
U0_21=andgate("U0_21")
U0_21.renamevar("U0_21i1","H")
U0_30=orgate("U0_30")
U0_30.renamevar("U0_30","C0")
U0_32=notgate("U0_32")
U0_31=andgate("U0_31")
U0_31.renamevar("U0_31","R0")
U0_11=U0_01.join("U0_01",U0_11,"U0_11i")
U0_10=U0_11.join("U0_11",U0_10,"U0_10i1")
U0_10=U0_00.join("U0_00",U0_10,"U0_10i0")
U0_20=U0_10.join("U0_10",U0_20,"U0_20i0")
U0_21=U0_10.join("U0_10",U0_21,"U0_21i0")
U0_32=U0_21.join("U0_21",U0_32,"U0_32i")
U0_31=U0_20.join("U0_20",U0_31,"U0_31i0")
R0=U0_32.join("U0_32",U0_31,"U0_31i1")
U0_30=U0_21.join("U0_21",U0_30,"U0_30i1")
C0=U0_01.join("U0_01",U0_30,"U0_30i0")
BIT0=C0.mold(R0)
print 'BIT0',BIT0


U1_00=orgate("U1_00")
U1_00.renamevar("U1_00i0","A1")
U1_00.renamevar("U1_00i1","B1")
U1_01=andgate("U1_01")
U1_01.renamevar("U1_01i0","A1")
U1_01.renamevar("U1_01i1","B1")
U1_11=notgate("U1_11")
U1_10=andgate("U1_10")
U1_20=orgate("U1_20")
U1_20.renamevar("U1_20i1","H1")
U1_21=andgate("U1_21")
U1_21.renamevar("U1_21i1","H1")
U1_30=orgate("U1_30")
U1_30.renamevar("U1_30","C1")
U1_32=notgate("U1_32")
U1_31=andgate("U1_31")
U1_31.renamevar("U1_31","R1")
U1_11=U1_01.join("U1_01",U1_11,"U1_11i")
U1_10=U1_11.join("U1_11",U1_10,"U1_10i1")
U1_10=U1_00.join("U1_00",U1_10,"U1_10i0")
U1_20=U1_10.join("U1_10",U1_20,"U1_20i0")
U1_21=U1_10.join("U1_10",U1_21,"U1_21i0")
U1_32=U1_21.join("U1_21",U1_32,"U1_32i")
U1_31=U1_20.join("U1_20",U1_31,"U1_31i0")
R1=U1_32.join("U1_32",U1_31,"U1_31i1")
U1_30=U1_21.join("U1_21",U1_30,"U1_30i1")
C1=U1_01.join("U1_01",U1_30,"U1_30i0")
BIT1=C1.mold(R1)


U2_00=orgate("U2_00")
U2_00.renamevar("U2_00i0","A2")
U2_00.renamevar("U2_00i1","B2")
U2_01=andgate("U2_01")
U2_01.renamevar("U2_01i0","A2")
U2_01.renamevar("U2_01i1","B2")
U2_11=notgate("U2_11")
U2_10=andgate("U2_10")
U2_20=orgate("U2_20")
U2_20.renamevar("U2_20i1","H2")
U2_21=andgate("U2_21")
U2_21.renamevar("U2_21i1","H2")
U2_30=orgate("U2_30")
U2_30.renamevar("U2_30","C2")
U2_32=notgate("U2_32")
U2_31=andgate("U2_31")
U2_31.renamevar("U2_31","R2")
U2_11=U2_01.join("U2_01",U2_11,"U2_11i")
U2_10=U2_11.join("U2_11",U2_10,"U2_10i1")
U2_10=U2_00.join("U2_00",U2_10,"U2_10i0")
U2_20=U2_10.join("U2_10",U2_20,"U2_20i0")
U2_21=U2_10.join("U2_10",U2_21,"U2_21i0")
U2_32=U2_21.join("U2_21",U2_32,"U2_32i")
U2_31=U2_20.join("U2_20",U2_31,"U2_31i0")
R2=U2_32.join("U2_32",U2_31,"U2_31i1")
U2_30=U2_21.join("U2_21",U2_30,"U2_30i1")
C2=U2_01.join("U2_01",U2_30,"U2_30i0")
BIT2=C2.mold(R2)


U3_00=orgate("U3_00")
U3_00.renamevar("U3_00i0","A3")
U3_00.renamevar("U3_00i1","B3")
U3_01=andgate("U3_01")
U3_01.renamevar("U3_01i0","A3")
U3_01.renamevar("U3_01i1","B3")
U3_11=notgate("U3_11")
U3_10=andgate("U3_10")
U3_20=orgate("U3_20")
U3_20.renamevar("U3_20i1","H3")
U3_21=andgate("U3_21")
U3_21.renamevar("U3_21i1","H3")
U3_30=orgate("U3_30")
U3_30.renamevar("U3_30","C3")
U3_32=notgate("U3_32")
U3_31=andgate("U3_31")
U3_31.renamevar("U3_31","R3")
U3_11=U3_01.join("U3_01",U3_11,"U3_11i")
U3_10=U3_11.join("U3_11",U3_10,"U3_10i1")
U3_10=U3_00.join("U3_00",U3_10,"U3_10i0")
U3_20=U3_10.join("U3_10",U3_20,"U3_20i0")
U3_21=U3_10.join("U3_10",U3_21,"U3_21i0")
U3_32=U3_21.join("U3_21",U3_32,"U3_32i")
U3_31=U3_20.join("U3_20",U3_31,"U3_31i0")
R3=U3_32.join("U3_32",U3_31,"U3_31i1")
U3_30=U3_21.join("U3_21",U3_30,"U3_30i1")
C3=U3_01.join("U3_01",U3_30,"U3_30i0")
BIT3=C3.mold(R3)

#print BIT0,BIT1,BIT2,BIT3
print "stages assembled",clock()-start

X1=BIT0.join("C0",BIT1,"H1")
#print X1
X2=X1.join("C1",BIT2,"H2")
#print X2
#print "----------------------------------------"
ADDER=X2.join("C2",BIT3,"H3")

print "adder done",clock()-start

def hashfromrow(row,vars):
	h={}
	for i in range(len(vars)):
		h[vars[i]]=row[i]
	return h
def addercheck(adder):
	for x in adder.table:
		v=hashfromrow(x,adder.vars)
		if v.has_key("H") and (v["H"]!='0'):
			continue
		a=v["A3"]+v["A2"]+v["A1"]+v["A0"]
		b=v["B3"]+v["B2"]+v["B1"]+v["B0"]
		c=v["C3"]+v["R3"]+v["R2"]+v["R1"]+v["R0"]
		a=int(a,2)
		b=int(b,2)
		c=int(c,2)
		if c != (a+b):
			print "!",x,v,a,b,c
			raise "uff"
addercheck(ADDER)
print "adder checked",clock()-start

zero=LogicFunction(["0"],["output"],0)
adder=zero.join("output",ADDER,"H")
print "second adder assembled",clock()-start
addercheck(adder)
print "second adder checked",clock()-start
print adder
print "4-bit adder is okay"

"""
f=LogicFunction(["0101","1001","1111"],["a","b","c","d"],2)
g=LogicFunction(["0011","1001","-111"],["e","f","g","h"],2)
res=f.join("c",g,"f")
print "result=",res

print f
print f.resultfor("00")
print f.resultfor("01")
print f.resultfor("10")
print f.resultfor("11")
"""

