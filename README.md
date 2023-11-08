# bop-tenant-scrape


### Scrape Securiti tenants in BOP for usage stats.

- Use scrape_bop.py for all tenants. 
- Use scrape_bop_tenant.py for specific tenants

--

## How does it work:
It launches Chromium via Selenium, waits for user to log into the BOP, then scrapes each "tenant summary" page. 

The scraping is done by exercising the GET and POST calls that are issued for populating the tenant summary page.

NOTE: Do not shut down the chromium that's laumched. The script has provision to connect to the same Chromium instance again and again. However, before launching the script, you need to make sure you are currently logged in because you will be kicked out to login page if you are idle for too long. The script can be extended to exercise any generic Reporting query to get data of modules that don't appear on Tenant Summary page today like: Assessments, Data Mapping, etc. 

The script produces a .json file by simply capturing the response of each API call under a unique key such as "dsp_stats", "conn_stats" etc. 

A separate script, produce_xls.py, is used to convert this json data into an .XLS file. The separation helps us tweak the xls generation process independent of the data collection.

--

## Pre-requisites:
- pip install selenium
- pip install webdriver-manager
- upgrade your chrome driver version using chromedriver_download.py
    - use https://sites.google.com/chromium.org/driver/
    - also https://googlechromelabs.github.io/chrome-for-testing/
    - replace the chrome version in the edgedl.me link at the bottom with yours. (Example: .../119.0.6045.105/mac-x64/...)
    - test your updated driver with test_chromedriver.py
