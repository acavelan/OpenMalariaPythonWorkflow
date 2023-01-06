import pandas as pd
import shutil

def to_df(scenarios, experiment):
    data = []
    for _, scenario in scenarios.iterrows():
        try:
            count = scenario['count']
            output = pd.read_csv(f"{experiment}/txt/{count}.txt", sep="\t", header=None)
            output.columns = ['survey', 'ageGroup', 'measure', 'value']
            output['count'] = count
            data.append(output)
        except Exception as e:
            print(e)
    
    return pd.concat(data)

def to_hdf5(scenarios, experiment):
    to_df(scenarios, experiment).to_hdf(f"{experiment}/output.h5", key='data', mode='w', data_columns=True, format='table', index=False, complib='blosc:blosclz', complevel=9)

def to_csv(scenarios, experiment):
    to_df(scenarios, experiment).to_csv(f"{experiment}/output.h5", index=False, compression='gzip')
