This code is the implementation of the algorithm proposed by Tang et al. (2019) for road map generation and updating using trajectory data.


【Usage】
1) unzip the package into a root folder (e.g. 'csu'), and add the folder into MATLAB/Octave search path.
2) convert your trajectroy data in the format same as the trips in 'data' folder.
   -- trip_0.txt
      X Y Time
3) create a MATLAB or Octave script file to run the algorithm, such as 'athens.m', 'berlin.m', 'chicago.m', 'joensuu.m' in the root folder.

4) for finer results, or different datasets, you can tune the parameters listed in Line 11-12 and Line 63-68, and other parameters. All these parameters would be set according to the average GPS position errors of trajectory data and the average road width in the study area.

5) The final result is saved in shapefile format, named as 'finalmap', which can be found in the 'results' folder.

【Demo】
running the command in the MATLAB or Octave command after you config the paths.
>> athens;



【Contact】
Jianbo Tang
Central South University, Changsha, China
e-mail: jianbo.tang@csu.edu.cn

please cites the article in follow if you find this code can help you, thanks.
Jianbo Tang, Min Deng, Jincai Huang, Huimin Liu, Xueying Chen. An Automatic Method for Detection and Update of Additive Changes in Road Network with GPS Trajectory Data [J]. ISPRS International Journal of Geo-Information, 2019, 8: 411. DOI: 10.3390/ijgi8070397.


【Statement】
This program cannot be used for any commercial activities and is limited to academic research. All copyrights are reserved by Central South University.

