import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import streamlit as st
from babel.numbers import format_currency



sns.set(style='whitegrid')

@st.cache_data
def create_daily_orders_df(df):
    daily_orders_df = df.resample(rule='D', on='order_approved_at').agg({
        "order_id": "nunique",
        "payment_value": "sum"
    })
    daily_orders_df = daily_orders_df.reset_index()
    daily_orders_df.rename(columns={
        "order_id": "order_count",
        "payment_value": "revenue"
    }, inplace=True)
    return daily_orders_df

@st.cache_data
def create_sum_order_items_df(df):
    sum_order_items_df = df.groupby("product_category_name_english")['payment_value'].sum().sort_values(ascending=False).reset_index()
    return sum_order_items_df

@st.cache_data
def create_sum_order_items_by_order_id_df(df):
    sum_order_items_df = df.groupby("product_category_name_english")['order_id'].nunique().sort_values(ascending=False).reset_index()
    sum_order_items_df.rename(columns={"order_id": "total_orders"}, inplace=True)
    return sum_order_items_df

@st.cache_data
def create_rfm_df(df, recent_date):
    rfm_df = df.groupby(by="customer_id", as_index=False).agg({
        "order_approved_at": "max",
        "order_id": "nunique",
        "payment_value": "sum"
    })

    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)
    return rfm_df

@st.cache_data
def load_data():
    df = pd.read_csv("all_data.csv")
    datetime_columns = ["order_approved_at",
                        "order_delivered_customer_date",
                        "order_delivered_carrier_date",
                        "order_estimated_delivery_date"]
    df.sort_values(by="order_approved_at", inplace=True)
    for column in datetime_columns:
        df[column] = pd.to_datetime(df[column], errors='coerce')
    return df

df = load_data()

recent_date = df["order_approved_at"].max()

min_date = df["order_approved_at"].min()
max_date = df["order_approved_at"].max()

with st.sidebar:
    st.image("https://raw.githubusercontent.com/uutsyazah/logo/refs/heads/main/Simple%20Olshop%20Logo.jpg")
    start_date, end_date = st.date_input(
        label='Rentang Waktu', min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

main_df = df[(df["order_approved_at"] >= str(start_date)) & 
              (df["order_approved_at"] <= str(end_date))]

daily_orders_df = create_daily_orders_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
sum_order_items_by_order_id_df = create_sum_order_items_by_order_id_df(main_df)


rfm_df = create_rfm_df(main_df, recent_date)


st.markdown("<h1 style='text-align: center;'>MY E-Commerce Dashboard!</h1>", unsafe_allow_html=True)

st.header('Daily Orders')

col1, col2 = st.columns(2)

with col1:
    total_orders = daily_orders_df.order_count.sum()
    st.metric("Total orders", value=total_orders)
with col2:
    total_revenue = format_currency(daily_orders_df.revenue.sum(), "BRL", locale='pt_BR') 
    st.metric("Total Revenue", value=total_revenue)

fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    daily_orders_df["order_approved_at"],
    daily_orders_df["order_count"],
    marker='o', 
    linewidth=2,
    color="#A91D3A"
)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)

st.pyplot(fig)


st.header("Best and Worst Performing Product")


red = '#A91D3A'
pink = '#FF6969'
colors = [red, pink, pink, pink, pink]

product_sales = df.groupby('product_category_name_english')['order_id'].count().reset_index()
product_sales.columns = ['product_category_name_english', 'total_sold']
product_sales = product_sales.sort_values(by='total_sold', ascending=False)

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(24, 6))

sns.barplot(x="total_sold", y="product_category_name_english", 
            data=product_sales.head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel(None)
ax[0].set_title("Best Performing Product", loc="center", fontsize=18)
ax[0].tick_params(axis='y', labelsize=15)

for i in ax[0].patches:
    ax[0].text(i.get_width() + 0.2, i.get_y() + i.get_height() / 2, 
               f'{int(i.get_width())}', ha='right', va='center', fontsize=12, color='black', weight='bold')

sns.barplot(x="total_sold", y="product_category_name_english", 
            data=product_sales.sort_values(by="total_sold", ascending=True).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel(None)
ax[1].invert_xaxis()  
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()  
ax[1].set_title("Worst Performing Product", loc="center", fontsize=18)
ax[1].tick_params(axis='y', labelsize=15)

for i in ax[1].patches:
    ax[1].text(i.get_width() - 0.2, i.get_y() + i.get_height() / 2, 
               f'{int(i.get_width())}', ha='left', va='center', fontsize=12, color='black', weight='bold')

st.pyplot(fig)



st.header("Best Customer Based on RFM Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)

with col2:
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)

with col3:
    avg_monetary = format_currency(rfm_df.monetary.mean(), "BRL", locale='pt_BR')
    st.metric("Average Monetary", value=avg_monetary)

rfm_df['short_customer_id'] = rfm_df['customer_id'].apply(lambda x: x[:5])  

fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(30, 6))

colors = ["#A91D3A", "#A91D3A", "#A91D3A", "#A91D3A", "#A91D3A"]

sns.barplot(y="recency", x="short_customer_id", data=rfm_df.sort_values(by="recency", ascending=True).head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel(None)
ax[0].set_title("By Recency (days)", loc="center", fontsize=18)
ax[0].tick_params(axis ='x', labelsize=15)

sns.barplot(y="frequency", x="short_customer_id", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel(None)
ax[1].set_title("By Frequency", loc="center", fontsize=18)
ax[1].tick_params(axis='x', labelsize=15)

sns.barplot(y="monetary", x="short_customer_id", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax[2])
ax[2].set_ylabel(None)
ax[2].set_xlabel(None)
ax[2].set_title("By Monetary", loc="center", fontsize=18)
ax[2].tick_params(axis='x', labelsize=15)

for axis in ax:
    axis.tick_params(axis='x', rotation=45)

st.pyplot(fig)
st.caption('Copyright (c) uut')


