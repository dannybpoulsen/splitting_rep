
import os
import models.SIR
import importlib.resources
import helpers.output
import helpers.uppaal
import experiments

import argparse

parser = argparse.ArgumentParser(description='Importance Splitting Test Framework')

progresser = helpers.uppaal.Progresser ()

jobshopgroup = parser.add_argument_group ("JobShop Case")
jobshopgroup.add_argument('--jobshop.enable',  dest="jobshop_enable",action="store_true",default=False,)
jobshopgroup.add_argument('--jobshop.effort',  type=int, dest="jobshop_effort",default=20,)
jobshopgroup.add_argument('--jobshop.offspring', type=int, dest="jobshop_offspring",default=20,)

jobshopgroup = parser.add_argument_group ("Running Case")
jobshopgroup.add_argument('--running.enable',  dest="running_enable",action="store_true",default=False,)
jobshopgroup.add_argument('--running.effort',  type=int, dest="running_effort",default=20,)
jobshopgroup.add_argument('--running.offspring', type=int, dest="running_offspring",default=20,)


args = parser.parse_args ()

uppaal = helpers.uppaal.Uppaal ("/home/caramon/Development/uppaal-package/uppaal-splitting")
outputer = helpers.output.OutputLocation ("./results")



jobs = []

if args.jobshop_enable:
    jobs.append (experiments.JobShopAllAlgo (outputer,uppaal,effort = args.jobshop_effort,offspring = args.jobshop_offspring,progresser = progresser))

if args.running_enable:
    jobs.append (experiments.RunningAllAlgo (outputer,uppaal,effort = args.running_effort,offspring = args.running_offspring,progresser = progresser))



for j in jobs:
    j.run ()

    
