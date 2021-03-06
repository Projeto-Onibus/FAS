#
# DataCorrection.py
# Descricao:
#

import configparser
import logging

import pandas as pd
import numpy as np
import cupy as cp

from .LineDetection import HaversineLocal

def CorrectData(detectionTable, busMatrix, linesMatrix, busList, lineList, CONFIGS):
	"""
	Description:
		Gets all of bus data and corrects each bus' line column based on results from FilterData

	Arguments:
		detectionTable - detectionTable[('<line>', '<direction>')]['<bus>'] -> True if line belongs to bus trajectory
			__________|Bus0|Bus1|...|BusN|
			|(Line0,0)|bool|bool|	|bool|
			|(Line0,1)|bool|bool|	|bool|
			|(Linei,j)|bool|bool|	|... |
			|(LineN,1)|bool|bool|...|bool|

		busMatrix - busMatrix[<bus>][<coord>][<lat/lon>]

		linesMatrix - linesMatrix[<line>][<coord>][<lat/lon>]

		busList - busList[<bus>] -> (busId)

		lineList - lineList[<line>] -> (<lineId>,<direction>)

		CONFIGS - configparser object

	Return:
		results - Pandas DataFrame of same bus data with appended column of corrected line column data

	Required Configurations:
		CONFIGS['line_correction']['limit'] - The minimun value to consider a set of points as a valid group
	"""

    
	# List of all lines detected for each bus. Series of tuples (<line>, <direction>, <onibus>)
	detections = detectionTable[detectionTable == True].stack()
	buses_detected = detections.index.get_level_values(2).unique() # Ids in wich a detection was made
	lines_detected = list(set(map(lambda x: (x[0], x[1]), detections.index))) # Lines that were detected
	busList = list(busList) 
	lineList = list(map(lambda x: (x[0]), lineList))
    

	correctedData = []

    # iteraing over each bus that has at least one detection
	for bus in buses_detected:
        # Selects the buses' coordinates
		busMap = np.array(busMatrix[busList.index(bus)])
		busMap = busMap[~np.any(np.isnan(busMap), axis=1)]
		
        # Select line
		lines = [i[0] for i in detectionTable[bus].loc[detectionTable[bus] == True].index.unique()]
		linesToCompare = []

        # Iterate over each line that was detected for this bus
        # Calculates a vector containing the detections along the bus coordinates
		for line in lines:
			lineMap = np.array(linesMatrix[lineList.index(line)])
			lineMap = lineMap[~np.any(np.isnan(lineMap), axis=1)]
			distanceMatrix = cp.asnumpy(HaversineLocal(cp.asarray(np.expand_dims(busMap,0)), cp.asarray(np.expand_dims(lineMap,0)))[0]) < CONFIGS['default_correction_method']['tolerance']
			distanceMatrix = np.squeeze(distanceMatrix)
			belongingArray = np.round(np.amax(distanceMatrix, axis=1))
			belongingArray = CorrectLine(belongingArray, CONFIGS['default_correction_method']['limit'])
			linesToCompare += [belongingArray]

        # Stacks all detections per line and creates a belonging matrix
		# For each bus, one coordinate selects line and the other a bus coordinate
		# The value is a boolean indicating if the line was reached in that coordinate
		belongingMatrix = np.stack(linesToCompare)
		# Sums over line dimension, if value is greater than 2, a conflict has ocurred
		# Conflict marks the index where this occurs
		conflicts1 = np.sum(belongingMatrix,axis=0)
		conflicts2 = np.nonzero(conflicts1 > 1)
		conflicts  = conflicts2[0] # removes tuple
		#conflicts = np.stack(np.nonzero(np.sum(belongingMatrix,axis=0) > 1))

		# If there was conflict
		if len(conflicts) != 0:

			# Matriz_prioridade consiste em uma matriz de M linhas onde M ?? o n??mero de linhas de ??nibus e N colunas onde N
			# ?? o n??mero de pontos onde ocorreu conflito
			# A matriz_prioridade ?? preenchida com o n??mero de pontos no grupo em que o conflito em um determinado ponto para
			# uma determinada linha foi detectado
			priorityMatrix = np.zeros((belongingMatrix.shape[0], conflicts.shape[0]))
			
			# Count the size of each continuos group for each line in the detectionMatrix
			# Each group is represented in the priorityMatrix by its group size
			for line in range(len(belongingMatrix)):
				#ocurrences, counters = torch.unique_consecutive(belongingMatrix[line], return_counts=True)
				ocurrences = belongingMatrix[line][np.insert(np.absolute(np.diff(belongingMatrix[line])) > 0.00001, 0, True)]
				counters = np.diff(np.concatenate(([True],np.absolute(np.diff(belongingMatrix[line])) > 0,[True])).nonzero()[0])
				auxiliarCounters = np.cumsum(counters, 0)
				for conflict in range(conflicts.shape[0]):
#					if len(conflicts[conflict]) == 0:
#						priorityMatrix[line][conflict] = 0
#						break
					contagemConflitos = np.where(auxiliarCounters > conflicts[conflict])[0]
					if len(contagemConflitos) == 0:
						priorityMatrix[line][conflict] = 0
						break
					grupo = contagemConflitos[0]

					# Is a matrix similar to belongingMatrix, but each continuos sets of 1 are replaced in the same indexes by this total group size
					priorityMatrix[line][conflict] = counters[grupo] if ocurrences[grupo] == 1 else 0

			
			# Calculates the 
			dominantLines = priorityMatrix.max(0)
			belongingMatrix = priorityMatrix.argmax(0)
	#		dominantLines = dominantLines if (dominantLines.shape != tuple() and dominantLines.shape != (1,)) else dominantLines
	#		# Por fim a matriz de pertencimento ?? atualizada eliminando os conflitos
	#		for line in range(len(belongingMatrix)):
	#			for conflict in range(conflicts.shape[0]):
	#				if line != dominantLines[conflict]:
	#					belongingMatrix[line][conflicts[conflict]] = 0
		else:
			belongingMatrix = priorityMatrix.argmax(0)

			# Para evitar flutua????es que possam surgir nesse processo os arrays de pertencimento de linha
			# passam novamente pela fun????o CorrectLine()
#			for line in range(len(belongingMatrix)):
#				belongingMatrix[line] = CorrectLine(belongingMatrix[line], CONFIGS['default_correction_method']['limit'])
#		correctedData += [[lines[i] for i in np.where(belongingMatrix == belongingMatrix.max(0))[0]]]
		correctedData += [[lines[i] for i in belongingMatrix]]
#
	# Cria????o de dataframe pandas. matriz de m linhas representando os ??nibus e n colunas representando os pontos de ??nibus.
	correctedDataframe = pd.DataFrame(correctedData, index=buses_detected)

	return correctedDataframe.T


def CorrectLine(LineDetected, limite):
	"""
	The function receives a 'belonging array'  for one line and the minimum group limit and eliminate fluctuations.
	Arguments:
		LineDetected: 'belonging array' (torch tensor).
		limit: The minimun value to consider a set of points as a valid group
	Return: new array without fluctuations
	"""
	
	# Resumimos a quantidade de informa????o utilizando o m??todo unique_consecutive, criando o tensor ocorrencias com
	# as sequ??ncias de grupos e o tensor contadores com o n??mero de ocorr??ncias para o i-??simo grupo
	#ocorrencias, contadores = torch.unique_consecutive(LineDetected, return_counts=True)
	ocorrencias = cp.asnumpy(LineDetected)[np.insert(np.absolute(np.diff(cp.asnumpy(LineDetected))) > 0.00001, 0, True)]
	contadores = np.diff(np.concatenate(([True],np.absolute(np.diff(cp.asnumpy(LineDetected))) > 0,[True])).nonzero()[0])

	# Array de contador auxiliar para saber onde alterar no array original
	contadores_auxiliar = contadores.cumsum()
	
	# Criar m??scara para substitui????o no array de LineDetected
	mascara = np.zeros((LineDetected.shape[0]), dtype="bool")

	substituidos = np.where(contadores < int(limite))[0]
	if len(substituidos) != 0:
		for grupo in substituidos:
			if grupo == 0:
				inicio = contadores_auxiliar[0]
			else:
				inicio = contadores_auxiliar[grupo - 1]
			fim = inicio + contadores[grupo]
			mascara[inicio:fim] = True

	# Eliminar flutua????es removendo grupos pequenos
	linha_Corrigida = np.where(mascara, np.logical_not(cp.asnumpy(LineDetected)).astype("int64"), cp.asnumpy(LineDetected).astype("int64"))
	
	return linha_Corrigida


if __name__ == "__main__":
	from time import time

	CONFIGS = configparser.ConfigParser()
	CONFIGS['default_correction_method'] = {'limit': '3', 'distanceTolerance': '300'}
	

	# Teste sanidade
#	 """
	matrizOnibus = pd.DataFrame(
		data={'M': np.array([1,1,0]), 'N': np.array([1,0,1]), 'O': np.array([0,1,0])},
		index=pd.MultiIndex.from_tuples([('B', '0'), ('A', '0'), ('A', '1')])
		)
	
	oni = np.array([[[1,0], [2,1], [3,3], [4,4], [2,4], [0,4], [float('NaN'),float('NaN')], [float('NaN'),float('NaN')]], [[1,1], [2,2], [3,3], [4,4], [5,5], [6,6], [7,7], [8,8]], [[4,4], [4,3], [4,2], [4,1], [3,1], [2,1], [float('NaN'),float('NaN')], [float('NaN'),float('NaN')]]], dtype=float)
	li = np.array([[[0,0], [1,1], [2,2], [3,3], [4,4]], [[2,4], [1,4], [1,2], [1,1], [0,0]], [[4,5], [5,6], [6,7], [7,8], [8,8]]], dtype=float)
	busList = [(i, 0) for i in "M,N,O".split(",")]
	lineList = [('A','0'), ('B', '0'), ('A', '1')]

	print("antes:\n", matrizOnibus)
	print("oni:\n",oni)
	print("li:\n",li)
	resultado = CorrectData(matrizOnibus, oni, li, busList, lineList, CONFIGS)
	print("depois:\n", resultado.to_string())
#	 """

	# Teste desempenho
	"""
	QO = 5000
	PPO = 3000
	QL = 2
	PPL = 3000
	oni = np.random.rand(QO,PPO,2) * 100
	li = np.random.rand(QL,PPL,2) * 100
	busList = ['O'+str(i) for i in range(QO)]
	lineList = [('L'+str(i),0) for i in range(QL)]
	
	matrizOnibus = pd.DataFrame((np.random.rand(QL,QO) > 0.5), index=pd.MultiIndex.from_tuples(lineList), columns=busList)

	print("Starting")
	start = time()
	resultado = CorrectData(matrizOnibus, oni, li, busList, lineList, CONFIGS)
	end = time()

	print(f"time:{end-start}")
	"""
