import math, os, sys, subprocess, torch, shutil
import pandas as pd
import numpy as np
import run, extract

# dictionary of OpenMalaria measure name <-> output number
from measures import mm, mmi

# if using the sciCORE cluster:
sciCORE = {
    'use' : False,
    'account' : 'penny',
    'jobName' : 'OpenMalaria'
}

# OpenMalaria
om = { 
    'version' : 44,
    'path' : "/home/acavelan/git/om-dev/fitting/om/openMalaria-44.0"
}
if sciCORE['use']: om['path'] = "/scicore/home/chitnis/GROUP/openMalaria-44.0/"

# Scaffold xml to use and a name
scaffolds = {
    "R0000GA"
}

# switch to only run, plot or both
do_run = False
do_extract = False

experiment = 'test'

# Fixed
pop_size = 10000
burn_in_years = 30
access = 0.2029544 # 5-day probability
start_year = 2000
end_year = 2020
outdoor_biting = 0.2

# Variable
seeds = 10
modes = ["perennial", "seasonal"]
eirs = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.5, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20, 22, 25, 30, 35, 40, 45, 50, 65, 70, 80, 90, 100, 120, 150, 200, 250, 500, 750, 1000]

# Test (12 scenarios with 2000 popsize); uncomment to overwrite other settings and do a quick test
# pop_size = 300
# eirs = [2, 10, 20, 40]#, 60, 80, 100, 200]
# modes = ["perennial", "seasonal"]
# seeds = 3

# Computed
burn_in = start_year - burn_in_years
outdoor = outdoor_biting
indoor = 1.0 - outdoor

# Define functional form of non-perennial, seasonal setting
season_daily = 1 + np.sin(2 * np.pi * (np.arange(0,365) / 365))
season_month = [season_daily[1+int(i*(365/12))] for i in range(0, 12)]
season_month = season_month / np.max(season_month)
    
# return a list of scenarios
def create_scenarios():
    count = 0
    scenarios = []
    for scaffold in scaffolds.items():
        xml = None
        with open(f"scaffolds/{scaffold}.xml", "r") as fp:
            xml = fp.read()

        xml = xml.replace(f"@version@", f"{om['version']}")
        xml = xml.replace(f"@pop_size@", f"{pop_size}")
        xml = xml.replace(f"@burn_in@", f"{burn_in}")
        xml = xml.replace(f"@access@", f"{access}")
        xml = xml.replace(f"@start_year@", f"{start_year}")
        xml = xml.replace(f"@end_year@", f"{end_year}")
        xml = xml.replace(f"@indoor@", f"{indoor}")
        xml = xml.replace(f"@outdoor@", f"{outdoor}")

        for eir in eirs:
            for seed in range(0,seeds):
                for mode in modes:
                    scenario = xml.replace('@seed@', str(seed))
                    scenario = scenario.replace('@eir@', str(eir))

                    if mode == "seasonal": seasonality = season_month
                    elif mode == "perennial": seasonality = np.ones(12)
                    else: print("unknown mode:", mode)

                    for i in range(1,13):
                        scenario = scenario.replace(f'@seasonality{i}@', str(seasonality[i-1]))
                
                    with open(f"{experiment}/xml/{count}.xml", 'w') as fo:
                        fo.write(f"{scenario}")
                        scenarios.append({"scaffoldName": scaffold, "eir": eir, "seed": seed, "mode": mode, "count": count})
                        count += 1
    return scenarios

# run all the scenarios and write the scenarios metadata to scenarios.csv
if do_run:
    print(f"Cleaning Tree...", flush=True)
    shutil.rmtree("{experiment}", ignore_errors = True)
    os.makedirs(os.path.relpath(f"{experiment}/xml"), exist_ok=True)
    os.makedirs(os.path.relpath(f"{experiment}/txt"), exist_ok=True)
    os.makedirs(os.path.relpath(f"{experiment}/fig"), exist_ok=True)

    print(f"Creating scenarios...", flush=True)
    scenarios = create_scenarios()

    print(f"Running {len(scenarios)} scenarios...", flush=True)
    run.run_scenarios(scenarios, experiment, om, sciCORE)
    pd.DataFrame(scenarios).to_csv(f'{experiment}/scenarios.csv', index=False)

# concatenate all txt outputs from OpenMalaria to a nice output.csv file
if do_extract:
    print(f"Extracting results...", flush=True)
    shutil.rmtree(f"{experiment}/output.h5", ignore_errors = True)
    scenarios = pd.read_csv(f'{experiment}/scenarios.csv')
    extract.to_csv(scenarios, experiment)
    # extract.to_hdf5(scenarios, experiment)

# load scenarios.csv and output.csv as dataframes
# merge them (on the 'count' column) to get all the data in one place