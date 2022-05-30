import importlib.resources
import models.JobShop
import helpers.uppaal
import tabulate


class JobShop:
    def __init__(self, outputloc,uppaal,prefix ="JobShop"):
        self._outputloc = outputloc.subLocation (prefix or "JobShop")
        self._uppaal = uppaal
        self._model = importlib.resources.read_text (models.JobShop,"JobShop.xml")
        
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
    
            
    def estimateProbabilities (self,effort=20,offspring=20):
        rows = []
        for jobs in range(1,100,5):
            model = self._model.replace ("#JOBS#",str(jobs))
            
            fe_prob,_ = self._runFixedEffort (model,jobs,effort)
            fs_prob,_ = self._runFixedSplitting (model,jobs,offspring,effort)
            ad_prob,_ =self._runAdaptive (model,jobs)

            row = [jobs,fe_prob,fs_prob,ad_prob]
            print (row)
            rows.append(row)
        print (tabulate.tabulate (rows,headers=["Jobs","Fixed Effort","Fixed Splitting", "Adaptive"]))
