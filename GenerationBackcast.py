
from Dispatch import *

#print(PRISMQuery.plantParameters('2021-01-01', '2022-01-01', 'ELGIN'))

ElginHRCOParameters = {
    'startDate': '01/01/2022',
    'endDate': '3/31/2022',
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

testDispatch = initialDispatch(ElginHRCO.hourlyData)

for idx, dispatch in np.ndenumerate(testDispatch):
    print(idx[0], dispatch)

print("Backcast complete.")
