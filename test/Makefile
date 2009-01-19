%.edif: %.v
	iverilog -tfpga -o $@ $<

%: %.v
	iverilog  -o $@ $<

%.vcd: %.v 
	iverilog  -o `basename $< .v` $<
	./`basename $< .v`
	gtkwave $@

clean:
	rm -f *.vcd *.edif *.vcd
	for i in *.v; do rm -f `basename $$i .v`;done

