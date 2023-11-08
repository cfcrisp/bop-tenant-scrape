# produce_xls.py
#
# Takes the .json file produced by scrape_bop.py and
# generates a .xls file.

import xlsxwriter
import json
import sys
import pdb
from datetime import datetime

def write_appliance_stats(workbook, hdr_format, tenant_stats):

    worksheet = workbook.add_worksheet("Appliance")
    worksheet.set_column(0,2,40)
    worksheet.set_column(3,10,15)
    row = 0
    worksheet.write_row(row, 0, ['Tenant Name', "ID", "Name", "Gravity Version", "Version", "Status", "Total Nodes" ], hdr_format) 
    for t in tenant_stats:
        appl_stats = t.get('appl_stats', {})
        if appl_stats is None:
            print("Warning: appl_stats is None for ", t['name'],". Skipping write_appliance_stats.")
            continue
        list = appl_stats.get('data', [])
        for appl in list:
            if appl['id'] == 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx':
                continue
            row += 1
            worksheet.write_row(row, 0, [  t['name'], \
                appl["id"], appl["name"], appl["cluster_current_version"], appl["appliance_current_version"], \
                appl["status"], appl["total_nodes"] ])
        
def write_dsp_stats(workbook, hdr_format, tenant_stats):
    worksheet = workbook.add_worksheet("DSP")
    worksheet.set_column(0,0,40)
    worksheet.set_column(1,3,20)

    row = 0
    worksheet.write_row(row, 0, ['Tenant Name', \
        "# unique Data subjects", "Avg # of DSRs per Data Subject", "# DSP users w/ no passwords"], hdr_format)
    for t in tenant_stats:
        dsp_stats = t.get('dsp_stats', {})
        if dsp_stats is None:
            print("Warning: dsp_stats is None. Skipping write_dsp_stats.")
            continue
        dsp = dsp_stats.get('data', {})
        if dsp:
            row += 1
            worksheet.write_row(row, 0, [  t['name'], \
                dsp["unique_data_subjects_count"], \
                dsp["average_requests_per_user"], \
                dsp["users_without_password_count"] ])

def write_dsr_form_stats(workbook, hdr_format, tenant_stats):
    worksheet = workbook.add_worksheet("DSR Forms")
    worksheet.set_column(0,0,40)
    worksheet.set_column(1,15,15)

    row = 0
    worksheet.write_row(row, 0, ['Tenant Name', \
            "Type", "Attachment", "Automation", "Delayed Task Creation", "Language", "Median Restriction", \
            "Parallel Requests", "Published", "Selective Data Store" ], hdr_format )
    for t in tenant_stats:
        form_stats = t.get('dsr_forms', {})
        if form_stats is None:
            print("Warning: form_stats is None for ", t['name'],". Skipping write_dsr_form_stats.")
            continue
        form_types = form_stats.get('data', {})
        for form_type in form_types:
            f = form_types[form_type]
            count = f["attachment_enabled"] + f["automation"] + f["delayed_task_creation"] +    \
                    f["language_enabled"] + f["median_restriction"] + f["parallel_requests"] + \
                    f["published"] + f["selective_data_store"]
            if count == 0:
                continue
            row += 1
            worksheet.write_row(row, 0, [  t['name'], \
                form_type, f["attachment_enabled"], f["automation"], f["delayed_task_creation"],    \
                    f["language_enabled"], f["median_restriction"], f["parallel_requests"], \
                    f["published"], f["selective_data_store"] ])

def write_dsr_wksp_stats(workbook, hdr_format, tenant_stats):
    dsr_type_enums = { 1: 'Access', 2: 'Port', 3: 'Erase', 4: 'Rectify', 5: 'Restrict', 6: 'Object', \
        7: 'Restrict Auto', 8: 'Do Not Sell', 9: 'Multiple', 10: 'Confirmation', 11: 'Disclosure of Subprocessors' }

    worksheet = workbook.add_worksheet("DSR")
    worksheet.set_column(0,0,40)
    worksheet.set_column(1,15,10)

    row = 0
    worksheet.write_row(row, 0, ['Tenant Name', \
            'Access', 'Port', 'Erase', 'Rectify', 'Restrict', 'Object', \
            'Restrict Auto', 'Do Not Sell', 'Multiple', 'Confirmation', 'Disclosure of Subprocessors', 'Unknown', 'Total'  ], hdr_format)
    for t in tenant_stats:
        wksp_stats = t.get('dsr_wksp', {})
        if wksp_stats is None:
            print("Warning: wksp_stats is None for ", t['name'],". Skipping write_dsr_wksp_stats.")
            continue
        dsr_type_stats = wksp_stats.get('data', [])
        flat = { 'Unknown' : 0, 'Total' : 0} 
        for e in dsr_type_stats:
            dsr_type = dsr_type_enums.get(e['request_type'])
            if dsr_type:
                flat[dsr_type] = e['ticket_count']
            else:
                flat['Unknown'] += e['ticket_count']
            flat['Total'] += e['ticket_count']
        row += 1
        if flat.get('Unknown') == 0:
            flat['Unknown'] = None
        worksheet.write_row(row, 0, [  t['name'], \
            flat.get('Access', ''), flat.get('Port', ''), flat.get('Erase', ''), flat.get('Rectify', ''), \
            flat.get('Restrict', ''), flat.get('Object', ''), flat.get('Restrict Auto', ''), \
            flat.get('Do Not Sell', ''), flat.get('Multiple', ''), flat.get('Confirmation', ''), \
            flat.get('Disclosure of Subprocessors', ''), flat.get('Unknown', ''), flat.get('Total', '')  ])

def write_connectors(workbook, hdr_format, tenant_stats):
    worksheet = workbook.add_worksheet("Connector List")
    worksheet.set_column(0,0,40)
    worksheet.set_column(1,15,15)

    row = 0
    worksheet.write_row(row, 0, ['Tenant Name', \
            "Data System Id", "Instance Name", "Connector Type", "Connector Type Id", "Cloud Connector Id", \
            "On Prem Connector Id", "On Prem Cluster Id", "Activated", "State" ], hdr_format)

    for t in tenant_stats:
        connectors = t.get('connectors', {})
        if connectors is None:
            print("Warning: connectors is None for ", t['name'],". Skipping write_connectors.")
            continue
        data = connectors.get('data', [])
        for conn in data:
            row += 1
            worksheet.write_row(row, 0, [  t['name'], \
                conn.get("id",""),
                conn.get("name",""),
                conn.get("ds_connector_type",""),
                conn.get("connector_type_id",""),
                conn.get("cloud_connector_id",""),
                conn.get("on_prem_connector_id",""),
                conn.get("on_prem_cluster_id",""),
                conn.get("created_at",""),
                conn.get("state","") ])

def write_conn_stats(workbook, hdr_format, tenant_stats):
    worksheet = workbook.add_worksheet("Connector Stats")
    worksheet.set_column(0,0,40)
    worksheet.set_column(1,15,15)

    row = 0
    worksheet.write_row(row, 0, ['Tenant Name', \
            "Type", "Vendor", "Name", "Status", "Connector Type", "Files Processed", \
            "Files Skipped", "Files Classified", "Rows Classified", \
            "Total Bytes Classified", "Files in Error", "Files Processed/hr" ], hdr_format)
        
    for t in tenant_stats:
        conn_stats = t.get('conn_stats', {})
        if conn_stats is None:
            print("Warning: conn_stats is None for ", t['name'],". Skipping write_conn_stats.")
            continue
        data = conn_stats.get('data', [])
        for conn in data:
            row += 1
            worksheet.write_row(row, 0, [  t['name'], \
                conn.get("datasource_type",""),
                conn.get("connector_type_id",""),
                conn.get("datasource_name",""),
                conn.get("status",""),
                conn.get("connector_type",""),
                conn.get("file_total_count",""),
                conn.get("file_filter_count",""),
                conn.get("file_scanned_count",""),
                conn.get("row_total_count",""),
                conn.get("file_scan_size_count",""),
                conn.get("file_error_count",""),
                conn.get("avg_scan_rate", "") ])

def convert_timestamp(ts):
    if ts:
        return datetime.fromtimestamp(ts/1000).strftime('%b %d, %Y')
    else:
        return "Unknown"

def make_sub_name(start_ts, end_ts):
    return "Subscription (" + \
        convert_timestamp(start_ts) + '-' + \
        convert_timestamp(end_ts) + ")" 

def write_cum_conn_stats(workbook, hdr_format, tenant_stats, key_name, sheet_name):
    worksheet = workbook.add_worksheet(sheet_name)
    worksheet.set_column(0,1,40)
    worksheet.set_column(2,15,15)

    row = 0
    worksheet.write_row(row, 0, ['Tenant Name', \
            "Type", "Total Unique Vendors", "Total Connectors", "Total Rows Processed", "Total Files Processed", "Total Bytes Processed" ], hdr_format)
        
    for t in tenant_stats:
        cum_conn_stats = t.get(key_name, {})
        if cum_conn_stats is None:
            print("Warning: cum_conn_stats is None for ", t['name'],". Skipping write_cum_conn_stats.")
            continue
        data = cum_conn_stats.get('data', {})

        current = data.get("current", {})
        if current:
            row += 1
            worksheet.write_row(row, 0, [  t['name'], \
                "Current", current['vendors'], current['connectors'] ])
        
        hist = data.get("historical", {})
        if hist:
            row += 1
            worksheet.write_row(row, 0, [  t['name'], \
                "Lifetime", hist.get('vendors',''), hist.get('connectors', ''), hist.get('row_total_count', ''), \
                hist.get('file_total_count', ''), hist.get('file_scan_size_count', '') ])

        subs = data.get("subscriptions", [])
        if subs:
            for sub in subs:
                row += 1
                worksheet.write_row(row, 0, [  t['name'], \
                    make_sub_name(sub.get('start_time',0), sub.get('end_time', 0)),  \
                    sub.get('vendors', ''), sub.get('connectors',''), sub.get('row_total_count', ''), \
                    sub.get('file_total_count', ''), sub.get('file_scan_size_count','') ])

def write_cookie_domain_stats(workbook, hdr_format, tenant_stats):
    worksheet = workbook.add_worksheet("Cookie Consent Domains")
    worksheet.set_column(0,1,40)
    worksheet.set_column(2,15,15)

    row = 0
    worksheet.write_row(row, 0, ['Tenant Name', \
        "Domain Group", "Domains", "Draft", "Published", "Last Code generated" ], hdr_format)
    for t in tenant_stats:
        dg_stats = t.get('cookie_domain_stats', {})
        if dg_stats is None:
            print("Warning: dg_stats is None for ", t['name'],". Skipping write_cookie_domain_stats.")
            continue
        data = dg_stats.get('data', [])
        for dg in data:
            row += 1
            worksheet.write_row(row, 0, [  t['name'], \
                dg['name'], dg['cookie_consent_domains'], dg['draft_state'], \
                dg['published_state'], convert_timestamp(dg['last_code_generated']) ])

def write_cookie_scan_stats(workbook, hdr_format, tenant_stats):
    worksheet = workbook.add_worksheet("Cookie Consent Scans")
    worksheet.set_column(0,1,40)
    worksheet.set_column(2,15,15)

    row = 0
    worksheet.write_row(row, 0, ['Tenant Name', \
        "Domain Group", "Completed", "Aborted", "Last Scan" ], hdr_format)
    for t in tenant_stats:
        dg_stats = t.get('cookie_scan_stats', {})
        if dg_stats is None:
            print("Warning: dg_stats is None for ", t['name'],". Skipping write_cookie_scan_stats.")
            continue
        data = dg_stats.get('data', [])
        for dg in data:
            row += 1
            worksheet.write_row(row, 0, [  t['name'], \
                dg['domain_group'], dg['scan_completed'], dg['scan_aborted'], \
                convert_timestamp(dg['last_scan_initiated']) ])


def write_univ_consent_stats(workbook, hdr_format, tenant_stats):
    worksheet = workbook.add_worksheet("Univ Consent")
    worksheet.set_column(0,1,40)
    worksheet.set_column(2,15,15)

    row = 0
    worksheet.write_row(row, 0, ['Tenant Name', \
        "Endpoint", "Draft", "Published" ], hdr_format)
    for t in tenant_stats:
        ep_stats = t.get('form_consent_stats', {})
        if ep_stats is None:
            print("Warning: ep_stats is None for ", t['name'],". Skipping write_univ_consent_stats.")
            continue
        data = ep_stats.get('data', [])
        for ep in data:
            row += 1
            worksheet.write_row(row, 0, [  t['name'], \
                ep['name'], ep['draft_state'], ep['published_state'] ])

def write_lite_tenant_cookie_consent_record_stats(workbook, hdr_format, tenant_stats):
    worksheet = workbook.add_worksheet("Cookie Consent")
    worksheet.set_column(0,4,40)
    worksheet.set_column(2,15,15)

    row = 0
    worksheet.write_row(row, 0, ['Tenant Name', \
        "Tenant Domain", "Tenant Owner", "Created On", "Last Accessed", "GRANTED", "DECLINED", "WITHDRAWN", "NOACTION"  ], hdr_format)
    for t in tenant_stats:
        stats = t.get('consent_record_stats', {}).get('data', [])
        granted = declined = withdrawn = noaction = 0
        #pdb.set_trace()
        for stat in stats:
            #stat = stats[ndx]
            if stat["consented_item_activity_id"] == 1:
                granted = stat["no_of_consents"]
            if stat["consented_item_activity_id"] == 2:
                declined = stat["no_of_consents"]
            if stat["consented_item_activity_id"] == 3:
                withdrawn = stat["no_of_consents"]
            elif stat["consented_item_activity_id"] == 4:
                noaction = stat["no_of_consents"]

        row += 1
        worksheet.write_row(row, 0, [  t['name'], \
                t['domain'], t['lite_owner'], \
                convert_timestamp(t['created_at']), convert_timestamp(t['last_accessed']),     \
                granted, declined, withdrawn, noaction])


if __name__ == "__main__":

    if len(sys.argv) != 3:
        print("Usage: produce_xls.py <stats_json_file_name> [PAID|LITE]")
        sys.exit(-1)

    stats_json_file_name = sys.argv[1]
    with open(stats_json_file_name) as json_file:
        tenant_stats = json.load(json_file)

    stats_xls_file_name = stats_json_file_name.replace(".json", ".xlsx")

    # Create a workbook and add a worksheet.
    workbook = xlsxwriter.Workbook(stats_xls_file_name)
    hdr_format = workbook.add_format({'bold': True})

    if sys.argv[2] == "PAID":
        write_appliance_stats(workbook, hdr_format, tenant_stats)

        write_dsr_form_stats(workbook, hdr_format, tenant_stats)
        write_dsr_wksp_stats(workbook, hdr_format, tenant_stats)
        write_dsp_stats(workbook, hdr_format, tenant_stats)

        write_connectors(workbook, hdr_format, tenant_stats)
        write_conn_stats(workbook, hdr_format, tenant_stats)
        write_cum_conn_stats(workbook, hdr_format, tenant_stats, 'cum_conn_stats', "Cum Conn Stats")
        write_cum_conn_stats(workbook, hdr_format, tenant_stats, 'cum_cloud_conn_stats', "Cum Conn Stats - Securiti Cloud")

        write_cookie_domain_stats(workbook, hdr_format, tenant_stats)
        write_cookie_scan_stats(workbook, hdr_format, tenant_stats)

        write_univ_consent_stats(workbook, hdr_format, tenant_stats)
    else:
        write_lite_tenant_cookie_consent_record_stats(workbook, hdr_format, tenant_stats)
    

    workbook.close()
