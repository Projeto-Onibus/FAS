import cupy as cp
import pandas as pd
import numpy as np
import geopandas as gpd
import movingpandas as mpd

from .data_processing import LineCorrection, LineDetection

def PadArray(array, maxSize):
    return np.pad(array,((0,maxSize - array.shape[0]),(0,0)),constant_values=np.NaN)

def ExtractLineArray(array):
#    print(array['trajectory'].iloc[0])
    return np.asarray(array['trajectory'].iloc[0].coords)

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
        self.__lineList = list(lineData['line'].unique())

    def FASAlgorithm(self,busMatrix,lineMatrix):
        busGpu = cp.asarray(busMatrix) 
        linesGpu = cp.asarray(lineMatrix)
        detectionMatrix = LineDetection.Algorithm(busGpu,linesGpu,self.__parameters['FASAlgorithm']['tolerance'],self.__parameters['FASAlgorithm']['detectionPercentage'])
        detectionTable = pd.DataFrame(detectionMatrix.T,
                index=pd.Index(data=self.__lineList,
                                name="lines"),
                columns=pd.Index(data=self.__busList,name='buses')
                )
        print(detectionTable)
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
        lineArrays = lineData.groupby("line").apply(ExtractLineArray)
        maxSize = lineArrays.apply(lambda x:x.shape[0]).max()
        lineMatrix = np.stack(lineArrays.apply(PadArray,0,(maxSize,)))
        
        print(lineMatrix)
        # Aplying algorithm
        results =  self.__algorithms['FASAlgorithm'](busMatrix,lineMatrix)

        # Generating output

        return output
        

def main():
    import pandas as pd

    lines = pd.read_pickle('../lines_internorte.pickle')
    buses = pd.read_pickle('../trajects.pickle')

    linesTested = ['371','457','678']
    busFilter = buses[buses['line_reported'].isin(linesTested)].index.get_level_values(0).unique().to_list()
    
    print("Onibus testados:")
    print(busFilter)
    print("Linhas testadas:")
    print(linesTested)
    print("Entrando na correcao....")
    corrector = Corrector()
    resultado = corrector.Correct(buses.loc[busFilter],lines.loc[lines['line'].isin(linesTested)])
    print("Execucao com sucesso")
    print(resultado)


if __name__ == '__main__':
    main()
