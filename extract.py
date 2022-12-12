import pandas as pd
import shutil

def to_hdf5(scenarios, hdf5file, append=False):
    if append == False:
        shutil.rmtree(hdf5file, ignore_errors = True)

    data = []
    for _, scenario in scenarios.iterrows():
        try:
            count = scenario['count']
            output = pd.read_csv(f"output/txt/{count}.txt", sep="\t", header=None)
            output.columns = ['survey', 'ageGroup', 'measure', 'value']
            output['count'] = count
            data.append(output)
            # output.to_hdf(hdf5file, key='data', mode='a', append=True, data_columns=True, format='table', index=False, complib='blosc:blosclz', complevel=9)
        except Exception as e:
            print(e)
            
    data = pd.concat(data)
    data.to_hdf(hdf5file, key='data', mode='w', data_columns=True, format='table', index=False, complib='blosc:blosclz', complevel=9)
