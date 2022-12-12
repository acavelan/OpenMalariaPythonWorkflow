import math, os, sys, subprocess, torch, shutil
import pandas as pd
import numpy as np

def exec(command):
    return subprocess.Popen(command, shell = True, stderr=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True, text=True)

def run_scicore(scenarios, om_path, sciCORE_account, sciCORE_jobName):
    with open(f"output/commands.txt", "w") as batch_file:
        for scenario in scenarios:
            count = scenario["count"]
            outputfile = f'txt/{scenario["count"]}.txt'
            toHDF5 = os.path.dirname(os.path.realpath(__file__)) + '/toHDF5.py'
            command = f'openMalaria -s xml/{count}.xml --output {outputfile}'
            batch_file.write(f'export PATH=$PATH:{om_path} && {command}\n')

        n = len(scenarios)

        with open(f"job.sh", "r") as batchFile:
            script = batchFile.read()
            script = script.replace('@N@', str(n))
            script = script.replace('@account@', sciCORE_account)
            script = script.replace('@jobname@', sciCORE_jobName)

            with open(f'output/start_array_job.sh', 'w') as batch:
                batch.write(script)
    
    subprocess.run(f'cd output && sbatch --wait start_array_job.sh', shell=True)

def run_local(scenarios, om_path):
    processes = []
    for scenario in scenarios:
        count = scenario["count"]
        outputfile = f'txt/{scenario["count"]}.txt'
        toHDF5 = os.path.dirname(os.path.realpath(__file__)) + '/toHDF5.py'
        command = f'openMalaria -s xml/{count}.xml --output {outputfile}'
        processes.append(exec(f'export PATH=$PATH:{om_path} && cd output && {command}'))

    for p in processes:
        try:
            outs, errs = p.communicate(timeout=300)
            # print(outs)
            # print(errs)
            p.wait()
        except subprocess.TimeoutExpired:
            p.kill()

def run_scenarios(scenarios, hdf5file, om_path, om_version, sciCORE=False, sciCORE_account="penny", sciCORE_jobName="OpenMalaria"):
    shutil.copy(om_path+'/densities.csv', "output/")
    shutil.copy(om_path+f'/scenario_{om_version}.xsd', f'output/scenario_{om_version}.xsd')
    
    if sciCORE: run_scicore(scenarios, om_path, sciCORE_account, sciCORE_jobName)
    else: run_local(scenarios, om_path)
