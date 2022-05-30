import os
import os.path

class OutputLocation:
    def __init__(self,path):
        os.makedirs (path,exist_ok = True)
        self._path = path

    def outputPath (self,path):
        return os.path.join (self._path,path)

    def subLocation (self,path):
        loc = os.path.join (self._path,path)
        return OutputLocation (loc)

    
