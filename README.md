# CORVIS
**CO**VID-19 **R**apid **Vis**ualization

CORVIS is a simple, flexible Python library designed to let small organizations and individuals easily analyze and visualize COVID-19 data. CORVIS has several key pieces of core functionality:

1. **Automated data acquisition.** CORVIS automatically downloads data from two major public repositories: [The COVID Tracking Project](https://covidtracking.com/api) and the [2019 Novel Coronavirus COVID-19 (2019-nCoV) Data Repository by Johns Hopkins CSSE](https://github.com/CSSEGISandData/COVID-19). CORVIS minimizes download time by automatically storing the latest versions of each dataset locally, only updating these datasets when new data is available. CORVIS also joins these two datasets together into a single unified dataframe for easy analysis.
1. **Simple filtering and aggregation.** CORVIS provides a simple, powerful function to filter and aggregate data at the county, state/province, and national/regional level.
1. **Straightforward data manipulation functions.** CORVIS gives users a variety of functions to transform and align data. Quickly and easily apply moving averages, calculate per-capita cases, identify a common 'day zero' starting point across multiple areas, calculate daily changes, and more.
1. **Easy-to-use plotting tool.** Quickly plot and compare data using a single plotting function
1. **Standard data formats.** All data is stored as `pandas` DataFrames, so advanced users can use their favorite tools and applications for deeper research.
