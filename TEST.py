from DispatchFunctions import *
from DispatchManagement import *
from WriteToExcel import *
from calendar import monthrange

endaDate = '2021-12-31'#np.datetime64(datetime.datetime.today(), 'D') + np.timedelta64(2, 'D')
startDate = '2021-01-01'

ParameterDir = r'C:/users/mzhuravlev/OneDrive - CEPM/PROJECTS/Python/Backcast/'

BackcastParameters = json.loads(
        open(
            ParameterDir + 'TestBackcastAssetParameters.json'
        ).read()
    )

print("Running backcast")
backcastDict = runDispatch(BackcastParameters, startDate, endaDate)

# writes output to file
FolderDir = r'C:/Users/mzhuravlev/OneDrive - CEPM/PROJECTS/Python/Backcast/'
TemplateFile = 'TEST.xlsx'

for iAsset in backcastDict:
    
    print("Writing to file: " +  iAsset)

    print("Writing hourly data...")

    WriteToFile(backcastDict[iAsset].hourlyData,
        FolderDir + TemplateFile, 
        iAsset + ' Hourly',
        1, 
        1)

    print("Writing summary data...")

    WriteToFile(backcastDict[iAsset].summary,
        FolderDir + TemplateFile, 
        iAsset + ' Summary',
        1, 
        1)

print("Backcast complete.")
