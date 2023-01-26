import pandas as pd
from PRISMQueries import *

###################################
# Class that pulls data from PRISM
########################################

class PRISMDataDownload:

    __version__ = '0.0.1'

    pullFromPRISM = pullFromPRISM
    
    importPlantParameters = importPlantParameters

    importIsoDaLmpPrism = importIsoDaLmpPrism

    importFuelPricePrism = importFuelPricePrism

    importFuelTransportPrism = importFuelTransportPrism

    importEmissionsPricesPrism = importEmissionsPricesPrism

    populateInputs = populateInputs
    

    def __init__(self, plantParameters, server = 'DC01DAPP01'):

        self.plantCode = plantParameters['plantCode']

        self.isoName = plantParameters['isoName']

        self.powerNode = plantParameters['powerNode']

        self.fuelPoint = plantParameters['fuelPoint']

        self.gasDayStartHour = plantParameters['gasDayStartHour']

        self.startDate =  pd.to_datetime(plantParameters['startDate'])
        
        self.sQLStartDate = pd.to_datetime(self.startDate).isoformat()
        
        self.endDate =  pd.to_datetime(plantParameters['endDate'])
        
        self.sQLEndDate = pd.to_datetime(self.endDate).isoformat()


    def __str__(self):

        return ('start: {0}; end: {1}; plant: {2}'.format(
                (self.sQLStartDate),
                (self.sQLEndDate),
                (self.plantCode),
            ))
    


###################################
# Class that appends data to PRISM
########################################

class PRISMDataUpload:

    __version__ = '0.0.1'

    importPlantParameters = importPlantParameters

    importIsoDaLmpPrism = importIsoDaLmpPrism

    importFuelPricePrism = importFuelPricePrism

    importFuelTransportPrism = importFuelTransportPrism

    importEmissionsPricesPrism = importEmissionsPricesPrism

    def __init__(self, dbName, tableName, server = 'DC01DAPP01', usrname = 'XXX', pw='xxx', ):
        
        self.plantCode = plantParameters['plantCode']

        self.isoName = plantParameters['isoName']

        self.powerNode = plantParameters['powerNode']

        self.fuelPoint = plantParameters['fuelPoint']

        self.startDate =  pd.to_datetime(plantParameters['startDate'])
        
        self.sQLStartDate = pd.to_datetime(self.startDate).isoformat()
        
        self.endDate =  pd.to_datetime(plantParameters['endDate'])
        
        self.sQLEndDate = pd.to_datetime(self.endDate).isoformat()