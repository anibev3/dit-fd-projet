import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px


st.set_page_config(page_title="Projet Final - Transactions", layout="wide")


@st.cache_data
def load_data():
    df = pd.read_csv("Dataset.csv")
    df["TransactionStartTime"] = pd.to_datetime(df["TransactionStartTime"])
    df["Date"] = df["TransactionStartTime"].dt.date
    df["Hour"] = df["TransactionStartTime"].dt.hour
    df["Day"] = df["TransactionStartTime"].dt.day
    df["Month"] = df["TransactionStartTime"].dt.month
    df["AmountAbs"] = df["Amount"].abs()
    df["MargeBrute"] = df["Value"] - df["AmountAbs"]
    df["TauxRentabilite"] = (df["MargeBrute"] / df["AmountAbs"].replace(0, pd.NA)) * 100
    return df


df = load_data()

st.title("Dashboard Interactif - Projet Final")
st.write("Analyse des transactions, des montants et des cas de fraude.")

st.sidebar.header("Filtres")

date_min = pd.to_datetime(df["Date"].min())
date_max = pd.to_datetime(df["Date"].max())
date_range = st.sidebar.date_input("Filtrer par date", [date_min, date_max])

if len(date_range) == 2:
    start_date = pd.to_datetime(date_range[0]).date()
    end_date = pd.to_datetime(date_range[1]).date()
    df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]

product_choices = st.sidebar.multiselect(
    "ProductCategory",
    sorted(df["ProductCategory"].unique()),
    default=sorted(df["ProductCategory"].unique()),
)
channel_choices = st.sidebar.multiselect(
    "ChannelId",
    sorted(df["ChannelId"].unique()),
    default=sorted(df["ChannelId"].unique()),
)
pricing_choices = st.sidebar.multiselect(
    "PricingStrategy",
    sorted(df["PricingStrategy"].unique()),
    default=sorted(df["PricingStrategy"].unique()),
)
fraud_choices = st.sidebar.multiselect(
    "FraudResult",
    sorted(df["FraudResult"].unique()),
    default=sorted(df["FraudResult"].unique()),
)

df = df[
    df["ProductCategory"].isin(product_choices)
    & df["ChannelId"].isin(channel_choices)
    & df["PricingStrategy"].isin(pricing_choices)
    & df["FraudResult"].isin(fraud_choices)
]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Transactions", len(df))
col2.metric("Montant total", f"{df['AmountAbs'].sum():,.0f}")
col3.metric("Valeur totale", f"{df['Value'].sum():,.0f}")
col4.metric("Fraudes", int(df["FraudResult"].sum()))

st.subheader("Evolution du nombre de transactions par jour")
transactions_per_day = df.groupby("Date").size().reset_index(name="NombreTransactions")
fig_line = px.line(
    transactions_per_day,
    x="Date",
    y="NombreTransactions",
    title="Nombre de transactions par jour",
)
st.plotly_chart(fig_line, use_container_width=True)

left_col, right_col = st.columns(2)

with left_col:
    st.subheader("Transactions par heure")
    fig_hour, ax_hour = plt.subplots(figsize=(10, 4))
    sns.countplot(data=df, x="Hour", color="skyblue", ax=ax_hour)
    ax_hour.set_title("Repartition des transactions par heure")
    ax_hour.set_xlabel("Heure")
    ax_hour.set_ylabel("Nombre de transactions")
    st.pyplot(fig_hour)

with right_col:
    st.subheader("Repartition par canal")
    channel_counts = df["ChannelId"].value_counts().reset_index()
    channel_counts.columns = ["ChannelId", "Count"]
    fig_pie = px.pie(
        channel_counts,
        names="ChannelId",
        values="Count",
        title="Repartition des transactions par canal",
    )
    st.plotly_chart(fig_pie, use_container_width=True)

st.subheader("Valeur moyenne par categorie de produit")
avg_value = df.groupby("ProductCategory")["Value"].mean().sort_values().reset_index()
fig_bar = px.bar(
    avg_value,
    x="ProductCategory",
    y="Value",
    color="Value",
    title="Valeur moyenne par categorie",
)
st.plotly_chart(fig_bar, use_container_width=True)

st.subheader("Heatmap de correlation")
numeric_columns = ["Amount", "Value", "PricingStrategy", "FraudResult", "Hour", "Day", "Month", "AmountAbs", "MargeBrute"]
fig_corr, ax_corr = plt.subplots(figsize=(10, 5))
sns.heatmap(df[numeric_columns].corr(numeric_only=True), annot=True, cmap="coolwarm", ax=ax_corr)
st.pyplot(fig_corr)

st.subheader("Analyse de la fraude par categorie")
fraud_by_category = (
    df.groupby("ProductCategory")["FraudResult"]
    .mean()
    .sort_values(ascending=False)
    .reset_index()
)
fraud_by_category["FraudResult"] = fraud_by_category["FraudResult"] * 100
fig_fraud = px.bar(
    fraud_by_category,
    x="ProductCategory",
    y="FraudResult",
    color="FraudResult",
    title="Taux de fraude par categorie (%)",
)
st.plotly_chart(fig_fraud, use_container_width=True)

st.subheader("Tableau d'analyse")
groupby_col = st.selectbox(
    "Grouper par",
    ["ProductCategory", "ChannelId", "PricingStrategy", "FraudResult", "Month"],
)
st.dataframe(
    df.groupby(groupby_col)[["AmountAbs", "Value", "MargeBrute"]]
    .agg(["mean", "sum", "count"])
    .round(2)
)

with st.expander("Apercu des donnees"):
    st.dataframe(df)

csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    "Telecharger les donnees filtrees",
    csv,
    "transactions_filtrees.csv",
    "text/csv",
)
