import math, os, sys, subprocess, shutil
import platform
import pandas as pd
import numpy as np
import concurrent.futures

def exec(command):
    return subprocess.Popen(command, shell = True, stderr=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True, text=True)

def prepare(output, om):
    shutil.copy(om['path']+"/densities.csv", f"{output}/")
    shutil.copy(om['path']+f"/scenario_{om['version']}.xsd", f"{output}/scenario_{om['version']}.xsd")
    
def run_slurm(scenarios, output, om, slurm):
    prepare(output, om)
    
    with open(f"{output}/commands.txt", "w") as batch_file:
        for _, scenario in scenarios.iterrows():
            index = scenario["index"]
            outputfile = f"txt/{scenario['index']}.txt"
            command = f"openMalaria -s xml/{index}.xml --output {outputfile}"
            batch_file.write(f"export PATH=$PATH:{om['path']} && {command}\n")

        cpus_per_task = slurm['cpus_per_task']
        batch_size = slurm['batch_size']
        n = math.ceil(len(scenarios) / batch_size)

        with open(f"job.sh", "r") as batchFile:
            script = batchFile.read()
            script = script.replace('@N@', str(n))
            script = script.replace('@CPUS_PER_TASK@', str(cpus_per_task))
            script = script.replace('@BATCH_SIZE@', str(batch_size))
            script = script.replace('@prepare@', om['prepare'])

            # Replace general placeholders
            for key, value in slurm.items():
                script = script.replace(f"@{key}@", str(value))

            with open(f"{output}/start_array_job.sh", 'w') as batch:
                batch.write(script)
    
    subprocess.run(f"cd {output} && sbatch --wait start_array_job.sh", shell=True)

def run_command(command, cwd):
    process = subprocess.Popen(
        command,
        shell=True,              # Enable shell execution
        cwd=cwd,                 # Change working directory
        stdout=subprocess.PIPE,  # Capture stdout
        stderr=subprocess.PIPE,   # Capture stderr
        executable="/bin/bash" if platform.system() == "Linux" else None  # Use Bash only on Linux
    )
    stdout, stderr = process.communicate()  # Wait for process to complete
    return stdout, stderr, process.returncode
            
def run_local(scenarios, output, om, max_workers=os.cpu_count()):
    print(f'Using {max_workers} workers.')
    prepare(output, om)
    
    commands = []
    for _, scenario in scenarios.iterrows():
        index = scenario["index"]
        outputfile = f"txt/{index}.txt"
        commands.append(f"{om['prepare']} {om['path']}/openMalaria -s xml/{index}.xml --output {outputfile}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit tasks with limited parallelism
        futures = [executor.submit(run_command, command, output) for command in commands]

    first = True
    for future in concurrent.futures.as_completed(futures):
        stdout, stderr, returncode = future.result()
        if first:
            print(f"Command completed with return code {returncode}", flush=True)
            if stdout:
                print(stdout.decode(), flush=True)
            if stderr:
                print(stderr.decode(), flush=True)
            print("Note: only showing output for the first process")
            first = False
