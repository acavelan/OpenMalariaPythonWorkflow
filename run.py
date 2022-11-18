import math, os, sys, subprocess, torch, shutil
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def exec(command):
    return subprocess.Popen(command, shell = True, stderr=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True, text=True)

def run_scicore():
    with open(f"output/commands.txt", "w") as batch_file:
        for scenario in scenarios:
            command = f'openMalaria -s 2_xml_files/{scenario["count"]}.xml --output 3_om_output/{scenario["count"]}.txt'
            batch_file.write(f'export PATH=$PATH:{ompath} && {command}\n')

        n = len(scenarios)

        with open(f"job.sh", "r") as batchFile:
            script = batchFile.read()
            script = script.replace('@N@', str(n))

            with open(f'output/start_array_job.sh', 'w') as batch:
                batch.write(script)
    
    subprocess.run(f'cd output && sbatch --wait start_array_job.sh', shell=True)

def run_local():
    processes = []
    for scenario in scenarios:
        command = f'openMalaria -s 2_xml_files/{scenario["count"]}.xml --output 3_om_output/{scenario["count"]}.txt'
        processes.append(exec(f'export PATH=$PATH:../{ompath} && cd output && {command}'))

    for p in processes:
        try:
            p.wait(timeout=300)
        except subprocess.TimeoutExpired:
            p.kill()
            
def run():
    shutil.copy(ompath+'/densities.csv', "output/")
    shutil.copy(ompath+f'/scenario_{newVersion}.xsd', f'output/scenario_{newVersion}.xsd')
    
    if sciCORE:
        run_scicore()
    else:
        run_local()
