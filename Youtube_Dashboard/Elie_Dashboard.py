#Import Library
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from datetime import datetime


#Define Function
def style_negative(v, props=''):
    """ Style negative values in dataframe"""
    try: 
        return props if v < 0 else None
    except:
        pass
    
def style_positive(v, props=''):
    """Style positive values in dataframe"""
    try: 
        return props if v > 0 else None
    except:
        pass   

def audience_simple(country):
    """Show top represented countries"""
    if country == 'US':
        return 'USA'
    elif country == 'IN':
        return 'India'
    else:
        return 'Other'
    
    
#Load Data and Feature engineering

#streamlit offer the feature that everytime that we can load the data once and not everytime we reload the page
@st.cache_data
def load_data():
    #Every column from CSV except first row
    df_agg = pd.read_csv('Aggregated_Metrics_By_Video.csv').iloc[1:,:]
    #This CSV show if the viewer was suscribed to the channel or not
    df_agg_sub = pd.read_csv('Aggregated_Metrics_By_Country_And_Subscriber_Status.csv')
    df_comments = pd.read_csv('Aggregated_Metrics_By_Video.csv')
    df_time = pd.read_csv('Video_Performance_Over_Time.csv')
    #Rename the column
    df_agg.columns = ['Video','Video title','Video publish time','Comments added','Shares','Dislikes','Likes',
                      'Subscribers lost','Subscribers gained','RPM(USD)','CPM(USD)','Average % viewed','Average view duration',
                      'Views','Watch time (hours)','Subscribers','Your estimated revenue (USD)','Impressions','Impressions ctr(%)']
    df_agg['Video publish time'] = pd.to_datetime(df_agg['Video publish time'], format='%b %d, %Y')
    #convert from String to Datetime to make it usefull
    df_agg['Average view duration'] = df_agg['Average view duration'].apply(lambda x: datetime.strptime(x,'%H:%M:%S'))
    #Calculate the average duration view in seconds
    df_agg['Avg_duration_sec'] = df_agg['Average view duration'].apply(lambda x: x.second + x.minute*60 + x.hour*3600)
    df_agg['Engagement_ratio'] =  (df_agg['Comments added'] + df_agg['Shares'] +df_agg['Dislikes'] + df_agg['Likes']) /df_agg.Views
    df_agg['Views / sub gained'] = df_agg['Views'] / df_agg['Subscribers gained']
    df_agg.sort_values('Video publish time', ascending = False, inplace = True)
    return  df_agg, df_agg_sub, df_comments, df_time


#create dataframes from the function
df_agg, df_agg_sub, df_comments, df_time = load_data()


#additional data engineering for aggregated data 
df_agg_diff = df_agg.copy()
#Only the last 12 month most recent videos
metric_date_12mo = df_agg_diff['Video publish time'].max() - pd.DateOffset(months =12)
median_agg = df_agg_diff[df_agg_diff['Video publish time'] >= metric_date_12mo]
columns_to_exclude = ['Video','Video title', 'Video publish time', 'Average view duration']
median_agg = median_agg.drop(columns=columns_to_exclude)
#median only on continious values
median_agg = median_agg.median()

#create differences from the median for values 
#Just numeric columns 
numeric_cols = np.array((df_agg_diff.dtypes == 'float64') | (df_agg_diff.dtypes == 'int64'))

#Set the value of the numeric column - the median_agg (percent difference)
df_agg_diff.iloc[:,numeric_cols] = (df_agg_diff.iloc[:,numeric_cols] - median_agg).div(median_agg)

#Build Dashboard
add_sidebar = st.sidebar.selectbox('Aggregate or Individual Video', ('Aggregate Metrics','Individual Video Analysis'))

#Show individual metrics 

if add_sidebar == 'Aggregate Metrics':
    st.write("YouTube Aggregated Data")
    df_agg_metrics = df_agg[['Video publish time','Views','Likes','Subscribers','Shares','Comments added','RPM(USD)','Average % viewed',
                         'Avg_duration_sec', 'Engagement_ratio','Views / sub gained']]
    df_agg_metrics = df_agg_metrics.reset_index(drop=True)
    metric_date_6mo = df_agg_metrics['Video publish time'].max() - pd.DateOffset(months =6)
    metric_date_12mo = df_agg_metrics['Video publish time'].max() - pd.DateOffset(months =12)
    metric_medians6mo = df_agg_metrics[df_agg_metrics['Video publish time'] >= metric_date_6mo]
    metric_medians6mo = metric_medians6mo.drop(columns = ['Video publish time'])
    metric_medians6mo = metric_medians6mo.median()
    metric_medians12mo = df_agg_metrics[df_agg_metrics['Video publish time'] >= metric_date_12mo]
    metric_medians12mo = metric_medians12mo.drop(columns = ['Video publish time'])
    metric_medians12mo = metric_medians12mo.median()


    col1, col2, col3, col4, col5 = st.columns(5)
    columns = [col1, col2, col3, col4, col5]

    count = 0
    for i in metric_medians6mo.index:
        with columns[count]:
            delta = (metric_medians6mo[i] - metric_medians12mo[i])/metric_medians12mo[i]
            st.metric(label= i, value = round(metric_medians6mo[i],1), delta = "{:.2%}".format(delta))
            count += 1
            if count >= 5:
                count = 0
        
    #get date information / trim to relevant data 
    df_agg_diff['Publish_date'] = df_agg_diff['Video publish time'].apply(lambda x: x.date())
    df_agg_diff_final = df_agg_diff.loc[:,['Video title','Publish_date','Views','Likes','Subscribers','Shares','Comments added','RPM(USD)','Average % viewed',
                             'Avg_duration_sec', 'Engagement_ratio','Views / sub gained']]
    
    
    numeric_columns = df_agg_diff_final.select_dtypes(include='number')
    df_agg_numeric_lst = numeric_columns.median().index.tolist()
    df_to_pct = {}
    for i in df_agg_numeric_lst:
         df_to_pct[i] = '{:.1%}'.format
    
   #add color to our dataframe when its positive or negative 
    st.dataframe(df_agg_diff_final.style.hide().applymap(style_negative, props='color:red;').applymap(style_positive, props='color:green;').format(df_to_pct))
   
   
if add_sidebar == 'Individual Video Analysis':
    videos = tuple(df_agg['Video title'])
    video_select = st.selectbox('Pick a Video:', videos)
    
    #Filter when picking a specific video
    agg_filtered = df_agg[df_agg['Video title'] == video_select]
    agg_sub_filtered = df_agg_sub[df_agg_sub['Video Title'] == video_select]
    agg_sub_filtered['Country'] = agg_sub_filtered['Country Code'].apply(audience_simple)
    agg_sub_filtered.sort_values('Is Subscribed', inplace= True) 
    
    fig = px.bar(agg_sub_filtered, x ='Views', y='Is Subscribed', color ='Country', orientation ='h')
    #order axis 
    st.plotly_chart(fig)

    
    
    
    
    
    
    



