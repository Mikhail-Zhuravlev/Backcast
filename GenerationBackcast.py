
from Dispatch import *
from WriteToExcel import *
import time

#print(PRISMQuery.plantParameters('2021-01-01', '2022-01-01', 'ELGIN'))

startTime = time.perf_counter()

ElginHRCOParameters = {
    'startDate': '01/01/2022',
    'endDate': '7/13/2022',
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

ElginHRCO.hourlyData['isRunning'] = 0

ElginHRCO.hourlyData['PREMIUM'] = 0

for idx, dispatch in np.ndenumerate(dispatchTrackerV3):

    if dispatch.isOn == 1:
    
        for iRunHour in range(dispatch.startIndex, dispatch.endIndex + 1):
        
            ElginHRCO.hourlyData['runHour'][iRunHour] = iRunHour - dispatch.startIndex + 1
            ElginHRCO.hourlyData['isRunning'][iRunHour] = 1

#CLean this up in a seperate function
ElginHRCO.hourlyData.loc[ElginHRCO.hourlyData['runHour'] != 1, 'START_COST'] = 0

ElginHRCO.hourlyData.loc[ElginHRCO.hourlyData['runHour'] == 0, 'MARGIN'] = 0

ElginHRCO.hourlyData.loc[ElginHRCO.hourlyData['runHour'] == 0, 'VOM_COST'] = 0

ElginHRCO.hourlyData.loc[ElginHRCO.hourlyData['runHour'] == 0, 'FUEL_COST'] = 0

ElginHRCO.hourlyData.loc[ElginHRCO.hourlyData['runHour'] == 0, 'POWER_REVENUE'] = 0

ElginHRCO.hourlyData.loc[(ElginHRCO.hourlyData['DAY'] == 1) & (ElginHRCO.hourlyData['HE'] == 1) , 'PREMIUM'] = 303800

ElginHRCO.hourlyData['MARGIN'] = ElginHRCO.hourlyData['MARGIN'] - ElginHRCO.hourlyData['START_COST']

ElginHRCO.hourlyData = ElginHRCO.hourlyData.loc[ElginHRCO.hourlyData['DATE']>= ElginHRCO.startDate].copy()

ElginHRCO.summary = ElginHRCO.hourlyData[['DATE', 'FUEL_COST', 'START_COST', 'VOM_COST', 'POWER_REVENUE', 'MARGIN', 'isRunning', 'PREMIUM']].groupby(by='DATE', ).sum()

ElginHRCO.summary['NET_MARGIN'] = ElginHRCO.summary['PREMIUM'] - ElginHRCO.summary['MARGIN']

#ElginHRCO.summary = ElginHRCO.summary.loc[ElginHRCO.summary['DATE'] >= ElginHRCO.startDate].copy()

# writes output to file
FolderDir = r'C:/Users/mzhuravlev/OneDrive - CEPM/PROJECTS/Python/Backcast/'
TemplateFile = 'TEST.xlsx'

WriteToFile(ElginHRCO.hourlyData,
            FolderDir + TemplateFile, 
            'Target',
            1, 
            1)

WriteToFile(ElginHRCO.summary,
FolderDir + TemplateFile, 
'Summary',
1, 
1)

#os.chdir(FolderDir)
#os.system('start excel.exe "' + FolderDir + TemplateFile + '"')

#for idx, dispatch in np.ndenumerate(testDispatch):
#    print(idx[0], dispatch)

def writeToPRISM(df, database, server = 'DC01DAPP01'):

    conn = pyodbc.connect(
        'Driver={SQL Server Native Client 11.0};'
        'Server=' + server +';'
        'Database=' + database + ';'
        'Uid=PrismExec;pwd=Pri$m2018%;'
        )
    
    cursor = conn.cursor()

    inputString = """exec dbo.InsertElginHRCOSettlementDetails @dt=?,@fuel=?,@strt=?,@vom=?,@rev=?,@mrgn=?,@hrs=?,@prm=?,@net=?;"""
    
    for i in df.itertuples():
        
        values = i[0:]
        
        cursor.execute(inputString, values)
        
        conn.commit()

    cursor.close()

writeToPRISM(ElginHRCO.summary, 'TPT', server = 'DC01DAPP01')

print("Backcast complete.")
