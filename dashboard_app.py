## IMPORTS

import pandas as pd
import streamlit as st
import ons_data_collection
import pickle

#--------------------------------------------------------------------

### LOADING DATA ###

# This code is not currently being used as was affecting online deployment
# # import our ONS data which is already saved in dataframe pkl file
# try: 
#     df = 
# except:
#     ons_data_collection.get_all_data()
#     df = pd.read_pickle('./Data/Dataframe/ons_df.pkl')

# # set a start parameter with an experimental memo cacher
# @st.experimental_memo
# def start():
#     ons_data_collection.get_all_data()
#     df = pd.read_pickle('ons_df.pkl')
#     return df

# # This is a temporary piece of code to allow for deployment from static .csv
# def get_test_data():
#     # read in csv file
#     df = pd.read_csv('ons_csv_test.csv')
#     # fix the columns
#     # add MultiIndex column headers and convert to time-series with datetime
#     df = ons_data_collection.fix_df_columns(df)
#     df = ons_data_collection.df_to_MultiIndex_time_series(df)
#     return df

#### IGNORE FOR NOW

# # starting function
# def get_test_data():
#     """A temporary function for loading data from our test csv dataset.
#     Then performs our fixes and shaping. Convert everything to numeric,
#     add in new columns for non-volatile goods trade"""
    
#     # read in csv file
#     df = pd.read_csv('ons_csv_test.csv')
    
#     # fix the columns
#     # add MultiIndex column headers and convert to time-series with datetime
#     df = ons_data_collection.fix_df_columns(df)
#     df = ons_data_collection.df_to_MultiIndex_time_series(df)
    
#     # convert everything to numeric
#     df = df.apply(pd.to_numeric, errors='coerce')
#     # and fill NaNs from error coercion
#     df.fillna(0, inplace=True)
    
#     # add our non-volatile columns onto it
#     df = ons_data_collection.add_non_volatile_col(df)
    
#     return df


#--------------------------------------------------------------------

### LOADING LISTS FROM PRE-BUILD PICKLE FILES ###

# get our commodity list from pkl file
# this is constructed from original dataframe, taking unique entries
open_file=open('./Data/pkl_lists/commodity_list.pkl', 'rb')
commodity_list = pickle.load(open_file)
open_file.close()
# add on a term Non-Volatile Goods, a category we have calculated and added
# sort it again alphabetically
commodity_list.append('Non-Volatile Goods')
commodity_list.sort()

# get our partner list from pkl file
open_file=open('./Data/pkl_lists/partner_list.pkl', 'rb')
partner_list = pickle.load(open_file)
open_file.close()

#--------------------------------------------------------------------

### SET INTO WIDE MODE
### set page config must be called as first streamlit command

# setting the page title, icon and opening in wide mode
st.set_page_config(page_title = "UK Goods Exports", page_icon = 'uk',layout="wide")

#--------------------------------------------------------------------

### LOADING IN DATA FROM OUR TEST FILE

# setup a function to load in data and preprocess that can be cached
# show spinner as False to remove yellow notification from top
@st.cache(show_spinner=False)
def start_dashboard():
    df = ons_data_collection.get_test_data()
    return df

# start it
df = start_dashboard()

#--------------------------------------------------------------------

### SETTING MAIN TITLE AND INTRO TEXT ###

# title
st.write("""
# UK Goods Exports  
#### Data: [ONS: Trade in goods: country-by-commodity exports](https://www.ons.gov.uk/economy/nationalaccounts/balanceofpayments/datasets/uktradecountrybycommodityexports)""")

#intro
st.write("""
##### This dashboard is for analysing UK goods exports to different trading partners around the world. The first section looks at the UK's overall goods exports to a chosen trade partner. The second section looks at overall UK exports to that same partner by SITC 1 digit product categories. The third section compares UK exports to a chosen partner and product to a range of other trading partners. The fourth section allow comparisons of exports of several different products to a single partner. The fifth sections allows comparisons across (customisable groupings of trade partners). In sections 3 and 4, products can be chosen across a range of SITC 1, 2 and 3 digit codes, as published by the ONS within this dataset. By default all charts are on a 12 month rolling sum basis, but the degree of rolling can be set in the sidebar and rolling can be set as "1" to explore only monthly values. Minimum and maximum date ranges for the charts can be set using the sliders in the sidebar. Side bar sliders control all the visuals at once.

---
""")

#--------------------------------------------------------------------

## SETTING UP THE FIRST THREE PLOTS FOR TOTAL EXPORTS

# setting up select boxes for our list of partners and trade products
partner_select = st.selectbox('Which main trade partner do you want to analyse?', partner_list, index = partner_list.index('Whole world') )

# choosing whether want to look at total or non-volatile goods
ttl_or_nonv_select = st.selectbox('Do you want to look at total goods or non-volatile goods? (i.e. excluding Fuels & Unspecified Goods)',
                                 ['Total', 'Non-Volatile Goods'],
                                 index = 0)

# use these values to filter df for first two charts
plot_df = (df.xs(partner_select, axis=1, level=0)
             .xs(ttl_or_nonv_select, axis=1, level=1)
          )

# rename the columns to the partner name
plot_df.columns = [partner_select]

# setting up a slider to choose rolling level
rol_val = st.sidebar.slider('Monthly Rolling Sum (set as "1" for no rolling)', min_value=1, max_value=12, value=12)
plot_df = plot_df.rolling(rol_val).sum().dropna() # edit the plotting df accordingly

# setting a yearly range to be diplayed on the axis
# set as two separate slides for min and max
min_year = st.sidebar.slider('Date Range - Minimum', 
                               min_value=plot_df.index.min().year, 
                               max_value=plot_df.index.max().year,
                               value=2016
                              )

max_year = st.sidebar.slider('Date Range - Maximum', 
                               min_value=plot_df.index.min().year, 
                               max_value=plot_df.index.max().year,
                              value=2022
                              )
# convert the min and max years to strings so can use with .loc to index plots for x-axis
min_year = str(min_year)
max_year = str(max_year)

# write a title for the first section
st.write(
f"""
---
##### UK {ttl_or_nonv_select}  Exports to {partner_select} """)

# create plotting dfs that are filtered by year range
plot_abs_df = plot_df.round(1).loc[min_year:max_year] # our plot for absolute values
plot_diff_df = plot_df.diff(12).round(1).loc[min_year:max_year] # our plot for absolute values
plot_percent_df = plot_df.pct_change(12).mul(100).dropna().round(1).loc[min_year:max_year] # our plot for yoy change

# add in some auto-generated text showing the latest figures based on various sliders

# first set a 'shift' word to based on if increase or decrease
# note the odd spacing and extra 'n' to handle language
shift = 'n increase' if plot_diff_df.iloc[-1,0] > 0 else ' decrease'

# setup two separate statements for if rolling is on (rol_val>1) or off
# for each
    # first line handles month and timeframe
    # second line handles the type, partner and total amount
    # third line handles whether year on year increase or decrease and by how much
if rol_val>1:
    st.write(f"""> **Over the {rol_val} months through to {plot_abs_df.index[-1].month_name()} {plot_abs_df.index[-1].year}, UK {ttl_or_nonv_select} exports to {partner_select} reached £{round(plot_abs_df.iloc[-1,0]/1_000, 2)} billion. This represents a{shift} of {round(plot_percent_df.iloc[-1,0], 1)}% (or £{round(abs(plot_diff_df.iloc[-1,0]/1_000), 2)} billion) year-on-year.**""")
else:
    st.write(f"""> **In {plot_abs_df.index[-1].month_name()} {plot_abs_df.index[-1].year}, UK {ttl_or_nonv_select} exports to {partner_select} reached £{round(plot_abs_df.iloc[-1,0]/1_000, 2)} billion. This represents a{shift} of {round(plot_percent_df.iloc[-1,0], 1)}% (or £{round(abs(plot_diff_df.iloc[-1,0]/1_000), 2)} billion) year-on-year.**""")

# add an extra empty line for spacing
st.write(' ')
    
# create three separate columns
cola1, cola2, cola3 = st.columns((1,1,1))

with cola1: 
    # plot a line chart of monthly absolute values
    if rol_val > 1:
        st.write(f"UK {ttl_or_nonv_select} exports to {partner_select}, rolling {str(rol_val)}M sum, £s millions") #title
    else:
        st.write(f"UK {ttl_or_nonv_select} exports to {partner_select}, monthly, £s millions")
    st.line_chart(plot_abs_df)           #line chart
    

with cola2: 
    # plot a line chart of gbp yoy change
    if rol_val > 1:
        st.write(f"UK {ttl_or_nonv_select} exports to {partner_select}, rolling {str(rol_val)}M sum, £ millions change yoy") #title
    else:
        st.write(f"UK {ttl_or_nonv_select} exports to {partner_select}, monthly, £s millions change yoy")
    st.line_chart(plot_diff_df)           #line chart

with cola3:
    # plot a line of monthly yoy % change
    if rol_val > 1:
        st.write(f"UK {ttl_or_nonv_select} exports to {partner_select}, rolling {str(rol_val)}M sum, % change yoy") #title
    else:
        st.write(f"UK {ttl_or_nonv_select} exports to {partner_select}, monthly, % change yoy")
    st.line_chart(plot_percent_df)


st.write("""> *This section shows the UK's total (or Non-volatile goods) exports to the selected partner based on the selections made above. The charts show the total value, the yoy change in £s and the yoy change in % terms. By default, values are set to rolling 12 month sums, but the degree of rolling can be lowered using the slider in the sidebar. If rolling is set equal to '1', monthly values will be shown. The number of years shown can also be controlled by the sliders in the sidebar.*""")

#--------------------------------------------------------------------
   
### SETTING UP THE SECOND THREE PLOTS FOR EXPORTS BY SITC 1-DIGIT
    
# create a list of codes for the SITC one-digit categories
if ttl_or_nonv_select == 'Total':
    sitc1_list = ['1','2','3','4','5','6','7','8','9']
elif ttl_or_nonv_select == 'Non-Volatile Goods':
    sitc1_list = ['1','2','4','5','6','7','8']
    
# index our df using the new sitc list and our selected partner
# Transpose the df, use pd index slice and transpose back
idx = pd.IndexSlice
plot_sitc1_df = df.T.loc[idx[partner_select,sitc1_list,:,:] ,:].T

# create a list of names from the comm_desc part of our multi-index with list comprehension
# set this list of names as the column names
sitc_1dig_names = [x[2] for x in plot_sitc1_df.columns]
plot_sitc1_df.columns = sitc_1dig_names

# add the page-wide rolling factor to our plot
plot_sitc1_df2 = plot_sitc1_df.rolling(rol_val).sum().dropna() # edit the plotting df accordingly

# create three new plot dfs using this newly subsetted dataframe
plot_sitc1_abs_df = plot_sitc1_df2.round(1).loc[min_year:max_year] # for plotting absolute values
plot_sitc1_diff_df = plot_sitc1_df2.diff(12).round(1).loc[min_year:max_year] # for plotting absolute values
plot_sitc1_percent_df = plot_sitc1_df2.pct_change(12).mul(100).dropna().round(1).loc[min_year:max_year] # the % change yoy

# creating a title for the second section
st.write(
f"""
---
##### UK {ttl_or_nonv_select} Exports to {partner_select} by SITC 1 Digit Code.""")

# create two dataframes based on the last row of the absolute and diff plot dataframes
# sort by descending value
# label as text because we are using for text description
abs_text_df = plot_sitc1_abs_df.iloc[-1,:].T.sort_values(ascending=False)    
diff_text_df = plot_sitc1_diff_df.iloc[-1,:].T.sort_values(ascending=False)

# work out the sign (+ or -) of strongest and weakest performers
# save sign as a string for using in our text
sign_strong = '+' if diff_text_df.iloc[0] > 0 else '-'
sign_weak = '+' if diff_text_df.iloc[-1] > 0 else '-'

# write two cases, one for if rolling is on or off
# for each:
    # state the period in question and total exports over that period
    # write the three largest export categories over that period, using new abs_text_df
    # then add in our strongest and weakest performer from sorted diff_text_df
    # use our created sign_strong and sign_weak to handle text (and make values absolutes)
    
if rol_val>1:
    st.write(f"""> **Over the {rol_val} months through to {plot_abs_df.index[-1].month_name()} {plot_abs_df.index[-1].year}, UK {ttl_or_nonv_select} exports to {partner_select} reached £{round(plot_abs_df.iloc[-1,0]/1_000, 2)} billion. Over this period, the UK's largest exports to {partner_select} were {abs_text_df.index[0]} (£{abs_text_df.iloc[0]}m), {abs_text_df.index[1]} (£{abs_text_df.iloc[1]}m), and {abs_text_df.index[2]} (£{abs_text_df.iloc[2]}m). The strongest performing  category was {diff_text_df.index[0]} ({sign_strong}£{abs(diff_text_df.iloc[0])}m yoy), and the weakest performing category was {diff_text_df.index[-1]} ({sign_weak}£{abs(diff_text_df.iloc[-1])}m yoy).**""")

else:
    st.write(f"""> **In {plot_abs_df.index[-1].month_name()} {plot_abs_df.index[-1].year}, UK {ttl_or_nonv_select} exports to {partner_select} reached £{round(plot_abs_df.iloc[-1,0]/1_000, 2)} billion. In that month, the UK's largest exports to {partner_select} were {abs_text_df.index[0]} (£{abs_text_df.iloc[0]}m), {abs_text_df.index[1]} (£{abs_text_df.iloc[1]}m), and {abs_text_df.index[2]} (£{abs_text_df.iloc[2]}m). The strongest performing  category was {diff_text_df.index[0]} ({sign_strong}£{abs(diff_text_df.iloc[0])}m yoy), and the weakest performing category was {diff_text_df.index[-1]} ({sign_weak}£{abs(diff_text_df.iloc[-1])}m yoy).**""")

# setting up the multi-selector for which SITC 1 digit codes to include
sitc1_abs_list = st.multiselect('Select SITC 1 digit categories to include in charts', sitc_1dig_names, default=sitc_1dig_names)

# create three separate columns
colb1, colb2, colb3 = st.columns((1,1,1))

# plot relevant chart in each column: 1. absolute, 2. yoy diff, 3. % change yoy
with colb1: 
    # plot a bar chart of monthly absolute values
    # handle titles depending on opage-wide rolling factor
    if rol_val > 1:
        st.write(f"UK {ttl_or_nonv_select} exports to {partner_select} by SITC 1 Digit, rolling {str(rol_val)}M sum, £s millions") #title
    else:
        st.write(f"UK {ttl_or_nonv_select} exports to {partner_select} by SITC 1 Digit, monthly, £s millions")   
    st.bar_chart(plot_sitc1_abs_df[sitc1_abs_list]) #line chart
    

with colb2: 
    # plot a bar chart of monthly absolute values
    # handle titles depending on opage-wide rolling factor
    if rol_val > 1:
        st.write(f"UK {ttl_or_nonv_select} exports to {partner_select} by SITC 1 Digit, rolling {str(rol_val)}M sum, £s millions yoy change") #title
    else:
        st.write(f"UK {ttl_or_nonv_select} exports to {partner_select} by SITC 1 Digit, monthly, £s millions yoy change")
    st.bar_chart(plot_sitc1_diff_df[sitc1_abs_list])           #line chart

with colb3: 
    # plot a bar chart of monthly absolute values
    # handle titles depending on opage-wide rolling factor
    if rol_val > 1:
        st.write(f"UK {ttl_or_nonv_select} exports to {partner_select} by SITC 1 Digit, rolling {str(rol_val)}M sum, % yoy change") #title
    else:
        st.write(f"UK {ttl_or_nonv_select} exports to {partner_select} by SITC 1 Digit, monthly, % yoy change")
    st.line_chart(plot_sitc1_percent_df[sitc1_abs_list])           #line chart


st.write("""> *This section shows the UK's total (or Non-volatile goods) exports to the selected partner based on the selections made, by SITC 1 digit codes. SITC 1 digit categories can be turned on/off using the multi-selector. If analysing 'Non-Volatile' goods, Fuels (SITC '3') and Unspecified Goods (SITC '9') will not be available in the multi-selector. The charts show the total value, the yoy change in £s and the yoy change in % terms. By default, values are set to rolling 12 month sums, but the degree of rolling can be lowered using the slider in the sidebar. If rolling is set equal to '1', monthly values will be shown. The number of years shown can also be controlled by the sliders in the sidebar.*""")
    
#--------------------------------------------------------------------
   
### SETTING UP THE THIRD THREE PLOTS FOR COMPARING BY CHOSEN PRODUCT

# write the title and intro for section 3
st.write(
f"""
---  
##### UK exports to multiple partners, for selected product category
This section shows the UK's exports of the selected product categoory to the range of selected partners by the total value, 
the yoy change in £s and the yoy change in % terms. The product category and comparison partners can be set using the options. 
The number of months over which to roll values can be changed, or turned off entirely, within the side bar.
"""
)

# setup a list of starting comparitors
if partner_select != 'Whole world':
    comparitors = [partner_select, 'Whole world', 'Total EU(28)', 'Extra EU 28 (Rest of World)']
else:
    comparitors = ['Whole world', 'Total EU(28)', 'Extra EU 28 (Rest of World)']

# setup a list of codes + descriptions concatenated together from headers
# will use this to construct a unique list
# and then a dictionary so can use selection from this list to do the subsetting on desc header
list_tuples_codeDesc_desc = [(header[1] +' : ' +header[2],   # tuple part one - code + description
                              header[2])                    # tuple part 2 - description
                             for header in df.columns]
# use set to get the unique values, and make a list again
list_set_tuples_codeDesc_desc = list(set(list_tuples_codeDesc_desc))

# get list of codes concatentenated with descriptions for multi-selector
# then sort it in ascending order
codes_desc_list = [item[0] for item in list_set_tuples_codeDesc_desc]
codes_desc_list.sort()

# creating the dictionary which will use to get desc for codeDesc, to subset our headers
dict_codeDesc_desc = {item[0]:item[1] for item in list_set_tuples_codeDesc_desc}

# create a selectbox for choosing commodity to look at comparison chart for
product_select_codeDesc = st.selectbox('Select a product to compare across partners', codes_desc_list, index= codes_desc_list.index('T : Total'))

# convert this to a description only which we can use to subset headers, using our dict
product_select = dict_codeDesc_desc[product_select_codeDesc]

# setting up the trading partner multi-selector
multipartner_select = st.multiselect('Select trade partners to include', partner_list, default=comparitors)

# index our dataframe using our selections
# need to transpose once and then back again.
# use colons (:) to pick all instances for code and flow index
idx = pd.IndexSlice
plot_compare_partner_df = df.T.loc[idx[multipartner_select,:,product_select,:] ,:].T

# create a list of names from the comm_desc part of our multi-index
# set this list of names as the column names
compare_partner_names = [x[0] for x in plot_compare_partner_df.columns]
plot_compare_partner_df.columns = compare_partner_names

# add the rolling factor to our plotting df
plot_compare_partner_df = plot_compare_partner_df.rolling(rol_val).sum().dropna() # edit the plotting df accordingly

# create three new plot dfs using this newly subsetted dataframe
plot_compare_partner_abs_df = plot_compare_partner_df.round(1).loc[min_year:max_year] # for plotting absolute values
plot_compare_partner_diff_df = plot_compare_partner_df.diff(12).dropna().round(1).loc[min_year:max_year] # for plotting absolute values
plot_compare_partner_percent_df = plot_compare_partner_df.pct_change(12).mul(100).dropna().round(1).loc[min_year:max_year] # the % change yoy

# create three separate columns
colc1, colc2, colc3 = st.columns((1,1,1))

# plot a separate chart in each column
with colc1: 
    # plot a line chart of monthly absolute values
    # handle titles depending on the rolling factor
    if rol_val > 1:
        st.write(f"UK {product_select} exports to {partner_select}, rolling {str(rol_val)}M sum, £s millions") #title
    else:
        st.write(f"UK {product_select} exports to {partner_select}, monthly, £s millions")
    st.line_chart(plot_compare_partner_abs_df)           #line chart

with colc2: 
    # plot a line chart of gbp yoy change
    # handle titles depending on the rolling factor
    if rol_val > 1:
        st.write(f"UK {product_select} exports to {partner_select}, rolling {str(rol_val)}M sum, £s millions change yoy") #title
    else:
        st.write(f"UK {product_select} exports to {partner_select}, £s millions change yoy")
    st.line_chart(plot_compare_partner_diff_df)           #line chart

with colc3:
    # plot a line of monthly yoy % change
    # handle titles depending on the rolling factor
    if rol_val > 1:
        st.write(f"UK {product_select} exports to {partner_select}, rolling {str(rol_val)}M sum, % change yoy") #title
    else:
        st.write(f"UK {product_select} exports to {partner_select}, monthly, % change yoy")
    st.line_chart(plot_compare_partner_percent_df)

#--------------------------------------------------------------------

### SETTING UP THE FOURTH THREE PLOTS FOR COMPARING BY CHOSEN PRODUCT

# write the title and intro for section 3
st.write(
f"""
---  
##### UK exports of multiple products, for selected a selected partner
This section shows the UK's exports of the selected trade partner for a range of different commodities by the total value, 
the yoy change in £s and the yoy change in % terms. The product category and comparison partners can be set using the options. 
The number of months over which to roll values can be changed, or turned off entirely, within the side bar.
"""
)

# create a selectbox for choosing commodity to look at comparison chart for
mulprod_partner_select = st.selectbox('Choose which partner you want to compare products', partner_list, index= partner_list.index(partner_select))

# create a list of default products for our multi-select box
default_product_multi_select = ['NV : Non-Volatile Goods', 'T : Total']

# create a multi-select box using our codes+desc list
mulprod_codesDesc_product_select = st.multiselect('Which products would you like to compare?', codes_desc_list, default=default_product_multi_select)

# convert this to a description only which we can use to subset headers, using our dict
# use a list comprehension so can take in and give out a list
mulprod_product_select = [dict_codeDesc_desc[product] for product in mulprod_codesDesc_product_select]

# index our dataframe using our selections
# need to transpose once and then back again.
# use colons (:) to pick all instances for code and flow index
idx = pd.IndexSlice
plot_compare_product_df = df.T.loc[idx[mulprod_partner_select,:,mulprod_product_select,:] ,:].T

# create a list of names from the comm_desc part of our multi-index
# set this list of names as the column names
compare_names = [x[2] for x in plot_compare_product_df.columns]
plot_compare_product_df.columns = compare_names

# add the rolling factor to our plotting df
plot_compare_product_df = plot_compare_product_df.rolling(rol_val).sum().dropna() # edit the plotting df accordingly

# create three new plot dfs using this newly subsetted dataframe
plot_compare_product_abs_df = plot_compare_product_df.round(1).loc[min_year:max_year] # for plotting absolute values
plot_compare_product_diff_df = plot_compare_product_df.diff(12).dropna().round(1).loc[min_year:max_year] # for plotting absolute values
plot_compare_product_percent_df = plot_compare_product_df.pct_change(12).mul(100).dropna().round(1).loc[min_year:max_year] # the % change yoy

# create three separate columns
cold1, cold2, cold3 = st.columns((1,1,1))

# create a product string name for inserting into title
# take the list of descriptions (without codes) add then together with an "and" for the last one
multiprod_title_string = ''   # empty string
multiprod_counter = 0         # setup a counter at zero
if len(mulprod_product_select) > 1:           # if more than one selected
    for item in mulprod_product_select[:-1]:  # for everything before last ter
        if multiprod_counter == 0:            # for first term just equals the name
            multiprod_title_string = item
            multiprod_counter += 1                       
        else:                                 # for everything else, previous name + comma + new name
            multiprod_title_string = multiprod_title_string +', ' +item
            multiprod_counter += 1
    multiprod_title_string = multiprod_title_string +' and ' +mulprod_product_select[-1]   # add the final name with an and
else:                                         # for when only one thing selected
    multiprod_title_string = str(mulprod_product_select[0])

# plot a separate chart in each column
with cold1: 
    # plot a line chart of monthly absolute values
    # handle titles depending on the rolling factor
    if rol_val > 1:
        st.write(f"UK exports to {mulprod_partner_select} of {multiprod_title_string}, rolling {str(rol_val)}M sum, £s millions") #title
    else:
        st.write(f"UK exports to {mulprod_partner_select} of {multiprod_title_string}, monthly, £s millions")
    st.line_chart(plot_compare_product_abs_df)           #line chart

with cold2: 
    # plot a line chart of gbp yoy change
    # handle titles depending on the rolling factor
    if rol_val > 1:
        st.write(f"UK exports to {mulprod_partner_select} of {multiprod_title_string}, rolling {str(rol_val)}M sum, £s millions change yoy") #title
    else:
        st.write(f"UK exports to {mulprod_partner_select} of {multiprod_title_string}, £s millions change yoy")
    st.line_chart(plot_compare_product_diff_df)           #line chart

with cold3:
    # plot a line of monthly yoy % change
    # handle titles depending on the rolling factor
    if rol_val > 1:
        st.write(f"UK exports to {mulprod_partner_select} of {multiprod_title_string}, rolling {str(rol_val)}M sum, % change yoy") #title
    else:
        st.write(f"UK exports to {mulprod_partner_select} of {multiprod_title_string}, monthly, % change yoy")
    st.line_chart(plot_compare_product_percent_df)

    
st.write('---')
    
#--------------------------------------------------------------------

### SETTING UP THE FIFTH THREE PLOTS FOR COMPARING A GROUP FOR A CHOSEN PRODUCT

# write the title and intro for section 3
st.write(
f"""
---  
##### Analysing Custom Trade Partner Groups, for a chosen product.
This section shows the UK's exports of the selected commodity to customisable groupings of trade partners. The charts show the absolute volume of exports, the yoy change in £s and the yoy change in % terms. The product category can be chosen using the customs slider. 
Custom trade partner groupings can be made using the multi-select box, and each grouping can be given it's own custom name.
The number of months over which to roll values can be changed, or turned off entirely, within the side bar.
"""
)

# setup a list of codes + descriptions concatenated together from headers
# will use this to construct a unique list
# and then a dictionary so can use selection from this list to do the subsetting on desc header
list_tuples_codeDesc_desc = [(header[1] +' : ' +header[2],   # tuple part one - code + description
                              header[2])                    # tuple part 2 - description
                             for header in df.columns]
# use set to get the unique values, and make a list again
list_set_tuples_codeDesc_desc = list(set(list_tuples_codeDesc_desc))

# get list of codes concatentenated with descriptions for multi-selector
# then sort it in ascending order
codes_desc_list = [item[0] for item in list_set_tuples_codeDesc_desc]
codes_desc_list.sort()

# creating the dictionary which will use to get desc for codeDesc, to subset our headers
dict_codeDesc_desc = {item[0]:item[1] for item in list_set_tuples_codeDesc_desc}

# create a selectbox for choosing commodity to look at comparison chart for
group_product_select_codeDesc = st.selectbox('Select a product to compare across partner groupings', codes_desc_list, index= codes_desc_list.index('T : Total'))

# convert this to a description only which we can use to subset headers, using our dict
group_product_select = dict_codeDesc_desc[group_product_select_codeDesc]

cole1, cole2, cole3 = st.columns((1,1,1))

with cole1:
    group1_partners = st.multiselect('Select trade partners to include in Group 1', partner_list, default=['China', 'Hong Kong', 'Macao'])
    group1_name = st.text_input('Give your first group a custom name (optional)',value='Group 1')

with cole2:
    group2_partners = st.multiselect('Select trade partners to include in Group 2', partner_list, default=['United States inc Puerto Rico', 'Canada'])
    group2_name = st.text_input('Give your second group a custom name (optional)',value='Group 2')
    
with cole3:
    group3_partners = st.multiselect('Select trade partners to include in Group 3', partner_list, default=['Germany', 'France','Italy','Netherlands'])
    group3_name = st.text_input('Give your third group a custom name (optional)',value='Group 3')

# index our dataframe using our selections
# need to transpose once and then back again.
# use colons (:) to pick all instances for code and flow index
# sum these to get aggregates for each of our groups
idx = pd.IndexSlice
group1_series = df.T.loc[idx[group1_partners,:,group_product_select,:] ,:].sum()
group2_series = df.T.loc[idx[group2_partners,:,group_product_select,:] ,:].sum()
group3_series = df.T.loc[idx[group3_partners,:,group_product_select,:] ,:].sum()

# turn these three series into a dataframe
group_df = group1_series.to_frame()
group_df['col2'] = group2_series
group_df['col3'] = group3_series

# and use our custom names to rename columns
group_df.columns = [group1_name, group2_name, group3_name]

# add the rolling factor to our plotting df
group_df = group_df.rolling(rol_val).sum().dropna() # edit the plotting df accordingly

plot_group_abs_df = group_df.round(1).loc[min_year:max_year] # for plotting absolute values
plot_group_diff_df = group_df.diff(12).dropna().round(1).loc[min_year:max_year] # for plotting absolute values
plot_group_percent_df = group_df.pct_change(12).mul(100).dropna().round(1).loc[min_year:max_year] # the % change yoy

# create three separate columns
colf1, colf2, colf3 = st.columns((1,1,1))

# plot a separate chart in each column
with colf1: 
    # plot a line chart of monthly absolute values
    # handle titles depending on the rolling factor
    if rol_val > 1:
        st.write(f"UK {product_select} exports to chosen groupings, rolling {str(rol_val)}M sum, £s millions") #title
    else:
        st.write(f"UK {product_select} exports to chosen groupings, monthly, £s millions")
    st.line_chart(plot_group_abs_df)           #line chart

with colf2: 
    # plot a line chart of gbp yoy change
    # handle titles depending on the rolling factor
    if rol_val > 1:
        st.write(f"UK {product_select} exports to chosen groupings, rolling {str(rol_val)}M sum, £s millions change yoy") #title
    else:
        st.write(f"UK {product_select} exports to chosen groupings, £s millions change yoy")
    st.line_chart(plot_group_diff_df)           #line chart

with colf3:
    # plot a line of monthly yoy % change
    # handle titles depending on the rolling factor
    if rol_val > 1:
        st.write(f"UK {product_select} exports to chosen groupings, rolling {str(rol_val)}M sum, % change yoy") #title
    else:
        st.write(f"UK {product_select} exports to chosen groupings, monthly, % change yoy")
    st.line_chart(plot_group_percent_df)

st.write('---')

    
    
#ENDS#



