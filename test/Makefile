%.edif: %.v
	iverilog -tfpga -o $@ $<

%: %.v
	iverilog  -o $@ $<

%.vcd: %.v 
	iverilog  -o `basename $< .v` $<
	./`basename $< .v`
	gtkwave $@

all: galcounter.edif test1.edif test2.edif test3.edif test4.edif test5.edif test6.edif

clean:
	rm -f *.vcd *.edif *.vcd
	for i in *.v; do rm -f `basename $$i .v`;done

