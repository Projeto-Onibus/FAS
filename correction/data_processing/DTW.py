from tslearn.metrics import dtw_path_from_metric
from .utils import haversine_meters

def DTW(path1, path2):
    return dtw_path_from_metric(path1,path2,metric=haversine_meters)
