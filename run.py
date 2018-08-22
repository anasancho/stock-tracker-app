# -*- coding: utf-8 -*-
''' IMPORT DEPENDENCIES '''
from flask import Flask, render_template, request, redirect
from flask_bootstrap import Bootstrap
from config import Config
import os, os.path, requests

#from datetime import datetime

import quandl
import numpy as np
import pandas as pd
import bokeh
from bokeh.plotting import figure
#from bokeh.io import show
from bokeh.embed import components

from fbprophet import Prophet
#import scipy
#import sklearn
#from sklearn.externals import joblib
#from pathlib import Path
#from itertools import zip_longest


''' FLASK APP CONFIG '''
# Flask App Setup
app = Flask(__name__)
app.vars={}
feat = ['p_open', 'p_close', 'p_range']
# Setup Bootstrap
bootstrap = Bootstrap(app)
# Setup Bokeh
bv = bokeh.__version__
# Setup Quandl
quandl.ApiConfig.api_key = "rstWsx8KJr9rTbDe8WHb"
# Set configuration from config.py
app.config.from_object(Config)
# On Bluemix, get the port number from the environment variable VCAP_APP_PORT
# When running this app on the local machine, default the port to 8080
port = int(os.getenv('VCAP_APP_PORT', 8080))
host = '0.0.0.0'


''' FLASK WEB ROUTES '''
@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    # Request is a GET
    # --------------------------------------------|
    if request.method == 'GET':
        return render_template('index.html')
    # Request is a POST
    # --------------------------------------------|
    else:
        app.vars['stock_ticker'] = request.form['stock_ticker']
        app.vars['model_type'] = request.form['model_type']
        app.vars['future_days'] = int(request.form['future_days'])
        # Set desired observed features for plot
        app.vars['select'] = [feat[q] for q in range(3) if feat[q] in request.form.getlist('features')]
        return redirect('/graph')


@app.route('/graph',methods=['GET','POST'])
def graph():
    # Download financial data to Pandas DataFrame
    # --------------------------------------------|
    # Check if data is already stored as .csv file
    csv_filename = '%s_past.csv' % (app.vars['stock_ticker'])
    try:
        past_data = pd.read_csv(csv_filename)
        print('past data read from csv file!')
        # to change use .astype() 
        past_data.info()
        print(past_data.info())
        past_data['date'] = past_data.date.astype(np.datetime64)
        #print(past_data)
        past_data.info()
        print(past_data.info())
    # Download data from quandl if necessary
    except:
        past_data = quandl.get_table('WIKI/PRICES',
                                     ticker = [app.vars['stock_ticker']], 
                                     qopts = { 'columns': ['date', 'open', 'high', 'low', 'close'] },
                                     date = { 'gte': '2015-01-01' },
                                     paginate=True)
        past_data.to_csv(csv_filename, encoding='utf-8', index=False)
    # Set dataframe index and type of entries
    past_data.set_index('date')
    past_data[['open','high','low','close']] = past_data[['open','high','low','close']].astype(float)
    # Rename the dataframe date column to 'ds' (for use with fbprophet package)
    past_data.rename(columns={'date':'ds'}, inplace=True)
    past_data.info()
    print(past_data.info())
        
    # Build Prediction Model
    # --------------------------------------------|
    # Check if future data is already stored as .csv file
    csv_filename = '%s_%s_future.csv' % (app.vars['stock_ticker'], app.vars['model_type'])
    print(csv_filename)
    try:
        future_data = pd.read_csv(csv_filename) #nrows=app.vars['future_days']
        print('future data read from csv file!')
        future_data['ds'] = future_data.ds.astype(np.datetime64)
        future_data['yhat'] = future_data.yhat.astype(float)
        #print(future_data)
    # Create fbprophet model and store future data as .csv file
    except:
        # instantiate model object
        model = Prophet(daily_seasonality=False,
                        weekly_seasonality=False, 
                        yearly_seasonality=True,
                        changepoint_prior_scale=0.05,
                        changepoints=None)
        model.add_seasonality(name='monthly', period=30.5, fourier_order=5)
        # instantiate train dataframe
        train_df = past_data.copy()
        train_df.rename(columns={app.vars['model_type']:'y'}, inplace=True)
        train_df = train_df.filter(items=['ds', 'y'])
        # train model
        model.fit(train_df)
        # create future_data DataFrame
        future_data = model.make_future_dataframe(periods=365, freq='D')
        future_data = model.predict(future_data)
        # write future data to .csv file
        future_data.to_csv(csv_filename, encoding='utf-8', index=False)
    # Set dataframe index and type of entries
    future_data.set_index('ds')

    # Make Bokeh plot
    # ------------------- ------------------------|
    p = figure(plot_width=850, plot_height=550, title=app.vars['stock_ticker'], x_axis_type="datetime")
    # Plot past data
    if 'p_range' in app.vars['select']:
        tmpx = np.array([past_data.ds, past_data.ds[::-1]]).flatten()
        tmpy = np.array([past_data.high, past_data.low[::-1]]).flatten()
        p.patch(tmpx, tmpy, alpha=0.3, color="#669999", legend='Range (High/Low) (Real)')
    if 'p_open' in app.vars['select']:
        p.line(past_data.ds, past_data.open, line_width=2, line_color="#FF4D4D", legend='Valor na Abertura (Real)')
    if 'p_close' in app.vars['select']:
        p.line(past_data.ds, past_data.close, line_width=2, line_color="#4D4DFF", legend='Valor no Fechamento (Real)')
    # Plot future data
    # Drop future data last rows
    future_data.drop(future_data.tail(365-app.vars['future_days']).index, inplace=True)
    if app.vars['model_type'] == 'open':
        p.line(future_data.ds, future_data.yhat, line_width=2, line_color="#FF0066", legend='Valor na Abertura (Modelo)')
    elif app.vars['model_type'] == 'closed':
        p.line(future_data.ds, future_data.yhat, line_width=2, line_color="#6666FF", legend='Valor no Fechamento (Modelo)')
    # Plot axis labels
    p.legend.orientation = "vertical"
    p.xaxis.axis_label = "Data"
    p.xaxis.axis_label_text_font_style = 'bold'
    p.xaxis.axis_label_text_font_size = '16pt'
    p.xaxis.major_label_orientation = np.pi/4
    p.xaxis.major_label_text_font_size = '14pt'
    initial_bound = past_data.ds.iloc[-1]
    final_bound = past_data.ds.iloc[0]
    p.xaxis.bounds = (initial_bound, final_bound)
    p.yaxis.axis_label = "Valor ($ USD)"
    p.yaxis.axis_label_text_font_style = 'bold'
    p.yaxis.axis_label_text_font_size = '16pt'
    p.yaxis.major_label_text_font_size = '12pt'
    # Set tag variable
    app.vars['tag'] = 'Plotagem de dados observados desde %s-%s-%s até %s-%s-%s. Dias modelados no futuro: %s' % (past_data.ds.iloc[-1].year, past_data.ds.iloc[-1].month, past_data.ds.iloc[-1].day, past_data.ds.iloc[0].year, past_data.ds.iloc[0].month, past_data.ds.iloc[0].day, app.vars['future_days'])
    # Capture stock metadate from quandl
    req = 'https://www.quandl.com/api/v3/datasets/WIKI/'
    req = '%s%s.json?api_key=rstWsx8KJr9rTbDe8WHb&collapse=daily' % (req, app.vars['stock_ticker'])
    req = '%s&start_date=2018-01-01' % (req)
    r = requests.get(req)
    # Set desc variable
    app.vars['desc'] = r.json()['dataset']['name'].split(',')[0]

    # render graph template
    # ------------------- ------------------------|
    script, div = components(p)
    return render_template('graph.html', bv=bv, ticker=app.vars['stock_ticker'],
                            ttag=app.vars['desc'], yrtag=app.vars['tag'],
                            script=script, div=div)


''' MAIN FUNCTION '''
if __name__ == '__main__':
    app.run(host=host, port=port, debug=True)