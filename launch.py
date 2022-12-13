import math, os, sys, subprocess, torch, shutil
import pandas as pd
import numpy as np
import run, extract
import plot

# dictionary of OpenMalaria measure name <-> output number
from measures import mm, mmi

# if using the sciCORE cluster:
sciCORE = False
sciCORE_account = "penny"
sciCORE_jobName = "OpenMalaria"

# OpenMalaria
om_version = 44
om_path = "/home/acavelan/git/om-dev/fitting/om/openMalaria-44.0"
if sciCORE: om_path = "/scicore/home/chitnis/GROUP/openMalaria-44.0/"

hdf5file = 'output.h5'

# switch to only run, plot or both
do_run = False
do_extract = True
do_plot = True

# Scaffold xml to use and a name
scaffolds = {
    "R0000GA.xml" : "R0000GA",
    # "desc_true.xml" : "desc_true",
    # "desc_true_vec.xml" : "desc_true_vec",
    # "desc_false_vec.xml" : "desc_false_vec",
    # "desc_false_vec_het_CV5.xml" : "desc_false_vec_het_CV5",
}

# Fixed
age_groups = [0.5,1,2,5,10,15,20,100] # must reflect the xml monitoring section
pop_size = 10000
burn_in_years = 30
access = 0.2029544 # 5-day probability
start_year = 2000
end_year = 2020
outdoor_biting = 0.2

# Variable
seeds = 15
modes = ["perennial", "seasonal"]
eirs = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.5, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20, 22, 25, 30, 35, 40, 45, 50, 65, 70, 80, 90, 100, 120, 150, 200, 250, 500, 750, 1000]

# Test (12 scenarios with 2000 popsize); uncomment to overwrite other settings and do a quick test
pop_size = 300
eirs = [2, 10, 20, 40, 60, 80, 100, 200]
modes = ["perennial", "seasonal"]
seeds = 3

# Computed
burn_in = start_year - burn_in_years
outdoor = outdoor_biting
indoor = 1.0 - outdoor
age_groups = np.array(age_groups)
age_group_labels = [str(age_groups[i-1])+"-"+str(age_groups[i]) for i in range(1, len(age_groups))]
age_group_labels = [str(0)+"-"+str(age_groups[0])] + age_group_labels

# Define functional form of non-perennial, seasonal setting
season_daily = 1 + np.sin(2 * np.pi * (np.arange(0,365) / 365))
season_month = season_daily[13:365:30]
season_month = season_month / np.max(season_month)
    
# return a list of scenarios
def create_scenarios():
    count = 0
    scenarios = []
    for scaffoldXml, scaffoldName in scaffolds.items():
        xml = None
        with open(f'scaffolds/{scaffoldXml}', "r") as fp:
            xml = fp.read()

        xml = xml.replace(f'@version@', f'{om_version}')
        xml = xml.replace(f'@pop_size@', f'{pop_size}')
        xml = xml.replace(f'@burn_in@', f'{burn_in}')
        xml = xml.replace(f'@access@', f'{access}')
        xml = xml.replace(f'@start_year@', f'{start_year}')
        xml = xml.replace(f'@end_year@', f'{end_year}')
        xml = xml.replace(f'@indoor@', f'{indoor}')
        xml = xml.replace(f'@outdoor@', f'{outdoor}')

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
                
                    with open(f'output/xml/{count}.xml', 'w') as fo:
                        fo.write(f'{scenario}')
                        scenarios.append({"scaffoldName": scaffoldName, "eir": eir, "seed": seed, "mode": mode, "count": count})
                        count += 1
    return scenarios

if do_run:
    print(f'Cleaning Tree...', flush=True)
    shutil.rmtree("output", ignore_errors = True)
    os.makedirs(os.path.relpath(f'output/xml'), exist_ok=True)
    os.makedirs(os.path.relpath(f'output/txt'), exist_ok=True)
    os.makedirs(os.path.relpath(f'output/fig'), exist_ok=True)

    print(f'Creating scenarios...', flush=True)
    scenarios = create_scenarios()

    print(f'Running {len(scenarios)} scenarios...', flush=True)
    run.run_scenarios(scenarios, om_path, om_version, sciCORE, sciCORE_account, sciCORE_jobName)
    pd.DataFrame(scenarios).to_csv('scenarios.csv', index=False)

if do_extract:
    print(f'Extracting results to hdf5 file...', flush=True)
    scenarios = pd.read_csv('scenarios.csv')
    extract.to_hdf5(scenarios, hdf5file)

if do_plot:
    print(f'Loading...', flush=True)
    scenarios = pd.read_csv('scenarios.csv')
    df = pd.read_hdf('output.h5', key='data')

    # User part below
    print(f'Post processing... ', flush=True)
    df = df.dropna() # drop rows with NaN
    df = df.reset_index(drop=True)
    
    # remove first survey and sum them up
    df = df.drop(df[df.survey == 1].index)
    df = df.groupby(['count', 'measure', 'ageGroup'], as_index=False).value.sum()

    # adjust nHost for age_groups 0 to 1 
    yearsAtRisk = np.array(age_groups)
    yearsAtRisk[yearsAtRisk > 1] = 1
    df.loc[(df.measure == mmi['nHost']), 'value'] *= yearsAtRisk[df[(df.measure == mmi['nHost'])].ageGroup-1]

    print(f'Plotting... ', flush=True)
    age_groups_on_plot = [[0,5],[5,10],[10,15],[15,20]]
    plot.prevalence2to10_to_incidence(df, scenarios, ['nUncomp'], age_groups_on_plot, age_groups, 'Clinical incidence (events per person per year)', [0, 6], f'output/fig/prevalence_to_incidence.pdf')
    plot.prevalence2to10_to_incidence(df, scenarios, ['expectedSevere'], age_groups_on_plot, age_groups, 'Severe cases (events per person per year)', [0, 0.1], f'output/fig/prevalence_to_severe.pdf')
    plot.prevalence2to10_to_incidence(df, scenarios, ['expectedDirectDeaths', 'expectedIndirectDeaths'], age_groups_on_plot, age_groups, 'Mortality (events per person per year)', [0, 0.03], f'output/fig/prevalence_to_death.pdf')

    prev_categories = [[0.5,5],[6,14],[22,38],[43,57]]
    for mode in scenarios['mode'].unique():
        plot.age_incidence(df, scenarios, mode, ['nUncomp'], 'Clinical incidence (events per person per year)', prev_categories, [0, 5.9], age_groups, f'output/fig/age_incidence_{mode}.pdf')
        plot.age_incidence(df, scenarios, mode, ['expectedSevere'], 'Severe cases (events per person per year)', prev_categories, [0, 0.25], age_groups, f'output/fig/age_severe_{mode}.pdf')
        plot.age_incidence(df, scenarios, mode, ['expectedDirectDeaths', 'expectedIndirectDeaths'], 'Mortality (events per person per year)', prev_categories, [0, 0.06], age_groups, f'output/fig/age_death_{mode}.pdf')
        
    for mode in scenarios['mode'].unique():
        plot.eir_to_prevalence2to10(df, scenarios, mode, age_groups, f'output/fig/eir_to_prevalence_{mode}.pdf')
        plot.eir_to_prevalence2to10(df, scenarios, mode, age_groups, f'output/fig/eir_to_prevalence_{mode}.pdf')
        plot.eir_to_prevalence2to10(df, scenarios, mode, age_groups, f'output/fig/eir_to_prevalence_{mode}.pdf')
    
    print(f'Done.', flush=True)