
from Dispatch import *
from WriteToExcel import *
import time

#print(PRISMQuery.plantParameters('2021-01-01', '2022-01-01', 'ELGIN'))

startTime = time.perf_counter()

ElginHRCOParameters = {
    'startDate': '01/01/2022',
    'endDate': '6/28/2022',
    'fuelPoint': 'Chicago CityGates Midpoint',
    'gasDayStartHour': 0,
    'powerNode': 'NI HUB',
    'isoName': 'PJM',
    'plantCode': 'ELGINHRCO',
    'minRun': 0}



ElginHRCO = GenerationAsset(ElginHRCOParameters)

ElginHRCO.populateInputs()

ElginHRCO.alignHourlyParameters()

ElginHRCO.calculateHourlyMargins()

unmergedDispatches = initialDispatch(ElginHRCO.hourlyData)

bruteForceDispatched = bruteForceRunOptimization(unmergedDispatches)

dispatchTrackerV3 = cleanOOTMRuns(bruteForceDispatched)

ElginHRCO.hourlyData['runHour'] = 0


for idx, dispatch in np.ndenumerate(dispatchTrackerV3):

    if dispatch.isOn == 1:
    
        for iRunHour in range(dispatch.startIndex, dispatch.endIndex + 1):
        
            ElginHRCO.hourlyData['runHour'][iRunHour] = iRunHour - dispatch.startIndex + 1


# writes output to file
FolderDir = r'C:/Users/mzhuravlev/OneDrive - CEPM/PROJECTS/Python/Backcast'
TemplateFile = 'TEST.xlsx'

#WriteToFile(ElginHRCO.hourlyData,
#            FolderDir + TemplateFile, 
#            'Dispatch Summary (Python)',
#            1, 
#            1)

os.chdir(FolderDir)
os.system('start excel.exe "' + FolderDir + TemplateFile + '"')

#for idx, dispatch in np.ndenumerate(testDispatch):
#    print(idx[0], dispatch)

print("Backcast complete.")
