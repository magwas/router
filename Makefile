all:
	make -C test

clean:
	-rm *.pyc libs/*.pyc devices/*.pyc
	make -C test clean

