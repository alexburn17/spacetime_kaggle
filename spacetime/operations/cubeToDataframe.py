import pandas as pd
import numpy as np

def cube_to_dataframe(cube):

    # load data
    ds = cube.get_data_array()
    shapeVal = len(ds.shape)

    # if 3d or 4d data
    if shapeVal == 4:

        df = ds.to_dataframe(name = "value", dim_order = ["lat", "lon", "variables", "time"])
        df = df.reset_index()

    else:

        df = ds.to_dataframe(name = "value", dim_order = ["lat", "lon", "time"])
        df = df.reset_index()

    return df