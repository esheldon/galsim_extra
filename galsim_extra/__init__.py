import glob, os

d = os.path.dirname(__file__)
files = glob.glob(os.path.join(d,'*.py'))
for f in files:
    module = os.path.basename(f)
    module = module.replace('.py','')
    if module != '__init__':
        exec("from . import "+module)
