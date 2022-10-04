import netCDF4 as nc
import numpy as np
from spacetime.objects.cubeObject import cube
from spacetime.operations.time import cube_time, return_time

def load_cube(file):

    # get data set
    ds = nc.Dataset(file)

    # get time
    time = return_time(ds.variables["time"])

    # get var names
    vars = list(ds.variables.keys())
    matches = ['time', 'lat', 'lon', 'spatial_ref']
    varNames = list(set(vars)-set(matches))

    # get structure
    if len(varNames) > 1:
        struc = "filestovar"
    else:
        struc = "filestotime"


    cube_ds = cube(ds, fileStruc = struc, names=varNames, timeObj=time)

    return cube_ds

    ds.close()