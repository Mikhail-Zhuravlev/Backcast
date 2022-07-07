import datetime

import pandas as pd


class dispatchPeriod:
    
    def __init__(self, isOn = 0, startindex = 0, endIndex = 0, incMargin = 0, startCost = 0):
        self.isOn = isOn
        self.startIndex = startindex
        self.endIndex = endIndex
        self.incMargin = incMargin
        self.startCost = startCost
        
    def __str__(self):
        return 'isOn: {0}; startIndex: {1}; endIndex: {2}; incMargin: {3}; startCost: {4}; Net: {5}'.format(
            "{:.0f}".format(self.isOn),
            "{:.0f}".format(self.startIndex),
            "{:.0f}".format(self.endIndex), 
            "{:.0f}".format(self.incMargin),
            "{:.0f}".format(self.startCost),
            "{:.0f}".format(-self.startCost+self.incMargin)
        )
        
    def setStart(self, startindex):
        self.startIndex = startindex
    
    def setEnd(self, endIndex):
        self.endIndex = endIndex
        
    def setMargin(self, incMargin):
        self.incMargin = incMargin
        
    def setStartCost(self, startCost):
        self.startCost = startCost


def createHourlyTable(self):

    dtRange =  pd.date_range(start = self.startDate, end = self.endDate, freq='1H')

    self.hourlyData = pd.DataFrame({ 'DateTime': dtRange})
        
    self.hourlyData['DATE'] = pd.DatetimeIndex(self.hourlyData['DateTime']).date
    
    self.hourlyData['YEAR'] = pd.DatetimeIndex(self.hourlyData['DateTime']).year
    
    self.hourlyData['MONTH'] = pd.DatetimeIndex(self.hourlyData['DateTime']).month
    
    self.hourlyData['FUTURE_MONTH'] = pd.to_datetime({'year':self.hourlyData['YEAR'],
                                        'month':self.hourlyData['MONTH'],
                                        'day':1})
    
    self.hourlyData['HB'] = pd.DatetimeIndex(self.hourlyData ['DateTime']).hour - 1 
    
    self.hourlyData.loc[self.hourlyData['HB'] == -1, 'HB'] = 23
                                
    self.hourlyData['HE'] = pd.DatetimeIndex(self.hourlyData ['DateTime']).hour

    self.hourlyData.loc[self.hourlyData['HE'] == 0, 'HE'] = 24
    
    #HE0 (now HE24 for clarity) belongs in the previous day
    self.hourlyData.loc[self.hourlyData['HE'] == 24, ['DATE']] = (
        pd.DatetimeIndex(self.hourlyData.loc[self.hourlyData['HE'] == 24, 'DateTime']).date
        - datetime.timedelta(days=1)
        )
    
    self.hourlyData['MODEL_HOUR'] = self.hourlyData.index


def alignHourlyParameters(self):

    self.createHourlyTable()

    self.hourlyData = pd.merge(
        self.hourlyData
        ,self.plantParameters
        ,how = 'left'
        ,on = 'FUTURE_MONTH'
        ,suffixes=('', '_DROP')
        ).fillna(0)
    
    self.hourlyData.drop(self.hourlyData.filter(regex='_DROP$').columns.tolist(),axis=1, inplace=True)

    self.hourlyData = pd.merge(
        self.hourlyData,
        self.DaLmp,
        how = 'left',
        on = 'DateTime',
        suffixes=('', '_DROP')
        ).fillna(0)

    self.hourlyData.drop(self.hourlyData.filter(regex='_DROP$').columns.tolist(),axis=1, inplace=True)
    
    self.hourlyData = pd.merge(
        self.hourlyData,
        self.fuelPrice,
        how = 'left',
        on = 'DATE',
        suffixes=('', '_DROP')
        ).fillna(0)

    self.hourlyData.drop(self.hourlyData.filter(regex='_DROP$').columns.tolist(),axis=1, inplace=True)

    self.hourlyData = pd.merge(
        self.hourlyData,
        self.fuelTransport,
        how = 'left',
        on = 'FUTURE_MONTH',
        suffixes=('', '_DROP')
        ).fillna(0)

    self.hourlyData.drop(self.hourlyData.filter(regex='_DROP$').columns.tolist(),axis=1, inplace=True)
    
    self.hourlyData = pd.merge(
        self.hourlyData,
        self.emissionsPrices,
        how = 'left',
        on = 'DATE',
        suffixes=('', '_DROP')
        ).fillna(0)

    self.hourlyData.drop(self.hourlyData.filter(regex='_DROP$').columns.tolist(),axis=1, inplace=True)

    excessColList = ['HB'
    , 'MONTH_NUM'
    , 'TPT_PROD_STGY_NUM'
    , 'TPT_PROD_STGY_NAME'
    , 'TPT_TEST_STGY_NUM'
    , 'TPT_TEST_STGY_NAME'
    , 'RUNHOURS'
    , 'UNIT_HUB_BASIS_SYMBOL'
    , 'CHANGED_BY'
    , 'MODELED_IN_CXL'
    ]
    
    self.hourlyData.drop(labels = excessColList
    , axis = 1
    , inplace = True
    )


def calculateHourlyMargins(self):

    self.hourlyData['DISPATCH_MW'] = self.hourlyData['MAX_CAP']

    self.hourlyData['POWER_REVENUE'] = self.hourlyData[self.powerNode] * self.hourlyData['DISPATCH_MW']

    self.hourlyData['FUEL_COST'] = self.hourlyData['HEAT_RATE'] * self.hourlyData['DISPATCH_MW'] * (
        self.hourlyData[self.fuelPoint] + self.hourlyData['TRANSPORT_ADDER']
    )

    self.hourlyData['EMISSION_COST'] = self.hourlyData['HEAT_RATE'] * self.hourlyData['DISPATCH_MW'] * (
        self.hourlyData['CO2'] * self.hourlyData['CO2Price']
        + self.hourlyData['NOx'] * self.hourlyData['NOXPrice']
        + self.hourlyData['SO2'] * self.hourlyData['SO2Price']
    ) / 2000
    
    self.hourlyData['VOM_COST'] = self.hourlyData['VOM']  * self.hourlyData['DISPATCH_MW'] + self.hourlyData['NO_LOAD_COST']

    self.hourlyData['START_COST'] = self.hourlyData['START_FUEL']  *  ( self.hourlyData[self.fuelPoint] + self.hourlyData['TRANSPORT_ADDER'] ) + self.hourlyData['START_OM']

    self.hourlyData['NET_MARGIN'] = (
        self.hourlyData['POWER_REVENUE']
        - self.hourlyData['FUEL_COST']
        - self.hourlyData['EMISSION_COST']
        - self.hourlyData['VOM_COST']
    )

#    self.hourlyData['NMlessStart'] = (
#        self.hourlyData['NET_MARGIN']
#        - self.hourlyData['START_COST']
#    )



