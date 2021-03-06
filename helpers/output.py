import os
import os.path

class OutputLocation:
    def __init__(self,path):
        os.makedirs (path,exist_ok = True)
        self._path = path

    def outputFile (self,path):
        return open (os.path.join (self._path,path),"w")

    def outputPath (self,path):
        return os.path.join (self._path,path)

    def getDestination (self):
        return self._path
    
    def subLocation (self,path):
        loc = os.path.join (self._path,path)
        return OutputLocation (loc)

    
    
