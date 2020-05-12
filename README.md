# CORVIS
### **CO**VID-19 **R**apid **Vis**ualization

CORVIS is a simple, flexible Python library designed to let small organizations and individuals easily analyze and visualize COVID-19 data. CORVIS has several key pieces of core functionality:

1. **Automated data acquisition.** CORVIS automatically downloads data from two major public repositories: [The COVID Tracking Project](https://covidtracking.com/api) and the [2019 Novel Coronavirus COVID-19 (2019-nCoV) Data Repository by Johns Hopkins CSSE](https://github.com/CSSEGISandData/COVID-19). CORVIS minimizes download time by automatically storing the latest versions of each dataset locally, only updating these datasets when new data is available. CORVIS also joins these two datasets together into a single unified dataframe for easy analysis.
1. **Simple filtering and aggregation.** CORVIS provides a simple, powerful function to filter and aggregate data at the county, state/province, and national/regional level.
1. **Straightforward data manipulation functions.** CORVIS gives users a variety of functions to transform and align data. Quickly and easily apply moving averages, calculate per-capita cases, identify a common 'day zero' starting point across multiple areas, calculate daily changes, and more.
1. **Easy-to-use plotting tool.** Quickly plot and compare data using a single plotting function
1. **Standard data formats.** All data is stored as `pandas` DataFrames, so advanced users can use their favorite tools and applications for deeper research.

# Examples

Load, filter, analyze, and plot data with just a few lines of code!

	from corvis.corvis import *

	unifiedDataCORVIS = LoadCORVISData(verbose=True)

	corvisDataToPlot = FilterCORVISData(unifiedDataCORVIS, country='US', aggregateBy=CORVISAggregations.COUNTRY, metric=CORVISMetrics.CONFIRMED, sourceData=CORVISDatasources.ALL, combineDatasources=CORVISCombineDatasourcesBy.MAX)

	CreateCORVISPlot(corvisDataToPlot, graphTitle='United States: Confirmed Cases')


A more advanced example:

	from corvis.corvis import *

	unifiedDataCORVIS = LoadCORVISData(verbose=True)

	corvisDataToPlot = FilterCORVISData(unifiedDataCORVIS, country='US', state=['NY', 'NJ'], aggregateBy=CORVISAggregations.COUNTRY, metric=CORVISMetrics.CONFIRMED, sourceData=CORVISDatasources.ALL, combineDatasources=CORVISCombineDatasourcesBy.MAX)
	stayHomeCorvisDataToPlot = FilterCORVISData(unifiedDataCORVIS, country='US', state=['!NY', '!NJ', '!IA', '!NE', '!ND', '!SD', '!AR','!WY', '!UT', '!OK'], aggregateBy=CORVISAggregations.COUNTRY, metric=CORVISMetrics.CONFIRMED, sourceData=CORVISDatasources.ALL, combineDatasources=CORVISCombineDatasourcesBy.MAX)
	stayHomePartialCorvisDataToPlot = FilterCORVISData(unifiedDataCORVIS, country='US', state=['WY', 'UT', 'OK'], aggregateBy=CORVISAggregations.COUNTRY, metric=CORVISMetrics.CONFIRMED, sourceData=CORVISDatasources.ALL, combineDatasources=CORVISCombineDatasourcesBy.MAX)
	StayHomeNoneCorvisDataToPlot = FilterCORVISData(unifiedDataCORVIS, country='US', state=['IA', 'NE', 'ND', 'SD', 'AR'], aggregateBy=CORVISAggregations.COUNTRY, metric=CORVISMetrics.CONFIRMED, sourceData=CORVISDatasources.ALL, combineDatasources=CORVISCombineDatasourcesBy.MAX)

	corvisDataToPlot = corvisDataToPlot.append(stayHomeCorvisDataToPlot, ignore_index=True)
	corvisDataToPlot = corvisDataToPlot.append(stayHomePartialCorvisDataToPlot, ignore_index=True)
	corvisDataToPlot = corvisDataToPlot.append(StayHomeNoneCorvisDataToPlot, ignore_index=True)

	corvisDataToPlot = ComputeCORVISPerCapita(corvisDataToPlot, 100000)
	corvisDataToPlot = ComputeCORVISMovingAverage(corvisDataToPlot, 14)
	corvisDataToPlot = ComputeCORVISMovingAverage(corvisDataToPlot, 14)

	corvisDataToPlot = ComputeCORVISDailyChange(corvisDataToPlot)
	corvisDataToPlot = ComputeCORVISDailyChange(corvisDataToPlot)

	graphLegend = ['New York and New Jersey', 'Stay-at-home order, statewide (minus NY/NJ)', 'Stay-at-home order, some areas',  'No stay-at-home order']

	CreateCORVISPlot(corvisDataToPlot, graphLegend, 'United States: Confirmed Cases – Per-Capita Rate of Change (14-day double moving average)', xLabel='Date', yLabel='Daily change per 100k people', startGraphAtThreshold=0.05)

 

# Functions

## LoadCORVISData()
`LoadCORVISData()` allows us to quickly and easily load the latest COVID-19 data directly from the server. Once loaded, it stores a copy of the data on our local server, along with the fingerprint for that data. On subsequent calls, it only downloads the data from the server again if the server has updated its fingerprint, meaning there is new data.

`LoadCORVISData()` also performs some basic data cleaning, manipulation, and collation. It selects fields of primary interest to data researchers and discards others (such as ISO and FIPS codes.) It also aligns data from different datasets to a single unified structure. Finally, it uses a lookup table to populate missing `Population` values in the dataset.

### Parameters:
- `datasourceToLoad`: a single `CORVISDatasources` enumerated value. The datasource to load. Default is `CORVISDatasources.ALL` (load data from all available sources.)
- `dataPath`: a raw string representing a file path. The location to which to save data files. Defaults to the home directory (`~/`). *Note: all saved data files are hidden.*
- `forceDownload`: a boolean value. When `True`, forces the application to download data from remote servers, bypassing the local saved data files. Default is `False`.
- `verbose`: a boolean value. Provides verbose output when `True`. Default is `False`.

### Returns:
- a single `pandas` `DataFrame` containing a valid CORVIS dataset.


##FilterCORVISData()
`FilterCORVISData()` allows users to quickly capture data for specific criteria, such as country, state, county, and metric.

###Parameters:

- `sourceCORVISDataframe`: a CORVIS dataframe generated by this library.
- `country`: a string or list of strings, used to filter by Country/Region. To exclude a country from a filter, add an exclamation point `!` to the beginning of the string.
- `state`: a string or list of strings, used to filter by State/Province. To exclude a state from a filter, add an exclamation point `!` to the beginning of the string.
- `county`: a string or list of strings, used to filter by County. To exclude a county from a filter, add an exclamation point `!` to the beginning of the string.
- `region`: an alias for `country`
- `province`: an alias for `state`
- `aggregateBy`: a single `CORVISAggregations` value. determines how to - aggregate your data: globally, nationally, by state, or not at all. 
- `metric`: a single `CORVISMetrics` value or list of `CORVISMetrics` values. Determines which metrics to filter (e.g. CORVISMetrics.POSITIVE, CORVISMetrics.RECOVERED)
- `filterMissingPopulation`: boolean, defaults `True`. Determines whether or not to filter out records that do not have a population associated with them (e.g. cruise ships, special departments.) This is important when performing per-capita analysis.
-  `sourceData`: a single `Datasource` value, defaults to `CORVISDatasources.ALL`. The datasource to filter on.
- `allowStateCodesInFilters`: a boolean. If `True`, then state codes (e.g. `NY`) will work when identifying US states. If `False`, then states must be spelled out (e.g. `New York`.) Defaults to `True`.

### Returns:
- a single `pandas` `DataFrame` containing a valid CORVIS dataset.


## TransformCORVISDataToDayZero()

We can use the `TransformCORVISDataToDayZero()` function to transform any of our CORVIS 'calendar day' datasets to a 'Day Zero' format. the `threshold` parameter indicates the threshold in cases/deaths/recoveries that an area needs to exceed in order to begin counting from day zero.

For example, if a dataframe of confirmed infections is fed into this function with a threshold of 200, then day zero for any given record will be the first day with 200 or more confirmed cases.

This function makes it easy to align different areas to a common starting point for an area-by-area comparison.

*Note: **use caution when using dataframes containing more than one metric.** Dataframes with more than one metric will use the same threshold value for all metrics. As a result, a single location will likely identify a different day zero for each metric associated with that location.*

### Parameters:
- `sourceCORVISDataframe`: a CORVIS dataframe generated by this library.
- `thresholdValue`: a single number. The minimum threshold value that must be met or exceeded to determine day zero.
- `dropNAColumns`: a boolean. if `True`, drops all trailing columns that contain only NA values. Defaults to `True`.


### Returns:
- a single `pandas` `DataFrame` containing a valid CORVIS dataset.

## ComputeCORVISMovingAverage()

This function allows us to compute a moving average over a period of days. This can be useful to eliminate noise or variances introduced to our data by poor reporting or day-of-week effects.

The built-in `rolling()` method in `pandas` does a great job of calculating the rolling average, with one caveat: it either handles the front end of our window as `N/A` or pushes the tail end of our window into the future, neither of which we really want. To get around this, I'm adding dummy columns to the start of our dataframe and copying our first column values into those dummy dataframes. Then, I'm dropping them after calculating our moving average.

This lets us have a bit of a lead-in on our front end. It isn't perfect; using this function on 'day zero' dataframes will have a slightly inaccurate start-up, but will quickly normalize once the moving average window is fully over our live data. This is an issue we can live with.

### Parameters:
- `sourceCORVISDataframe`: a CORVIS dataframe generated by this library.
- `windowRange`: the range of days the moving average should cover. Default = `7` (average data over one week.)


### Returns:
- a single `pandas` `DataFrame` containing a valid CORVIS dataset.


##ComputeCORVISDailyChange()

Computes the day-by-day change for a CORVIS dataframe as the difference from the previous day's total.

### Parameters:
- `sourceCORVISDataframe`: a CORVIS dataframe generated by this library.


### Returns:
- a single `pandas` `DataFrame` containing a valid CORVIS dataset.

## ComputeCORVISPerCapita()

Computes per-capita values for a CORVIS dataframe.

### Parameters:
- `sourceCORVISDataframe`: a CORVIS dataframe generated by this library.
- `denominator`: the "per" in "number of cases per". For example, a denominator of 1000 will return results for "number of cases per 1000 people". Defaults to 1.


### Returns:
- a single `pandas` `DataFrame` containing a valid CORVIS dataset.

##GetCORVISHighestValues()

Gets the `numberToGet` records containing the highest values in the given dataframe.

### Parameters:
- `sourceCORVISDataframe`: a CORVIS dataframe generated by this library.
- `numberToGet`: the number of highest value records to get.


### Returns:
- a single `pandas` `DataFrame` containing a valid CORVIS dataset.

## CreateCORVISPlot()

A convenience method for quickly creating a line graph from a CORVIS dataframe.
This function will plot all records in the CORVIS dataframe, so it is strongly recommended the user filters and aggregates their data to their liking before using this plotting function.

### Parameters
- `sourceCORVISDataframe`: a CORVIS dataframe generated by this library.
- `valuesForLegend`: a single `CORVISPlotValues` enumerated value, or a list of strings: the values to use in the graph's legend. Defaults to `None`, which does not show any legend.
- `graphTitle`: a single string, the title of the graph.
- `xLabel`: a single string, the label for the x-axis. Optional; auto-generates by default
- `yLabel`: a single string, the label for the y-axis. Optional; auto-generates by default
- `yScale`: a single string, indicating what kind of scale to use on the y-axis. Main options are 'linear' (default) or 'log'. *(Also supports any other axis scale supported by `matplotlib.pyplot`, but these two should be all you need.)*
- `startGraphAtThreshold`: a number. If not `None`, the x-axis will begin the graph once a value greater than `startGraphAtThreshold` has been reached in the graph data. Default is `None`. 
- `saveToFile`: a single string. Saves the generated plot to the file path/name provided. If not provided, the generated graph will be displayed in an interactive window.


### Returns:
This function has no return value.


## Data Acquisition and Standardization

At present, we have two major sources of data: [The COVID Tracking Project](https://covidtracking.com/api), the [2019 Novel Coronavirus COVID-19 (2019-nCoV) Data Repository by Johns Hopkins CSSE](https://github.com/CSSEGISandData/COVID-19). Each source provides its own tallies of daily data, each source provides different levels of granularity, and each source provides different metrics.


To facilitate analysis, CORVIS creates a standardized dataset from each of these sources.



## Enumerated Types

Where practical, CORVIS uses enumerated types for parameter inputs. It is strongly recommended that you use these enumerated types wherever they are called for in the documentation. This helps to avoid confusion and invalid inputs, and helps protect your scripts from changes in future versions. 

For example, instead of using `FilterCORVISData( ... aggregateBy='country' ... )`, use `FilterCORVISData( ... aggregateBy=CORVISAggregations.COUNTRY ... )`.

The enumerated types are as follows:

		class CORVISDatasources(Enum):
		  ALL = 'All Datasources'
		  JHU = 'Johns Hopkins University'
		  COVID_TRACKING = 'The Covid Tracking Project'
		  CTP = 'The Covid Tracking Project' # alias for COVID_TRACKING

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

