import numpy as np
import cupy as cp

from correction.data_processing.LineDetection import Algorithm

def test_Algorithm():
    
    # Aproximate distances
    # 0.1 -> 11.5km
    # 0.01 -> 1.15km
    # 0.001 -> 150m
    # 0.0001 -> 15m

    A = np.array([
            # Line 1
            [
                [22.0,43.0],
                [22.0001,43.0],
                [22.0002,43.0],
                [22.0003,43.0],
                [22.0004,43.0]
            ],
            # Line 2
            [
                [22.0,43.0],
                [22.0,43.0001],
                [22.0,43.0002],
                [22.0,43.0003],
                [22.0,43.0004]
            ]
        ])
    
    B = np.array([
            # Line 1
            # Line 2
            [
                [22.0,43.0],
                [22.0,43.0001],
                [22.0,43.0002],
                [22.0,43.0003],
                [22.0,43.0004]
            ],
            [
                [22.0,43.0],
                [22.0001,43.0],
                [22.0002,43.0],
                [22.0003,43.0],
                [22.0004,43.0]
            ]
        ])
    
    C = (Algorithm(cp.asarray(A),cp.asarray(B),10,0.9)).get()
    assert(np.array_equal(C,np.array([[0,1],[1,0]])))


    
