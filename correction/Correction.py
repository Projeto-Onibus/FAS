import cupy as cp
import pandas as pd
import numpy as np
import geopandas as gpd
import movingpandas as mpd

from .data_processing import LineCorrection, LineDetection

def PadArray(array, maxSize):
    return np.pad(array,((0,maxSize - array.shape[0]),(0,0)),constant_values=np.NaN)

def ExtractLineArray(array):

    return np.asarray(array['trajectory'].coords)

class Corrector:
    
    def __init__(self):
        self.__algorithms = {
                'FASAlgorithm':self.FASAlgorithm
            }
        self.__parameters = {
                'FASAlgorithm': {
                    'tolerance': 300,
                    'detectionPercentage':0.9,
                    'correctionLimit':3
                    }
                }
        self.__lineData = None
        self.__busData = None

    def SetBusData(self,busData):
        self.__busData = busData.copy()
        self.__busList = list(busData.index.get_level_values(0).unique())

    def SetLineData(self,lineData):
        self.__lineData = lineData.copy()
        self.__lineList = list(lineData.index)

    def FASAlgorithm(self,busMatrix,lineMatrix):
        busGpu = cp.asarray(busMatrix) 
        linesGpu = cp.asarray(lineMatrix)
        #print(lineMatrix[0])
        #print(busMatrix[0])
        detectionMatrix = LineDetection.Algorithm(busGpu,linesGpu,self.__parameters['FASAlgorithm']['tolerance'],self.__parameters['FASAlgorithm']['detectionPercentage'])
        #print(detectionMatrix)
        #print(detectionMatrix.any())
        detectionTable = pd.DataFrame(detectionMatrix.T,
                index=pd.Index(data=self.__lineList,
                                name="lines"),
                columns=pd.Index(data=self.__busList,name='buses')
                )
        print(detectionTable)
        print(detectionTable.to_numpy().any())
        return LineCorrection.CorrectData(detectionTable,busMatrix,lineMatrix,self.__busList, self.__lineList,
            {'default_correction_method':
                {
                    'tolerance':self.__parameters['FASAlgorithm']['tolerance'],
                    'limit':self.__parameters['FASAlgorithm']['correctionLimit']
                }
            }
            )

    def Correct(self, busData, lineData):
        
        self.SetBusData(busData)
        self.SetLineData(lineData)

        # Creating bus matrix
        busArrays = busData[['latitude','longitude']].groupby('bus_id').apply(np.asarray)
        maxSize = busArrays.apply(lambda x: x.shape[0]).max()
        busMatrix = np.stack(busArrays.apply(PadArray,0,(maxSize,)))
        
        # Creating line matrix 
        lineArrays = lineData.apply(ExtractLineArray,1)
        maxSize = lineArrays.apply(lambda x:x.shape[0]).max()
        lineMatrix = np.stack(lineArrays.apply(PadArray,0,(maxSize,)))
        
        # TODO: Fix compatibility with haversine and other standards so lat/lon position dont have to be swapped
        lineMatrix[:,:,[0,1]] = lineMatrix[:,:,[1,0]]

        results =  self.__algorithms['FASAlgorithm'](busMatrix,lineMatrix)

        # Generating output

        return output
        

def main():
    import pandas as pd

    lines = pd.read_pickle('../lines_internorte.pickle')
    buses = pd.read_pickle('../trajects.pickle')

    linesTested = ['456','678']
    busFilter = buses[buses['line_reported'].isin(linesTested)].index.get_level_values(0).unique().to_list()
    lineFilter = lines['line'].isin(linesTested)

    print("Onibus testados:", len(busFilter))
    print("Linhas testadas:",len(linesTested))
    #print(lines.loc[lineFilter])
    print("Entrando na correcao....")
    corrector = Corrector()
    resultado = corrector.Correct(buses.loc[busFilter],lines.loc[lineFilter])
    print("Execucao com sucesso")
    print(resultado)


if __name__ == '__main__':
    main()
