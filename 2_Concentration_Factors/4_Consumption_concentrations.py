import numpy as np

import pandas as pd


output = pd.read_csv('output_matrix.csv',index_col=0)


Country = list(output.columns)
A = ['agr','ene','ind','nrtr','rcoc','rcoo','shp','slv','wst']
output = pd.DataFrame.to_numpy(output)
output = np.mat(output)

shp1 = np.zeros(shape=(273739,))
for i in Country[:-1]:
    for j in A:
        shp = pd.read_csv('concentration_factors' + '/' + i + '_' + j.lower() + '_cf.csv')
        shp1 = np.row_stack((shp1,shp['TotalPM25'].values))

shp = pd.read_csv('concentration_factors/ROW_cf.csv')
shp1 = np.row_stack((shp1,shp['TotalPM25'].values))


# Concentration Factors: 273739 * 1871
# Output matrix: 1871 * 188
# Consumption-based concentration matrix: 273739 * 188
concentration_matrix = shp1[1:].T * output


# consumption based concentration matrix
concentration_matrix_df = pd.DataFrame(concentration_matrix)
concentration_matrix_df.columns = Country
concentration_matrix_df.to_csv('comparison/concentration_matrix.csv')