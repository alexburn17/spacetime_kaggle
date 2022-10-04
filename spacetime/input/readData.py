from spacetime.objects.fileObject import file_object
from osgeo import gdal

def read_data(dataList=None):

    fileData = []

    for i in range(len(dataList)):
        fileData.append(gdal.Open(dataList[i]))

    ds = file_object(fileData)

    return ds