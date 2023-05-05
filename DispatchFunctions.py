
#from click import pass_context
from PRISMDataClass import *
from HourlyDataSetup import *

class GenerationAsset(PRISMDataDownload):
    
    createHourlyTable = createHourlyTable

    alignHourlyParameters = alignHourlyParameters

    calculateHourlyMargins = calculateHourlyMargins


def dispatchPeriodAggregator (dataTable):
#Aggregates hourly dispatch into periods of in-the-money and out-of-the-money

    hourMargin = 0
    runHour = 0
    dispatchIndex = 0
    dispatchTracker = []
    
    for index, currentHour in dataTable.iterrows():
        
        priorHourMargin = hourMargin
        
        hourMargin = currentHour['MARGIN']
        
        if hourMargin == 0: 
            hourMargin = -.01 

        #For testing
        print('index:{0} priorHourMargin:{1} hourMargin:{2} dispatchIndex:{3}'.format(
           ("{:.0f}".format(index)),
           ("{:.0f}".format(priorHourMargin)),
           "{:.0f}".format(hourMargin),
           "{:.0f}".format(dispatchIndex-1)
        ))
        
        if (priorHourMargin / hourMargin) <= 0:
            
            inTheMoney = 0
            
            if hourMargin > 0:
                inTheMoney = 1
            
            dispatchTracker.append(dispatchPeriod(
                incInTheMoney = inTheMoney,
                startindex = index,
                endIndex = 0,
                incMargin = 0,
                startCost = dataTable['START_COST'][index]
            ))
            
            if dispatchIndex > 0:
                
                priorStart = dispatchTracker[dispatchIndex-1].startIndex
                
                dispatchMargin = dataTable['MARGIN'][priorStart:index].sum()
                
                dispatchTracker[dispatchIndex-1].setEnd(index-1)
                
                dispatchTracker[dispatchIndex-1].setMargin(dispatchMargin)
            
            dispatchIndex = dispatchIndex + 1
            
    return dispatchTracker
    

def bruteForceRunOptimization(dispatchTracker):

    mergeDepth = 30
   
    tempDispatchTracker = dispatchTracker.copy()
    
    listLength = len(tempDispatchTracker)
    
    toDrop = []
    
    #updatedDispatch = []
    
    dispatchIndex = 0 

    #Check each combination of dispatches
    while dispatchIndex < (listLength - 2):
        
        #cannot merge past the end of the list
        if (listLength - dispatchIndex - 1) < (mergeDepth * 2):
            
            mergeDepth = int((listLength - dispatchIndex -1) / 2)

            if mergeDepth < 0:
                
                mergeDepth = 0
             
        #is the plant economical in this period on an hourly basis
        incInTheMoney = tempDispatchTracker[dispatchIndex].incInTheMoney
        
        #is it worth considering merging over the next OOTM period
        isEconomical = (
            tempDispatchTracker[dispatchIndex ].incMargin
            + tempDispatchTracker[dispatchIndex + 1].incMargin
        )
        
        if ((incInTheMoney == 1) & (isEconomical > 0)):
        
            bestMargin = tempDispatchTracker[dispatchIndex].incMargin
            bestStart = dispatchIndex
            bestEnd = dispatchIndex
            
            tempMargin = tempDispatchTracker[dispatchIndex].incMargin
            #startFwdMerge = dispatchIndex
            
            print(('Current Margin: {0}, Start: {1}, End: {2}. Best Margin: {3}, Start: {4}, End: {5}.').format(
            '{:,.2f}'.format(tempMargin),
            dispatchIndex,
            dispatchIndex,
            '{:,.2f}'.format(bestMargin),
            bestStart,
            bestEnd))
            
            #attempt to merge into later dispatches to maximize incremental margin
            for depth in range (0,  mergeDepth):
                
                #never merge over an OOtM period whose loss > start cost
                #if the next ITM + OOTM preiod bring margins below 0,
                #the run is better off starting after or ending before 
                nextITMIndex = dispatchIndex + 2 * (depth + 1)
                nextOoTMIndex = dispatchIndex + 2 * (depth + 1) - 1 
                nextStart = -1 * tempDispatchTracker[nextITMIndex].startCost
                ootmLoss = 1 * tempDispatchTracker[nextOoTMIndex].incMargin
                #print(('nextStart: {0}, ootmLoss: {1}').format(
                #'{:,.2f}'.format(nextStart),
                #'{:,.2f}'.format(ootmLoss)
                # ))
                            
                if  (ootmLoss + tempMargin < 0) or (nextStart > ootmLoss):
                    
                    break
                
                #Increment the temp margin by the next periods (OOTM+ITM)
                tempMargin += (
                        tempDispatchTracker[nextOoTMIndex].incMargin
                        + tempDispatchTracker[nextITMIndex].incMargin
                    )
                
                #if losses accumulate to more than a new start, stop iterating
                if tempMargin <= (bestMargin + nextStart):
                    
                    break
                                
                if tempMargin >= bestMargin:
                        
                        bestMargin = tempMargin
                        
                        #bestStart = dispatchIndex
                        
                        bestEnd = dispatchIndex + 2 * (depth + 1)

                print(('Current Margin: {0}, Start: {1}, End: {2}. Best Margin: {3}, Start: {4}, End: {5}.').format(
                '{:,.2f}'.format(tempMargin),
                dispatchIndex,
                dispatchIndex + 2 * (depth + 1),
                '{:,.2f}'.format(bestMargin),
                bestStart,
                bestEnd))
                
            #merge best margins forward
            tempDispatchTracker = mergeDispatchTrackerRuns(tempDispatchTracker, dispatchIndex, bestEnd)
            
            listLength = len(tempDispatchTracker)
            
            #print(("Merged: {0}-{1} {2}").format(
            #    dispatchIndex,
            #    bestEnd,
            #    str(tempDispatchTracker[dispatchIndex])
            #))
            
            # updatedDispatch.append(
            #     dispatchPeriod (
            #         incInTheMoney = 1,
            #         startindex = tempDispatchTracker[dispatchIndex].startIndex,
            #         endIndex = tempDispatchTracker[bestEnd].endIndex,
            #         incMargin = bestMargin,
            #         startCost = tempDispatchTracker[dispatchIndex].startCost
            #     )
            # )     
        
            #drop merged dispatches
            # for dropIndex in range (dispatchIndex, bestEnd):
            #     toDrop.append(dropIndex)
                            
            #iterate index
            # if dispatchIndex == bestEnd:
            
            #     dispatchIndex = bestEnd + 1
            
            # else:
            
            #     dispatchIndex = bestEnd + 1

        else:
            
            #print(("Not Merged: {0} {1}").format(
            #    dispatchIndex,
            #    str(tempDispatchTracker[dispatchIndex])
            #))
            
            #updatedDispatch.append(tempDispatchTracker[dispatchIndex])
            
            dispatchIndex += 1
        
    return tempDispatchTracker


def mergeDispatchTrackerRuns(tempDispatchTracker, earlierindex, latterIndex):
    #merge best margins forward
    
    targetPeriod = tempDispatchTracker[earlierindex]

    targetPeriod.setEnd(tempDispatchTracker[latterIndex].endIndex)

    for i in (latterIndex, earlierindex, -1):

        targetPeriod.addMargin(tempDispatchTracker[i].incMargin)

        del tempDispatchTracker[i]

    return tempDispatchTracker


def flagValidRuns(dispatchTracker, minMargin = 0, minRunTime = 0):
#Populates .isDispatching flag based on min criteria 1 = yes, 0 = no

    for dispatchPeriod in dispatchTracker:
        
        isValid = 1

        if dispatchPeriod.runtime() < minRunTime:
            #does dispatch meet min run time
            isValid = isValid * 0
        
        if dispatchPeriod.netMargin() < minMargin:
            #is dispatch Economical 
            isValid = isValid * 0
        
        dispatchPeriod.isDispatching = isValid



def fixMinRunTime(hourlyData, dispatchTracker, targetPeriodIndex, minRunTime):

    lowestCostHours = findLowestCostHours(hourlyData, dispatchTracker, targetPeriodIndex, minRunTime)

    mergeForward = mergeDispatchPeriods()

    mergeBackward = 1

    bestScenario = max(lowestCostHours.netMargin, mergeForward.netMargin, mergeBackward.netMargin)

    if bestScenario == lowestCostHours.netMargin:
        x=1
    
    elif bestScenario == lowestCostHours.netMargin:
        x=1
    
    elif bestScenario == lowestCostHours.netMargin:
        x=1

    else:
        x = "error"


def findLowestCostHours(hourlyData, dispatchTracker, targetPeriodIndex, minRunTime):

    updatedDispatchTracker = dispatchTracker.copy()

    targetPeriod = updatedDispatchTracker[targetPeriodIndex]
    
    currentRunLength = targetPeriod.runtime()

    while currentRunLength < minRunTime:
        
        previousHourMargin = hourlyData[targetPeriod.startIndex-1]['MARGIN']
        
        nextHourMargin = hourlyData[targetPeriod.endIndex+1]['MARGIN']
        
        if previousHourMargin > nextHourMargin:

            targetPeriod.startIndex = targetPeriod.startIndex - 1

            updatedDispatchTracker[targetPeriodIndex - 1].endIndex = targetPeriod.startIndex - 1
        
        else:

            targetPeriod.endIndex = targetPeriod.endIndex - 1

            updatedDispatchTracker[targetPeriodIndex + 1].startIndex = targetPeriod.endIndex + 1
    
        currentRunLength = targetPeriod.runtime()

    return updatedDispatchTracker


def mergeDispatchPeriods(dispatchTracker, targetPeriodIndex, minRunTime, direction=1):

    updatedDispatchTracker = dispatchTracker.copy()

    targetPeriod = updatedDispatchTracker[targetPeriodIndex]
    
    currentRunLength = targetPeriod.runtime()

    while currentRunLength < minRunTime:
    
        ootmPeriod = updatedDispatchTracker[targetPeriodIndex + 1 * direction]

        itmPeriod = updatedDispatchTracker[targetPeriodIndex + 2 * direction]
    
        if itmPeriod.isDispatching:
            #if the ITM period is already valid, the margins impact is only
            #the intermediate OoTM period margins and start avoidance
            
            marginModifier = itmPeriod.startCost + ootmPeriod.incMargin

        else:
            #if the ITM period is NOT already invalid, the margins impact is 
            #the margins from both intermediate OoTM and ITM periods

            marginModifier = itmPeriod.incMargin + ootmPeriod.incMargin

        #merge the target period into the other period



    return updatedDispatchTracker, marginModifier


def cleanOOTMRuns(dispatchTracker):
#Drops runs that are incrementally in the money but not economical

    tempDispatchTracker = dispatchTracker.copy()
    
    listLength = len(tempDispatchTracker)
    
    toDrop = []
    
    dispatchIndex = 1
    
    while dispatchIndex < (listLength - 1):
        
        if (tempDispatchTracker[dispatchIndex].incInTheMoney == 1):
            
            netMargin = tempDispatchTracker[dispatchIndex].incMargin - tempDispatchTracker[dispatchIndex].startCost
            
            if (netMargin <= 0):
                
                #merges the current ITM run with the proceeding and preceeding OoTM runs
                tempDispatchTracker[dispatchIndex + 1].setMargin(
                    tempDispatchTracker[dispatchIndex + 1].incMargin
                    + tempDispatchTracker[dispatchIndex].incMargin
                    + tempDispatchTracker[dispatchIndex - 1].incMargin
                )

                tempDispatchTracker[dispatchIndex + 1].setStartCost(tempDispatchTracker[dispatchIndex - 1].startCost)    
                    
                tempDispatchTracker[dispatchIndex + 1].setStart(tempDispatchTracker[dispatchIndex - 1].startIndex)

                toDrop.append(dispatchIndex)
                toDrop.append(dispatchIndex - 1)
        
        dispatchIndex += 1
        
    for index in sorted(toDrop, reverse=True):
        del tempDispatchTracker[index]
                              
    return tempDispatchTracker