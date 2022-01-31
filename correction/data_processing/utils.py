import numpy as np
from haversine import haversine, haversine_vector, Unit


def HaversineMeters(a,b):
    """
    HaversineMeters
    
    """
    return haversine(a,b,unit=Unit.METERS)

def HaversineTrajectoryTotalLength(a):
    """! @brief Given a trajectory in WSG84, returns its total length in meters.
    
    Given a trajectory consisting of n points in a numpy array of dimensions (n x 2), it returns the total length of this trajectory in meters.
    This array is considered as a list of points in the format [latitude,longitude].

    @param a (np.array (n x 2)) Matrix where n is the total number of points in the trajectory. Points are represented as [lat,lon].
    
    @returns (float) total length of the trajectory, in meters.
    """
    return np.sum(haversine_vector(a[1:,:],a[:-1,:],unit=Unit.METERS))


def TracktablePropertyList(traj,propName):
    propList = []
    for i in traj:
        propList.append(i.property(propName))
    return propList

def TracktableSetPropertyPoints(traj,propName,propVal):
    for i in traj:
        i.set_property(propName,propVal)


def TracktableTimestampList(traj):
    timestamps = []
    for i in traj:
        timestamps.append(i.timestamp)
    return timestamps


def TracktableSplittedPropertyClassification(originalTraj, splittedTrajs, propName):
    """
    @brief Classifies points in the original trajectory based on individual classifications of the splitted trajectory

    Takes an trajectory and a list of subsets of that trajectory. 
    For each item on the list, it will take the value of a property defined by propName and set for each point in the original trajectory corresponding to its subset the same property name and value

    @param originalTraj original trajectory that generated the splitted trajectory list 
    @param splittedTrajs List of trajectories that are subsets of originalTraj, those trajectories may or may not have a trajectory-defined property
    @param propName The name of the property to set on the original trajectory


    """
    for subtraj in splittedTrajs:
        propVal = subtraj.property(propName)
        # Skips if trajectory was not set
        if not propVal:
            continue
        # Iterates through points of original trajectory
        for i in originalTraj:
            # Passes if out of property
            if i.timestamp > subtraj[-1].timestamp:
                break
            # If current index in subtraj, sets property
            elif i.timestamp >= subtraj[0].timestamp:
                i.set_property(propName,propVal)


