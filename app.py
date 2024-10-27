#IMPORT LIBRARIES
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from millify import millify
from millify import prettify
from geopy.geocoders import Nominatim

from sklearn.ensemble import RandomForestRegressor

#PAGE CONFIG
st.set_page_config(
    page_title="Abhay's College House Prices Dashboard",
    layout="wide",
    initial_sidebar_state="expanded")


#PREPROCESSING
df = pd.read_excel("House_Price.xlsx").drop(columns="Record")

df["Build_year"] = pd.to_datetime(df["Build_year"], format="%Y")
df['Age_at_sale'] = df["Sale_date"].dt.year - df["Build_year"].dt.year #Creating age of house column
df["Price_per_sqft"] = df["Sale_amount"]/df["Sqft_home"]
df["Build_year"] = df["Build_year"].dt.strftime('%Y-%m-%d')

df['State'] = df['Town'].str[-2:]
df['Town'] = df['Town'].str.split(',').str[0] #Splitting town into town and state

state = df['State'].value_counts().reset_index()
state.columns = ['State', 'Sale Count'] #creating statewise dataframe

state = pd.merge(state, df.groupby('State')['Sale_amount'].mean().reset_index(), on='State')
state = pd.merge(state, df.groupby('State')['Price_per_sqft'].mean().reset_index(), on='State')
state = state.rename(columns={"Sale_amount" : "Average Price"}) 
state = state.sort_values(by="Average Price") #Adding average price per state column

#SIDEBAR CONFIGURATION
with st.sidebar:
    st.title('US College House Prices  Dashboard')

    uni = st.selectbox("Select a university", list(df["University"].unique()), index=list(df["University"].unique()).index("Virginia Tech"))
    data = df[df["University"] == uni]
    towndata = data
    with st.popover("Filters"):
        startprice, endprice = st.select_slider("Price Range (in $)", options = list(data["Sale_amount"].sort_values().unique()), value = (data["Sale_amount"].min(), data["Sale_amount"].max()))

        startage, endage = st.select_slider("House Age (in years)", options = list(data["Age_at_sale"].sort_values().unique()), value = (data["Age_at_sale"].min(), data["Age_at_sale"].max()))

        startbed, endbed = st.select_slider("Beds", options = list(data["Beds"].sort_values().unique()), value = (data["Beds"].min(), data["Beds"].max()))

        startbath, endbath = st.select_slider("Baths", options = list(data["Baths"].sort_values().unique()), value = (data["Baths"].min(), data["Baths"].max()))

        startsqft, endsqft = st.select_slider("House Size (in sq.ft)", options = list(data["Sqft_home"].sort_values().unique()), value = (data["Sqft_home"].min(), data["Sqft_home"].max()))
    
    st.write("")
    st.subheader("Average metrics in "+data["Town"].values[0])
    st.metric(label = "House Price", value = "$"+prettify(round(data["Sale_amount"].mean(), 0)), delta = prettify(round(data["Sale_amount"].mean()-df["Sale_amount"].mean(), 0))+" vs. average")

    st.metric(label = "House Size", value = prettify(round(data["Sqft_home"].mean(), 0))+" sq.ft.", delta = prettify(round(data["Sqft_home"].mean()-df["Sqft_home"].mean(), 0))+" vs. average")

    st.metric(label = " Price per Sq.Ft.", value = "$"+prettify(round(data["Price_per_sqft"].mean(), 0)), delta = prettify(round(data["Price_per_sqft"].mean()-df["Price_per_sqft"].mean(), 0))+" vs.  average")

    #MAP
    geolocator = Nominatim(user_agent="abhay")
    location = geolocator.geocode(uni+", "+data["Town"].values[0]+", "+data["State"].values[0])
    data['LAT'] = location.latitude
    data['LONG'] = location.longitude
    st.map(data, latitude="LAT", longitude="LONG", height=200)

#NATION CONTAINER
with st.container(border = True, height=330, key="nation"):
    col1, col2, col3 = st.columns([1.2,1.5,0.9])
    with col1:
        fig1 = px.bar(state[state["Sale Count"]>410].sort_values(by="Sale Count"), x='Sale Count', y='State', color_continuous_scale="reds", range_color=(800, 100), orientation='h', text_auto=True, color="Sale Count", height = 340)
        fig1.update_layout(title="Most Sales", coloraxis_showscale=False)
        st.plotly_chart(fig1)
    
    with col2:
        fig2 = px.choropleth(state, locations='State', locationmode="USA-states", color='Average Price', scope="usa", color_continuous_scale="reds", height = 350)
        fig2.update_layout(title="Average house price")
        fig2.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig2)
    
    with col3:
        st.dataframe(state,
                 height=300,
                 column_order=("State", "Price_per_sqft"),
                 hide_index=True,
                 width=None,
                 column_config={
                    "State": st.column_config.TextColumn(
                        "States",
                    ),
                    "Price_per_sqft": st.column_config.ProgressColumn(
                        "Price per square foot",
                        format="$%0.2f",
                        min_value=0,
                        max_value=max(state.Price_per_sqft),
                     )}
                 )

#UNIVERSITY CONTAINER
with st.container(border=False, height=500, key="university"):
    data = data[(data["Sale_amount"] >= startprice) & (data["Sale_amount"] <= endprice) & (data["Age_at_sale"] >= startage) & (data["Age_at_sale"] <= endage)]
    data = data[(data["Beds"]>=startbed) & (data["Beds"]<=endbed) & (data["Baths"]>=startbath) & (data["Baths"]<=endbath) & (data["Sqft_home"] >= startsqft) & (data["Sqft_home"] <= endsqft)]
    data['Sale_date'] = data['Sale_date'].dt.strftime('%Y-%m-%d')
    col1, col2 = st.columns([1,1.1])
    with col1:
        st.caption(str(len(data))+" listings found")
        st.dataframe(data,
                    hide_index=True,
                    column_order = ("Sale_date", "Sale_amount","Sqft_home", "Beds", "Baths", "Age_at_sale"),
                    column_config={
                        "Sale_date": st.column_config.DateColumn(
                            "Sale Date",
                            format = "D MMM YYYY"
                        ),
                        "Sale_amount": st.column_config.NumberColumn(
                            "Sale price",
                            format="$%d",
                            min_value=0,
                        ),
                        "Age_at_sale": st.column_config.NumberColumn(
                            "Property age",
                            format="%d years",
                            min_value=0,
                        ),
                        "Sqft_home": st.column_config.NumberColumn(
                            "Size",
                            format="%d sq.ft.",
                        ),
                        }
                        
                    )
    
    with col2:
        tablist = ["Sales Distribution", "Sales by date", "Price estimate"]
        tabs = st.tabs(tablist)

        with tabs[0]:
            subtabs = st.tabs(["with Beds", "with Baths", "with Size", "with Age of house"])
            with subtabs[0]:
                st.plotly_chart(px.histogram(towndata, x="Beds", y="Sale_amount", height=350, color_discrete_sequence=["darkred"]))
            with subtabs[1]:
                st.plotly_chart(px.histogram(towndata, x="Baths", y="Sale_amount", height=350, color_discrete_sequence=["darkred"]))
            with subtabs[2]:
                st.plotly_chart(px.histogram(towndata, x="Sqft_home", y="Sale_amount", height=350, nbins=20, color_discrete_sequence=["darkred"]))
            with subtabs[3]:
                st.plotly_chart(px.histogram(towndata, x="Age_at_sale", y="Sale_amount", height=350, nbins=20, color_discrete_sequence=["darkred"]))
        
        with tabs[1]:
            temp = data.groupby('Sale_date')['Sale_amount'].sum().reset_index()
            st.plotly_chart(px.line(temp, x="Sale_date", y="Sale_amount", height=380, color_discrete_sequence=["darkred"]))
        
        with tabs[2]:
            X = towndata[["Beds", "Baths", "Sqft_home", "Age_at_sale"]]
            y = towndata["Sale_amount"]
            model = RandomForestRegressor()
            model.fit(X, y)

            st.write("Input values to predict the price")
            c1, c2 = st.columns(2)
            with c1:
                beds = st.text_input("Number of Beds", value="3")
                baths = st.text_input("Number of Baths", value="2")
            with c2:
                sqft_home = st.text_input("Square Footage of Home", value="2000")
                age_at_sale = st.text_input("Age of Home at Sale", value="10")

            # Predict sale amount on submit
            if st.button("Estimate Sale Amount"):
                try:
                    input = pd.DataFrame({
                        'Beds': [float(beds)],
                        'Baths': [float(baths)],
                        'Sqft_home': [float(sqft_home)],
                        'Age_at_sale': [float(age_at_sale)]
                    })
                    
                    # Predict
                    prediction = model.predict(input)[0]
                    st.write(f"Estimated Sale Amount: ${prediction:,.2f}")
                except ValueError:
                    st.write("Please enter valid numeric values.")

