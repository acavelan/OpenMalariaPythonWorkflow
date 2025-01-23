import math, os, sys, subprocess, shutil
import pandas as pd
import numpy as np

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

def run_local(scenarios, output, om):
    prepare(output, om)
    
    processes = []
    for _, scenario in scenarios.iterrows():
        index = scenario["index"]
        outputfile = f"txt/{index}.txt"
        command = f"{om['prepare']} && openMalaria -s xml/{index}.xml --output {outputfile}"

        # Construct environment
        env = os.environ.copy()
        env["PATH"] += f":{om['path']}"
        
        # Change to the output directory and execute the command
        process = subprocess.Popen(
            command,
            shell=True,              # Enable shell execution
            cwd=output,              # Change working directory
            env=env,                 # Pass the modified environment
            executable="/bin/bash",  # Use Bash 
            stdout=subprocess.PIPE,  # Capture stdout
            stderr=subprocess.PIPE   # Capture stderr
        )
        processes.append(process)
    
    # Wait for all processes to complete
    for process in processes:
        stdout, stderr = process.communicate()
        # if process.returncode != 0:
        #     print(f"Error: {stderr.decode().strip()}")
        # else:
        #     print(f"Success: {stdout.decode().strip()}")
