# -*- coding: utf-8 -*-
"""
Created on Wed Jul 17 13:59:41 2019

@author: vjackson

This program is to automate pulling data for the secretary's chart. This chart
ranks all 50 states and DC on a number of BLS indicators: Unemployment rate, 
Total Non-Farm Employment, Total Private employment. These indicators are compared
as actual values, and as changes over time. 


Steps: 
    1) Import the excel file containing series IDs to a pandas DataFrame
    2) Call the BLS API to pull the data and add rankings:
       a) Unemployment Rate
       b) Total Non-Farm 
       c) Total Private    
    3) Organize the results into a DataFrame 
    4) Export the dataframe to excel 
    
"""
# LIBRARIES 

import pandas as pd 
from API import *
import json
import requests
#%% 1) Import the excel file containing series IDs to a pandas DataFrame
''' The excel file should follow this format: 
    Columns - State, Unemployment Rate, Total Non-Farm, Total Private 
''' 

seriesids= pd.read_excel('SecChart Series Ids.xlsx', dtype='object')

#create a column for FIPS by taking the FIPS number from the TNF Series IDs
seriesids['FIPS']=seriesids['Total Non-Farm'].apply(lambda x: str(x[3:5]))

#set the DataFrame index to FIPS codes 
seriesids = seriesids.set_index('FIPS')

#create a dict to map FIPS to StateNames 
statesdict = seriesids['State'].to_dict()

#%% 2) Call the BLS API to pull the data and add rankings

def difference (x,y): 
    return float(x) -float(y)

# a) UNEMPLOYMENT RATE 

ursignature = json.dumps({'seriesid': list(seriesids['Unemployment Rate'][:25]),\
                          'startyear' : '2022', 'endyear': '2022', \
                          'registrationkey' :api_key})
urp= requests.post('https://api.bls.gov/publicAPI/v2/timeseries/data/', \
                   data=ursignature, headers=headers)
urdata = json.loads(urp.text)

#BLS limits API calls to 50, split request into two sets of 25 and 26

ursignature2 = json.dumps({'seriesid': list(seriesids['Unemployment Rate'][25:]),\
                          'startyear' : '2022', 'endyear': '2022', 
                          'registrationkey' :api_key})
urp2 =  requests.post('https://api.bls.gov/publicAPI/v2/timeseries/data/', \
                   data=ursignature2, headers=headers)
urdata2 =json.loads(urp2.text)

urdata['Results']['series'].extend(urdata2['Results']['series']) #join two requests together

urlist=[]
for state in urdata['Results']['series']:
    st = state['seriesID'][5:7] #pull fips code
    january = float(state['data'][-1]['value']) #January is the last in the list 
    cm = float(state['data'][0]['value']) #current month is the first in the list
    urlist.append((st, january, cm))
    
UnemploymentRate= pd.DataFrame(urlist,\
                               columns = ['FIPS', 'January_UR', 'CurrentMonth_UR'])
            

#Calculate the January to Current Month Change
UnemploymentRate['Change_UR']= UnemploymentRate.apply\
(lambda row: float(row['CurrentMonth_UR'])-float(row['January_UR']), axis=1)

#Rank the Unemployment Rate
UnemploymentRate['Rank_UR']=UnemploymentRate['CurrentMonth_UR'].rank(ascending=True, method='min')

#Rank the change in Unemployment Rate
UnemploymentRate['RankChange_UR']=UnemploymentRate['Change_UR'].rank(ascending=True, method='min')

#set index to join to other data-sets for export 
UnemploymentRate= UnemploymentRate.set_index('FIPS')

#%%
#b) TOTAL NON-FARM

#BLS limits API calls to 50, split request into two sets of 25 and 26
tnfsignature = json.dumps({'seriesid':list(seriesids['Total Non-Farm'][:25]),\
                           'startyear' :'2015', 'endyear':'2022',\
                          'registrationkey': api_key, 'calculations': True})
        
tnfsignature2 = json.dumps({'seriesid':list(seriesids['Total Non-Farm'][25:]),\
                           'startyear' :'2015', 'endyear':'2022',\
                          'registrationkey': api_key, 'calculations': True})

tnfp = requests.post('https://api.bls.gov/publicAPI/v2/timeseries/data/', \
                   data=tnfsignature, headers=headers)

tnfp2 = requests.post('https://api.bls.gov/publicAPI/v2/timeseries/data/', \
                   data=tnfsignature2, headers=headers)
tnfdata=json.loads(tnfp.text)
tnfdata2=json.loads(tnfp2.text)

#combine two results into one
tnfdata['Results']['series'].extend(tnfdata2['Results']['series'])


tnflist=[]
for state in tnfdata['Results']['series']:
    st= state['seriesID'][3:5] #pull state fips
    values={} #empty dictionary to store 3 values: Current Month, Jan 15, Jan 20
    for point in state['data']:
        if 'latest' in point:
            values.update(currentmonth = float(point['value'])) #current month to dictionary
            otm=float(point['calculations']['net_changes']['1']) #current  month otm
            otmpct=float(point['calculations']['pct_changes']['1']) #current month otm%
            oty=float(point['calculations']['net_changes']['12']) #current month oty
            otypct=float(point['calculations']['pct_changes']['12']) #current month oty%            
        elif (point['year'] == '2015' or point['year']=='2022') and point['period']=='M01':
            values.update({point['periodName']+' '+point['year']:float(point['value'])}) #adding Jan 15 and Jan 19
    tnflist.append((st, values['January 2015'], values['January 2022'],values['currentmonth'], otm, otmpct, oty, otypct))
    #all data points added to a tuple with fips. This tuple added to the tnflist
     
#convert the tnflist into a DataFrame
Tnf = pd.DataFrame(tnflist,\
                   columns=['FIPS', 'Jan 2015_TNF', 'January_TNF',\
                            'CurrentMonth_TNF', 'OTM_TNF', 'OTMPCT_TNF', 'OTY_TNF', 'OTYPCT_TNF'])
#Difference from January 2015 to current
Tnf['2015Diff_TNF']=Tnf.apply(lambda row: difference(row['CurrentMonth_TNF'],row['Jan 2015_TNF']), axis=1) 
#Difference from January 2019 to current
Tnf['Change_TNF']=Tnf.apply(lambda row: difference(row['CurrentMonth_TNF'], row['January_TNF']), axis=1)
#Percent change from January 2019 to current 
Tnf['ChangePct_TNF']=Tnf.apply(lambda row: row['Change_TNF']/float(row['January_TNF']), axis=1)
#Percent change from January 2015 to current
Tnf['2015DiffPct_TNF']=Tnf.apply(lambda row: row['2015Diff_TNF']/float(row['Jan 2015_TNF']), axis=1)
#List of Total Non-Farm indicators to be ranked
Tnftoberanked=['OTM_TNF', 'OTMPCT_TNF', 'OTY_TNF', 'OTYPCT_TNF', '2015Diff_TNF', 'Change_TNF'\
               ,'ChangePct_TNF', '2015DiffPct_TNF']
#for loop - creates columns in the DataFrame with the rankings for items in the 
#tnftoberanked list
for indicator in Tnftoberanked: 
    col=indicator+" rank"
    Tnf[col]=Tnf[indicator].rank(ascending=False, method='min')

#set the index to FIPS code, in order to join with other dataframe later
Tnf = Tnf.set_index('FIPS')

#c) TOTAL PRIVATE

#again, two API calls due to BLS limit of 50
tpsignature=json.dumps({'seriesid':list(seriesids['Total Private'][:25]),\
                        'startyear':'2015', 'endyear':'2022',\
                        'registrationkey':api_key, 'calculations': True})

tpsignature2=json.dumps({'seriesid':list(seriesids['Total Private'][25:]),\
                        'startyear':'2015', 'endyear':'2022',\
                        'registrationkey':api_key, 'calculations': True})
tpp = requests.post('https://api.bls.gov/publicAPI/v2/timeseries/data/', \
                   data=tpsignature, headers=headers)

tpp2 = requests.post('https://api.bls.gov/publicAPI/v2/timeseries/data/', \
                   data=tpsignature2, headers=headers)
tpdata=json.loads(tpp.text)
tpdata2=json.loads(tpp2.text)

#put the two results sets together into one
tpdata['Results']['series'].extend(tpdata2['Results']['series'])

tplist=[]
for state in tpdata['Results']['series']:
    st= state['seriesID'][3:5] #pull state fips 
    values={}  #empty dictionary to store 3 values: Current Month, Jan 15, Jan 20
    for point in state['data']:
        if 'latest' in point: 
            values.update(currentmonth = float(point['value'])) #current month to dictionary
            otm=float(point['calculations']['net_changes']['1']) #otm stored as variable
            otmpct=float(point['calculations']['pct_changes']['1']) #otm% stored as variable
            oty=float(point['calculations']['net_changes']['12']) #oty stored as variable
            otypct=float(point['calculations']['pct_changes']['12']) #oty% stored as variable            
        elif (point['year'] == '2015' or point['year']=='2022') and point['period']=='M01':
            #collect the Jan 2015 and Jan 2021 data, add to the dictionary
            values.update({point['periodName']+' '+point['year']:float(point['value'])})
    tplist.append((st, values['January 2015'], values['January 2022'],values['currentmonth'], otm, otmpct, oty, otypct))
           #all data points added to a tuple with fips. This tuple added to the tplist
#convert the tplist into a DataFrame
Tp = pd.DataFrame(tplist,\
                   columns=['FIPS', 'Jan 2015_TP', 'January_TP',\
                            'CurrentMonth_TP', 'OTM_TP', 'OTMPCT_TP', 'OTY_TP', 'OTYPCT_TP'])

Tp['2015Diff_TP']=Tp.apply(lambda row: difference(row['CurrentMonth_TP'],row['Jan 2015_TP']), axis=1) 

Tp['Change_TP']=Tp.apply(lambda row: difference(row['CurrentMonth_TP'], row['January_TP']), axis=1)

Tp['ChangePct_TP']=Tp.apply(lambda row: row['Change_TP']/float(row['January_TP']), axis=1)

Tp['2015DiffPct_TP']=Tp.apply(lambda row: row['2015Diff_TP']/float(row['Jan 2015_TP']), axis=1)

Tptoberanked=['OTM_TP', 'OTMPCT_TP', 'OTY_TP', 'OTYPCT_TP', '2015Diff_TP', 'Change_TP',\
              'ChangePct_TP', '2015DiffPct_TP']

for indicator in Tptoberanked: 
    col=indicator+" rank"
    Tp[col]=Tp[indicator].rank(ascending=False, method='min')

Tp = Tp.set_index('FIPS')
#%%3) ORGANIZE THE RESULTS INTO A DATAFRAME

SecChart = UnemploymentRate.join([Tnf, Tp])
SecChart['State']=SecChart.index.map(statesdict)
#organize the fields into the correcct order for the secretary's chart
OrderList=['State','CurrentMonth_UR', 'January_UR', 'Change_UR', 'Rank_UR', 'RankChange_UR',\
           'OTM_TNF', 'OTM_TNF rank', 'OTMPCT_TNF', 'OTMPCT_TNF rank', 'OTY_TNF',\
           'OTY_TNF rank', 'OTYPCT_TNF' , 'OTYPCT_TNF rank', 'OTM_TP', 'OTM_TP rank',\
           'OTMPCT_TP', 'OTMPCT_TP rank', 'OTY_TP', 'OTY_TP rank', 'OTYPCT_TP',\
           'OTYPCT_TP rank', 'January_TNF', 'CurrentMonth_TNF', 'Change_TNF', 'Change_TNF rank',\
           'ChangePct_TNF', 'ChangePct_TNF rank', 'January_TP', 'CurrentMonth_TP',\
           'Change_TP', 'Change_TP rank','ChangePct_TP', 'ChangePct_TP rank',\
           'Jan 2015_TNF','2015Diff_TNF', '2015Diff_TNF rank', '2015DiffPct_TNF', '2015DiffPct_TNF rank',\
           'Jan 2015_TP','2015Diff_TP', '2015Diff_TP rank', '2015DiffPct_TP', '2015DiffPct_TP rank']
SecChart=SecChart[OrderList].copy()

#%%4) EXPORT TO EXCEL

#identify the most recent period in each dataset to ensure data is up to date

datecheck = [('tp' ,tpdata['Results']['series'][0]['data'][0]['periodName'] + " "\
           + tpdata['Results']['series'][0]['data'][0]['year']),
           ('tnf', tnfdata['Results']['series'][0]['data'][0]['periodName'] + " "\
           + tnfdata['Results']['series'][0]['data'][0]['year']),
           ('UR', urdata['Results']['series'][0]['data'][0]['periodName'] + " "\
            + urdata['Results']['series'][0]['data'][0]['year'])]
datecheckdf = pd.DataFrame(datecheck, columns = ["Program", "Date"])
writer = pd.ExcelWriter('SecChartDec22.xlsx', engine = 'xlsxwriter')
datecheckdf.to_excel(writer, sheet_name="Check", index=False)
SecChart.to_excel(writer)
writer.save()

            
