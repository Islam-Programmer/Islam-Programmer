import pandas as pd
import streamlit as st
import numpy as np
import pyodbc, urllib
from sqlalchemy import create_engine

# # **SQL ALCHEMY METHOD**----------------------------------------
# params = urllib.parse.quote_plus(
#     "Driver={SQL Server};"
#     "Server=DESKTOP-IF1AF28;"
#     "Database=KCC;"
#     "Trusted_Connection=yes;"
# )
# engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
# #----------------------------------------------------------------

# # **PYODBC METHOD**------------------------------------
# conn = pyodbc.connect(
#    r'Driver={SQL Server};'
#    r'Server=DESKTOP-IF1AF28;'  
#    r'Database=KCC;'        
#    r'Trusted_Connection=yes;'
# )

# query = """
#     Select c.CustomerName,
#     c.CustomerID,
#     OrderDate,
#     o.OrderID,
#     OrderTotal,
#     Phone

#     From dbo.Orders o

#     Join dbo.Customers c on o.CustomerID = c.CustomerID
#     Join dbo.Order_Product op on o.OrderID = op.OrderID

#     Order by OrderDate 
# """
# # -----------------------------------------------------

@st.cache_data
def load_data():
    df = pd.read_csv('.devcontainer/orders.csv')
    df.drop_duplicates(inplace=True)
    df = df.iloc[:, 1:]
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    df['OrderDate'] = pd.to_datetime(df['OrderDate'], errors='coerce')
    return df

def main():
    df = load_data()
    
    df['Month'] = df['OrderDate'].dt.to_period('M')

    def human_format(num):
        if num >= 1_000_000:
            return f"${num/1_000_000:.1f}M"
        elif num >= 1_000:
            return f"${num/1_000:.1f}k"
        else:
            return num
        
    total_revenues = df['OrderTotal'].sum()
    total_orders_count = df['OrderID'].count()
    total_orders_average = df['OrderTotal'].mean()
    total_orders_per_customer = df.groupby('CustomerName')['OrderID'].count().mean()
    customers_count = df['CustomerName'].nunique()

    orders_per_month = (
        df.groupby('Month')['OrderID']
        .count()
        .reset_index()
        .rename(columns={'OrderID': 'Orders'})
    )    #orders_per_month.rename(columns={'OrderID': 'Orders'})
    orders_per_month['Month'] = orders_per_month["Month"].dt.to_timestamp()

    # KPIs
    st.title('OverView')
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric('Total Revenues', human_format(total_revenues))
    col2.metric('Orders Count', total_orders_count)
    col3.metric('Revenue Average', human_format(total_orders_average))
    col4.metric('Orders P/C', int(total_orders_per_customer))
    col5.metric('Customers', human_format(customers_count))
    st.divider()
    st.divider()


    st.dataframe(df)
    
    st.title("Revenues Per Month")

    revenues_per_month = df.groupby('Month')['OrderTotal'].sum()

    revenues_per_month.index = revenues_per_month.index.to_timestamp()
    st.line_chart(revenues_per_month)


    top_10_clients = (
        df.groupby('CustomerName')['OrderTotal']
        .sum()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={'OrderTotal': 'Total Revenue'})
    )

    st.divider()
    st.subheader("Top 5 Clients by Revenue")
    st.dataframe(top_10_clients)
    st.divider()
    st.subheader('Orders Per Month')
    st.line_chart(orders_per_month, x='Month', y='Orders')


    st.divider()
    st.subheader('Our Best Customers')
    customers_orders = df.groupby('CustomerName')['OrderID'].nunique()
    out_best_customers = customers_orders[customers_orders > 1]
    our_best_customers_df = (out_best_customers
                        .reset_index()
                        .rename(columns={'OrderID' : 'Total Orders'})
                        .sort_values(by='Total Orders', ascending=False))

    st.dataframe(our_best_customers_df)
    st.divider()
    df['Date'] = df['OrderDate'].apply(lambda x: str(x)[:10])
    df['Month'] = df['OrderDate'].apply(lambda x: str(x)[:7])
    df['Year'] = df['OrderDate'].apply(lambda x: str(x)[:4])

    total_per_day = df.groupby(df['OrderDate'].dt.day)['OrderTotal'].sum().reset_index()
    total_per_month = df.groupby(df['OrderDate'].dt.month)['OrderTotal'].sum().reset_index()
    total_per_year = df.groupby(df['OrderDate'].dt.year)['OrderTotal'].sum().reset_index()

    for i in [total_per_day, total_per_month, total_per_year]:
        i.rename(columns={'OrderDate':'Date', 'OrderTotal':'Total Revenue'})

    df.rename(columns={'OrderDate':'Date'})

    
    

    
    with st.sidebar.form(key='SideBarForm'):
        date_filter = st.selectbox('Date Filter', ['Day', 'Month', 'Year'])
        submit = st.form_submit_button('Apply Changes')
    if submit:
        st.subheader(f'Filtered Data Based On [{date_filter}]')
        if date_filter == 'Day':
            st.write(total_per_day)
            st.area_chart(total_per_day)
        elif date_filter == 'Month':
            st.write(total_per_month)
            st.area_chart(total_per_month)
        elif date_filter == 'Year':
            st.write(total_per_year)
            st.bar_chart(total_per_year)
        
    else:
        st.info('Filter Data in side bar to display.')



    

if __name__ == "__main__":
    main()


# ********* RUN CODE ************
# python -m streamlit run test.py
