from datetime import *
from DispatchFunctions import *
from WriteToExcel import *
from calendar import monthrange
import json
import time

#print(PRISMQuery.plantParameters('2021-01-01', '2022-01-01', 'ELGIN'))

#startTime = time.perf_counter()
endaDate = np.datetime64(datetime.datetime.today(), 'D') + np.timedelta64(2, 'D')

# PortfolioHierarchy = json.loads(
#         open(
#             ParameterDir + 'PortfolioHierarchy.json'
#         ).read()
#     )

ElginHRCOParameters = {
    'startDate': '2021-03-31',
    'endDate': '2021-05-01',
    'CO2Source': 'PRISM',
    'fuelSource': 'PRISM',
    'fuelPoint': 'AGT CityGates Midpoint',
    'gasDayStartHour': 10,
    'powerSource': 'PRISM',
    'powerNode': 'H.INTERNAL_HUB',
    'isoName': 'ISONE',
    'plantCode': 'TVTONHRCO',
    'minRun': 0}



ElginHRCO = GenerationAsset(ElginHRCOParameters)

ElginHRCO.populateInputs()

ElginHRCO.alignHourlyParameters()

ElginHRCO.calculateHourlyMargins()

unmergedDispatches = dispatchPeriodAggregator(ElginHRCO.hourlyData)

bruteForceDispatched = bruteForceRunOptimization(unmergedDispatches)

dispatchTrackerV3 = cleanOOTMRuns(bruteForceDispatched)

ElginHRCO.hourlyData['runHour'] = 0

ElginHRCO.hourlyData['isDispatching'] = 0

ElginHRCO.hourlyData['PREMIUM'] = 0

for idx, dispatch in np.ndenumerate(dispatchTrackerV3):

    if dispatch.incInTheMoney == 1:
    
        for iRunHour in range(dispatch.startIndex, dispatch.endIndex + 1):
        
            ElginHRCO.hourlyData['runHour'][iRunHour] = iRunHour - dispatch.startIndex + 1
            ElginHRCO.hourlyData['isDispatching'][iRunHour] = 1

#CLean this up in a seperate function
ElginHRCO.hourlyData.loc[ElginHRCO.hourlyData['runHour'] != 1, 'START_COST'] = 0

#ElginHRCO.hourlyData.loc[ElginHRCO.hourlyData['runHour'] == 0, 'MARGIN'] = 0

#ElginHRCO.hourlyData.loc[ElginHRCO.hourlyData['runHour'] == 0, 'VOM_COST'] = 0

#ElginHRCO.hourlyData.loc[ElginHRCO.hourlyData['runHour'] == 0, 'FUEL_COST'] = 0

#ElginHRCO.hourlyData.loc[ElginHRCO.hourlyData['runHour'] == 0, 'POWER_REVENUE'] = 0

for iYear in pd.unique(ElginHRCO.hourlyData['YEAR']):

        for iMonth in range(1,13):

            ElginHRCO.hourlyData.loc[(ElginHRCO.hourlyData['YEAR'] == iYear) &
             (ElginHRCO.hourlyData['YEAR'] == iYear) & 
             (ElginHRCO.hourlyData['MONTH'] == iMonth) & 
             (ElginHRCO.hourlyData['HE'] == 1) , 'PREMIUM'] = 915810/monthrange(iYear, iMonth)[1]

ElginHRCO.hourlyData['MARGIN'] = ElginHRCO.hourlyData['MARGIN'] - ElginHRCO.hourlyData['START_COST']

ElginHRCO.hourlyData = ElginHRCO.hourlyData.loc[ElginHRCO.hourlyData['DATE']>= ElginHRCO.startDate].copy()

ElginHRCO.summary = ElginHRCO.hourlyData[['DATE', 'FUEL_COST', 'START_COST', 'VOM_COST', 'EMISSION_COST',  'POWER_REVENUE', 'MARGIN', 'isDispatching', 'PREMIUM']].groupby(by='DATE', ).sum()

ElginHRCO.summary['NET_MARGIN'] = ElginHRCO.summary['PREMIUM'] - ElginHRCO.summary['MARGIN']

#ElginHRCO.summary = ElginHRCO.summary.loc[ElginHRCO.summary['DATE'] >= ElginHRCO.startDate].copy()

# writes output to file
FolderDir = r'C:/Users/mzhuravlev/Desktop/' #r'C:/Users/mzhuravlev/OneDrive - CEPM/PROJECTS/Python/Backcast/'
TemplateFile = 'TEST.xlsx'

print("Writing to file...")

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

#writeToPRISM(ElginHRCO.summary, 'TPT', server = 'DC01DAPP01')

print("Backcast complete.")
