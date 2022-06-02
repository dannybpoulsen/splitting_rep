import os
import subprocess

class CmakeCompiler:
    def __init__ (self,location):
        self._location = location

    def compile (self,library):
        name = os.path.split (library)[1]
        dest = os.path.abspath (os.path.join (self._location,name))
        if not os.path.exists(dest):
            os.makedirs (dest)
       
        subprocess.run (["cmake","-DCMAKE_BUILD_TYPE=Release",f"{library}"],cwd=dest) 
        subprocess.run (["make"],cwd=dest) 
        return dest
    
