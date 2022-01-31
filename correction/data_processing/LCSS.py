from tslearn.metrics import lcss_path_from_metric
from .utils import HaversineMeters


def LCSS(path1,path2,tolerance=1):
    path1inv = path1[:,[1,0]]
    path2inv = path2[:,[1,0]]
    return lcss_path_from_metric(path1inv,path2inv,tolerance,metric=HaversineMeters)[1]


if __name__ == "__main__":
    import numpy as np 
    a = np.array(
        [
            [-22.01,-43.01],
            [-22.02,-43.02],
            [-22.03,-43.03]
        ]
    )
    b = np.array(
        [
            [-22.01,-43.01],
            [-22.02,-43.02],
            [-22.03,-43.01]
        ]
    )
    print(f"a:\n{a}")
    print(f"b:\n{b}")
    print(f"Haversine vector:\n{haversine_vector(a,b,unit=Unit.METERS)}")
    print("LCSS(a,b):")
    print(LCSS(a,b))
