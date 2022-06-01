import os

import importlib.resources
import models.CovidLink
import helpers.uppaal
import helpers.compiler
import tabulate
import json
from matplotlib import pyplot as plt

from statistics import mean
from statistics import stdev

import plotly.graph_objects as go
from plotly.subplots import make_subplots



class Covid:
    def __init__ (self,
                 outputloc,
                 uppaal,
                 prefix ="Covid",
                 progresser = None):
        self._outputloc = outputloc.subLocation (prefix or "CovidLink")
        self._uppaal = uppaal
        self._model = importlib.resources.read_text (models.CovidLink,"model.xml")
        self._progresser = progresser
        self._prefix = prefix
        

    def getModel (self,libloc):
        return self._model.replace ("#COVIDPATH#",libloc)

    def getLib (self):
        with importlib.resources.path (models.CovidLink,"code") as libby:
            print (libby)
            compiler = helpers.compiler.CmakeCompiler (self._outputloc.getDestination ())
            return  os.path.join (compiler.compile (libby),"libcovidlink.so")
            
    
    def __str__(self):
        return self._prefix
    
    
class CovidSimulate(Covid):
    def __init__(self,
                 outputloc,
                 uppaal,
                 progresser = None,
                 simulations = 1
                 ):
        super().__init__(outputloc,uppaal,"CovidSimulation",progresser)
        self._simulations = simulations
        
    def run (self):
        libloc = self.getLib () 
        model = self.getModel (str(libloc))
        env = { "LD_PRELOAD" : "/usr/lib/libasan.so",
                "UPPAAL_SPLITTING_API" : str(libloc)
        }
        traj = ["S","E","I","R","H","V"]
        parser = helpers.uppaal.parseSamplingLog (traj)
        inp = ",".join ([f"{n}()" for n in traj])
        query = f"simulate {self._simulations} [<=250] {{ {inp} }}"
        options = ["-F","0.25","-O","csv"]
        res = self._uppaal.runVerification (model,query,parser, options= options, env = env)

        #fig = make_subplots (rows = len(res)+1,cols = 1)

        fig_health = plt.figure ()
        ax_health  = fig_health.add_axes ([.25,.25,0.5,0.5])

        for i,data in enumerate(res):
            # Specify the plots
            x = data["time"]

            fig = plt.figure ()
            ax =  fig.add_axes ([.25,.25,0.5,0.5])


            for label in traj:
                #fig.add_trace(go.Line(x=x, y=y, name=label),row = i+1,col =1)
                ax.plot (x,data[label],label = label)

            ax_health.plot (x,data["H"],label = f"H_{i}")


            ax.set_xlabel ("Days")
            ax.set_ylabel ("Individuals")
            #ax.set_title ("Pandemic Model")
            ax.legend ()

            fig.savefig (str(self._outputloc.outputPath (f"simulation_{i}.png")))

        fig_health.savefig (str(self._outputloc.outputPath ("healths.png")))



class CovidAdaptive(Covid):
    def __init__(self,
                 outputloc,
                 uppaal,
                 progresser = None,
                 limit =600
                 ):
        super().__init__(outputloc,uppaal,"CovidEstimation",progresser)
        self._limit = limit
        
    def run (self):
        
        
        libloc = self.getLib ()
            
        model = self.getModel (str(libloc))
        env = { "LD_PRELOAD" : "/usr/lib/libasan.so",
                "UPPAAL_SPLITTING_API" : str(libloc)
        }
        options = [
            "--splitting.adaptive.effort","100",
            "--splitting.adaptive.retain","50"]
        query = f"Pr[<=250] (<>) adaptive I_d () -> {self._limit}"
        ad_prob,level_data = self._uppaal.runVerification (model,query,helpers.uppaal.parseEstim, options=options,  env = env)
        with self._outputloc.outputFile ("summary.json") as outfile:
            levels  = [
                {"value" : l._value,
                 "success" : l._success,
                 "effort" : l._effort
                 }
                for l in level_data
            ]


            res = {"probability" : ad_prob,
                   "time" : self._uppaal.elapsed (),
                   "model" : model,
                   "levels" : levels
                   }

            with self._outputloc.outputFile ("summary.json") as outfile:
                json.dump (res,outfile)

            with self._outputloc.outputFile ("levels.csv") as outfile:
                outfile.write ("Level, Value, Satis, Effort, Probability\n")
                for i,l in enumerate(level_data):
                    outfile.write (f"{i},{l._value},{l._success},{l._effort},{l._success / l._effort}\n")
        
