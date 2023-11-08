# scrape_bop.py
#
# Script to scrape telemetry (usage stats) of every tenant in of BOP.
#
# It launches Chromium via Selenium, waits for user to log into the BOP,
# takes your specific tenant, and then scrapes the "tenant summary" page of
# it. The scraping is done by exercising the GET and POST calls
# that are issued for populating the tenant summary page.
#
# NOTE: Do not shut down the chromium that's laumched. The script has provision to connect
# to the same Chromium instance again and again. However, before launching the script,
# you need to make sure you are currently logged in because you will be kicked out to
# login page if you are idle for too long.
#
# The script can be extended to exercise any generic Reporting query
# to get data of modules that don't appear on Tenant Summary page today.
# some examples are: Assessments, Data Mapping, 

# The script produces a .json file by simply capturing the response of each API call
# under a unique key such as "dsp_stats", "conn_stats" etc.
#
# A separate script, produce_xls_from_json.py, is used to convert this json data into an .XLS file
# The separation helps us tweak the xls generation process independent of the data collection.

#https://www.thepythoncode.com/article/automate-login-to-websites-using-selenium-in-python
#https://selenium-python.readthedocs.io/
#sudo pip install selenium
#sudo pip install webdriver-manager

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import json
import sys
import requests
import base64
import pdb
import time
import re
from datetime import date

bop_inst_regex = "prod-[a-z\-]*bop"

def process_post_api(driver, tenant_id, request_url, payload):
    cookie_header = ""
    for cookie in driver.get_cookies():
        if cookie['name'] == '_xsrf':
            xsrftoken = base64.b64decode(cookie['value'].split('|')[0])
        cookie_header += cookie['name'] + '=' + cookie['value'] + "; "
    headers = { 'X-Tenant-Id' : tenant_id, 'Cookie' : cookie_header, 'X-Xsrftoken': xsrftoken}
    response = requests.post(request_url, data=payload, headers=headers)
    return response.json(), None

def process_get_api(driver, request_url):
    driver.get(request_url)
    WebDriverWait(driver=driver, timeout=20).until(
        lambda x: x.execute_script("return document.readyState === 'complete'")
    )
    e = driver.find_element(By.XPATH, "/html/body/pre")
    response = json.loads(e.text)
    return response, response.get('next')

def get_tenants_list(driver, tenant_type):
    # get list of tenant IDs
    tenants = []
    if tenant_type == "PAID":
        #request_url = bop_host + "/bop/v1/tenants?tenant_type=customer&access_level=premium&sort=name"
        request_url = bop_host + "/bop/v1/tenants?is_lite=false&sort=name"
    elif tenant_type == "LITE":
        request_url = bop_host + "/bop/v1/tenants?is_lite=true&sort=name"
    else:
        return []

    while request_url:
        response_json, next_request_url = process_get_api(driver, request_url)
        for t in response_json['data']:
            tenants.append(t)
        if next_request_url:
            request_url = bop_host + next_request_url
        else:
            request_url = None
    return tenants



def connect_to_browser(bop_instance, bop_host):

    browser_session_file = bop_instance + "_bop_browser_session.json"

    CHROME_DRIVER_PATH = "/usr/local/bin/chromedriver"

    #initialize webdriver
    s = Service(CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=s)
    #driver = webdriver.Chrome(ChromeDriverManager().install())

    # check whether browser from previous run is still running
    reconnected = False
    try:
        with open(browser_session_file) as json_file:
            session = json.load(json_file)
            if session and session.get('url') and session.get('id'):
                driver = webdriver.Remote(command_executor = session['url'], desired_capabilities = {})
                driver.close()   # this prevents the dummy browser
                driver.session_id = session['id']  
                reconnected = True
                driver.get(bop_host)
    except:
        pass
            
    if not reconnected:
        driver.get(bop_host)
        input("Press Enter after you successfully logged into BOP")

        # save handle to the browser session; we will reconnect to the same browser again
        session = {}
        session['url'] = driver.command_executor._url 
        session['id'] = driver.session_id

        with open(browser_session_file, 'w') as outfile:
            json.dump(session, outfile)

    #do not close driver.close() because we need the browser to be running to reconnect to it
    return driver


appl_stats_query = '{"source":"tenant_appliance","skip_cache":true,"response_config":{"format":1},"fields":[{"name":"id"},{"name":"name"},{"name":"status"},{"name":"appliance_current_version"},{"name":"cluster_current_version"},{"name":"appliance_node_id","type":"aggregate","options":{"function":"count","alias":"total_nodes"}}],"group_by":[{"field":"id"}],"pagination":{"type":"limit-offset","offset":0,"limit":1000},"order_by":["name"]}'

dsr_wksp_query = '{"source":"dsr_ticket","skip_cache":true,"response_config":{"format":1},"fields":[{"name":"id","type":"aggregate","options":{"function":"count","alias":"ticket_count"}}],"group_by":[{"field":"request_type"}]}'

connectors_query = '{"source":"tenant_data_source","skip_cache":true,"response_config":{"format":1},"fields":[{"name":"id"},{"name":"name"},{"name":"on_prem_cluster_id"},{"name":"on_prem_connector_id"},{"name":"cloud_connector_id"},{"name":"connector_type_id"},{"name":"ds_connector_type"},{"name":"cloud_connector_created_at"},{"name":"on_prem_connector_created_at"},{"name":"created_at"},{"name":"state"}],"pagination":{"type":"limit-offset","offset":0,"limit":10000},"order_by":["id"]}'

cookie_domain_stats_query = '{"source":"tenant_domain_group","skip_cache":true,"response_config":{"format":1},"fields":[{"name":"id"},{"name":"name"},{"name":"website_domain_id","type":"aggregate","options":{"function":"count_distinct","alias":"cookie_consent_domains"}},{"name":"draft_cookie","type":"aggregate","options":{"function":"count_distinct","alias":"draft_state"}},{"name":"cmp_current_policy","type":"aggregate","options":{"function":"count_distinct","alias":"published_state"}},{"name":"consent_banner","type":"aggregate","options":{"function":"max","alias":"last_code_generated"}}],"filter":{"op":"ne","field":"website_domain_deleted","value":true},"group_by":[{"field":"id"}],"pagination":{"type":"limit-offset","offset":0,"limit":1000},"order_by":["name"]}'

cookie_policy_stats_query = '{"source":"tenant_domain_group","skip_cache":true,"response_config":{"format":1},"fields":[{"name":"id"},{"name":"name"},{"name":"cmp_current_policy","type":"aggregate","options":{"function":"count_distinct","alias":"published_state"}},{"name":"consent_banner_domain","type":"aggregate","options":{"function":"max","alias":"geo_location_enabled"}}],"filter":{"op":"ne","field":"website_domain_deleted","value":true},"group_by":[{"field":"id"}],"pagination":{"type":"limit-offset","offset":0,"limit":1000},"order_by":["name"]}'

form_consent_stats_query = '{"source":"form_endpoint_info","skip_cache":true,"response_config":{"format":1},"fields":[{"name":"id"},{"name":"name"},{"name":"cmp_form_information_id","type":"aggregate","options":{"function":"count_distinct","alias":"published_state"}},{"name":"cmp_draft_form_information_id","type":"aggregate","options":{"function":"count_distinct","alias":"draft_state"}}],"filter":{"op":"ne","field":"cmp_form_information_deleted","value":true},"group_by":[{"field":"id"}],"pagination":{"type":"limit-offset","offset":0,"limit":10000},"order_by":["name"]}'

# don't use this on non-lite-tenants as it's not bounded to a specific time period
lite_tenant_consent_records_query = '{"source":"category_consents_flat_cmp_cookie_consent_overview","response_config":{"format":1},"fields":[{"name":"consented_item_activity_id","type":"aggregate","options":{"function":"count_star","alias":"no_of_consents"}}],"group_by":[{"field":"consented_item_activity_id"}],"skip_cache":true}'

def print_usage():
    print("Usage: scrape_bop_tenant.py <bop_url> [PAID|LITE]")
    print()
    print("Example: scrape_bop_tenant.py https://prod-bop.securiti.xyz PAID")

if __name__ == "__main__":

    if len(sys.argv) != 3:
        print_usage()
        sys.exit(-1)

    bop_host = sys.argv[1]
    tenant_type = sys.argv[2]
    #pdb.set_trace()
    bop_instance = re.search(bop_inst_regex, bop_host).group()

    driver = connect_to_browser(bop_instance, bop_host)

    tenants = get_tenants_list(driver, tenant_type)

    ##for debugging
    #tenants = [ { 'identifier' : 'ac148030-769c-49c3-95d9-312b84bb140d', 'domain' : 'securitidemo.com', 'name' : 'Securiti Demo' } ]
    #tenants = [ { 'identifier' : 'ab269dbc-4beb-43a5-b6dc-cd147909c2f2', 'domain' : 'lazada.com', 'name' : 'Lazada - Prod' } ]

    for t in tenants:
        time.sleep(1)
        print("Processing %s" % t['domain'])

        if sys.argv[2] == "LITE":
            t['consent_record_stats'],_ = process_post_api(driver, t['identifier'],    \
                                            bop_host + "/reporting/v1/bop/sources/query?ref=liteTenantConsentRecordCounts", \
                                            lite_tenant_consent_records_query)
            continue

        try: 
            t['appl_stats'],_       = process_post_api(driver, t['identifier'], bop_host + "/reporting/v1/bop/sources/query?GetApplianceStats", appl_stats_query) 
        except:
            pass
        
        try: 
            t['dsp_stats'], _       = process_get_api(driver, bop_host + "/bop/v1/reports/dsp/" + t['identifier'])
        except:
            pass
        
        try:
            t['dsr_forms'], _       = process_get_api(driver, bop_host + "/bop/v1/reports/dsr_forms/" + t['identifier'])
            t['dsr_wksp'],_         = process_post_api(driver, t['identifier'], bop_host + "/reporting/v1/bop/sources/query", dsr_wksp_query) 
        except:
            pass
        
        try:
            t['connectors'],_           = process_post_api(driver, t['identifier'], bop_host + "/reporting/v1/bop/sources/query", connectors_query)
        except:
            pass
        
        try:
            t['conn_stats'],_           = process_get_api(driver, bop_host + "/bop/v1/reports/connector/cumulative_volume/" + t['identifier'])
            t['cum_conn_stats'], _      = process_get_api(driver, bop_host + "/bop/v1/reports/tenants/" + t['identifier'] + "/connector_stats")
            t['cum_cloud_conn_stats'],_ = process_get_api(driver, bop_host + "/bop/v1/reports/tenants/" + t['identifier'] + "/cloud_connector_stats")
        except:
            pass

        try:
            t['cookie_domain_stats'],_  = process_post_api(driver, t['identifier'], bop_host + "/reporting/v1/bop/sources/query", cookie_domain_stats_query)
            t['cookie_scan_stats'],_    = process_get_api(driver, bop_host + "/bop/v1/reports/cookie_consent/scans/" + t['identifier'] + "?offset=0&limit=1000&order_by=domain_group&sort_by=asc")
            t['cookie_policy_stats'],_  = process_post_api(driver, t['identifier'], bop_host + "/reporting/v1/bop/sources/query", cookie_policy_stats_query)
            t['cookie_compl_stats'],_   = process_get_api(driver, bop_host + "/bop/v1/reports/cookie_consent/compliance/" + t['identifier'] + "?offset=0&limit=1000&order_by=domain_group&sort_by=asc")

            t['form_consent_stats'],_   = process_post_api(driver, t['identifier'], bop_host + "/reporting/v1/bop/sources/query", form_consent_stats_query)
        except:
            pass

    

    today = date.today().strftime("%B %d, %Y")
    with open(bop_instance + " - Tenant Stats - " + today + ".json", 'w') as outfile:
        json.dump(tenants, outfile)
    print("Done!")
