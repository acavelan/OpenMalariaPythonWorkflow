import math, os, sys, subprocess, torch, shutil
import pandas as pd
import numpy as np

def exec(command):
    return subprocess.Popen(command, shell = True, stderr=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True, text=True)

def run_scicore(scenarios, om_path):
    with open(f"output/commands.txt", "w") as batch_file:
        for scenario in scenarios:
            command = f'openMalaria -s xml/{scenario["count"]}.xml --output txt/{scenario["count"]}.txt'
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
        command = f'openMalaria -s xml/{scenario["count"]}.xml --output txt/{scenario["count"]}.txt'
        processes.append(exec(f'export PATH=$PATH:{om_path} && cd output && {command}'))

    for p in processes:
        try:
            outs, errs = p.communicate(timeout=300)
            print(outs)
            print(errs)
            p.wait()
        except subprocess.TimeoutExpired:
            p.kill()
            
def run_scenarios(scenarios, om_path, om_version, sciCORE=False):
    shutil.copy(om_path+'/densities.csv', "output/")
    shutil.copy(om_path+f'/scenario_{om_version}.xsd', f'output/scenario_{om_version}.xsd')
    
    if sciCORE: run_scicore(scenarios, om_path)
    else: run_local(scenarios, om_path)

def om_output_to_df(scenarios):
    data = []
    for scenario in scenarios:
        try:
            output = pd.read_csv(f"output/txt/{scenario['count']}.txt", sep="\t", header=None)
            output.columns = ['survey', 'ageGroup', 'measure', 'value']
            for key in scenario.keys():
                output[key] = scenario[key]
            data.append(output)
        except Exception as e:
            print(e)

    return pd.concat(data)