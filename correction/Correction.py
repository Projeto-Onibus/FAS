import pdb
import multiprocessing
import cupy as cp
import pandas as pd
import numpy as np
import geopandas as gpd
import movingpandas as mpd
from tracktable.applications.trajectory_splitter import split_when_idle


from .data_processing.FAS import LineCorrection, LineDetection
from .data_processing.LCSS import LCSS
from .data_processing.utils import TracktableSplittedPropertyClassification 
def PadArray(array, maxSize):
    return np.pad(array,((0,maxSize - array.shape[0]),(0,0)),constant_values=np.NaN)

def ExtractLineArray(array):

    return np.asarray(array['trajectory'].coords)

class Corrector:
    
    def __init__(self):
        self.__algorithms = {
                'FAS':self.FASAlgorithm,
                'LCSS':self.LCSSAlgorithm
            }
        self.__parameters = {
                'FAS': {
                    'tolerance': 150,
                    'detectionPercentage':0.9,
                    'correctionLimit':3,
                    'detectionMethod':'HighestThree'
                    },
                'LCSS':{
                    'tolerance': 300
                },
                'trajectory_splitter':{
                    'distance':30, # meters
                    "time":10 # minutes
                    }
            }
        self.__lineData = None
        self.__busData = None
        self.__currentAlgorithm = 'FAS'

    def SetBusData(self,busData):
        self.__busData = busData.copy()
        self.__busList = list(busData.index.get_level_values(1))
        self.__busArrays = self.__busData['trajectory'].apply(np.asarray)
        maxSize = self.__busArrays.apply(lambda x: x.shape[0]).max()
        self.__busMatrix = np.stack(self.__busArrays.apply(PadArray,0,(maxSize,)))
    
    def getBusData(self):
        return self.__busData

    def SetLineData(self,lineData):
        self.__lineData = lineData.copy()
        self.__lineList = lineData[['line','direction']].values.tolist()
        # Creating line matrix 
        self.__lineArrays = self.__lineData.apply(ExtractLineArray,1)
        maxSize = self.__lineArrays.apply(lambda x:x.shape[0]).max()
        self.__lineMatrix = np.stack(self.__lineArrays.apply(PadArray,0,(maxSize,)))

    def getLineData(self):
        return self.__lineData

    def getAvailableAlgorithms(self):
        return self.__algorithms.keys()

    def getAlgorithm(self):
        return self.__currentAlgorithm

    def setAlgorithm(self,newAlgorithm):
        if not newAlgorithm in self.getAvailableAlgorithms():
            raise Exception(f"Algorithm '{newAlgorithm}' not in list of available algorithms: {self.getAvailableAlgorithms()}")
        self.__currentAlgorithm = newAlgorithm

    def AnalyseData(self):
        with open("internal_data.txt",'w') as fil:
            fil.write(f"busData:\n{self.__busData}\n\n")
            fil.write(f"busList:\n{self.__busList}\n\n")
            fil.write(f"busArrays:\n{self.__busArrays}\n\n")
            fil.write(f"busMatrix:\n{self.__busMatrix}\n\n")
            fil.write(f"lineData:\n{self.__lineData}\n\n")
            fil.write(f"lineList:\n{self.__lineList}\n\n")
            fil.write(f"lineArrays:\n{self.__lineArrays}\n\n")
            fil.write(f"lineMatrix:\n{self.__lineMatrix}\n\n")
    
    def LCSSAlgorithm(self):
        detectionTable = pd.DataFrame(False,index=np.array(self.__lineList).T.tolist(),columns=self.__busList).astype('bool')

        progressoTotal = len(self.__busMatrix)
        progresso = 0
        
        #self.__busData['separated_trajectories'] = self.__busData['trajectory'].apply(tracktable.applications.trajectory_splitter.split_when_idle,self.__parameters['trajectory_splitter']['time']*60,self.__parameters,self.__parameters['trajectory_splitter']['distance'])
        for indexBus, bus in self.__busData.iterrows():
            progresso += 1
            separatedTrajectories = split_when_idle(bus['trajectory'],self.__parameters['trajectory_splitter']['time']*60,self.__parameters['trajectory_splitter']['distance']/1000,5)
            for trajectoryIndex, trajectory in enumerate(separatedTrajectories):
                with multiprocessing.Pool(5) as p:
                    lineResults = p.starmap(LCSS,[(np.asarray(trajectory),i,self.__parameters['LCSS']['tolerance']) for i in self.__lineMatrix])
                resultedLineIndex = pd.Series(lineResults)
                resultedLineIndex = resultedLineIndex.idxmax()
                trajectory.set_property('LCSS_detection',str(self.__lineList[resultedLineIndex]))

            TracktableSplittedPropertyClassification(bus['trajectory'],separatedTrajectories,'LCSS_detection')
        
        return True

    def FASAlgorithm(self,detect=False,detectionPercentage=False,divisions=6):
        self.AnalyseData()
        busGpu = cp.asarray(self.__busMatrix[:,:,[1,0]]) 
        linesGpu = cp.asarray(self.__lineMatrix[:,:,[1,0]])
        

        detectionTable = pd.DataFrame(
            index = pd.MultiIndex.from_tuples(self.__lineList,name=("line",'direction')),
            columns = pd.Index(data=self.__busList,name='buses')
         )
        
        # Iterating array in safe division
        for busSegment in range(0,busGpu.shape[0],divisions):
            for lineSegment in range(0,linesGpu.shape[0],divisions):
                detectionMatrix = LineDetection.Algorithm(busGpu[busSegment:busSegment+divisions,:,:],linesGpu[lineSegment:lineSegment+divisions,:,:],self.__parameters['FAS']['tolerance'])
                detectionTableAppend = pd.DataFrame(detectionMatrix.T,
                        index = pd.MultiIndex.from_tuples(self.__lineList[lineSegment:lineSegment+divisions],
                                        name = ("line",'direction')),
                        columns = pd.Index(data=self.__busList[busSegment:busSegment+divisions],name = 'buses')
                     )
                detectionTable.iloc[lineSegment:lineSegment+divisions,busSegment:busSegment+divisions] = detectionTableAppend
        
        # Returns detection percentage
        if detect and detectionPercentage:
            return detectionTable

        if self.__parameters['FAS']['detectionMethod'] == "AbovePercentage":
            # Applies detection percentage and outputs boolean detection table
            detectionTable = detectionTable > self.__parameters['FAS']['detectionPercentage']
        elif self.__parameters['FAS']['detectionMethod'] == "HighestThree":
            for columnName in detectionTable.columns:
                print(detectionTable[columnName].sort_values(ascending=False).iloc[:3])
                detectionTable[columnName] = detectionTable[columnName].isin(detectionTable[columnName].sort_values(ascending=False).iloc[:3])

        # Returns boolean detection table
        if detect:
            return detectionTable

        if not detectionTable.any().any():
            raise Exception("No detections could be made.")
        
        results =  LineCorrection.CorrectData(detectionTable,self.__busMatrix[:,:,[1,0]],self.__lineMatrix[:,:,[1,0]],self.__busList, self.__lineList,
            # Config parameters
            {
                'default_correction_method':
                {
                    'tolerance':self.__parameters['FAS']['tolerance'],
                    'limit':self.__parameters['FAS']['correctionLimit']
                }
            }
        )
#        results.columns = results.columns.to_list().sort()
        reindexedBusData = self.__busData.reorder_levels(['bus_id','time_detection'])
        for index, bus in results.T.iterrows():
            try:
                curBusTrajectory = reindexedBusData.loc[index]['trajectory'].iloc[0]
                for i in range(len(curBusTrajectory)):
                    curBusTrajectory[i].set_property("FAS_detection",results[index][i])
            except KeyError:
                for i in range(len(curBusTrajectory)):
                    curBusTrajectory[i].set_property("FAS_detection","")

        return results
    
    def Correct(self, busData=None, lineData=None):

        if busData:
            self.SetBusData(busData)
        if lineData:
            self.SetLineData(lineData)
        
        if type(self.__busData) == type(None):
            raise Exception("Missing bus data")

        if type(self.__lineData) == type(None):
            raise Exception("Missing Line data")
        
        return self.__algorithms[self.__currentAlgorithm]()

         
    
    def getResults(self):
        return self.results

def main():
    import pandas as pd

    lines = pd.read_pickle('../lines_internorte.pickle')
    buses = pd.read_pickle('../trajects.pickle')

    linesTested = ['456','678']
    busFilter = buses[buses['line_reported'].isin(linesTested)].index.get_level_values(0).unique().to_list()
    lineFilter = lines['line'].isin(linesTested)

    corrector = Corrector()
    resultado = corrector.Correct(buses.loc[busFilter],lines.loc[lineFilter])


if __name__ == '__main__':
    main()
