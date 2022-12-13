import pandas as pd
import shutil

def to_hdf5(scenarios, experiment):
    data = []
    for _, scenario in scenarios.iterrows():
        try:
            count = scenario['count']
            output = pd.read_csv(f"{experiment}/txt/{count}.txt", sep="\t", header=None)
            output.columns = ['survey', 'ageGroup', 'measure', 'value']
            output['count'] = count
            data.append(output)
            # output.to_hdf(hdf5file, key='data', mode='a', append=True, data_columns=True, format='table', index=False, complib='blosc:blosclz', complevel=9)
        except Exception as e:
            print(e)

    data = pd.concat(data)
    data.to_hdf(f"{experiment}/output.h5", key='data', mode='w', data_columns=True, format='table', index=False, complib='blosc:blosclz', complevel=9)
