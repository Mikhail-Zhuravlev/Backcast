import pandas as pd
import numpy as np
import pyodbc

def pullFromPRISM(self, queryStr, database, server = 'DC01DAPP01'):

    self.conn = pyodbc.connect(
        'Driver={SQL Server Native Client 11.0};'
        'Server=' + server +';'
        'Database=' + database + ';'
        'Uid=Prismreader;pwd=Pri$m2016%;'
        )
    
    with self.conn:
        
        return pd.read_sql_query(queryStr, self.conn)


def writeToPRISM(self, df, database, server = 'DC01DAPP01'):

    self.conn = pyodbc.connect(
        'Driver={SQL Server Native Client 11.0};'
        'Server=' + server +';'
        'Database=' + database + ';'
        'Uid=PrismExec;pwd=Pri$m2018%;'
        )
    
    cursor = self.conn.cursor()

    inputString = """exec dbo.InsertElginHRCOSettlementDetails @dt=?,@fuel=?,@strt=?,@vom=?,@rev=?,@mrgn=?,@hrs=?,@prm=?,@net=?;"""
    
    for i in df.itertuples():
        
        values = i[1:]
        
        cursor.execute(inputString, values)
        
        self.conn.commit()

    cursor.close()


def populateInputs(self):

    self.importPlantParameters()

    self.importIsoDaLmpPrism()

    self.importFuelPricePrism()

    self.importFuelTransportPrism()

    self.importEmissionsPricesPrism()


def importPlantParameters(self):
        
    queryStr = """SELECT T.*
                FROM [TPT].[dbo].[TPT_PLANT_DETAILS] T
                Inner Join (
                    SELECT MAX([EFFECTIVE_DATE]) as MaxDate, [PLANT_NAME], [YEAR], [MONTH_NUM]
                    FROM [TPT].[dbo].[TPT_PLANT_DETAILS]
                    WHERE EFFECTIVE_DATE <= '""" + self.sQLStartDate + """'
                    AND PLANT_NAME LIKE '""" + self.plantCode+ """'
                    GROUP BY [PLANT_NAME], [YEAR], [MONTH_NUM]
                    ) TM
                    on T.[PLANT_NAME] = TM.[PLANT_NAME]
                    and T.[YEAR] = TM.[YEAR]
                    and T.[MONTH_NUM] = TM.[MONTH_NUM]
                    and T.[EFFECTIVE_DATE] = TM.MaxDate
                    WHERE T.[YEAR] <= YEAR('""" + self.sQLEndDate + """')
                    and T.[YEAR] >= YEAR('""" + self.sQLStartDate + """')
                    ORDER BY T.[YEAR] ASC, T.MONTH_NUM ASC"""
        
    self.plantParameters = self.pullFromPRISM(queryStr, database = 'TPT')
        
    self.plantParameters['FUTURE_MONTH'] = pd.to_datetime({'year':self.plantParameters['YEAR'],
                            'month':self.plantParameters['MONTH_NUM'],
                            'day':1})

    self.plantParameters.loc[self.plantParameters['MODELED_IN_CXL'] == 'No', 'MAX_CAP'] = 0


def importIsoDaLmpPrism(self):

    if self.isoName == 'ISONE':
            
        queryStr = """SELECT *
            FROM  [ISONE].[dbo].[DAY_AHEAD_LMPS]
            WHERE NodeName LIKE '""" + self.powerNode + """%'
            AND PriceTime >= DATEADD(DAY, DATEDIFF(DAY, 0, '""" + self.sQLStartDate + """'), 0)
            AND PriceTime <= DATEADD(DAY, DATEDIFF(DAY, 0, '""" + self.sQLEndDate + """'), 0)
            ORDER BY PriceTime;"""
            
        LmpDatabase = 'ISONE'

        self.DaLmp = self.pullFromPRISM(queryStr, database = LmpDatabase)

        self.DaLmp['DateTime'] = pd.DatetimeIndex(self.DaLmp['PriceTime'])

        self.DaLmp.rename(columns={'Price' : self.powerNode }, inplace=True)

    elif self.isoName == 'PJM':
            
        queryStr = """SELECT *
            FROM  [eDataFeed].[dbo].[DAY_AHEAD_LMPS]
            WHERE NodeName LIKE '""" + self.powerNode + """%'
            AND PriceTime >= DATEADD(DAY, DATEDIFF(DAY, 0, '""" + self.sQLStartDate + """'), 0)
            AND PriceTime <= DATEADD(DAY, DATEDIFF(DAY, 0, '""" + self.sQLEndDate + """'), 0)
            ORDER BY PriceTime;"""

        LmpDatabase = 'eDataFeed'

        self.DaLmp = self.pullFromPRISM(queryStr, database = LmpDatabase)

        self.DaLmp['DateTime'] = pd.DatetimeIndex(self.DaLmp['PriceTime'])

        self.DaLmp.rename(columns={'Price' : self.powerNode }, inplace=True)

    elif self.isoName == 'ERCOT':
            
        queryStr = """SELECT *
            FROM  [ERCOT].[dbo].[DAM_LMPS]
            WHERE NodeName LIKE '""" + self.powerNode + """%'
            AND PriceDate >= DATEADD(DAY, DATEDIFF(DAY, 0, '""" + self.sQLStartDate + """'), 0)
            AND PriceDate <= DATEADD(DAY, DATEDIFF(DAY, 0, '""" + self.sQLEndDate + """'), 0)
            ORDER BY PriceDate, HE;"""

        LmpDatabase = 'ERCOT'

        self.DaLmp = self.pullFromPRISM(queryStr, database = LmpDatabase)
           
        self.DaLmp['DateTime'] = (
            pd.DatetimeIndex(self.DaLmp['PriceDate'])+pd.to_timedelta(self.DaLmp['HE'], unit='h')
        )
            
        #In other tables the relevant column is namded 'Price', in ERCOT is is named 'LMP'.
        #This streamlines downstream calculations
        self.DaLmp.rename(columns={'LMP' : self.powerNode }, inplace=True)
    
    self.DaLmp = self.DaLmp[['DateTime', self.powerNode]]

      
def importFuelPricePrism(self):

    queryStr = """SELECT Symbols.SYMBOL_DESC,Symbols.SYMBOL_NAME,  Prices.*
        FROM [COMMODITIES].[dbo].[PLATTS_VALUES] Prices
        LEFT JOIN [COMMODITIES].[dbo].[PLATTS_SYMBOLS] Symbols 
            ON Prices.SYMBOL_NAME = Symbols.SYMBOL_NAME
        WHERE Symbols.SYMBOL_DESC LIKE '""" + self.fuelPoint + """%'
        AND Prices.VALUE_DATE >= DATEADD(DAY, DATEDIFF(DAY, 0, '""" + self.sQLStartDate + """'), 0)
        AND Prices.VALUE_DATE <= DATEADD(DAY, DATEDIFF(DAY, 0, '""" + self.sQLEndDate + """'), 0)
        ORDER BY Prices.VALUE_DATE;"""

    fuelPriceTable = self.pullFromPRISM(queryStr, database = 'COMMODITIES')
    
    fuelPriceTable['Date'] = pd.DatetimeIndex(fuelPriceTable['VALUE_DATE']).date

    self.fuelPrice = fuelPriceTable[['Date', 'VALUE']].rename(
            columns={'Date' : 'DATE', 'VALUE' : self.fuelPoint})


def importFuelTransportPrism(self):

    queryStr =  """SELECT T.*
        FROM [TPT].[dbo].[UNIT_TRANSPORT_ADDERS] T
        Inner Join (
            SELECT MAX([EFFECTIVE_DATE]) as MaxDate, [UNIT], [FUTURE_MONTH], [MONTHYEAR]
            FROM [TPT].[dbo].[UNIT_TRANSPORT_ADDERS]
            WHERE EFFECTIVE_DATE <= '""" + self.sQLStartDate + """'
            AND UNIT LIKE '""" + self.plantCode + """'
            GROUP BY [UNIT], [FUTURE_MONTH], [MONTHYEAR]
        ) TM on T.[UNIT] = TM.[UNIT]
        and T.[FUTURE_MONTH] = TM.[FUTURE_MONTH]
        and T.[MONTHYEAR] = TM.[MONTHYEAR]
        and T.[EFFECTIVE_DATE] = TM.MaxDate
        WHERE T.FUTURE_MONTH >= DATEADD(MONTH, DATEDIFF(MONTH, 0, '""" + self.sQLStartDate + """'), 0)
        AND T.FUTURE_MONTH <= DATEADD(MONTH, DATEDIFF(MONTH, 0, '""" + self.sQLEndDate + """'), 0)
        ORDER BY T.[FUTURE_MONTH]"""

    fuelTransportTable = self.pullFromPRISM(queryStr, database = 'COMMODITIES')

    fuelTransportTable['FUTURE_MONTH'] = pd.to_datetime(fuelTransportTable['FUTURE_MONTH'])

    self.fuelTransport = fuelTransportTable[['FUTURE_MONTH', 'TRANSPORT_ADDER']]


def importEmissionsPricesPrism(self):

    queryStr =  """SELECT co2.EFFECTIVE_DATE
                , MONTH(co2.EFFECTIVE_DATE) as MONTH_NUM
                , co2.Price AS CO2Price
                , nox.Price AS NOXPrice
                , noxAnn.Price AS NOXAnnual
                , so2.Price AS SO2Price
            FROM [COMMODITIES].[dbo].[EMISSIONS_PRICES] as co2

        LEFT OUTER JOIN [COMMODITIES].[dbo].[EMISSIONS_PRICES] nox 
            ON nox.EFFECTIVE_DATE = co2.EFFECTIVE_DATE
            AND nox.COMMODITY = 'NOX'

        LEFT OUTER JOIN [COMMODITIES].[dbo].[EMISSIONS_PRICES] noxAnn 
            ON noxAnn.EFFECTIVE_DATE = co2.EFFECTIVE_DATE
            AND noxAnn.COMMODITY = 'NOXAnnual'

        LEFT OUTER JOIN [COMMODITIES].[dbo].[EMISSIONS_PRICES] so2 
            ON so2.EFFECTIVE_DATE = co2.EFFECTIVE_DATE
            AND so2.COMMODITY = 'SO2'

        WHERE co2.COMMODITY = 'CO2'
        AND co2.[EFFECTIVE_DATE] >= '""" + self.sQLStartDate + """'
        AND co2.[EFFECTIVE_DATE] <= '""" + self.sQLEndDate + """'
        ORDER BY co2.[EFFECTIVE_DATE]"""

    self.emissionsPrices = self.pullFromPRISM(queryStr, database = 'COMMODITIES')

    self.emissionsPrices['DATE'] = pd.DatetimeIndex(self.emissionsPrices['EFFECTIVE_DATE']).date
    
    self.emissionsPrices.loc[self.emissionsPrices['MONTH_NUM'] < 5,'NOXPrice'] = self.emissionsPrices.loc[self.emissionsPrices['MONTH_NUM'] < 5,'NOXAnnual']

    self.emissionsPrices.loc[self.emissionsPrices['MONTH_NUM'] > 9,'NOXPrice'] = self.emissionsPrices.loc[self.emissionsPrices['MONTH_NUM'] > 9,'NOXAnnual']