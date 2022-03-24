# Data patterns for BusData and Line Data

The data structures used in this package are defined with the help of Pandas, GeoPandas, shapely and Tracktable packages. All buses trajectories
are of the special type `tracktable.domain.terrestrial.Trajectory` and all lines trajectories are `shapely.geometry.LineString`. The pandas DataFrame 
keeps track of identifiable information such as ids and datetime that are useful in indexing. 

The DataFrame containing all buses trajectories is commonly reffered as `BusData` and its columns are:

| name | type | description | Obs | 
| --- | --- | --- | --- |
| date | datetime.date | data de coleta da trajetória | | 
| bus\_id | string | identificador do ônibus | | 
| traj\_id | int | identificador de trajetoria | | 
| trajectory | tracktable.domain.terrestrial.Trajectory | a trajetória do ônibus ao longo do dia | |

For lines trajectories, there is the `LineData` DataFrame with columns as:

| nome | tipo | descrição | observações |
| --- | --- | --- |--- |
| line | string | Identificador da linha | | 
| direction | bool | Sentido da linha (Fwd/Rev)| |
| variant | string | Variação das linhas (para identifica-las unicamente) | A ser adicionado |
| Description | string | String que descreve a trajetória da linha | |
| Operator | string | String identificando o consórcio/empresa responsável | |
| Trajectory | shapely.LineString | Trajetória da linha | geometria do DataFrame |

Given numerous ocurrences of lines containing the same line number and direction, whenever a line must be fully identified in a string the following pattern will be adopted:

\<line\_id\>\_\<direction\>\_\<hash\>

where: 

* line\_id: String containing the standard line identification
* Direction: unsigned integer indicating line directions 0,1,2...
* hash: Is the standard hash function on python3.8 applied to the lines description, this hash get's limited by 4 bits and added 65, the result is interpreted as a char. Same as picking a letter from A to P.

Using this standard, the string representing the line can be calculated in the following example:

```
lineString = f"{LineData['line']}_{LineData['direction']}_{char(65 + hash(LineData['description']) & 15)}"
```

Examples would be:
"457\_0\_F"
"913\_1\_D"
