import pandas as pd
import shutil

def to_df(scenarios, experiment):
    data = []
    for _, scenario in scenarios.iterrows():
        try:
            index = scenario['index']
            output = pd.read_csv(f"{experiment}/txt/{index}.txt", sep="\t", header=None)
            output.columns = ['survey', 'ageGroup', 'measure', 'value']
            output['index'] = index
            data.append(output)
        except Exception as e:
            print(e)
    
    return pd.concat(data)
