import importlib.resources
import models.JobShop
import helpers.uppaal
import tabulate
import json
from matplotlib import pyplot as plt

from statistics import mean
from statistics import stdev

class JobShopCore:
    def __init__ (self,
                 outputloc,
                 uppaal,
                 prefix ="JobShop",
                 effort = 20,
                 offspring = 20,
                 progresser = None):
        self._outputloc = outputloc.subLocation (prefix or "JobShop")
        self._uppaal = uppaal
        self._model = importlib.resources.read_text (models.JobShop,"JobShop.xml")
        self._effort = effort
        self._offspring = offspring
        self._progresser = progresser
        
    def _runFixedEffort (self,model,jobs,effort = 20):
        ll =  list (range (1,jobs,3))
        ll.append(jobs+1)
        query = f"Pr[<={jobs*5+1}] (<>) levels level() {{ {','.join ([str(i) for i in ll])} }}"
        options = ["--splitting.algorithm","0","--splitting.effort",f"{effort}"]
        return self._uppaal.runVerification (model,query,options=options,postprocess = helpers.uppaal.parseEstim)
    
        
    def _runFixedSplitting (self,model,jobs,offspring = 20,effort = 20):
        ll =  list (range (1,jobs,3))
        ll.append(jobs+1)
        query = f"Pr[<={jobs*5+1}] (<>) levels level() {{ {','.join ([str(i) for i in ll])} }}"
        options = ["--splitting.algorithm","1","--splitting.offspring",f"{offspring}","--splitting.start_effort",f"{effort}"]
        
        return self._uppaal.runVerification (model,query,options=options,postprocess = helpers.uppaal.parseEstim)
    
    def _runAdaptive (self,model,jobs):
        query = f"Pr[<={jobs*5+1}] (<>) adaptive level() -> Jobs+1"
        return self._uppaal.runVerification (model,query,postprocess = helpers.uppaal.parseEstim)
    
    
    
    def __str__(self):
        return "JobShop"
    
    
class JobShopAllAlgo(JobShopCore):
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
        super().__init__(outputloc,uppaal,"JobShopAllAlgo",effort,offspring,progresser)
        self._min = min
        self._max = max
        self._step = step
        self._repeat = repeat
        
    
    def run (self):
        rows = []
        summary_dict = {"results" : []}
        summary_prob_plot_data = {}
        plotloc = self._outputloc.subLocation ("plots")
        for jobs in range(self._min,self._max,self._step):
            model = self._model.replace ("#JOBS#",str(jobs))
            ins_dict = {"jobs" : jobs,"model" : model}

            fe_prob_list = []
            fs_prob_list = []
            ad_prob_list = []

            fe_time_list = []
            fs_time_list = []
            ad_time_list = []
            
            
            for rep in range(0,self._repeat):

                if self._progresser:
                    self._progresser.message (f"{self} - {jobs} - Repeat: {rep}")
                
                fe_prob,_ = self._runFixedEffort (model,jobs,self._effort)
                fe_prob_list.append (fe_prob)
                fe_time_list.append (self._uppaal.elapsed ())
                
                fs_prob,_ = self._runFixedSplitting (model,jobs,self._offspring,self._effort)
                fs_prob_list.append (fs_prob)
                fs_time_list.append (self._uppaal.elapsed ())
                
                
                ad_prob,_ =self._runAdaptive (model,jobs)
                ad_prob_list.append (ad_prob)
                ad_time_list.append (self._uppaal.elapsed ())
                
                
            ins_dict["probabilities"] = {
                "Fixed Effort" : fe_prob_list,
                "Fixed Splitting" : fs_prob_list,
                "Adaptive" : ad_prob_list
                }
            ins_dict["exec_time"] = {
                "Fixed Effort" : fe_time_list,
                "Fixed Splitting" : fs_time_list,
                "Adaptive" : ad_time_list
                }
            summary_dict["results"].append (ins_dict)

            fig = plt.figure ()
            ax = fig.add_axes ([.25,.25,0.5,0.5])
            ax.boxplot ([fe_prob_list,fs_prob_list,ad_prob_list],labels = ["Fixed Effor","Fixed Splitting", "Adaptive"])
            ax.set_xlabel ("Algorithm")
            ax.set_ylabel ("Probability")
            ax.set_title (f"Jobshop-{jobs}")
            fig.savefig (plotloc.subLocation ("probabilities").outputPath (f"Probabilities_{jobs}.png"))

            fig = plt.figure ()
            ax = fig.add_axes ([.25,.25,0.5,0.5])
            ax.boxplot ([fe_time_list,fs_time_list,ad_time_list],labels = ["Fixed Effor","Fixed Splitting", "Adaptive"])
            ax.set_xlabel ("Algorithm")
            ax.set_ylabel ("Time")
            ax.set_title (f"Jobshop-{jobs}")
            fig.savefig (plotloc.subLocation ("time").outputPath (f"time_{jobs}.png"))
            
            summary_prob_plot_data[jobs] = (mean(fe_prob_list),mean(fs_prob_list),mean(ad_prob_list))
            
            
            row = [jobs,mean(fe_prob_list),stdev(fe_prob_list),mean(fs_prob_list),stdev(fs_prob_list),mean(ad_prob_list),stdev(ad_prob_list)]
            rows.append(row)
        with self._outputloc.outputFile ("summary.json") as outfile:
            json.dump (summary_dict,outfile)
        
        

        with self._outputloc.outputFile ("summary.table") as outfile:
            outfile.write (tabulate.tabulate (rows,headers=["Jobs","Fixed Effort (m)","Fixed Effort (std)","Fixed Splitting (m)", "Fixed Splitting (std)", "Adaptive (m)","Adaptive (std)"]))

        with self._outputloc.outputFile ("summary.csv") as outfile:
            outfile.write (",".join (["Jobs","Fixed Effort (m)","Fixed Effort (std)","Fixed Splitting (m)", "Fixed Splitting (std)", "Adaptive (m)","Adaptive (std)"])+"\n")
            for r in rows:
                outfile.write (",".join ([str(i) for i in r])+"\n")
        
