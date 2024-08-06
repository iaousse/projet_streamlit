# main.py
import streamlit as st
import pandas as pd
import geopandas as gpd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import folium
from folium.features import GeoJsonTooltip
from streamlit_folium import folium_static

#import bcrypt

combined_data = pd.read_parquet('data/combined_data.parquet')
provinces_data = pd.read_parquet('data/provinces.parquet')
geojson_provinces = gpd.read_file('data/updated_provinces.json')
geojson_regions = gpd.read_file('data/updated_maroc.geojson')
grappes_regions = pd.read_parquet('data/grappes_regions.parquet')
circles_data = pd.read_parquet('data/cercles.parquet')  # Ajouter les données des cercles
#print("combined_data")
#print(combined_data['cldh_label'].head())

combined_data['cldh_label'] = combined_data['cldh_label'].astype(str).str.strip()
circles_data['cldh_label'] = circles_data['cldh_label'].astype(str).str.strip()

# Agrégation des données par cercle
circle_data = combined_data.groupby('cldh_label').agg(
expra_1=('expra', lambda x: (x == 1).sum()),
expra_0=('expra', lambda x: (x == 0).sum()),
unique_grappe=('grappe', pd.Series.nunique)
).reset_index()

# Fusion avec circles_data
circle_data = circle_data.merge(circles_data, left_on='cldh_label', right_on='cldh_label')
print(circle_data.columns)
print(circle_data.head())
circle_data = circle_data.merge(combined_data[['cldh_label', 'province_label']].drop_duplicates(), on='cldh_label', how='left')
print(circle_data.head())