import streamlit as st
import psycopg2
import json


def init_connection():
    return psycopg2.connect(**st.secrets["postgres"])

conn = init_connection()

c = conn.cursor()

#fetch data
#Table 1
@st.cache_data
def view_all_total_pop_data():
   c.execute("SELECT * from total_pop_data_1961_2022")
   data = c.fetchall()
   return data


#Table 2
@st.cache_data
def view_pop_by_nationality_data():
   c.execute("SELECT * from pop_by_nationality_data")
   data = c.fetchall()
   return data

#Table 3
@st.cache_data
def view_projected_pop_data_2020_2040():
   c.execute("SELECT * from projected_pop_data_2020_2040")
   data = c.fetchall()
   return data


#Table 4
@st.cache_data
def view_migration_pop_data():
   c.execute("SELECT * from migration_pop_data")
   data = c.fetchall()
   return data

#Table 5
@st.cache_data
def view_birth_death_pop_data():
   c.execute("SELECT * from birth_death_pop_data")
   data = c.fetchall()
   return data


#Table 6
@st.cache_data
def view_population_since_2011_data():
   c.execute("SELECT * from population_since_2011")
   data = c.fetchall()
   return data


#Table 7
@st.cache_data
def view_studyarea_stuttgart():
    # Replace these values with your database connection details
   
    c = conn.cursor()
    c.execute("SELECT id, name, schluessel, ST_AsGeoJSON(wkb_geometry), centroid_lat, centroid_lon FROM studyarea_stuttgart")
    geodata = c.fetchall()
    
    
    # Convert the data to GeoJSON format
    features = []
    for row in geodata:
        feature = {
            "type": "Feature",
            "geometry": json.loads(row[3]),  # Convert GeoJSON string to dict
            "properties": {
                "id": row[0],
                "name": row[1],
                "schluessel": row[2],
                "centroid_lat": row[4],
                "centroid_lon": row[5],
                
            }
        }
        features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    return geojson