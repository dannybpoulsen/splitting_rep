
import os
import models.SIR
import importlib.resources
import helpers.output
import helpers.uppaal
import experiments

import argparse

parser = argparse.ArgumentParser(description='Importance Splitting Test Framework')
parser.add_argument('--jobshop.effort',  type=int, dest="jobshop_effort",default=20,)
parser.add_argument('--jobshop.offspring', type=int, dest="jobshop_offspring",default=20,)

args = parser.parse_args ()

uppaal = helpers.uppaal.Uppaal ("/home/caramon/Development/uppaal-package/uppaal-splitting")
outputer = helpers.output.OutputLocation ("./results")



jobshop = experiments.JobShop (outputer,uppaal)
jobshop.estimateProbabilities  (effort = args.jobshop_effort,offspring = args.jobshop_offspring)
