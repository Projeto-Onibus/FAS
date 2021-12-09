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

