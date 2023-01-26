from numpy import NaN
import requests
import pandas as pd
import pdfplumber
import matplotlib.pyplot as plt

year = ['2017','2018','2019','2020','2021','2022']##,
mnth = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
table_settings = {
    "vertical_strategy": "text",
    "horizontal_strategy": "text"
    }


def retrieve_month(mnth,year):
    if year>='2021' and (mnth in ['Jun','Jul','Aug','Sep','Oct','Nov','Dec'] or year>'2021'):
        usda_url = "https://www.fns.usda.gov/sites/default/files/media/file/CostofFood"+mnth+year+"LowModLib.pdf"
        fieldnames = pd.Series(['label','low_weekly','moderate_weekly','liberal_weekly','low_monthly','moderate_monthly','liberal_monthly'])
    else:
        usda_url = "https://www.fns.usda.gov/sites/default/files/media/file/CostofFood"+mnth+year+".pdf"
        fieldnames = pd.Series(['label','thrifty_weekly','low_weekly','moderate_weekly','liberal_weekly','thrifty_monthly','low_monthly','moderate_monthly','liberal_monthly'])
    
    #URL of the file to be downloaded 
    usda = requests.get(usda_url) # create HTTP response object
    usda_name = 'usda'+mnth+year+'.pdf'
    with open(usda_name,'wb') as f:
	    f.write(usda.content)

    pdf = pdfplumber.open(usda_name)
    bounding_box = (50, 150, 600, 375)
    table=pdf.pages[0].crop(bounding_box).extract_table(table_settings)
    #display(table[4])

    df_usdaSource = pd.DataFrame(table[1::],columns=fieldnames)

    df_usdaSource['modCost'] = 0.0

    for x in range(0, 18):
         if df_usdaSource['moderate_monthly'].iloc[x] not in ['','cost plan']:
            df_usdaSource['modCost'].iloc[x] = float(df_usdaSource['moderate_monthly'].iloc[x].replace('$',''))

    justRelevant = df_usdaSource[['label','modCost']]
    calcdAvg = justRelevant.groupby('label').mean('modCost')

    calcdAvg['gender'] = 'E'
    calcdAvg['vintage'] = mnth+year
    if mnth == 'Jan':
        calcdAvg['Date'] = year+'-01'
    elif mnth == 'Feb':
        calcdAvg['Date'] = year+'-02'
    elif mnth == 'Mar':
        calcdAvg['Date'] = year+'-03'
    elif mnth == 'Apr':
        calcdAvg['Date'] = year+'-04'
    elif mnth == 'May':
        calcdAvg['Date'] = year+'-05'
    elif mnth == 'Jun':
        calcdAvg['Date'] = year+'-06'
    elif mnth == 'Jul':
        calcdAvg['Date'] = year+'-07'
    elif mnth == 'Aug':
        calcdAvg['Date'] = year+'-08'
    elif mnth == 'Sep':
        calcdAvg['Date'] = year+'-09'
    elif mnth == 'Oct':
        calcdAvg['Date'] = year+'-10'
    elif mnth == 'Nov':
        calcdAvg['Date'] = year+'-11'
    elif mnth == 'Dec':
        calcdAvg['Date'] = year+'-12'
    calcdAvg['ageclass'] = calcdAvg.index

    return(calcdAvg)

outputfieldnames = pd.Series(['label','modCost','gender','vintage','Date','ageclass'])
outputDf = pd.DataFrame(columns=outputfieldnames)

for y in year:
    for x in mnth:
        dataframe = retrieve_month(x,y)
        outputDf=pd.concat([outputDf, dataframe])
        

chartDf = outputDf[['Date','ageclass','modCost']]

#chart it!
x = chartDf['Date'].drop_duplicates()
y01 = chartDf[chartDf['ageclass']=='1 year']['modCost']
y23 = chartDf[chartDf['ageclass']=='2-3 years']['modCost']
y45 = chartDf[chartDf['ageclass']=='4-5 years']['modCost']
y68 = chartDf[chartDf['ageclass']=='6-8 years']['modCost']
y911 = chartDf[chartDf['ageclass']=='9-11 years']['modCost']
y1213 = chartDf[chartDf['ageclass']=='12-13 years']['modCost']
y1418 = chartDf[chartDf['ageclass']=='14-18 years']['modCost']
y1950 = chartDf[chartDf['ageclass']=='19-50 years']['modCost']
y5170 = chartDf[chartDf['ageclass']=='51-70 years']['modCost']
y7199 = chartDf[chartDf['ageclass']=='71+ years']['modCost']


#ax = chartDf.plot.line(subplots=True, x='Year')
plt.plot(x, y23)
plt.plot(x, y68)
plt.plot(x, y911)
plt.plot(x, y1418)
plt.plot(x, y1950)


plt.show()

display('Finished!')
