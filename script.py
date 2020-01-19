#-*- coding: utf-8 -*-

######################################################################
###  THE INTELLIGENT INVESTOR TOOL
###  AUTHOR: Arthur Mello
###  CREATION DATE: 14/07/2019
######################################################################

#########################
###  DATA GENERATION  ###
#########################

import pandas as pd
pd.options.display.float_format = '{:.2f}'.format

# Importing data
url = "https://www.fundamentus.com.br/resultado.php"
tables = pd.read_html(url)
data = tables[0]

# Cleaning data
def clean_numbers(pd_series):
    x = pd_series.str.replace('.', '').astype('float64')
    return x
numbercols = ['Liq.2meses',u'Patrim. Líq']
data[numbercols] = data[numbercols].apply(clean_numbers)

def clean_percentage(pd_series):
    x = pd_series.str.replace('%', '')
    x = x.str.replace(',', '')
    x = x.str.replace('.', '').astype('float64')
    x = x.div(10000)
    return x
percent_cols = ['Div.Yield','Mrg Ebit',u'Mrg. Líq.','ROIC','ROE','Cresc. Rec.5a']
data[percent_cols] = data[percent_cols].apply(clean_percentage)

colstodivideby100 = [u'Cotação','P/L','P/VP','PSR','P/Ativo','P/Cap.Giro',
    'P/EBIT','P/Ativ Circ.Liq','EV/EBITDA','Liq. Corr.',
    'Liq.2meses',u'Patrim. Líq',u'Dív.Brut/ Patrim.']

for col in colstodivideby100:
    data[col] = data[col].astype(str).str.replace('.','').astype(float).div(100)

data = data.drop(['PSR', 'P/Cap.Giro','EV/EBIT','Liq.2meses'], axis = 1)
# Creating filters

# Intelligent Investor filter
def intelligent_investor_filter(df):
    df2 = df.copy()
    df2 = df2[df2[u'Patrim. Líq'] > 50000000] # minimum market cap
    df2 = df2[(df2['ROIC'] > 0)] # positive ROIC
    df2 = df2[(df2['EV/EBITDA'] > 0)] # positive EV/EBITDA
    df2 = df2[df2['Div.Yield'] > 0] # some dividends
    df2 = df2[df2['Cresc. Rec.5a'] > 0] # some revenue growth
    df2 = df2[(df2['P/L'] * df2['P/VP']).between(0, 22.5)] # moderate P/E and P/book value
    df2 = df2[df2['P/Ativ Circ.Liq'] > 0] # positive working capital
    return df2


intelligent_investor_data = intelligent_investor_filter(data)
intelligent_investor_data.reset_index(drop=True, inplace=True)

# Cheap stocks
def cheap_stocks_filter(df):
    df2 = df.copy()
    df2 = df2[df2['P/VP'].between(0, 1)] # price is smaller than book value
    return df2

cheap_stocks_data = cheap_stocks_filter(data)
cheap_stocks_data.reset_index(drop=True, inplace=True)

#########################
##  DATA PRESENTATION  ##
#########################

# Formatting data
def reinsert_percentage(pd_series):
    x = round(pd_series*100,3).astype(str)
    return x

def format_small_currency(pd_series):
    x = pd_series
    x = 'R$ ' + round(x,3).astype(str)
    return x
small_currency_columns = ['Cotação']

def format_big_currencies(pd_series):
    x = pd_series
    x = 'R$ ' + (round(x/1000000,2)).astype(str) + 'MM'
    return x
big_currency_columns = ['Patrim. Líq']

def general_format(df):
    df2 = df.copy()
    df2[percent_cols] = df2[percent_cols].apply(reinsert_percentage)
    df2[small_currency_columns] = df2[small_currency_columns].apply(format_small_currency)
    df2[big_currency_columns] = df2[big_currency_columns].apply(format_big_currencies)
    return df2

from flask import Flask, request, render_template
import os

TEMPLATE_DIR = os.path.abspath('./templates')
STATIC_DIR = os.path.abspath('./static')

app = Flask(__name__, template_folder=TEMPLATE_DIR,
            static_folder=STATIC_DIR)

@app.route('/investor-tool', methods=("POST", "GET"))
def html_table():
    select = request.form.get('comp_select')

    if select == 'Intelligent Investor':
        py_table = intelligent_investor_data
    elif select == 'Cheap stocks':
        py_table = cheap_stocks_data
    else:
        py_table = data

    py_table = general_format(py_table)

    app.root_path = os.path.dirname(os.path.abspath(__file__))
    return render_template(
        'basic.html',
        strategies=[{'name':'Select a strategy'},{'name':'Intelligent Investor'},
                    {'name':'Cheap stocks'}],
        table = py_table.to_html(classes='data', index= False),
        titles = py_table.columns.values,

        select = select
        )


if __name__ == '__main__':
    app.run(debug=True)
