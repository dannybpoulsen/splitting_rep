import os
import tempfile
import shutil
import json
import subprocess
import os
import sys
import multiprocessing
import pyparsing as pp
import time


class Progresser:
    def __enter__(self):
        sys.stdout.write ("\n")
        return self
    
    def __exit__ (self, exc_type, exc_value, exc_traceback):
        sys.stdout.write ("\n")
        
    def message (self,string):
        sys.stdout.write ("\r\u001b[0J{0}".format(string))


class EstimResult:
    def __init__ (self,
                  prob,
                  confidence,
                  satisruns,
                  totalruns,
                  histogram):
        self._probability = prob
        self._confidence = confidence,
        self._runs = totalruns
        self._satisruns = satisruns
        self._histogram = histogram
        assert(self._runs >= self._satisruns)

    def getProbability (self):
        return self._probability

    def getConfidence (self):
        return self._confidence

    def getTotalRuns (self):
        return self._runs

    def getSatisRuns (self):
        return self._satisruns

    def getHistogram (self):
        return self._histogram

    

def parsePlot (line):
    interval = (pp.Literal ("[") + pp.pyparsing_common.number + pp.Literal (",") + pp.pyparsing_common.number + pp.Literal ("]")).setParseAction ( lambda s,l,t: (t[1],t[3]))
    valuesIN = (pp.Literal ("Values in") + interval).setParseAction (lambda s,l,t: t[1])
    mean = (pp.Literal ("mean=")+pp.pyparsing_common.number ()).setParseAction (lambda s,l,t: t[1])
    steps = (pp.Literal ("steps=")+pp.pyparsing_common.number ()).setParseAction (lambda s,l,t: t[1])
    values = (pp.Literal (":")+pp.OneOrMore (pp.pyparsing_common.number ())).setParseAction (lambda s,l,t: t[1:])
    parser = valuesIN+mean+steps+values
    res = parser.parseString (line)
    ran,mean,steps,counts = res[0],res[1],res[2],res[3:]
    return Histogram([(ran[0]+i*steps,ran[0]+(i+1)*steps,val) for i,val in enumerate (counts)])


def parseProbStd (line):
    parser = (pp.Literal ("(")+pp.pyparsing_common.number+pp.Literal ("/") + pp.pyparsing_common.number + pp.Literal ("runs)")+pp.Literal (f"Pr(<> ...) in [")+pp.pyparsing_common.number ()+pp.Literal (",")+pp.pyparsing_common.number ()+pp.Literal("] (")+pp.pyparsing_common.number()+pp.Literal("% CI)")).setParseAction (lambda s,l,t:
                                                                                                                                                                                                             (t[1],t[3],t[6],t[8],t[10]))
    return parser.parseString (line)[0]


def parseProbSplit (line):
    parser = (pp.Literal (f"Pr(<> ... ) in ")+pp.pyparsing_common.number () + pp.Literal (".")) .setParseAction (lambda s,l,t:     t[1] )
    return parser.parseString (line)[0]

class LevelData:
    def  __init__ (self,value,success,effort):
        self._value = value
        self._success = success
        self._effort = effort
    
def parseLevelData (lines):
    #Level 0 (4) 12 / 100
    
    parser = (pp.Literal (f"Level ")+pp.pyparsing_common.number () + pp.Literal ("(") + pp.pyparsing_common.number () + pp.Literal (")") + pp.pyparsing_common.number () + pp.Literal ("/")+pp.pyparsing_common.number()).setParseAction (lambda s,l,t:     LevelData (t[3],t[5],t[7] ))
    
    for l in lines:
        yield parser.parseString (l)[0]

def parseEstim (tmpdir,stdout):
    lines = [r for r in stdout.decode().split('\n') if r != ""]
    
    if "Formula is satisfied" in stdout.decode ():
        resline = lines[1]
        probline = lines[2]
        
 
        return parseProbSplit (probline),list (parseLevelData (lines[3:-1]))
              
    else:
        return 0.0,[]

        
def justPrint  (tmpdir,stdout):
    print (stdout)
    
class Uppaal:
    def __init__ (self,uppaalinst):
        self._uppaalpath = os.path.abspath (uppaalinst)
        
    def __setupDirectory (self,tmpdir,xmlmodel):
        modelexec = os.path.join (tmpdir,"model.xml")
        with open(modelexec,'w') as ff:
            ff.write (xmlmodel)
        return modelexec
                    

            
    def runVerification (self,xmlmodel, query,postprocess = None,options = []):
        pp = postprocess or justPrint
        with tempfile.TemporaryDirectory() as tmpdir:

            querypath = os.path.join (tmpdir,"queery.q")
            with open (querypath,'w') as ff:
                ff.write (query)
            
            modelpath = self.__setupDirectory (tmpdir,xmlmodel)
            binarypath = os.path.join (self._uppaalpath,"bin","verifyta")
            params = [binarypath,"-s","-q"]+options+[modelpath,querypath]
            starttime = time.perf_counter ()
            res = subprocess.run (params,cwd = tmpdir,capture_output=True)
            endtime = time.perf_counter ()
            self._elapsed = endtime - starttime
            return pp (tmpdir,res.stdout)
        

    def elapsed (self):
        return self._elapsed
        
