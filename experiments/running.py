import importlib.resources
import models.running
import helpers.uppaal
import tabulate
import json
from matplotlib import pyplot as plt

from statistics import mean
from statistics import stdev

class RunningCore:
    def __init__ (self,
                 outputloc,
                 uppaal,
                 prefix ="JobShop",
                 effort = 20,
                 offspring = 20,
                 progresser = None):
        self._outputloc = outputloc.subLocation (prefix or "JobShop")
        self._uppaal = uppaal
        self._model = importlib.resources.read_text (models.running,"running.xml")
        self._effort = effort
        self._offspring = offspring
        self._progresser = progresser
        self._prefix = prefix
        
    def _runFixedEffort (self,model,jobs,effort = 20):
        ll =  list (range (1,jobs,1))
        ll.append(jobs+1)
        query = f"Pr[<={jobs*5+1}] (<>) levels Process.level() {{ {','.join ([str(i) for i in ll])} }}"
        options = ["--splitting.algorithm","0","--splitting.effort",f"{effort}"]
        return self._uppaal.runVerification (model,query,options=options,postprocess = helpers.uppaal.parseEstim)
    
        
    def _runFixedSplitting (self,model,jobs,offspring = 20,effort = 20):
        ll =  list (range (1,jobs,1))
        ll.append(jobs+1)
        query = f"Pr[<={jobs*5+1}] (<>) levels Process.level() {{ {','.join ([str(i) for i in ll])} }}"
        options = ["--splitting.algorithm","1","--splitting.offspring",f"{offspring}","--splitting.start_effort",f"{effort}"]
        
        return self._uppaal.runVerification (model,query,options=options,postprocess = helpers.uppaal.parseEstim)
    
    def _runAdaptive (self,model,jobs):
        query = f"Pr[<={jobs*5+1}] (<>) adaptive Process.level() -> {jobs}"
        return self._uppaal.runVerification (model,query,postprocess = helpers.uppaal.parseEstim)
    
    
    
    def __str__(self):
        return self._prefix
    
    
class RunningAllAlgo(RunningCore):
    def __init__(self,
                 outputloc,
                 uppaal,
                 effort = 20,
                 offspring = 20,
                 progresser = None,
                 min = 1,
                 max = 50,
                 step = 5,
                 repeat = 10
                 ):
        super().__init__(outputloc,uppaal,"RunningAllAlgo",effort,offspring,progresser)
        
    
    def run (self):
        rows = []
        summary_dict = {"results" : []}
        summary_prob_plot_data = {}
        plotloc = self._outputloc.subLocation ("plots")
        for jobs in range(100,101):
            model = self._model.replace ("#JOBS#",str(jobs))
            ins_dict = {"jobs" : jobs,"model" : model}

            fe_prob_list = []
            fs_prob_list = []
            ad_prob_list = []

            fe_time_list = []
            fs_time_list = []
            ad_time_list = []
            
            

            if self._progresser:
                self._progresser.message (f"{self} - {jobs} ")
                
            fe_prob,leveldata = self._runFixedEffort (model,jobs,self._effort)
            ad_prob,leveldata_ad = self._runAdaptive (model,jobs)
            
                #fs_prob,_ = self._runFixedSplitting (model,jobs,self._offspring,self._effort)
                #fs_prob_list.append (fs_prob)
                #fs_time_list.append (self._uppaal.elapsed ())
                
            ins_dict["Fixed Effort levels"] = [
                {"value" : l._value,
                 "success" : l._success,
                 "effort" : l._effort
                 }
                for l in leveldata
            ]

            ins_dict["Adatptive levels"] = [
                {"value" : l._value,
                 "success" : l._success,
                 "effort" : l._effort
                 }
                for l in leveldata_ad
            ]
            
            summary_dict["results"].append (ins_dict)

            
            
        with self._outputloc.outputFile ("summary.json") as outfile:
            json.dump (summary_dict,outfile)

        with self._outputloc.outputFile ("fixed_effort_levels.csv") as outfile:
            outfile.write ("Level, Value, Satis, Effort, Probability\n")
            for i,l in enumerate(leveldata):
                outfile.write (f"{i},{l._value},{l._success},{l._effort},{l._success / l._effort}\n")
        

        with self._outputloc.outputFile ("adaptive_levels.csv") as outfile:
            outfile.write ("Level, Value, Satis, Effort, Probability\n")
            for i,l in enumerate(leveldata):
                outfile.write (f"{i},{l._value},{l._success},{l._effort},{l._success / l._effort}\n")
        
        
