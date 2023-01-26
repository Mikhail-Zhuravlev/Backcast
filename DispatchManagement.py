from datetime import *
from DispatchFunctions import *
from WriteToExcel import *
import json

#print(PRISMQuery.plantParameters('2021-01-01', '2022-01-01', 'ELGIN'))

#startTime = time.perf_counter()

def runDispatch(BackcastParameters, startDate, endaDate):
    
    DispatchDict= {}

    for iPlant in BackcastParameters:
        
        print("Running Backcast for "+ iPlant)

        BackcastParameters[iPlant]["startDate"] = startDate

        BackcastParameters[iPlant]["endDate"] = endaDate

        DispatchDict[iPlant] = GenerationAsset(BackcastParameters[iPlant])

        DispatchDict[iPlant].populateInputs()

        DispatchDict[iPlant].alignHourlyParameters()

        DispatchDict[iPlant].calculateHourlyMargins()

        unmergedDispatches = initialDispatch(DispatchDict[iPlant].hourlyData)

        bruteForceDispatched = bruteForceRunOptimization(unmergedDispatches)

        DispatchDict[iPlant].cleanDispatch = cleanOOTMRuns(bruteForceDispatched)

        DispatchDict[iPlant].hourlyData['runHour'] = 0

        DispatchDict[iPlant].hourlyData['isRunning'] = 0

        DispatchDict[iPlant].hourlyData['PREMIUM'] = 0

        DispatchDict[iPlant].hourlyData.loc[
            (DispatchDict[iPlant].hourlyData['DAY'] == 1) &
             (DispatchDict[iPlant].hourlyData['HE'] == 1) , 'PREMIUM'
             ] = BackcastParameters[iPlant]["monthly_premium"] 

        for idx, dispatch in np.ndenumerate(DispatchDict[iPlant].cleanDispatch):

            if dispatch.isOn == 1:
            
                for iRunHour in range(dispatch.startIndex, dispatch.endIndex + 1):
                
                    DispatchDict[iPlant].hourlyData['runHour'][iRunHour] = iRunHour - dispatch.startIndex + 1
        
                    DispatchDict[iPlant].hourlyData['isRunning'][iRunHour] = 1

        DispatchDict[iPlant].summary = summarizeHourlyMargin(DispatchDict[iPlant].hourlyData)

    return DispatchDict


def summarizeHourlyMargin (hourlyDispatchData):
    
    hourlyDispatchData.loc[hourlyDispatchData['runHour'] != 1, 'START_COST'] = 0

    hourlyDispatchData.loc[hourlyDispatchData['runHour'] == 0, 'MARGIN'] = 0

    hourlyDispatchData.loc[hourlyDispatchData['runHour'] == 0, 'VOM_COST'] = 0

    hourlyDispatchData.loc[hourlyDispatchData['runHour'] == 0, 'FUEL_COST'] = 0

    hourlyDispatchData.loc[hourlyDispatchData['runHour'] == 0, 'POWER_REVENUE'] = 0

    hourlyDispatchData['MARGIN'] = hourlyDispatchData['MARGIN'] - hourlyDispatchData['START_COST']

    #hourlyDispatchData = hourlyDispatchData.loc[hourlyDispatchData['DATE']>= ElginHRCO.startDate].copy()

    summary = hourlyDispatchData[['DATE', 'FUEL_COST', 'START_COST', 'VOM_COST', 'POWER_REVENUE', 'MARGIN', 'isRunning', 'PREMIUM']].groupby(by='DATE', ).sum()

    summary['NET_MARGIN'] = summary['PREMIUM'] - summary['MARGIN']

    return summary