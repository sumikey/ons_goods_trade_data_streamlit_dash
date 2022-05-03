 # imports
import requests
from bs4 import BeautifulSoup
import pandas as pd
from zipfile import ZipFile
from io import BytesIO
import glob
import streamlit as st
import pickle

def get_latest_onscbcex_zip_url():
    """A function to return a URL for the latest version of the ONS's Country by Commodity Exports data.
    Scrapes the relevant ONS webpage and returns the latest/current version."""
    
    # print output to show where in process
    print('Getting URL for latest ONS data')
    
    # ONS CBC url to scrape
    url = 'https://www.ons.gov.uk/economy/nationalaccounts/balanceofpayments/datasets/uktradecountrybycommodityexports/current'
    
    # download webpage
    # parse html
    doc = requests.get(url)
    soup = BeautifulSoup(doc.text, features="lxml")
    
    # find all the h3 elements as a list
    # take the index of the element whose text is latest version
    for index, entry in enumerate(soup.find_all('h3')):
        if entry.text == 'Latest version':
            i = index

    # construct a url from base plus the href
    # look in parent and then a within that parent
    file_url = 'https://www.ons.gov.uk' + soup.find_all('h3')[i].parent.a['href']
    
    return file_url

def get_historic_onscbcex_zip_url():
    """A function to return a url for the historic (1997-2017) version of ONS's Country by Commodity Exports data.
    Scrapes the relevant ONS webpage and returns the current historic version"""
    
    # print output to show where in process
    print('Getting URL for historic ONS data')
    
    # ONS source page url to scrape
    url = 'https://www.ons.gov.uk/economy/nationalaccounts/balanceofpayments/datasets/uktradecountrybycommodityexports'
    
    # download webpage
    # parse html
    req = requests.get(url)
    soup = BeautifulSoup(req.text, features="lxml")
    
    # create file url add_on based on html
    # add onto the base url
    file_url = soup.find_all('li', {'class':"margin-top--0 margin-bottom--0"})[0].a['href']
    new_url = 'https://www.ons.gov.uk' + file_url
    
    return new_url

def download_unzip_onscbcex(url, data_folder='Current'):
    """A function to download a latest copy of the ONS's Country by Commodity export data.
    Uses our get_latest_onscbcex_zip_url() function to get url, downloads with requests.
    Uses Zipfile and Bytes IO to unzip and save in folder /Data. """
    
    # print output to show where in process
    print('Beginning download and unzip of data files')
        
#     # Split URL to get the file name
#     filename = url.split('/')[-1]
    
    # Downloading the file by sending the request to the URL
    req = requests.get(url)
    print(f'Downloading {data_folder} Data Completed')
    
    # extracting the zip file contents
    zipped= ZipFile(BytesIO(req.content))
    zipped.extractall(f'Data/{data_folder}/')
    print(f'{data_folder} data extracted from zip and saved in Data/{data_folder} folder.')
    
    # empty return
    return

def create_single_dataframe():
    """Finds the filepaths of the recently downloaded current and historic excel files.
    Extracts relevant parts from excel files, and converts to dataframes.
    Merges the historic and current datasets, and returns merged df."""
    
    # print output to show where in process
    print('Beginning creation of single dataframe')
    
    # create filepath names using glob
    filepath_h = glob.glob('Data/Historic/'+'*.xlsx')[0]
    filepath_c = glob.glob('Data/Current/'+'*.xlsx')[0]
    
    # read in dataframes using pandas
    print('Converting excel files to pandas dataframes, may take a while')
    df_c = pd.read_excel(filepath_c,sheet_name='3. Monthly Exports', skiprows=3)
    df_h = pd.read_excel(filepath_h, sheet_name='1. Country by Commodity Export', skiprows=3)
    print('Dataframe converstion completed, merging')
    
    # merge the two dataframes, add current columns after historic
    df = pd.merge(df_h, df_c, on=['COMMODITY', 'COUNTRY','DIRECTION'])
    
    print('Completed')
    # return merged df
    return df

def fix_df_columns(df):
    """A function to fix the dataframe columns included by default on ONS Country by Commodity Exports dataset.
    Removes the country codes from inside the country names column, splits the commodity column into code and description,
    removes the codes from the direction column"""
    
    # print output to show where in process
    print('Preprocessing dataframe columns')
    
    # create a list of country names only with codes removed
    country_names_only = []
    for item in df.COUNTRY:
        country_names_only.append(item[3:])
    
    # create a list of flow names only with codes removed
    flow_names_only = []
    for item in df.DIRECTION:
        flow_names_only.append(item[3:])

    # split the commodity column into the code and description lists
    comm_codes = []
    comm_desc = []
    for item in df.COMMODITY:
        for i in range(1,6):
            if item[i] == ' ':
                comm_codes.append(item[:i])
                comm_desc.append(item[i:].strip())
    
    # use our lists to overwrite three old columns and add new one COMM_CODE
    df['COUNTRY'] = country_names_only
    df['COMMODITY'] = comm_desc
    df['COMM_CODE'] = comm_codes
    df['DIRECTION'] = flow_names_only
    
    # return the adjusted df
    return df

def df_to_MultiIndex_time_series(df):
    """Adds a list of multi-index column """
    
    # print output to show where in process
    print('Adding Multi-Index Columns')
    
    # create empty list
    list_tuples = []
    # create a list of tuples from the zipped columns
    for item in zip(df.COUNTRY,df.COMM_CODE, df.COMMODITY,df.DIRECTION):
        list_tuples.append( (item[0], item[1], item[2], item[3]) )
    # convert to multi_index object
    index_tuples = pd.MultiIndex.from_tuples(list_tuples)
    
    # remove our categorical columns which are now in Multi-Index
    df = df.iloc[:,3:].iloc[:,:-1]
    
    # attach our MultiIndex to dataframe
    df.index = index_tuples
    
    # transpose to have MultIndex columns and arranged as time series
    df=df.T
    
    # convert date strings into datetime-able format
    # perform datetime conversion
    df.index = [date[0:4]+'-'+date[4:] for date in df.index]
    df.index = pd.to_datetime(df.index)
    
    # return the altered index
    return df

def get_all_data():
    """Creates a dataframe with a multi-index header of UK exports to all countries.
    Based on ONS Country by commodity exports. Takes historic data and current data and combines.
    Outputs a single dataframe """
    
    # print output to show started
    print('Beginning process to get all data')
    
    # scrape relevant zips from ONS website
    hist_url = get_historic_onscbcex_zip_url()
    current_url = get_latest_onscbcex_zip_url()
    
    # download and unzip files, save excel files into folders
    download_unzip_onscbcex(hist_url, data_folder='Historic')
    download_unzip_onscbcex(current_url, data_folder='Current')
    
    # create a single dataframe from the historic and current excel files
    df = create_single_dataframe()
    
    # fix the columns
    # add MultiIndex column headers and convert to time-series with datetime
    df = fix_df_columns(df)
    df = df_to_MultiIndex_time_series(df)
    
    # save df as a pick object so maintain multi-headers
    df.to_pickle('./Data/Dataframe/ons_df.pkl')
    
    # print output to say completed
    print('Completed process to get all data')
      
    # empty return
    return

def add_non_volatile_col(df):
    """Adds a column of exports of Non-Volatile goods (total goods minus fuels and unspecified goods).
    For each column in dataframe. Returns new dataframe with nv columns added on"""
    
    # Add a prrint statement so can see function being called.
    print('Calculating and adding non-volatile goods exports columns')
    
    # get our partner list from pkl file
    open_file=open('./Data/pkl_lists/partner_list.pkl', 'rb')
    partner_list = pickle.load(open_file)
    open_file.close()
    
    # enter for loop to cycle through all partner names
    for partner in partner_list:
        # create a temporary dataframe for that partner only
        # keep only the commodity code headers
        # remove commodity description and flow headers
        temp_df = (
                    df.xs(partner, axis=1, level=0)
                      .droplevel(axis=1, level=1)
                      .droplevel(axis=1, level=1)
                   )
        # create a new series of total minus '3' (Fuels) and '9' (Unspecified Goods)
        # use astype(float) to handle some values interpreted as strings
        series_nv = temp_df['T'] -temp_df['3'] -temp_df['9']
        # convert this series to a dataframe, transpose it for Multi-index adding
        df_nv = pd.DataFrame(series_nv).T
        # set the index to a multi-index object with partner name and Non-Volatile relevant terms
        df_nv.index = pd.MultiIndex.from_tuples([[partner, 'NV', 'Non-Volatile Goods', 'Exports']])
        # concatenate our new nv series df onto old df2
        # assign back to df so can pickup and add on next loop
        df = pd.concat([df, df_nv.T], axis=1)
    
    # return our df with the newly added Non-Volatile columns
    return df

def get_test_data():
    """A temporary function for loading data from our test csv dataset.
    Then performs our fixes and shaping. Convert everything to numeric,
    add in new columns for non-volatile goods trade"""
    
    # read in csv file
    df = pd.read_csv('ons_csv_test.csv')
    
    # fix the columns
    # add MultiIndex column headers and convert to time-series with datetime
    df = fix_df_columns(df)
    df = df_to_MultiIndex_time_series(df)
    
    # convert everything to numeric
    df = df.apply(pd.to_numeric, errors='coerce')
    # and fill NaNs from error coercion
    df.fillna(0, inplace=True)
    
    # add our non-volatile columns onto it
    df = add_non_volatile_col(df)
    
    return df
    
    
    