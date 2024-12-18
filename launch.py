import math, os, sys, subprocess, torch, shutil
import pandas as pd
import numpy as np
import run, extract

# dictionary of OpenMalaria measure name <-> output number
from measures import mm, mmi

# if using the sciCORE cluster:
sciCORE = {
    'use' : True,
    'account' : 'penny',
    'jobName' : 'OpenMalaria'
}

# OpenMalaria
om = { 
    'version' : 45,
    'path' : "/home/acavelan/git/fitting/om/openMalaria-45.0"
}
if sciCORE['use']: om['path'] = "/scicore/home/scicore/cavelan/git/fitting/OpenMalaria/om/openMalaria-45.0/"

# Scaffold xml to use
scaffolds = {
    "R0000GA" : "R0000GA"
}

# switch to only run, plot or both
do_run = True
do_extract = True
do_example =  True

experiment = 'benchmark' # name of the experiment folder

# Fixed parameters for all xmls
pop_size = 10000 # number of humans
start_year = 2000 # start of monitoring period
end_year = 2020 # end of monitoring period
burn_in = start_year - 30 # additional burn in time
access = 0.2029544 # 5-day probability
outdoor = 0.2
indoor = 1.0 - outdoor

# Variable
seeds = 10
modes = ["perennial", "seasonal"]
eirs = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.5, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20, 22, 25, 30, 35, 40, 45, 50, 65, 70, 80, 90, 100, 120, 150, 200, 250, 500, 750, 1000]

# For a quick test
# seeds = 3
# pop_size = 2000
# eirs = [1, 5, 10, 20, 50, 100]

# Define functional form of non-perennial, seasonal setting
season_daily = 1 + np.sin(2 * np.pi * (np.arange(0,365) / 365)) / 2 + np.cos(2 * np.pi * (np.arange(0,365) / 365)) / 2
season_month = [season_daily[1+int(i*(365/12))] for i in range(0, 12)]
season_month = season_month / np.max(season_month)
    
# return a list of scenarios
def create_scenarios():
    index = 0
    scenarios = []
    for scaffold, scaffoldName in scaffolds.items():
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
                
                    with open(f"{experiment}/xml/{index}.xml", 'w') as fo:
                        fo.write(f"{scenario}")
                        scenarios.append({"scaffoldName": scaffoldName, "eir": eir, "seed": seed, "mode": mode, "index": index})
                    index += 1
    return scenarios

# run all the scenarios and write the scenarios metadata to scenarios.csv
if do_run:
    print(f"Cleaning Tree...", flush=True)
    shutil.rmtree("{experiment}", ignore_errors = True)
    os.makedirs(os.path.relpath(f"{experiment}/xml"), exist_ok=True)
    os.makedirs(os.path.relpath(f"{experiment}/txt"), exist_ok=True)
    os.makedirs(os.path.relpath(f"{experiment}/fig"), exist_ok=True)
    os.makedirs(os.path.relpath(f"{experiment}/log"), exist_ok=True)

    print(f"Creating scenarios...", flush=True)
    scenarios = create_scenarios()
    pd.DataFrame(scenarios).to_csv(f'{experiment}/scenarios.csv', index=False)

    print(f"Running {len(scenarios)} scenarios...", flush=True)
    run.run_scenarios(scenarios, experiment, om, sciCORE)

# concatenate all txt outputs from OpenMalaria to a nice output.csv file
if do_extract:
    print(f"Extracting results...", flush=True)
    shutil.rmtree(f"{experiment}/output.csv", ignore_errors = True)
    scenarios = pd.read_csv(f'{experiment}/scenarios.csv')
    df = extract.to_df(scenarios, experiment)
    # df.to_csv(f"{experiment}/output.csv", index=False, compression='gzip')
    df.to_hdf(f"{experiment}/output.h5", key='df', mode='w', index=False) # Many times faster than csv

if do_example:
    print(f"Loading...", flush=True)
    scenarios = pd.read_csv(f'{experiment}/scenarios.csv')
    # df = pd.read_csv(f"{experiment}/output.csv", compression='gzip')
    df = pd.read_hdf(f"{experiment}/output.h5", key='df')
    df.reset_index(drop=True, inplace=True)

    # User part below
    print(f"Post processing...", flush=True)
    df.dropna(inplace=True)

    # remove first survey
    df.drop(df[df.survey == 1].index, inplace=True)

    # reset index
    df.reset_index(inplace=True)

    # Sum the surveys
    df = df.groupby(['index', 'measure', 'ageGroup'], as_index=False).value.sum()
