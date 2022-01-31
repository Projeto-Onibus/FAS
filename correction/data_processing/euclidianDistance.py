import numpy as np
from .utils import haversine_meters

def MinimalEuclidianWindowed(traj1,traj2,metric=haversine_meters):
    """! Returns the euclidian distance 
    """
    # Trajectory sizes
    t1Size = traj1.shape[0]
    t2Size = traj2.shape[0]

    # Always have T2 >= T1
    if t1Size > t2Size:
        t1,t2 = (traj2,traj1)
        t1Size, t2Size = (t2Size,t1Size)
    else:
        t1,t2 = (traj1,traj2)


    sizeDiff = t2Size - t1Size    

    # Repeats the same trajectory over new dimension
    expandArray = np.ones((sizeDiff+1,1,1))
    traj2Expand = traj2*expandArray

    # Rolls one unit per position on new dimension
    for i in range(sizeDiff+1):
        traj2Expand[i,:,:] = np.roll(traj2Expand[i,:,:],-i,axis=(0))
    traj2Expand = traj2Expand[:,:traj1.shape[0],:]

    # Matches amount of distance calculations for first trajectory
    traj1Expand = traj1*expandArray

    # Calculate 
    distanceArray = metric(traj1Expand,traj2Expand)

    # Averages on the points dimension and takes the minimal value on the window dimension
    return np.min(np.sum(distanceArray,axis=0)/distanceArray.shape[0])


def MinimalEuclidianWindowedScaled(traj1,traj2,metric=haversine_meters):
    # Trajectory sizes
    t1Size = traj1.shape[0]
    t2Size = traj2.shape[0]

    # Always have T2 >= T1
    if t1Size > t2Size:
        t1,t2 = (traj2,traj1)
        t1Size, t2Size = (t2Size,t1Size)
    else:
        t1,t2 = (traj1,traj2)
    
    # Finds a ratio between sizes
    dotRatio = int(np.floor(traj2.shape[0]/traj1.shape[0]))
    print(dotRatio)
    expandArray = np.ones((dotRatio,1,1))
    traj2Scaled = traj2*expandArray
    
    # Rolls one unit per position on new dimension
    for i in range(dotRatio):
        traj2Scaled[i,:,:] = np.roll(traj2Scaled[i,:,:],-i,axis=(0))
        
    a = np.zeros((traj2Scaled.shape[0],))
    for i in range(traj2Scaled.shape[0]):
        print(traj1,traj2Scaled[i,::dotRatio,:])
        a[i] = MinimalEuclidianWindowed(traj1, traj2Scaled[i,::dotRatio,:])

