import pandas as pd
import streamlit as st
import ons_data_collection
import pickle

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

def get_test_data():
    # read in csv file
    df = pd.read_csv('ons_csv_test.csv')
    # fix the columns
    # add MultiIndex column headers and convert to time-series with datetime
    df = ons_data_collection.fix_df_columns(df)
    df = ons_data_collection.df_to_MultiIndex_time_series(df)
    return df

# start it
df = get_test_data()
    
# get our commodity list from pkl file
open_file=open('./Data/pkl_lists/commodity_list.pkl', 'rb')
commodity_list = pickle.load(open_file)
open_file.close()

# get our partner list from pkl file
open_file=open('./Data/pkl_lists/partner_list.pkl', 'rb')
partner_list = pickle.load(open_file)
open_file.close()

st.write("""
# UK Goods Exports  

#### Data: [ONS: Trade in goods: country-by-commodity exports](https://www.ons.gov.uk/economy/nationalaccounts/balanceofpayments/datasets/uktradecountrybycommodityexports)
The data underlying this dashboard is pulled directly from the ONS's website, it may take a while to load upon first opening the website. 

This dashboard is for analysing UK goods exports to different trading partners around the world. The first section looks at the UK's total goods exports to the selected trade partner. The second section looks at UK exports to that same partner by SITC 1 digit product categories, products to be included can be turned on/off via the multi-selector. The third section compares UK exports of the selected partner and product to a range of other trading partners. By default all charts are on a monthly basis but rolling monthly values can be set using the slides in the page's sidebar. Minimum and maximum date ranges for the charts can be set using the sliders in the sidebar. Side bar sliders controll all the visuals at once.

---

""")

## SETTING UP THE FIRST THREE PLOTS FOR TOTAL EXPORTS

# setting up select boxes for our list of partners and trade products
partner_select = st.selectbox('Which main trade partner do you want to analyse?', partner_list)

# use these values to filter df for first two charts
plot_df = (df.xs(partner_select, axis=1, level=0)
             .xs('Total', axis=1, level=1)
          )
# rename the columns to the partner name
plot_df.columns = [partner_select]

# setting up a slider to choose rolling level
rol_val = st.sidebar.slider('Monthly Rolling Sum (set as "1" for no rolling)', min_value=1, max_value=12)
plot_df = plot_df.rolling(rol_val).sum().dropna() # edit the plotting df accordingly

# setting a yearly range to be diplayed on the axis
# set as two separate slides for min and max
min_year = st.sidebar.slider('Date Range - Minimum', 
                               min_value=plot_df.index.min().year, 
                               max_value=plot_df.index.max().year
                              )

max_year = st.sidebar.slider('Date Range - Maximum', 
                               min_value=plot_df.index.min().year, 
                               max_value=plot_df.index.max().year,
                              value=2022
                              )
# convert the min and max years to strings so can use with .loc to index
min_year = str(min_year)
max_year = str(max_year)

# write a title for the first section
st.write(f"""
---
##### Total UK Exports to {partner_select}  
This section shows the UK's total exports to the selected partner: the total value, the yoy change in £s and the yoy change in % terms. Values can be set to rolling monthly sums using the slider in the page's sidebar.""")

# create plotting dfs that are filtered by year range
plot_abs_df = plot_df.round(1).loc[min_year:max_year] # our plot for absolute values
plot_diff_df = plot_df.diff(12).round(1).loc[min_year:max_year] # our plot for absolute values
plot_percent_df = plot_df.pct_change(12).mul(100).dropna().round(1).loc[min_year:max_year] # our plot for yoy change

# create three separate columns
cola1, cola2, cola3 = st.columns((1,1,1))

with cola1: 
    # plot a line chart of monthly absolute values
    if rol_val > 1:
        st.write(f"UK total exports to {partner_select}, rolling {str(rol_val)}M sum") #title
    else:
        st.write(f"UK total exports to {partner_select}, monthly")
    st.line_chart(plot_abs_df)           #line chart

with cola2: 
    # plot a line chart of gbp yoy change
    if rol_val > 1:
        st.write(f"UK exports to {partner_select} by SITC 1 digit, rolling {str(rol_val)}M sum, GBP change yoy") #title
    else:
        st.write(f"UK exports to {partner_select} by SITC 1 digit, monthly, GBP change yoy")
    st.line_chart(plot_diff_df)           #line chart

with cola3:
    # plot a line of monthly yoy % change
    if rol_val > 1:
        st.write(f"UK total exports to {partner_select}, rolling {str(rol_val)}M sum, % change yoy") #title
    else:
        st.write(f"UK total exports to {partner_select}, monthly, % change yoy")
    st.line_chart(plot_percent_df)

### CREATING SECOND ROW OF THREE PLOTS
    
# create a list of codes for the SITC one-digit categories
sitc1_list = ['1','2','3','4','5','6','7','8','9']
# index our df using the new sitc list and our selected partner
# Transpose the df, use pd index slice and transpose back
idx = pd.IndexSlice
plot_sitc1_df = df.T.loc[idx[partner_select,sitc1_list,:,:] ,:].T
# create a list of names from the comm_desc part of our multi-index
# set this list of names as the column names
sitc_1dig_names = [x[2] for x in plot_sitc1_df.columns]
plot_sitc1_df.columns = sitc_1dig_names

# add the rolling factor
plot_sitc1_df2 = plot_sitc1_df.rolling(rol_val).sum().dropna() # edit the plotting df accordingly

# create three new plot dfs using this newly subsetted dataframe
plot_sitc1_abs_df = plot_sitc1_df2.round(1).loc[min_year:max_year] # for plotting absolute values
plot_sitc1_diff_df = plot_sitc1_df2.diff(12).round(1).loc[min_year:max_year] # for plotting absolute values
plot_sitc1_percent_df = plot_sitc1_df2.pct_change(12).mul(100).dropna().round(1).loc[min_year:max_year] # the % change yoy

st.write(f"""

---

##### UK Exports to {partner_select} by SITC 1 Digit Code

This section shows the UK's exports to the selected partner by SITC 1 digit: the total value, the yoy change in £s and the yoy change in % terms. SITC 1 digit categories can be turned on/off using the multi-selector. Values can be set to rolling monthly sums using the slider in the page's sidebar."""
        )

# setting up the multi-selector
sitc1_abs_list = st.multiselect('Select SITC 1 digit to include', sitc_1dig_names, default=sitc_1dig_names)

# create three separate columns
colb1, colb2, colb3 = st.columns((1,1,1))

with colb1: 
    # plot a bar chart of monthly absolute values
    if rol_val > 1:
        st.write(f"UK exports to {partner_select} by SITC 1 Digit, rolling {str(rol_val)}M sum") #title
    else:
        st.write(f"UK exports to {partner_select} by SITC 1 Digit, monthly")   
    st.bar_chart(plot_sitc1_abs_df[sitc1_abs_list])#[sitc1_abs_list])           #line chart

with colb2: 
    # plot a bar chart of monthly absolute values
    if rol_val > 1:
        st.write(f"UK exports to {partner_select} by SITC 1 Digit, rolling {str(rol_val)}M sum, GBP yoy change") #title
    else:
        st.write(f"UK exports to {partner_select} by SITC 1 Digit, monthly, GBP yoy change")
    st.bar_chart(plot_sitc1_diff_df[sitc1_abs_list])           #line chart

with colb3: 
    # plot a bar chart of monthly absolute values
    if rol_val > 1:
        st.write(f"UK exports to {partner_select} by SITC 1 Digit, rolling {str(rol_val)}M sum, % yoy change") #title
    else:
        st.write(f"UK exports to {partner_select} by SITC 1 Digit, monthly, % yoy change")
    st.line_chart(plot_sitc1_percent_df[sitc1_abs_list])           #line chart

### CREATING THE THIRD ROW OF PLOTS

st.write(f"""
---  
##### UK exports to selected partners, for selected product category

This section shows the UK's exports of the selected product categoory to the range of selected partners by the total value, the yoy change in £s and the yoy change in % terms. The product category and comparison partners can be set using the options. Values can be set to rolling monthly sums using the slider in the page's sidebar."""
        )

# setup a list of starting comparitors
comparitors = [partner_select, 'Whole world', 'Total EU(28)', 'Extra EU 28 (Rest of World)']

product_select = st.selectbox('Select a product to compare across partners', commodity_list)

# setting up the trading partner multi-selector
multipartner_select = st.multiselect('Select trade partners to include', partner_list, default=comparitors)

# index our dataframe using our selections
idx = pd.IndexSlice
plot_compare_df = df.T.loc[idx[multipartner_select,:,product_select,:] ,:].T

# create a list of names from the comm_desc part of our multi-index
# set this list of names as the column names
compare_names = [x[0] for x in plot_compare_df.columns]
plot_compare_df.columns = compare_names

# add the rolling factor
plot_compare_df = plot_compare_df.rolling(rol_val).sum().dropna() # edit the plotting df accordingly

# create three new plot dfs using this newly subsetted dataframe
plot_compare_abs_df = plot_compare_df.round(1).loc[min_year:max_year] # for plotting absolute values
plot_compare_diff_df = plot_compare_df.diff(12).dropna().round(1).loc[min_year:max_year] # for plotting absolute values
plot_compare_percent_df = plot_compare_df.pct_change(12).mul(100).dropna().round(1).loc[min_year:max_year] # the % change yoy

# create three separate columns
colc1, colc2, colc3 = st.columns((1,1,1))

with colc1: 
    # plot a line chart of monthly absolute values
    if rol_val > 1:
        st.write(f"UK {product_select} exports to {partner_select}, rolling {str(rol_val)}M sum") #title
    else:
        st.write(f"UK {product_select} exports to {partner_select}, monthly")
    st.line_chart(plot_compare_abs_df)           #line chart

with colc2: 
    # plot a line chart of gbp yoy change
    if rol_val > 1:
        st.write(f"UK {product_select} exports to {partner_select}, rolling {str(rol_val)}M sum, GBP change yoy") #title
    else:
        st.write(f"UK {product_select} exports to {partner_select}, GBP change yoy")
    st.line_chart(plot_compare_diff_df)           #line chart

with colc3:
    # plot a line of monthly yoy % change
    if rol_val > 1:
        st.write(f"UK {product_select} exports to {partner_select}, rolling {str(rol_val)}M sum, % change yoy") #title
    else:
        st.write(f"UK {product_select} exports to {partner_select}, monthly, % change yoy")
    st.line_chart(plot_compare_percent_df)


