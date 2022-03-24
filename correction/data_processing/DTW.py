from tslearn.metrics import dtw_path_from_metric
from .utils import HaversineMeters

def DTW(path1, path2):
    path1inv = path1[:,[1,0]]
    path2inv = path2[:,[1,0]]
    return dtw_path_from_metric(path1inv,path2inv,metric=HaversineMeters)[1]
