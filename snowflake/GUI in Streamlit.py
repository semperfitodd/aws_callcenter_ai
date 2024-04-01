# Import python packages
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import time
from plotly.subplots import make_subplots
import numpy as np
from snowflake.snowpark.context import get_active_session

# Write directly to the app
st.title("Call Center Analysis")

# Get the current credentials
session = get_active_session()

# Notice that we are not defining the database connection at all.
# That is very convenient.

# Retrieve transcript IDs.

# Select a call ticket for analysis
ticket_id = st.selectbox(
    "Select a transcript ID to proceed.",
    (101, 102, 103, 104, 105, 106, 107),
)
#ticket_id = st.selectbox()
st.write('You selected: ', ticket_id)

# Retrieve the ticket's details
sql_summary = "select" + \
    " TRANSCRIPT_ID, SENTIMENT_SCORE, TRANSCRIPT_SUMMARY" + \
    " from MIKE_CALL_ANALYSIS" + \
    " where TRANSCRIPT_ID=" + str(ticket_id)

df_summary = session.sql(sql_summary).collect()
st.write('')
st.subheader('Transcript Analysis')
st.write('')

overall_sentiment = df_summary[0]['SENTIMENT_SCORE']
summary = df_summary[0]['TRANSCRIPT_SUMMARY']

#st.write('Overall sentiment is '+str(overall_sentiment))
st.write('Summary (generated from LLM)')
st.write(summary)

# ---------------------------------------------------------------
# Retrieve the customer sentiment

sql_sentiment = "select" + \
    " SENTIMENT_START, SENTIMENT_END, SENTIMENT_PERCENT_CHANGE" + \
    " FROM JEFF_TRANSCRIPTS_SENTIMENT_BY_PERSON" + \
    " WHERE TRANSCRIPT_ID=" + str(ticket_id) + \
    " AND PERSON_ROLE='Customer'"
df_sentiment = session.sql(sql_sentiment).collect()

customer_sentiment_start = df_sentiment[0]['SENTIMENT_START']
customer_sentiment_end = df_sentiment[0]['SENTIMENT_END']
customer_sentiment_pct_chg = df_sentiment[0]['SENTIMENT_PERCENT_CHANGE']

# ---------------------------------------------------------------
# https://plotly.com/python/gauge-charts/
# https://plotly.github.io/plotly.py-docs/generated/plotly.graph_objects.Indicator.html

layout = go.Layout(
    height = 360,
    width = 360,
    autosize = False
)

fig1 = go.Figure(go.Indicator(
    value=round(customer_sentiment_start, 2),
    mode="gauge+delta+number",
    title = {'text': "Customer Sentiment Start"},
    #delta = {'reference': 0},  # renders the value twice
    gauge = {
        'axis':  {'range': [-1, 1], 'tickwidth': 1, 'tickcolor': "purple"},
             'steps' : [
                 {'range': [-1, -0.45], 'color': "red"},  #magenta
                 {'range': [-0.45, 0.45], 'color': "yellow"},  #wheat
                 {'range': [0.45, 1], 'color': "forestgreen"}],  #springgreen
        'bar': {'color':"lightblue", "thickness":0.3}
    },
        domain={'x': [0, 1], 'y': [0, 1]},  # horizonal positioning
    ),
    layout = layout
)

st.plotly_chart(
    fig1,
    use_container_width=True
)


# This is an optional step. Can be disabled.
st.write("Calculating the customer sentiment at the end of call...")
time.sleep(6)


fig2 = go.Figure(go.Indicator(
    value=round(customer_sentiment_end, 2),
    mode="gauge+delta+number",
    title = {'text': "Customer Sentiment End"},
    #delta = {'reference': 0},  # renders the value twice
    gauge = {
        'axis':  {'range': [-1, 1], 'tickwidth': 1, 'tickcolor': "purple"},
             'steps' : [
                 {'range': [-1, -0.45], 'color': "red"},
                 {'range': [-0.45, 0.45], 'color': "yellow"},
                 {'range': [0.45, 1], 'color': "forestgreen"}],
        'bar': {'color':"turquoise", "thickness":0.3}
    },
        domain={'x': [0, 1], 'y': [0, 1]},  # horizonal positioning
    ),
    layout = layout
)

st.plotly_chart(
    fig2,
    use_container_width=True
)

# ---------------------------------------------------------------
# Render the start and end gauges side by side.
# https://www.reddit.com/r/learnpython/comments/hdi49i/plotly_table_and_charts_subplot_specs_argument/

#fig_final = make_subplots(specs=[[{}]])

#fig_final.append_trace(fig1, row=1, col=1)
#fig_final.append_trace(fig2, row=1, col=2)

#st.plotly_chart(fig_final,use_container_width=True)

# ---------------------------------------------------------------
# Retrieve the parties
sql_people = "select distinct PERSON_NAME AS PERSON, PERSON_ROLE AS ROLE, BLOCK_SENTIMENT AS SENTIMENT FROM CALL_CENTER_ANALYSIS.CONSUMPTION.JEFF_TRANSCRIPTS_SENTIMENT_BY_PERSON WHERE TRANSCRIPT_ID="+str(ticket_id)
df_people = session.sql(sql_people).collect()
st.write('')
st.subheader('Parties Involved')
st.dataframe(data=df_people,use_container_width=True, hide_index=True)

# Retrieve the full transcrip text
sql_text = "select TRANSCRIPT_TEXT FROM CALL_CENTER_ANALYSIS.CONSUMPTION.MIKE_CALL_ANALYSIS WHERE TRANSCRIPT_ID="+str(ticket_id)
df_text = session.sql(sql_text).collect()
st.write('')
st.subheader('Full Transcript')
full_txt = str(df_text[0]['TRANSCRIPT_TEXT'])
st.write(full_txt)

# ---------------------------------------------------------------

