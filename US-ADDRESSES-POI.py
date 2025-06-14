import streamlit as st
import pandas as pd
import snowflake.connector
import pydeck as pdk
import plotly.express as px

# Streamlit UI Configuration
st.set_page_config(page_title="US POI Map", layout="wide")
st.title("📍 US POI Map Viewer")
st.markdown("View Points of Interest from Snowflake with Map, Filters, and Visualizations")

# Snowflake connection
conn = snowflake.connector.connect(
    user=st.secrets["snowflake"]["user"],
    password=st.secrets["snowflake"]["password"],
    account=st.secrets["snowflake"]["account"],
    warehouse=st.secrets["snowflake"]["warehouse"],
    database=st.secrets["snowflake"]["database"],
    schema=st.secrets["snowflake"]["schema"]
)

# Fetch data
query = "SELECT * FROM POI_ADDRESS_US"
df = pd.read_sql(query, conn)
conn.close()

# Clean data
df = df.dropna(subset=["LATITUDE", "LONGITUDE"])

# Sidebar filters
st.sidebar.header("🔍 Filter Options")
category_options = df["CATEGORY_MAIN"].dropna().unique()
category = st.sidebar.selectbox("Select Category", sorted(category_options))

filtered_df = df[df["CATEGORY_MAIN"] == category]

state_options = ["All"] + sorted(filtered_df["STATE"].dropna().unique())
state = st.sidebar.selectbox("Select State", state_options)
if state != "All":
    filtered_df = filtered_df[filtered_df["STATE"] == state]

city_options = ["All"] + sorted(filtered_df["CITY"].dropna().unique())
city = st.sidebar.selectbox("Select City", city_options)
if city != "All":
    filtered_df = filtered_df[filtered_df["CITY"] == city]

# Slider for row count
row_count = st.sidebar.slider("Number of rows to display", min_value=1, max_value=len(filtered_df), value=10)

# Summary
st.success(f"Total POIs in selection: {len(filtered_df)}")

# Map view
st.subheader("🗺️ Map View")
st.pydeck_chart(pdk.Deck(
    initial_view_state=pdk.ViewState(
        latitude=filtered_df["LATITUDE"].mean(),
        longitude=filtered_df["LONGITUDE"].mean(),
        zoom=10,
        pitch=40,
    ),
    layers=[
        pdk.Layer(
            "ScatterplotLayer",
            data=filtered_df,
            get_position='[LONGITUDE, LATITUDE]',
            get_color='[0, 128, 255, 160]',
            get_radius=150,
            pickable=True,
        ),
    ],
    tooltip={"text": "{POI_NAME}\n{CATEGORY_MAIN}\n{CITY}, {STATE}"}
))

# Data table
st.subheader("📋 Selected POI Records")
st.dataframe(filtered_df[["POI_NAME", "CATEGORY_MAIN", "CITY", "STATE", "LATITUDE", "LONGITUDE"]].head(row_count))

# Download button
st.download_button(
    label="⬇️ Download Filtered Data as CSV",
    data=filtered_df.to_csv(index=False),
    file_name="filtered_poi_data.csv",
    mime="text/csv"
)

# Category distribution chart
st.subheader("📊 POI Category Distribution (All Data)")
category_counts = df["CATEGORY_MAIN"].value_counts().reset_index()
category_counts.columns = ["Category", "Count"]
st.bar_chart(category_counts.set_index("Category"))

# Pie chart
st.subheader("📈 Category Distribution Pie Chart")
fig = px.pie(category_counts, names="Category", values="Count", title="POIs by Category")
st.plotly_chart(fig)

# State-wise distribution
st.subheader("🏙️ POI Distribution by State (All Data)")
state_counts = df["STATE"].value_counts().reset_index()
state_counts.columns = ["State", "POI Count"]
st.bar_chart(state_counts.set_index("State"))
