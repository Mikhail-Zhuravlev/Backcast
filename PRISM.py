import pyodbc
import pandas as pd
from PRISMQueries import *

###################################
# Class that pulls data from PRISM
########################################



class PRISMData:

    __version__ = '0.0.1'

    importPlantParameters = importPlantParameters

    importIsoDaLmpPrism = importIsoDaLmpPrism

    importFuelPricePrism = importFuelPricePrism

    importFuelTransportPrism = importFuelTransportPrism

    importEmissionsPricesPrism = importEmissionsPricesPrism

    def __init__(self, plantParameters, server = 'DC01DAPP01'):

        self.plantCode = plantParameters['plantCode']

        self.isoName = plantParameters['isoName']

        self.powerNode = plantParameters['powerNode']

        self.fuelPoint = plantParameters['fuelPoint']

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
    
    
    def pullFromPRISM(self, queryStr, database, server = 'DC01DAPP01'):
    
        self.conn = pyodbc.connect(
            'Driver={SQL Server Native Client 11.0};'
            'Server=' + server +';'
            'Database=' + database + ';'
            'Uid=Prismreader;pwd=Pri$m2016%;'
            )
        
        with self.conn:
            
            return pd.read_sql_query(queryStr, self.conn)

    


        