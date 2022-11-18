import math, os, sys, subprocess, torch, shutil
import pandas as pd
import numpy as np
import plot

# dictionary of OpenMalaria measure name <-> output number
from measures import mm, mmi

sciCORE = False
do_run = True
do_plot =  True

# Base model parameters and default xml with no intervention
templateFiles = ["R0000GA.xml"]
modelNames = ["R0000GA"]

ompath = "/home/acavelan/git/om-dev/fitting/om/openMalaria-44.0"
omversion = 44

# Fixed
age_groups = [0.5,1,2,5,10,15,20,100] # must reflect the xml monitoring section
pop_size = 2000
burn_in_years = 30
access = 0.15 # 5-day probability
start_year = 2000
end_year = 2020
outdoor_biting = 0.2

# Variable
seeds = 10
modes = ["perennial", "seasonal"]
eirs = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.5, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20, 22, 25, 30, 35, 40, 45, 50, 65, 70, 80, 90, 100, 120, 150, 200, 250, 500, 1000]

# Test (12 scenarios with 2000 popsize); uncomment to overwrite other settings and do a quick test
# pop_size = 2000
# modes = ["perennial", "seasonal"]
# eirs = [10, 20, 50]
# seeds = 2

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

xml_folder = "xml_files"
om_output_folder = "om_output"
figures_folder = "figures_output"

def exec(command):
    return subprocess.Popen(command, shell = True, stderr=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True, text=True)

def run_scicore(scenarios):
    with open(f"output/commands.txt", "w") as batch_file:
        for scenario in scenarios:
            command = f'openMalaria -s {xml_folder}/{scenario["count"]}.xml --output {om_output_folder}/{scenario["count"]}.txt'
            batch_file.write(f'export PATH=$PATH:{ompath} && {command}\n')

        n = len(scenarios)

        with open(f"job.sh", "r") as batchFile:
            script = batchFile.read()
            script = script.replace('@N@', str(n))

            with open(f'output/start_array_job.sh', 'w') as batch:
                batch.write(script)
    
    subprocess.run(f'cd output && sbatch --wait start_array_job.sh', shell=True)

def run_local(scenarios):
    processes = []
    for scenario in scenarios:
        command = f'openMalaria -s {xml_folder}/{scenario["count"]}.xml --output {om_output_folder}/{scenario["count"]}.txt'
        processes.append(exec(f'export PATH=$PATH:{ompath} && cd output && {command}'))

    for p in processes:
        try:
            outs, errs = p.communicate(timeout=300)
            print(outs)
            print(errs)
            p.wait()
        except subprocess.TimeoutExpired:
            p.kill()
            
def run_scenarios(scenarios):
    shutil.copy(ompath+'/densities.csv', "output/")
    shutil.copy(ompath+f'/scenario_{omversion}.xsd', f'output/scenario_{omversion}.xsd')
    
    if sciCORE: run_scicore(scenarios)
    else: run_local(scenarios)

# return a list of scenarios
def create_scenarios():
    count = 0
    scenarios = []
    for templateFile, modelName in zip(templateFiles, modelNames):
        xml = None
        with open(templateFile, "r") as fp:
            xml = fp.read()

        xml = xml.replace(f'@version@', f'{omversion}')
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
                
                    with open(f'output/{xml_folder}/{count}.xml', 'w') as fo:
                        fo.write(f'{scenario}')
                        scenarios.append({"modelName": modelName, "eir": eir, "seed": seed, "mode": mode, "count": count})
                        count += 1
    return scenarios

def post_process(scenarios, age_groups):
    data = []
    for _, scenario in scenarios.iterrows():
        try:
            output = pd.read_csv(f"output/{om_output_folder}/{scenario['count']}.txt", sep="\t", header=None)
            output.columns = ['survey', 'ageGroup', 'measure', 'value']
            output['eir'] = scenario['eir']
            output['seed'] = scenario['seed']
            output['mode'] = scenario['mode']
            output['modelName'] = scenario['modelName']
            data.append(output)
        except Exception as e:
            print(e)

    df = pd.concat(data)
    df = df.dropna() # drop rows with NaN
    df = df.reset_index(drop=True)
    
    # remove first survey and sum them up
    df = df.drop(df[df.survey == 1].index)
    df = df.groupby(['mode', 'modelName', 'eir', 'measure', 'ageGroup', 'seed'], as_index=False).value.sum()
    
    # adjust nHost for age_groups 0 to 1 
    yearsAtRisk = np.array(age_groups)
    yearsAtRisk[yearsAtRisk > 1] = 1
    df.loc[(df.measure == mmi['nHost']), 'value'] *= yearsAtRisk[df[(df.measure == mmi['nHost'])].ageGroup-1]

    return df

if do_run:
    shutil.rmtree("output", ignore_errors = True)
    os.makedirs(os.path.relpath(f'output/{xml_folder}'), exist_ok=True)
    os.makedirs(os.path.relpath(f'output/{om_output_folder}'), exist_ok=True)
    os.makedirs(os.path.relpath(f'output/{figures_folder}'), exist_ok=True)

    scenarios = create_scenarios()

    print(f'{len(scenarios)} scenarios created. Running... ', flush=True)
    
    run_scenarios(scenarios)

    print(f'Done.', flush=True)

    scenarios = pd.DataFrame(scenarios)
    scenarios.to_csv("scenarios.csv", index=False)

if do_plot:
    print(f'Loading and post processing... ', flush=True)
    scenarios = pd.read_csv("scenarios.csv")
    df = post_process(scenarios, age_groups)
    print('Done.')

    print(f'Plotting... ', flush=True)

    age_groups_on_plot = [[0,5],[5,10],[10,15],[15,20]]
    plot.prevalence2to10_to_incidence(df, ['nUncomp'], age_groups_on_plot, age_groups, 'Clinical incidence (events per person per year)', [0, 6], f'output/{figures_folder}/prevalence_to_incidence.pdf')
    plot.prevalence2to10_to_incidence(df, ['expectedSevere'], age_groups_on_plot, age_groups, 'Severe cases (events per person per year)', [0, 0.1], f'output/{figures_folder}/prevalence_to_severe.pdf')
    plot.prevalence2to10_to_incidence(df, ['expectedDirectDeaths', 'expectedIndirectDeaths'], age_groups_on_plot, age_groups, 'Mortality (events per person per year)', [0, 0.03], f'output/{figures_folder}/prevalence_to_death.pdf')

    prev_categories = [[0.5,5],[6,14],[22,38],[43,57]]
    for mode in df['mode'].unique():
        plot.age_incidence(df, mode, ['nUncomp'], 'Clinical incidence (events per person per year)', prev_categories, [0, 5.9], age_groups, f'output/{figures_folder}/age_incidence_{mode}.pdf')
        plot.age_incidence(df, mode, ['expectedSevere'], 'Severe cases (events per person per year)', prev_categories, [0, 0.25], age_groups, f'output/{figures_folder}/age_severe_{mode}.pdf')
        plot.age_incidence(df, mode, ['expectedDirectDeaths', 'expectedIndirectDeaths'], 'Mortality (events per person per year)', prev_categories, [0, 0.06], age_groups, f'output/{figures_folder}/age_death_{mode}.pdf')
        
    for mode in df['mode'].unique():
        plot.eir_to_prevalence2to10(df, mode, age_groups, f'output/{figures_folder}/eir_to_prevalence_{mode}.pdf')
        plot.eir_to_prevalence2to10(df, mode, age_groups, f'output/{figures_folder}/eir_to_prevalence_{mode}.pdf')
        plot.eir_to_prevalence2to10(df, mode, age_groups, f'output/{figures_folder}/eir_to_prevalence_{mode}.pdf')

    print(f'Done.', flush=True)