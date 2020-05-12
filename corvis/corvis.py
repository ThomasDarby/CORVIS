from enum import Enum
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import sys
import math
import time
import us
import random


class CORVISDatasources(Enum):
  ALL = 'All Datasources'
  JHU = 'Johns Hopkins University'
  COVID_TRACKING = 'The Covid Tracking Project'
  CTP = 'The Covid Tracking Project' # alias for COVID_TRACKING
#  NYT = 'New York Times'

class CORVISMetrics(Enum):
  ALL = 'all'
  CONFIRMED = 'Confirmed'
  DEATH = 'Death'
  RECOVERED = 'Recovered'
  NEGATIVE = 'Negative'
  HOSPITALIZED = 'Hospitalized'
  ICU = 'ICU'
  VENTILATOR = 'Ventilator'

class CORVISCombineDatasourcesBy(Enum):
  MIN = 'min'
  MAX = 'max'
  MEAN = 'mean'
  NONE = None


class CORVISAggregations(Enum):
  ALL = 'global'
  GLOBAL = 'global'
  COUNTRY = 'country'
  REGION = 'country'
  STATE = 'state'
  PROVINCE = 'state'
  COUNTY = None
  NONE = None

class CORVISPlotValues(Enum):
  SOURCE = 'Source'
  METRIC = 'Metric'
  COUNTRY = 'Country/Region'
  REGION  = 'Country/Region'
  STATE = 'Province/State'
  PROVINCE = 'Province/State'
  COUNTY = 'County'

# select a default plot style.
CORVISPlotStyle = 'fivethirtyeight'

# next, we'll provide a few global lists of column names for use in our functions.
CORVISAggregatorColumnNames = ['Source', 'Metric', 'Country/Region', 'Province/State', 'County']
CORVISBaselineColumnNames = ['Source', 'Metric', 'Country/Region', 'Province/State', 'County', 'Population', 'Lat', 'Long']
CORVISBreakpointColumnNames = ['Source', 'Metric', 'Country/Region', 'Province/State', 'County', 'Population',  'Lat', 'Long', 'DayZero']

# at present, we're supporting both the JHU dataset and The COVID Tracking Project (CTP) datasets.

# QUIRKS: several nations have unusual reporting in the JHU dataset. They are:
  # US: includes all population AS WELL AS and summable states. Will need to fix national/global summaries!
  # France: splits into mainland "" and colonies (small)
  # Australia: states only
  # Canada: states only
  # China: States only
  # Denmark: includes mainland "" and Faroe and Greenland
  # Netherlands: includes mainland "" and colonies (small)
  # United Kingdom: includes main islands "" and colonies (small)

CORVISIgnoreStatesForNationalCount = ['US']

def VerifyCORVISDataframe(sourceCORVISDataframe):
  if not isinstance(sourceCORVISDataframe, pd.DataFrame):
    raise ValueError("ERROR in VerifyCORVISDataframe(): this is not a valid CORVIS dataframe.")
  if sourceCORVISDataframe.shape[0] == 0:
    raise ValueError("ERROR in VerifyCORVISDataframe(): This dataframe is empty.")
  necessaryBaselineColumns = len(CORVISBaselineColumnNames)
  for currentColumn in sourceCORVISDataframe.columns:
    if currentColumn in CORVISBaselineColumnNames:
      necessaryBaselineColumns = necessaryBaselineColumns - 1
    else:
      if (necessaryBaselineColumns <= 0):
        # we have all our necessary baseline columns, so we can safely assume this is a valid CORVIS dataframe. Return true.
        return True
      else:
        # if we get here, we've found a column that is NOT a baseline column where we're expecting a baseline column. Throw an exception.
        raise ValueError("ERROR in VerifyCORVISDataframe(): this is not a valid CORVIS dataframe. An unexpected column [" + currentColumn + "] was found in the required columns.")
  # if we get here, we haven't found all of our necessary baseline columns. Throw an exception.
  raise ValueError("ERROR in VerifyCORVISDataframe(): this is not a valid CORVIS dataframe. It is missing some required columns at the start of the dataframe.")


def FindCORVISDataframeBreakPoint(datasetToUse):
  for i in range(len(datasetToUse.columns)):
    if not datasetToUse.columns[i] in CORVISBreakpointColumnNames:
      return i
  return -1

def GetCORVISThresholdDateLambda(row, thresholdValue, sourceDataframe):

  for i in range(row.shape[0]):
    if row[i] >= thresholdValue:
      return sourceDataframe.columns[i]
  return 'INVALID'

def GetCORVISPopulationLambda(row, refTable):
  # lambda function to find an area's population in the lookup table
  try:
    nameToCheck = row[2]
  except:
    nameToCheck = ''
  
  try:
    if (len(row[3]) > 0):
      nameToCheck = row[3] + ', ' + nameToCheck
  except: 
   pass

  try:
    if (len(row[4]) > 0):
      nameToCheck = row[4] + ', ' + nameToCheck
  except:
    pass
  if (nameToCheck == 'District of Columbia, District of Columbia, US'):
    # SPECIAL CASE: The data lists DC as both state and region, which is problematic. Simplify.
    nameToCheck = 'District of Columbia, US'
  returnValue = refTable[(refTable['Combined_Key'] == nameToCheck)]['Population'].max()
  return returnValue
  


def LoadCORVISData(datasourceToLoad = CORVISDatasources.ALL, dataPath='./', forceDownload=False, verbose=True):

  if verbose:
    print('loading from datasource: ' + str(datasourceToLoad.value))  
  proceedWithDownload = False

  ##########################
  ##### LOAD JHU DATA. #####
  ##########################
  
  if ((datasourceToLoad == CORVISDatasources.ALL) | (datasourceToLoad == CORVISDatasources.JHU)):
    if verbose:
      print('Loading JHU data...')

    canConnectToGithub = True
    try:
      repoInfo = pd.read_json('https://api.github.com/repos/CSSEGISandData/COVID-19/branches/master')
      repoInfo.commit.sha # check to see if we successfully loaded our repo info.
    except NameError:
      if verbose:
        print("ERROR: could not connect to JHU CORVISDatasources.")
        canConnectToGithub = False


    try:
      lastRepoInfoJHU = pd.read_json(dataPath+'.jhuRepoInfo.json')
    except:
      # if we couldn't even connect to Github, we're out of options. Fail out.
      if canConnectToGithub == False:
        print('ERROR: could not load local JHU data.')
        print('FATAL ERROR: cannot obtain JHU data remotely or locally.')
        exit(0)
      # if this file doesn't exist, pretend it does, but ruin the fingerprint.
      lastRepoInfoJHU = repoInfo
      lastRepoInfoJHU.commit.sha = "MISSING_LOCAL_FINGERPRINT"

    # next, confirm that we have all our necessary dataframes loaded.
    pd.set_option('mode.chained_assignment', None) # temporarily disable 'SettingWithCopyWarning' message
    try:
      timeSeriesConfirmedUS = pd.read_csv(dataPath+'.jhu_timeSeriesConfirmedUS.csv')
      timeSeriesConfirmedGlobal = pd.read_csv(dataPath+'.jhu_timeSeriesConfirmedGlobal.csv')
      timeSeriesDeathUS = pd.read_csv(dataPath+'.jhu_timeSeriesDeathUS.csv')
      timeSeriesDeathGlobal = pd.read_csv(dataPath+'.jhu_timeSeriesDeathGlobal.csv')
      timeSeriesRecoveredGlobal = pd.read_csv(dataPath+'.jhu_timeSeriesRecoveredGlobal.csv')
      lookupTable = pd.read_csv(dataPath+'.jhu_lookupTable.csv')
    except:
      # we don't have the data loaded locally; re-download.
      proceedWithDownload = True
      lastRepoInfoJHU.commit.sha = str(random.random)
    else:
      if verbose:
        print('Local JHU data available; checking for updates on server...')
      
    pd.set_option('mode.chained_assignment', 'warn')


    try:
      lastRepoInfoJHU
      if verbose:
        print("checking data fingerprints: " + str(lastRepoInfoJHU.commit.sha) + " == " + str(repoInfo.commit.sha) + "? [" + str(lastRepoInfoJHU.commit.sha == repoInfo.commit.sha) + "]")
    except:
      if verbose:
        print('JHU data not yet downloaded. Beginning download...')
      proceedWithDownload = True
    else:
      if (lastRepoInfoJHU.commit.sha == repoInfo.commit.sha):
        if verbose:
          print('Latest JHU data already available.')
      else:
        if verbose:
          print('Updated JHU data available; downloading...')
        proceedWithDownload = True

    if forceDownload:
      if verbose:
        print("Forcing re-download of JHU data.")
      proceedWithDownload = True

    if proceedWithDownload:
      try:
        if verbose:
          print('loading confirmed US cases...')
        timeSeriesConfirmedUS = pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv');
        if verbose:
          print('loading confirmed global cases...')
        timeSeriesConfirmedGlobal = pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv');
        if verbose:
          print('loading confirmed US deaths...')
        timeSeriesDeathUS = pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_US.csv');
        if verbose:
          print('loading confirmed global deaths...')
        timeSeriesDeathGlobal = pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv');
        if verbose:
          print('loading confirmed global recoveries...')
        timeSeriesRecoveredGlobal = pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv');
        if verbose:
          print('loading demographic/region lookup table...')
        lookupTable = pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/UID_ISO_FIPS_LookUp_Table.csv');
      except:
        print("ERROR: there was a problem loading the JHU dataset. Details: ")
        for i in range(len(sys.exc_info())):
          print("    " + str(sys.exc_info()[i]))

      # now, we want to eliminate unwanted columns from our results. JHU's data is a bit inconsistent across sets, so we'll do this by hand.
      if verbose:
        print('Transforming dataframes...')
      timeSeriesConfirmedUS =  timeSeriesConfirmedUS.drop(['UID','iso2','iso3','code3','FIPS','Combined_Key'], axis=1)
      timeSeriesDeathUS =  timeSeriesDeathUS.drop(['UID','iso2','iso3','code3','FIPS','Combined_Key'], axis=1)
      timeSeriesConfirmedUS = timeSeriesConfirmedUS.rename(columns={"Long_": "Long", "Province_State": "Province/State", "Country_Region": "Country/Region", "Admin2": "County"})
      timeSeriesDeathUS = timeSeriesDeathUS.rename(columns={"Long_": "Long", "Province_State": "Province/State", "Country_Region": "Country/Region", "Admin2": "County"})

      timeSeriesConfirmedUS['Metric'] = 'Confirmed'
      timeSeriesConfirmedGlobal['Metric'] = 'Confirmed'
      timeSeriesDeathUS['Metric'] = 'Death'
      timeSeriesDeathGlobal['Metric'] = 'Death'
      timeSeriesRecoveredGlobal['Metric'] = 'Recovered'

      timeSeriesConfirmedUS['Source'] = CORVISDatasources.JHU.value
      timeSeriesConfirmedGlobal['Source'] = CORVISDatasources.JHU.value
      timeSeriesDeathUS['Source'] = CORVISDatasources.JHU.value
      timeSeriesDeathGlobal['Source'] = CORVISDatasources.JHU.value
      timeSeriesRecoveredGlobal['Source'] = CORVISDatasources.JHU.value



      try:
        pd.set_option('mode.chained_assignment', None) # temporarily disable 'SettingWithCopyWarning' message
        timeSeriesConfirmedUS.to_csv(dataPath+'.jhu_timeSeriesConfirmedUS.csv', index=False)
        timeSeriesConfirmedGlobal.to_csv(dataPath+'.jhu_timeSeriesConfirmedGlobal.csv', index=False)
        timeSeriesDeathUS.to_csv(dataPath+'.jhu_timeSeriesDeathUS.csv', index=False)
        timeSeriesDeathGlobal.to_csv(dataPath+'.jhu_timeSeriesDeathGlobal.csv', index=False)
        timeSeriesRecoveredGlobal.to_csv(dataPath+'.jhu_timeSeriesRecoveredGlobal.csv', index=False)
        lookupTable.to_csv(dataPath+'.jhu_lookupTable.csv')
        pd.set_option('mode.chained_assignment', 'warn')
      except NameError:
        print("ERROR: one or more JHU datasources failed to download. Please re-run this script.")
        repoInfo.commit.sha = "BAD_LOCAL_DATA"
        return;

    if verbose:
      print('JHU data successfully loaded.')
    repoInfo.to_json(r'~/.jhuRepoInfo.json')


  #############################################
  ##### LOAD COVID TRACKING PROJECT DATA. #####
  #############################################
 
  if ((datasourceToLoad == CORVISDatasources.ALL) | (datasourceToLoad == CORVISDatasources.COVID_TRACKING)):

    if verbose:
      print('Loading CTP data...')
    ctpMetrics = ['positive', 'negative', 'hospitalizedCumulative', 'inIcuCumulative', 'onVentilatorCumulative', 'recovered']
    ctpMetricEnums = [CORVISMetrics.CONFIRMED, CORVISMetrics.NEGATIVE, CORVISMetrics.HOSPITALIZED, CORVISMetrics.ICU, CORVISMetrics.VENTILATOR, CORVISMetrics.RECOVERED]
    ctpDataframes = []

    proceedWithDownload = False

    try:
      lastRepoInfoCTP = pd.read_json(dataPath+'.ctpRepoInfo.json') # load the last modified date
      for i in range(len(ctpMetrics)):
        ctpDataframes.append(pd.read_csv(dataPath+'.cpt_timeSeries' + ctpMetrics[i] + '.csv'))
    except:
      # we haven't connected to the CTP servers yet. Set dummy data.
      ctpDataframes = []
      lastRepoInfoCTP = None
    
    try:
      currentRepoInfoCTP = pd.read_json('https://covidtracking.com/api/v1/us/current.json')
    except:
      currentRepoInfoCTP = None

    if (currentRepoInfoCTP is None and lastRepoInfoCTP is None):
      raise IOError("FATAL ERROR: Cannot connect to CTP server, and no local data is available. Aborting.")
    elif (currentRepoInfoCTP is None):
      # we can't connect to the server, so just load from disk.
      print('WARNING: Cannot connect to CTP server. Using local data instead. Data may be out of date.')
    elif (lastRepoInfoCTP is None):
      if verbose:
        print('No CTP data available on local disk. Will download.')
      proceedWithDownload = True
    else:
      if (currentRepoInfoCTP.lastModified[0] != lastRepoInfoCTP.lastModified[0]):
        # we have both local AND server data, and their fingerprints don't match. Re-download.
        if verbose:
          print('Updated CTP data available on server. Will download.')
          proceedWithDownload = True
      else:
        if verbose:
          print('Local CTP data is latest. Will not download new data.')

    if forceDownload:
      if verbose:
        print("Forcing re-download of CTP data.")
      proceedWithDownload = True

    if proceedWithDownload:
      try:
        if verbose:
          print('loading CTP state-by-state historical data...')
        ctpStatesData = pd.read_csv('https://covidtracking.com/api/v1/states/daily.csv');
      except:
        print("ERROR: there was a problem loading the CTP dataset. Details: ")
        for i in range(len(sys.exc_info())):
          print("    " + str(sys.exc_info()[i]))
      
      if verbose:
        print('transforming CTP data...')
      # transform our date to the standard format we're using (M/D/YY)
      ctpStatesData['date'] = ctpStatesData['date'].astype(str)
      ctpStatesData['date'] = ctpStatesData['date'].str[4:6].astype(int).astype(str) + '/' + ctpStatesData['date'].str[6:8].astype(int).astype(str) + '/' + ctpStatesData['date'].str[2:4]

      # CTP uses state abbreviations, whereas our standard uses full names. Fix that with the 'us' module.
      ctpStatesData['state'] = ctpStatesData['state'].apply(lambda x: str(us.states.lookup(x)))

      ctpStatesData = ctpStatesData.rename(columns={"Long_": "Long", "Province_State": "Province/State", "Country_Region": "Country/Region", "Admin2": "County"})

      # now, we need to transform our data into several timeseries, similar to what JHU has.
      # to do this, we'll create a series of dataframes for each metric, pivot them, flesh them out with standard columns, and append them to our unified dataframe.
      
      for i in range(len(ctpMetrics)):
        workingDataframe = ctpStatesData[['state', ctpMetrics[i], 'date']]
        workingDataframe = workingDataframe.pivot(index='state',  columns='date', values=workingDataframe.columns[1]).fillna(0).reset_index()
        workingDataframe.insert(1, 'Long', np.nan, True)
        workingDataframe.insert(1, 'Lat', np.nan, True)
        workingDataframe.insert(1, 'Population', np.nan, True)
        workingDataframe.insert(1, 'County', '', True)
        workingDataframe.insert(0, 'Country/Region', 'US', True)
        workingDataframe.insert(0, 'Metric', ctpMetricEnums[i].value, True)
        workingDataframe.insert(0, 'Source', CORVISDatasources.CTP.value, True)
        workingDataframe = workingDataframe.rename(columns={"state": "Province/State"})

        ctpDataframes.append(workingDataframe)
      

      try:
        pd.set_option('mode.chained_assignment', None) # temporarily disable 'SettingWithCopyWarning' message
        for i in range(len(ctpMetrics)):
          ctpDataframes[i].to_csv(dataPath+'.cpt_timeSeries' + ctpMetrics[i] + '.csv', index=False)
        pd.set_option('mode.chained_assignment', 'warn')
      except NameError:
        print("ERROR: one or more CTP datasources failed to download. Please re-run this script.")
        return;
      if currentRepoInfoCTP is not None:
        currentRepoInfoCTP.to_json(dataPath+'.ctpRepoInfo.json')

  #####################################################
  ##### END OF LOAD BLOCK. PROCEED WITH CLEANING. #####
  #####################################################

  if verbose:
    print('Data loading complete. Building unified CORVIS dataframe...')
  # construct return dataframe
  returnDataframe = pd.DataFrame(columns=CORVISBaselineColumnNames)
  if ((datasourceToLoad == CORVISDatasources.ALL) | (datasourceToLoad == CORVISDatasources.JHU)):
    returnDataframe = returnDataframe.append([timeSeriesConfirmedUS, timeSeriesDeathUS, timeSeriesConfirmedGlobal, timeSeriesDeathGlobal, timeSeriesRecoveredGlobal], ignore_index=True)
  if ((datasourceToLoad == CORVISDatasources.ALL) | (datasourceToLoad == CORVISDatasources.CTP)):
    returnDataframe = returnDataframe.append(ctpDataframes, ignore_index=True)
  
  
  # strip out "unnamed: 0" index column that was imported with original data
  returnDataframe = returnDataframe.loc[:, ~returnDataframe.columns.str.match('Unnamed')]

  # Clean up data
  returnDataframe['County'] = returnDataframe['County'].fillna('')
  returnDataframe['Province/State'] = returnDataframe['Province/State'].fillna('')


  # set string columns to type string, just to be extra cautious
  returnDataframe['Source'] = returnDataframe['Source'].astype("string")
  returnDataframe['Metric'] = returnDataframe['Metric'].astype("string")
  returnDataframe['County'] = returnDataframe['County'].astype("string")
  returnDataframe['Province/State'] = returnDataframe['Province/State'].astype("string")
  returnDataframe['Country/Region'] = returnDataframe['Country/Region'].astype("string")

  returnDataframe['Population'] = returnDataframe['Population'].replace(np.nan, 0)

  if ((datasourceToLoad == CORVISDatasources.ALL) | (datasourceToLoad == CORVISDatasources.JHU)):
    returnDataframe['Population'] = returnDataframe.apply(GetCORVISPopulationLambda, args=(lookupTable,), axis=1)
  else:
    print("WARNING: 'Population' is only calculated with the JHU dataset.")

  returnDataframe['Population'] = returnDataframe['Population'].fillna(-1)
  returnDataframe['Lat'] = returnDataframe['Lat'].fillna(1000) # fill with easy-to-catch junk data
  returnDataframe['Long'] = returnDataframe['Long'].fillna(1000) # fill with easy-to-catch junk data

  returnDataframe['Population'] = returnDataframe['Population'].astype(int)
  returnDataframe['Lat'] = returnDataframe['Lat'].astype(float)
  returnDataframe['Long'] = returnDataframe['Long'].astype(float)

  # scrub any countries that double-report at the national level.
  for nationalException in CORVISIgnoreStatesForNationalCount:
      returnDataframe = returnDataframe.drop(returnDataframe[(returnDataframe['Country/Region'] == nationalException) & (returnDataframe['Province/State'] == '')].index, axis=0)

  if verbose:
    print('CORVIS data successfully loaded. Ready.')
  return returnDataframe



def FilterCORVISData(sourceCORVISDataframe, country=None, state=None, county=None, region=None, province=None, aggregateBy=CORVISAggregations.NONE, metric=None, filterMissingPopulation=False, sourceData=CORVISDatasources.ALL, combineDatasources=None, allowStateCodesInFilters=True):
  

  VerifyCORVISDataframe(sourceCORVISDataframe)
  # first, check to see if our aliases are in use. If so, confirm that our primary entries aren't, then reassign accordingly.

  if (region is not None):
    if (country is not None):
      # we have entries for BOTH country AND province. Do not allow this.
      raise ValueError("ERROR: Ambiguous value: 'region' is an alias for 'country'. You cannot use both at the same time.")
    else:
      country = region

  if (province is not None):
    if (state is not None):
      # we have entries for BOTH country AND province. Do not allow this.
      raise ValueError("ERROR: Ambiguous value: 'province' is an alias for 'state'. You cannot use both at the same time.")
    else: 
      state = province

  if (metric is None):
    metric = CORVISMetrics.ALL

  if (combineDatasources is None):
    combineDatasources = CORVISCombineDatasourcesBy.NONE

  if isinstance(metric, CORVISMetrics):
    metric = [metric]

  # if country, county, or state is as a string, convert it to a 1-item list.

  if isinstance(country, str):
    country = [country]

  if isinstance(county, str):
    county = [county]

  if isinstance(state, str):
    state = [state]

  if country == ['']:
    country = []
  
  if county == ['']:
    county = []

  if state == ['']:
    state = []

  if country is None:
    country = []
  
  if county is None:
    county = []

  if state is None:
    state = []


  # next, sort our lists so we can compare them.
  country.sort()
  county.sort()
  state.sort()

  # get our datasource, and warn if it isn't the enumerated type.
  if isinstance(sourceData, CORVISDatasources):
    sourceData = sourceData.value
  else:
    print("Note: we recommend using one of the following enumerated values for the 'metric' parameter:")
    print("    CORVISDatasources.ALL, CORVISDatasources.JHU, CORVISDatasources.CTP")


  # get the value of our CORVISMetrics enumerated type, if that's what was passed.
  # Print a reminder to use the enumerated type if they don't.
  hasWarnedOnMetric = False
  for i in range(len(metric)):
    if isinstance(metric[i], CORVISMetrics):
      metric[i] = metric[i].value
    elif hasWarnedOnMetric:
      print("Note: we recommend using one of the following enumerated values for the 'metric' parameter:")
      print("    CORVISMetrics.ALL, CORVISMetrics.CONFIRMED, CORVISMetrics.DEATH, or CORVISMetrics.RECOVERED")
      hasWarnedOnMetric = True
    # confirm that our metric will work in its current context
    if not (metric[i] in ['Confirmed', 'Death', 'Recovered', 'all']):
      raise ValueError("'metric' must be one of the following values: 'confirmed', 'death', 'recovered', 'all' (default: 'all')")


  # get the value of our CORVISAggregations enumerated type, if that's what was passed.
  # Print a reminder to use the enumerated type if they don't.
  if isinstance(aggregateBy, CORVISAggregations):
    aggregateBy = aggregateBy.value
  elif aggregateBy is None:
    # do nothing
    pass
  else:
    print("Note: we recommend using one of the following enumerated values for the 'aggregateBy' parameter:")
    print("    CORVISAggregations.GLOBAL, CORVISAggregations.COUNTRY, CORVISAggregations.STATE, CORVISAggregations.COUNTY, CORVISAggregations.NONE")

  # confirm that our metric will work in its current context
  if not (aggregateBy in ['global', 'country', 'state', None]):
    raise ValueError("'aggregateBy' must be one of the following values: 'global', 'country', 'state', None (default)")

  # get the value of our CORVISCombineDatasourcesBy enumerated type, if that's what was passed.
  # Print a reminder to use the enumerated type if they don't.
  if isinstance(combineDatasources, CORVISCombineDatasourcesBy):
    combineDatasources = combineDatasources.value
  elif combineDatasources is None:
    # do nothing
    pass
  else:
    print("Note: we recommend using one of the following enumerated values for the 'combineDatasources' parameter:")
    print("    CORVISCombineDatasourcesBy.MIN, CORVISCombineDatasourcesBy.MAX, CORVISCombineDatasourcesBy.MEAN, CORVISAggregations.NONE")

  # confirm that our metric will work in its current context
  if not (combineDatasources in ['min', 'max', 'mean', None]):
    raise ValueError("'combineDatasources' must be one of the following values: 'min', 'max', 'mean', None (default)")


  returnDataframe = sourceCORVISDataframe.copy()

  # loop through our filter lists and extract any string that begins with '!'.
  # Put these values into a "does not include" filter list after removing the
  # '!' at the front.
  filterCountry = country
  filterState = state
  filterCounty = county

  notCountry = []
  notState = []
  notCounty = []
  country = []
  state = []
  county = []

  for currentFilterItem in filterCountry:
    if len(currentFilterItem) > 0:
      if (currentFilterItem[0] != '!'):
        country.append(currentFilterItem)
      else:
        currentFilterItem = currentFilterItem[1:]
        notCountry.append(currentFilterItem)

  for currentFilterItem in filterState:
    if len(currentFilterItem) > 0:
      if (currentFilterItem[0] != '!'):
        state.append(currentFilterItem)
      else:
        currentFilterItem = currentFilterItem[1:]
        notState.append(currentFilterItem)

  for currentFilterItem in filterCounty:
    if len(currentFilterItem) > 0:
      if (currentFilterItem[0] != '!'):
        county.append(currentFilterItem)
      else:
        currentFilterItem = currentFilterItem[1:]
        notCounty.append(currentFilterItem)

  # if requested, convert state codes to states. Will also properly capitalize other requests.
  if allowStateCodesInFilters:
    for i in range(len(state)):
      if us.states.lookup(state[i]):
        state[i] = str(us.states.lookup(state[i]))
    for i in range(len(notState)):
      if us.states.lookup(notState[i]):
        notState[i] = str(us.states.lookup(notState[i]))

  # it's possible the above 'not' filtering set some of our arrays to 'None'.
  # Address that here.

  # if country is None:
  #   country = []
  
  # if county is None:
  #   county = []

  # if state is None:
  #   state = []

  # if notCountry is None:
  #   notCountry = []
  
  # if notCounty is None:
  #   notCounty = []

  # if notState is None:
  #   notState = []



  # filter before we aggregate: it's faster!
  # if we need to filter our values, go in order of coarsest to finest: country, then state, then county.
  if (country != []):
    returnDataframe = returnDataframe[returnDataframe['Country/Region'].isin(country)]

  if (state != []):
    returnDataframe = returnDataframe[returnDataframe['Province/State'].isin(state)]

  if (county != []):
    returnDataframe = returnDataframe[returnDataframe['County'].isin(county)]

  if (notCountry != []):
    returnDataframe = returnDataframe[~returnDataframe['Country/Region'].isin(notCountry)]

  if (notState != []):
    returnDataframe = returnDataframe[~returnDataframe['Province/State'].isin(notState)]

  if (notCounty != []):
    returnDataframe = returnDataframe[~returnDataframe['County'].isin(notCounty)]

  if (filterMissingPopulation):
    returnDataframe = returnDataframe[returnDataframe['Population'] > 0]
    
  if (metric != [CORVISMetrics.ALL.value]):
    returnDataframe = returnDataframe[returnDataframe['Metric'].isin(metric)]

  if (sourceData != CORVISDatasources.ALL.value):
    returnDataframe = returnDataframe[returnDataframe['Source'] == str(sourceData)]

  try:
    VerifyCORVISDataframe(sourceCORVISDataframe)
  except ValueError:
    raise ValueError("ERROR in FilterCORVISData(): no data met the filtering criteria.")

  if (aggregateBy is not None):

    # set up our aggregators!
    # In the event we need to group our results, we need to be able to aggregate columns.
    # We have a LOT of columns, and the number grows every day.
    # Loop through all of our column names and build a dicionary of tuples
    # that we'll use to feed our aggregator function should we need to.

    aggregatorTuples = {}
    

    for colName in sourceCORVISDataframe:
      if not (colName in CORVISAggregatorColumnNames):
        if (colName in ['Lat', 'Long', 'Population']):
          aggregatorTuples[colName]='max'
        else:
          aggregatorTuples[colName]='sum'
    


    # if we need to aggregate our values, go in order of finest to coarsest: county, then state, then country.
    if (aggregateBy == 'state'):
      # clear all values for counties so they group together
      returnDataframe['County'] = ''
      returnDataframe = returnDataframe.groupby(CORVISAggregatorColumnNames).agg(aggregatorTuples).reset_index() # ooh, look, our aggregator tuples!
      # also, drop any records that don't have a value for Province/State: those will be nationwide values.
      returnDataframe = returnDataframe[returnDataframe['Province/State'] != '']

    if (aggregateBy == 'country'):
      # clear all values for states and counties so they group together
      returnDataframe['County'] = ''
      returnDataframe['Province/State'] = ''
      returnDataframe = returnDataframe.groupby(CORVISAggregatorColumnNames).agg(aggregatorTuples).reset_index()
      # also, drop any records that don't have a value for Country/Region: those will be nationwide values.
      returnDataframe = returnDataframe[returnDataframe['Country/Region'] != '']

    if (aggregateBy == 'global'):
      returnDataframe['County'] = ''
      returnDataframe['Province/State'] = ''
      returnDataframe['Country/Region'] = 'Global'
      returnDataframe = returnDataframe.groupby(CORVISAggregatorColumnNames).agg(aggregatorTuples).reset_index()

  if (combineDatasources is not None):
    # we want to aggregate our datasources based on the function passed. Note that population, lat, and long are always aggregated by MAX.

    aggregatorTuples = {}

    for colName in returnDataframe:
      if not (colName in CORVISAggregatorColumnNames):
        if (colName in ['Lat', 'Long', 'Population']):
          aggregatorTuples[colName]='max'
        else:
          aggregatorTuples[colName]=combineDatasources
    returnDataframe['Source'] = 'Combined'
    returnDataframe = returnDataframe.groupby(CORVISAggregatorColumnNames).agg(aggregatorTuples).reset_index()


  # finally, one more thing to check: if the source dataframe's last column is NA, then there's missing data for the day.
  # Unfortunately, our transformations above turn this into a zero-value.
  # Thus, if our last column in the return set is all zeroes, drop it.
  # repeat this process until all empty columns are gone.

  while (returnDataframe.iloc[:,-1].isna()).all():
    returnDataframe = returnDataframe.iloc[:, :-1]

  while (returnDataframe.iloc[:,-1] == 0).all():
    returnDataframe = returnDataframe.iloc[:, :-1]

  return returnDataframe
  
def TransformCORVISDataToDayZero(sourceCORVISDataframe, thresholdValue=100, dropNAColumns=True):

  VerifyCORVISDataframe(sourceCORVISDataframe)
  # This function converts the default 'counts on a given day' dataframe to a
  # 'days since this area reached the given thresholdValue' dataframe. It's
  # super useful for doing area-by-area comparisons when the disease may not
  # have hit on the same date.

  # First, we split off two dataframes: one with our location information,
  # the other with our day-by-day count information.

  datasetBreakpoint = FindCORVISDataframeBreakPoint(sourceCORVISDataframe)
  returnDataframe = sourceCORVISDataframe.copy().iloc[:, : datasetBreakpoint]
  daysDataframe = sourceCORVISDataframe.copy().iloc[:, (datasetBreakpoint) :]


  # we add a "DayZero" column to our location information dataframe, and
  # apply our 'GetCORVISThresholdDateLambda' function to it. This lambda function
  # runs down each column until it finds the first day that meets or exceeds
  # the given thresholdValue, then returns the column name for that cell.

  returnDataframe['DayZero'] = daysDataframe.apply(GetCORVISThresholdDateLambda, args=(thresholdValue, daysDataframe), axis=1)

  # Now, we create a 'DayZero' column on our day-by-day count dataframe,
  # and copy the values from our information dataframe onto it.
  daysDataframe.insert(0, 'DayZero', 0, True)
  daysDataframe['DayZero'] = returnDataframe['DayZero']

  # Then, we remove any rows that have an 'INVALID' day zero: that is,
  # the record didn't ever make it to the thresholdValue, and won't appear
  # in our results.
  returnDataframe = returnDataframe[returnDataframe['DayZero'] != 'INVALID']
  daysDataframe = daysDataframe[daysDataframe['DayZero'] != 'INVALID']

  # now we participate in the darkest of majicks, where we shift all of the
  # data in each row of our day-by-day dataframe to the left.
  # The number of columns we shift to the left is determined by the column
  # index number of the column name that corresponds with the value in our
  # 'DayZero' record. Thus, if 'DayZero' says 2/1/20, and 2/1/20 is, say,
  # the 10th column, we'll shift all values for that record left 10 columns.
  # You can drop a `print(daysDataframe.head())' above and below this for loop
  # if you want to see what's going on. It's spooky.
  for i in range(0, daysDataframe.shape[0]):
    columnNameToGet = daysDataframe.iloc[i,0]
    daysDataframe.iloc[[i]] = daysDataframe.iloc[[i]].shift(periods=1-daysDataframe.iloc[[i]].columns.get_loc(columnNameToGet), axis=1)

  # Almost done! We drop the 'DayZero' column from our day-by-day dataframe...
  daysDataframe = daysDataframe.drop('DayZero', axis=1)

  # ...and rename all of our remaining columns to the number of days since
  # day zero: '0', '1', '2', and so on.
  daysDataframe = daysDataframe.rename(columns={x:y for x,y in zip(daysDataframe.columns,range(0,len(daysDataframe.columns)))})

  # join our two dataframes back together, and we're set!
  returnDataframe = returnDataframe.join(daysDataframe)

  # drop columns with only NA values, unless requested otherwise.
  if dropNAColumns:
    returnDataframe = returnDataframe.dropna(axis=1, how='all')

  # finally, check our dataframe first: if it is empty, throw an exception.
  if returnDataframe.shape[0] == 0:
    raise ValueError("ERROR in TransformCORVISDataToDayZero(): the given thresholdValue (" + str(thresholdValue) + ") is too high. No data returned.")

  return returnDataframe

def ComputeCORVISMovingAverage(sourceCORVISDataframe, windowRange=7):

  VerifyCORVISDataframe(sourceCORVISDataframe)
  datasetBreakpoint = FindCORVISDataframeBreakPoint(sourceCORVISDataframe)
  returnDataframe = sourceCORVISDataframe.copy().iloc[:, : datasetBreakpoint]
  averagesDataframe = sourceCORVISDataframe.copy().iloc[:, (datasetBreakpoint) :]
  for i in range(windowRange):
    averagesDataframe.insert(0, 'dummy'+str(i), 0)
    averagesDataframe.iloc[:,0] = averagesDataframe.iloc[:,i+1]

  averagesDataframe = averagesDataframe.rolling(windowRange, axis=1).mean()

  averagesDataframe = averagesDataframe.iloc[:,windowRange:]

  returnDataframe = returnDataframe.join(averagesDataframe)

  return(returnDataframe)

def ComputeCORVISDailyChange(sourceCORVISDataframe):  
  VerifyCORVISDataframe(sourceCORVISDataframe)

  datasetBreakpoint = FindCORVISDataframeBreakPoint(sourceCORVISDataframe)
  returnDataframe = sourceCORVISDataframe.copy().iloc[:, : datasetBreakpoint]
  dailyChangeDataframe = sourceCORVISDataframe.copy().iloc[:, (datasetBreakpoint) :]

  dailyChangeDataframe = dailyChangeDataframe.diff(axis=1)
  dailyChangeDataframe.iloc[:,0] = dailyChangeDataframe.iloc[:,0].fillna(0)

  returnDataframe = returnDataframe.join(dailyChangeDataframe)

  return(returnDataframe)

def ComputeCORVISPerCapita(sourceCORVISDataframe, denominator=1):
  VerifyCORVISDataframe(sourceCORVISDataframe)
  datasetBreakpoint = FindCORVISDataframeBreakPoint(sourceCORVISDataframe)
  returnDataframe = sourceCORVISDataframe.copy().iloc[:, : datasetBreakpoint]
  perCapitaDataframe = sourceCORVISDataframe.copy().iloc[:, (datasetBreakpoint) :]

  perCapitaDataframe = perCapitaDataframe.div((returnDataframe['Population'].div(denominator)),axis=0)

  returnDataframe = returnDataframe.join(perCapitaDataframe)

  return(returnDataframe)

def GetCORVISHighestValues(sourceCORVISDataframe, numberToGet=5):
  VerifyCORVISDataframe(sourceCORVISDataframe)
  datasetBreakpoint = FindCORVISDataframeBreakPoint(sourceCORVISDataframe)

  sourceCORVISDataframe['maxValue'] = sourceCORVISDataframe.iloc[:, (datasetBreakpoint) :].max(axis=1)
  sourceCORVISDataframe = sourceCORVISDataframe.nlargest(n=numberToGet, columns='maxValue')
  sourceCORVISDataframe = sourceCORVISDataframe.drop('maxValue', axis=1)

  return sourceCORVISDataframe

def CreateCORVISPlot(sourceCORVISDataframe, valuesForLegend=None, graphTitle='', xLabel=None, yLabel=None, yScale='linear', startGraphAtThreshold=None, saveToFile=None):
  VerifyCORVISDataframe(sourceCORVISDataframe)

  if valuesForLegend is not None:
    if not isinstance(valuesForLegend, list):
      if not isinstance(valuesForLegend, CORVISPlotValues):
        print("NOTE: the CreateCORVISPlot() 'valuesForLegend' parameter should be either a single CORVISPlotValues enumerated value or a list of strings.")
  

  if isinstance(valuesForLegend, list):
    legendEntries = valuesForLegend
  else:
    legendEntries = []
  dataframeBreakpoint = FindCORVISDataframeBreakPoint(sourceCORVISDataframe)
  infoDataframe = sourceCORVISDataframe.iloc[:, : dataframeBreakpoint]
  plottingDataframe = sourceCORVISDataframe.iloc[:, dataframeBreakpoint :]

  if startGraphAtThreshold is not None:
    while ((plottingDataframe.iloc[:, 0] < startGraphAtThreshold).all() == True):
      plottingDataframe = plottingDataframe.iloc[:, 1:]


  if yLabel is None:
    yLabel = 'Cases'
  

  totalDaysPlotted = plottingDataframe.shape[1]
  axisTickPoints = []
  axisTickLabels = []
  tickSkip = 1
  if (totalDaysPlotted > 180):
    tickSkip = 90
  elif (totalDaysPlotted > 60):
    tickSkip = 15
  elif (totalDaysPlotted > 20):
    tickSkip = 7

  if 'DayZero' in infoDataframe.columns:
    # we have a 'day zero'-style graph; count up by days
    if xLabel is None:
      xLabel = 'Days since day zero'
    currentTick = 0
    while currentTick < totalDaysPlotted:
      axisTickPoints.append(currentTick)
      axisTickLabels.append(plottingDataframe.columns[currentTick])
      currentTick = currentTick + tickSkip;
  else:
    # we have a 'calendar'-style graph: go by first of the month
    if xLabel is None:
      xLabel = 'Date'
    currentTick = 0
    while currentTick < totalDaysPlotted:
      addTick = False
      if (tickSkip == 1):
        # always add a tick
        addTick = True
      elif (tickSkip == 7):
        if (plottingDataframe.columns[currentTick].split('/')[1] in ['1', '8', '15', '22']):
          addTick = True
      elif (tickSkip == 15):
        if (plottingDataframe.columns[currentTick].split('/')[1] in ['1', '15']):
          addTick = True
      elif (tickSkip == 90):
        if ((plottingDataframe.columns[currentTick].split('/')[1] == '1') and (plottingDataframe.columns[currentTick].split('/')[0] in '1,4,7,10')):
          addTick = True
      if addTick:
        axisTickPoints.append(currentTick)
        axisTickLabels.append(plottingDataframe.columns[currentTick])
      currentTick = currentTick + 1

  plt.figure(figsize=(18, 10), dpi= 80, facecolor='w', edgecolor='k')
  plt.style.use(CORVISPlotStyle)
  plt.title(graphTitle)

  for i in range(sourceCORVISDataframe.shape[0]):
    plt.plot(plottingDataframe.iloc[i])
    if isinstance(valuesForLegend, CORVISPlotValues):
      legendEntries.append(str(sourceCORVISDataframe.iat[int(i),int(sourceCORVISDataframe.columns.get_loc(valuesForLegend.value))]))
  
  if valuesForLegend is not None:
    plt.legend(legendEntries)
  plt.xticks(axisTickPoints, axisTickLabels)
  plt.xlabel(xLabel)
  plt.ylabel(yLabel)
  plt.yscale(yScale)
  if plottingDataframe.max().max() > 1000:
    plt.gca().yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter('{x:,.0f}'))

  if saveToFile is None:
    plt.show(block=True)
  else:
    plt.savefig(saveToFile)

