import pandas as pd
import numpy as np
import shutil

def to_df(scenarios, experiment):
    data = []
    for _, scenario in scenarios.iterrows():
        try:
            index = scenario['index']
            output = pd.read_csv(f"{experiment}/txt/{index}.txt", sep="\t", header=None)
            output['index'] = index
            data.append(output)
        except Exception as e:
            print(e)
    
    df = pd.concat(data)
    df.columns = ['survey', 'ageGroup', 'measure', 'value', 'index']
    df = df.astype(dtype = {
        'survey' : np.int32,
        'ageGroup' : np.int32,
        'measure' : np.int32,
        'value' : np.float64,
        'index' : np.int32
    })
    return df
