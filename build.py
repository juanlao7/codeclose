import sys
import os
import subprocess
from shutil import copyfile

def uninstall():
    subprocess.call('pip uninstall codeclose -y', shell=True)

def install():
    uninstall()
    subprocess.check_call('pip install . --user', shell=True)

def all():
    install()

for targetName in sys.argv[1:]:
    target = getattr(sys.modules[__name__], targetName)
    target()
