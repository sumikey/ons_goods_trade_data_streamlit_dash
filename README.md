## UK Goods Exports Dashboard
**A repository for downloading UK Country-by-Commodity Goods export data from the UK's Office for National Statistics, and creating a Streamlit dashboard for visualising simple trade trends**  
---  

**Files**  

ons_data_collection.py includes function to scrape and save the current version of the UK ONS's country by commodity exports data from the ONS website alongside a second much larger historic dataset of the same data. Additional functions preprocess and merge the two datasets, and save copies a pickled copy of a dataframe with columns of time series data and Multi-Index column headers categorising exports by partner, SITC commodity code and commodity description and flow (trade flow is kept as a redundant category, but in future will update this dashboard to include imports too). 

Data/pikl_lists contains a pickled list of commodity names and a pickled list of trade partners used as variables in the dashboard creation (it's quicker to store/access the pkl'd versions than to create again from the Multi_Index df).  

dashboard_app.py contains the code to run a streamlit web-app featuring visualisations of UK goods exports arranged by absolute values, yoy change in GBP and % yoy change. The web app includes selectors to choose the trade partner and products to be analysed; and sliders to set the level of rolling-sum (if desired) and the date range of the axis.

ons_csv_test.csv a pre-downloaded csv of ons data to simplify pre-processing and help with getting a functioning streamlit app running.

**Issues / To-Do**

dashboard_app.py is having issues deploying on streamlit: the files scraped from ons are zipped excels, and the preprocessed dataframe is then saved as a .pkl. This process works locally but is causing issues in deployment. For now the dashboard is running off of the pre-downloaded ons_csv_test.csv stored on github and is not scraping new data from the ONS website. Will fix in a future iteration.

---

A public version of the streamlit dashboard (for now running off ons_csv_text.csv) can be found here: https://share.streamlit.io/sumikey/trade_data_reporting/main/dashboard_app.py
