all:
	make -C test

clean:
	-rm *.pyc libs/*.pyc
	make -C test clean

