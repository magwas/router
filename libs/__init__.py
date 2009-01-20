import os
import imp

externals={}
path=os.path.abspath(__path__[0])
for f in os.listdir(path):
	module_name, ext = os.path.splitext(f) # Handles no-extension files, etc.
	if (ext == '.py') and (module_name != '__init__'):
		#print 'imported module: %s' % (module_name)
		x=open(path+'/'+f)
		module = imp.load_module(module_name,x,f,('.py','r',imp.PY_SOURCE))
		externals[module_name]=module

