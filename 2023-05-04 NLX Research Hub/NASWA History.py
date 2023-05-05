state_or_territory = "MN" #@param {type:"string"}
start = "2023-03-01" #@param {type:"date"}
end = "2023-04-01" #@param {type:"date"}
api_key = 'your api key here'

# Python package dependencies
import requests
import json
import pandas as pd
import time


# Import supporting files
zipXwalk = pd.read_excel("ziptoedr.xlsx")


# For the asynchronous API, we set our parameters and request the report
query_params = {
    "state_or_territory":state_or_territory, # Use an upper-case two digit code for the state or territory you intend to query
    "start":start, # Start date of the results (inclusive)
    "end":end, # End date of the results (inclusive). Please note that you cannot request more than 35 days of data at a time
    "format":"csv" # Currently supports csv and ndjson formats
}

headers = {
    'X-API-Key': api_key,
    'Content-Type': 'application/json'
}


# Requests the report from the Data Warehouse. 
report_request_response = requests.post('https://api.nlxresearchhub.org/api/job_reports/',
              headers=headers, data=json.dumps(query_params))


# wait for the report to complete and query the API until the report is complete
# Sleep for 10 seconds between requests to avoid rate limitations
not_done = True
while not_done:
    print("Sleeping for 10 seconds to wait for report")
    time.sleep(10)
    report_request_json = report_request_response.json()
    report_status_url = report_request_json['data'][0]['url']
    report_status_response = requests.get(report_status_url,headers=headers)
    report_status_json = report_status_response.json()
    if report_status_json['data']:
        if report_status_json['data'][0]['status'] == 'done':
            not_done = False
        else:
            print("Report Status: ", report_status_json['data'][0]['status'])

# output will contain the signed AWS S3 url that we download to a Pandas dataframe below
print("Report is done. Downloading...")
report_output_df = pd.read_csv(report_status_json['data'][0]['resource']['link'])

# add regional information
report_output_df = report_output_df.set_index('zipcode').join(zipXwalk.set_index('zipcode'), rsuffix='_r')
report_output_df = report_output_df.reset_index()


#add soc2 field
report_output_df['soc2'] = report_output_df['classifications_onet_code'].str[:2]






#report_output_df.to_excel('naswa.xlsx', index=False)
with open('naswa.xlsx', 'w') as f:
  #f.write(report_output_df.to_csv)
  report_output_df.to_excel('naswa.xlsx',index=True)


print("Download completed.")

