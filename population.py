import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_navigation_bar import st_navbar
import plotly.express as px
import plotly.graph_objs as go
from pgadmin_test import *
import numpy as np
import matplotlib.pyplot as plt





APP_TITLE = "Population Dashboard of Stuttgart"
APP_SUB_TITLE = "Source: [Statistisches Landesamt Baden-Württemberg](<https://www.statistik-bw.de/>)."

@st.cache_data    
def display_total_pop_facts(totalPop_df, district, year, newInsgesamt_field_name, metric_title):
    totalPop_df = totalPop_df[totalPop_df["jahr"] == year]
    if district:
        totalPop_df = totalPop_df[totalPop_df['landkreis'] == district]
    totalPop_df.drop_duplicates(inplace=True)
    totalPop = totalPop_df[newInsgesamt_field_name].sum()
    st.metric(metric_title, "{:,}".format(totalPop))
    

@st.cache_data
# Defining a new set of functions for Migration and BirthDeath db Tables
def display_total_migration_facts(migration_pop_df, district, year, migrate_WandInsgesamt_field_name, metric_title):
    migration_pop_df = migration_pop_df[migration_pop_df["jahr"] == year]
    if district:
        migration_pop_df = migration_pop_df[migration_pop_df["landkreis"] == district]
    migration_pop_df.drop_duplicates(inplace=False)
    totalWMigration = migration_pop_df[migrate_WandInsgesamt_field_name].sum()
    st.metric(metric_title, "{:,}".format(totalWMigration))


@st.cache_data
# Define a function for birth -------------------Up Next----------------
def display_total_birth_death_facts(birth_death_pop_df, district, year, birth_Insgesamt_field_name, metric_title):
    birth_death_pop_df = birth_death_pop_df[birth_death_pop_df["jahr"] == year]
    if district:
        birth_death_pop_df = birth_death_pop_df[birth_death_pop_df["landkreis"] == district]
    birth_death_pop_df.drop_duplicates(inplace=False)
    totalBirth = birth_death_pop_df[birth_Insgesamt_field_name].sum()
    st.metric(metric_title, "{:,}".format(totalBirth))

    # The Exponential Growth Model
def simulate_population_growth(initial_population, growth_rate, min_years, max_years):
    years = np.arange(min_years, max_years + 1)
    population = np.zeros(max_years - min_years + 1)
    population[0] = initial_population

    for t in range(1, max_years - min_years + 1):
        population[t] = population[t - 1] * (1 + growth_rate)
    return population


@st.cache_data
def get_district_coordinates():
    # Dummy coordinates for districts; replace with actual coordinates
    return {
        "Boeblingen": [48.678097564, 9.04276968349], #48.678097564, 9.94276968349],
        "Esslingen": [48.6481325204, 9.46869657201],
        "Goeppingen": [48.6630544963, 9.81755934689],
        "Rems-Murr": [48.8988202781, 9.61121998845],
        "Stuttgart": [48.775075166, 9.27205043906],
        "Ludwigsburg": [48.9400458226, 9.2230483754]
        # Add more districts and their coordinates here
    }

# Initialize the map object outside the function

m = folium.Map(location=[48.771, 9.881], zoom_start=9, scrollWheelZoom=True)

def display_map(totalPop_df, year, newInsgesamt_field_name, selected_color_theme, selected_district, map_key):
    district_coords = get_district_coordinates()
    
   

    # Add selected base map
    selected_basemap = st.sidebar.radio("Select Base Map", 
                                        ["CartoDb Positron", 
                                         "OpenStreetMap", 
                                         "Cartodb Dark Matter", 
                                         "Esri World Imagery"], 
                                        index=0)
    if selected_basemap == "CartoDb Positron":
        folium.TileLayer("cartodbpositron", name="CartoDb Positron").add_to(m)
    elif selected_basemap == "OpenStreetMap":
        folium.TileLayer("openstreetmap", name="OpenStreetMap").add_to(m)
    elif selected_basemap == "Cartodb Dark Matter":
        folium.TileLayer("cartodbdark_matter", name="Cartodb Dark Matter").add_to(m)
    elif selected_basemap == "Esri World Imagery":
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri",
            name="Esri World Imagery"
        ).add_to(m)

    show_study_area = st.sidebar.checkbox("Show Study Area Layer", value=True)
   
    if show_study_area:
        # Add study area to the choropleth layer
       
        study_area_geojson = view_studyarea_stuttgart()
        totalPop_df_year = totalPop_df[totalPop_df["jahr"] == year]

        choropleth = folium.Choropleth(
            geo_data=study_area_geojson,
            data=totalPop_df_year,
            columns=("landkreis", newInsgesamt_field_name),
            key_on='feature.properties.name',
            fill_color=selected_color_theme,
            line_opacity=0.9,
            highlight=True,
            name="Choropleth"
        )
        
        totalPop_df_year = totalPop_df_year.set_index("landkreis")
        totalPop_df_year.drop_duplicates(inplace=True)
        
        

        # Define the HTML template for the label with a dynamic font size
        # Define the HTML template for the label with a dynamic font size
        html_template = """
        <div id="district_name_{district_name}" style="font-size: <script>updateFontSize(zoom)</script>px; color: #333333">{district_name}</div>
        """

        # Define the JavaScript to set the font size based on the map's zoom level
        js_font_size = """
        <script>
        function updateFontSize(zoom) {
            var size = zoom * 1;  // Adjust the scaling factor as needed
            return size;
        }
        </script>
        """

        # Iterate through each feature in the GeoJSON data and add labels as text on the map
        for feature in choropleth.geojson.data["features"]:
            district_name = feature["properties"]["name"]
            population = totalPop_df_year.loc[district_name, newInsgesamt_field_name] if district_name in totalPop_df_year.index else "N/A"
            feature["properties"]["population"] = f"Population: {population:,}"
            centroid_lat = feature["properties"]["centroid_lat"]
            centroid_lon = feature["properties"]["centroid_lon"]
            
            # Add the JavaScript and district name to the HTML template
            html = js_font_size + html_template.format(district_name=district_name)
            
            # Create the label marker
            label = folium.map.Marker(
                [centroid_lat, centroid_lon], 
                icon=folium.features.DivIcon(
                    icon_size=(150, 36),
                    icon_anchor=(7, 20),
                    html=html
                )
            )
            
            # Add the label marker to the map
            label.add_to(m)

        choropleth.geojson.add_child(
            folium.features.GeoJsonTooltip(["name", "population"], labels=False)
        ).add_to(m)
        
    

        district_name_click = ""

        # If a district is selected, re-center and zoom the map
        if selected_district in district_coords:
            district_coord = district_coords[selected_district]
            m.fit_bounds([district_coord], max_zoom=11)

    else:
        # If not checked, provide an empty GeoJSON object
        study_area_geojson = {
            "type": "FeatureCollection",
            "features": []
        }
        district_name_click = ""

    st_folium(m, width=950, height=550, key=map_key)

    return district_name_click


    

def display_time_filters(totalPop_df):
    totalPop_df['jahr'] = totalPop_df['jahr'].str.extract('(\d{4})')
    year_list = list(totalPop_df["jahr"].unique())
    year_list.sort(reverse=True)
    selected_year = st.sidebar.selectbox("Year", year_list, key="year_selectbox")
    st.subheader(f"Population Summary in {selected_year}")
    return selected_year




    
def get_value(dataframe, district, year, field_name, label):
    value = dataframe[(dataframe['landkreis'] == district) & (dataframe['jahr'] == year)]
    if not value.empty:
        value = value[field_name].values[0]
        return f"<span style='font-size: smaller;'>{label}:<br>{value}</span>"
    else:
        return f"<span style='font-size: smaller;'>{label}:<br>Data not available</span>"




def generate_color_scale(values, selected_color_theme):
    # Get the color scale based on the selected theme
    color_scale = getattr(px.colors.sequential, selected_color_theme)
    
    # Normalize values between 0 and 1
    normalized_values = (values - min(values)) / (max(values) - min(values))
    
    # Get colors based on normalized values
    colors = [color_scale[int(value * (len(color_scale) - 1))] for value in normalized_values]

    
    return colors



def display_color_scale(selected_color_theme, width):
    # Get the color scale based on the selected theme
    color_scale = getattr(plt.cm, selected_color_theme)

    # Create a figure and axis without frame and axis
    fig, ax = plt.subplots(figsize=(width, 0.8))
    ax.axis('off')

    # Set the face color of the figure and axis to be transparent
    fig.patch.set_facecolor('none')
    ax.set_facecolor('none')

    # Create a color bar
    cbar = plt.colorbar(plt.cm.ScalarMappable(cmap=color_scale), ax=ax, orientation='horizontal')
    cbar.set_label('Color Scale', fontsize=9, color='white', labelpad=10)  # Set label color to white and adjust padding
    cbar.ax.tick_params(labelsize=8, colors='white')  # Set tick label color to white

    # Set tick labels as 'low' and 'high'
    cbar.set_ticks([0, 1])
    cbar.ax.set_xticklabels(['Low', 'High'])

    # Display the plot in Streamlit
    st.pyplot(fig)




def main():
    st.set_page_config(APP_TITLE, layout="wide")
    
    page = st_navbar(["Map Dashboard", "Simulation", "Data", "About"])
    # st.write(page)
    if page == "Map Dashboard":
        st.header("Population Dashboard of Stuttgart", divider="rainbow")
        # st.title(APP_TITLE) #Hochschule für Technik Stuttgart - GIS Studio 
        st.caption(APP_SUB_TITLE)
     
        
        

        #Load Data in Main
        #process data from query
        result_totalPop = view_all_total_pop_data()
        totalPop_df = pd.DataFrame(result_totalPop, 
                                   columns=["landkreis", 
                                            "id", 
                                            "jahr", 
                                            "insgesamt", 
                                            "unter_15", 
                                            "von_15_bis_18",
                                            "von_18_bis_25",
                                            "von_25_bis_40", 
                                            "von_40_bis_65", 
                                            "ab_65", 
                                            "primary_id"] )
   

        result_popNationality = view_pop_by_nationality_data()
        popNationality_df = pd.DataFrame(result_popNationality, columns=["id", "landkreis", "jahr", "insgesamt", "maennlich_insgesamt", "zusammen_Deutsche", "maennlich_Deutsche", "zusammen_Auslaender", "maennlich_Auslaender"] )

        result_projected_pop = view_projected_pop_data_2020_2040()
        projected_pop_df = pd.DataFrame(result_projected_pop, columns=["landkreis","id", "jahr", "insgesamt", "under_20", "von_20_bis_40", "von_40_bis_60", "von_60_bis_85", "ab_85", "primary_id"] )

        result_migration_pop = view_migration_pop_data()
        migration_pop_df = pd.DataFrame(result_migration_pop, columns=["landkreis_code", "landkreis", "jahr", "zugezo_insgesamt", "zugezo_maennlich", "fortgezo_insgesamt", "fortgezo_maennlich", "wandersaldo_insgesamt", "wandersaldo_maennlich", "id"] )

        result_birth_death_pop = view_birth_death_pop_data()
        birth_death_pop_df = pd.DataFrame(result_birth_death_pop, columns=["landkreis_code", "landkreis", "jahr", "lebendge_insgesamt", "lebendge_maennlich", "gestorb_insgesamt", "gestorb_maennlich", "geburten_uebersc_insgesamt", "geburten_uebersc_maennlich", "id"] )

        result_pop_since_2011 = view_population_since_2011_data()
        pop_since_2011_df = pd.DataFrame(result_pop_since_2011, columns=["landkreis", "id", "im_alter_von", "bev_insgesamt", "bev_maennlich", "bev_weiblich", "aus_zusammen", "aus_maennlich", "aus_weiblich"] )
    
        st.sidebar.image("./stuttgart_data/hft.ico", width=150)


        # DISPLAY FILTERS AND MAP
        map_column_totalpop_nat,  map_column, charts_3_column = st.columns([1, 1.7, 1])
        chart_row1, chart_row2 = charts_3_column.columns(2)
        table_totalpop_district = map_column_totalpop_nat.empty()
        chart_totapop = map_column_totalpop_nat.empty()
        chart_row1 = charts_3_column.empty()
        chart_row2 = charts_3_column.empty()
        chart_totalnat_district, col_migrate_2, chart_row2_pyramid = st.columns([1, 2, 1])
        
        
        # Sidebar for color theme selection
        # Define the color theme mapping
        color_theme_mapping = {
            'Yellow-Green': 'YlGn',
            'Yellow-Green-Blue': 'YlGnBu',
            'Green-Blue': 'GnBu',
            'Blue-Green': 'BuGn',
            'Purple-Blue-Green': 'PuBuGn',
            'Purple-Blue': 'PuBu',
            'Blue-Purple': 'BuPu',
            'Red-Purple': 'RdPu',
            'Purple-Red': 'PuRd',
            'Orange-Red': 'OrRd',
            'Yellow-Orange-Red': 'YlOrRd',
            'Yellow-Orange-Brown': 'YlOrBr',
            'Purples': 'Purples',
            'Blues': 'Blues',
            'Greens': 'Greens',
            'Oranges': 'Oranges',
            'Reds': 'Reds',
            'Greys': 'Greys'
        }

        with st.sidebar:
            selected_color_theme_name = st.selectbox('Select a color theme for heatmap', 
                                                     list(color_theme_mapping.keys()), 
                                                     key="color_theme_selectbox")
            if selected_color_theme_name in color_theme_mapping:
                selected_color_theme = color_theme_mapping[selected_color_theme_name]
            else:
                # If the selected color theme name is not found, use a default color theme
                selected_color_theme = 'Blues'  # Default color theme
            width = 2 
            display_color_scale(selected_color_theme, width)
            selected_district = st.selectbox("Select District", 
                                             ["Stuttgart"] + 
                                             sorted(totalPop_df["landkreis"].unique()), 
                                             index=0, 
                                             key="district_selectbox")

        

        # Main Content
        with map_column:
            selected_year = display_time_filters(totalPop_df)

            district_name_map_click = display_map(totalPop_df, 
                                                  selected_year, 
                                                  "insgesamt", 
                                                  selected_color_theme, 
                                                  selected_district, 
                                                  map_key="map_widget")
            if district_name_map_click:
                selected_district = district_name_map_click


        # DISPLAY METRICS
        
        # st.markdown("<hr>", unsafe_allow_html=True)  # Horizontal line using HTML
            
        
        # Total Population by district based on the selected year
        
        filtered_data = totalPop_df[totalPop_df['jahr'] == selected_year]

        # Generate color scale based on selected theme
        colors = generate_color_scale(filtered_data['insgesamt'], selected_color_theme)

        # Create a Plotly bar chart with colors
        fig_only_district = go.Figure(data=[
            go.Bar(x=filtered_data['landkreis'], y=filtered_data['insgesamt'], marker_color=colors)
        ])

        
        # Create a Plotly pie chart
        fig_only_district = go.Figure(data=[
            go.Pie(labels=filtered_data['landkreis'], values=filtered_data['insgesamt'], marker=dict(colors=colors))
        ])

        # Update layout
        fig_only_district.update_layout(
            title=f"Total Population by District in the Year {selected_year}",
            template='plotly_white',  
            width=400,
            height=400,
            legend=dict(
                x=-0.1,
                y=0.5,
                traceorder="normal"
            )
        )


        map_column_totalpop_nat, map_column, charts_3_column = st.columns([3, 1, 1])

        with chart_totapop:
            st.plotly_chart(fig_only_district)

        
        # ----------Create an empty DataFrame to store the projected population chart data--------
        selected_data_projected = projected_pop_df[projected_pop_df["landkreis"] == selected_district]

        # Rename columns
        selected_data_renamed = selected_data_projected.rename(columns={
            "under_20": "Under 20",
            "von_20_bis_40": "20-40",
            "von_40_bis_60": "40-60",
            "von_60_bis_85": "60-85",
            "ab_85": "85+"
        })

        # Get the base year values (2020)
        base_year = "20201)"
        
        base_year_data = selected_data_renamed[selected_data_renamed["jahr"] == base_year]

        if not base_year_data.empty:
            base_year_data = base_year_data.iloc[0]

            # Calculate the percentage for each age group based on the base year
            for age_group in ["Under 20", "20-40", "40-60", "60-85", "85+"]:
                selected_data_renamed[f'{age_group} (%)'] = (selected_data_renamed[age_group] / base_year_data[age_group]) * 100

            # Create a Plotly figure
            prjfig = go.Figure()

            # Add traces for each age group percentage
            for age_group in ["Under 20 (%)", "20-40 (%)", "40-60 (%)", "60-85 (%)", "85+ (%)"]:
                prjfig.add_trace(go.Scatter(x=selected_data_renamed["jahr"], y=selected_data_renamed[age_group], mode='lines+markers', name=age_group))

            # Update layout
            prjfig.update_layout(
                title=dict(
                    text=f"Projected Population by Age (%) in {selected_district}",
                    font=dict(size=16) 
                ),
                xaxis_title=dict(
                    text="Year",
                    font=dict(size=14)
                ),
                yaxis_title=dict(
                    text=f"% (base year {base_year[:-2]}) = 100%)",
                    font=dict(size=14)  
                ),
                legend_title=dict(
                    text="Age Group",
                    font=dict(size=12)  
                ),
                template='plotly_white',  
                yaxis=dict(
                    range=[0, 200],
                    tickfont=dict(size=12)  
                ), 
                xaxis=dict(
                    tickangle=270,
                    tickvals=[tick for tick in selected_data_renamed["jahr"]],  # Include all years as tick values
                    ticktext=[str(tick)[:-2] if tick == base_year else str(tick) for tick in selected_data_renamed["jahr"]],
                    tickfont=dict(size=12)  # Change font size for the x-axis labels
                ),
                width=400,  
                height=350 
            )
            
            with chart_row1:
                st.plotly_chart(prjfig)
        else:
            pass
        


        
        # ----------Create an empty DataFrame to store the Migration chart data-------
        
        migration_barchart_data = pd.DataFrame()
        
        for landkreis in migration_pop_df['landkreis'].unique():
            landkreis_data = migration_pop_df[migration_pop_df['landkreis'] == landkreis]
            migration_barchart_data[landkreis] = landkreis_data.set_index('jahr')['wandersaldo_insgesamt']  # Set 'jahr' as the index and add data to chart_data

        # Reset the index to use 'jahr' as a column
        migration_barchart_data.reset_index(inplace=True)

        # Melt the DataFrame to a long format for Plotly
        migration_barchart_data_long = migration_barchart_data.melt(id_vars=['jahr'], var_name='District', value_name='Migration Balance')

        mgrtfig = px.bar(migration_barchart_data_long, x='jahr', y='Migration Balance', color='District', barmode='group',
                    title='Total Migration Balance from 2015 to 2022 by District', labels={'jahr': 'Year', 'Migration Balance': 'Migration Balance'})

        # Update layout to make tick labels horizontal
        mgrtfig.update_layout(xaxis_tickangle=0)
        mgrtfig.update_layout(width=750, height=350)

            
        with col_migrate_2:
            st.plotly_chart(mgrtfig)


    # Population by Nationality Chart
        nationality_barchart_data = pd.DataFrame()

        # Loop through each unique 'landkreis' and add its data to the DataFrame
        for landkreis in popNationality_df['landkreis'].unique():
            landkreis_data = popNationality_df[popNationality_df['landkreis'] == landkreis]
            landkreis_data = landkreis_data.set_index('jahr')  # Set 'jahr' as the index
            nationality_barchart_data[f'{landkreis}'] = landkreis_data["zusammen_Auslaender"]

        nationality_bar_chart = px.bar(nationality_barchart_data, height=250, width=400)

        nationality_bar_chart.update_layout(
            legend=dict(x=1, y=0),  # Position the legend to the left side
            title="Nationality (Foreigners) in the Six Counties",
            xaxis_title="Year",
            yaxis_title="Population",
            template='plotly_white',
        )

        with chart_totalnat_district:
            st.plotly_chart(nationality_bar_chart)

        selected_data_birth_death = birth_death_pop_df[birth_death_pop_df["landkreis"] == selected_district]
        
        # Rename columns
        selected_data_renamed = selected_data_birth_death.rename(columns={
            "lebendge_insgesamt": "Total live births", 
            "lebendge_maennlich": "Total male live births", 
            "gestorb_insgesamt": "Total deaths", 
            "gestorb_maennlich": "Total male deaths", 
            "geburten_uebersc_insgesamt": "Total surplus/deficit", 
            "geburten_uebersc_maennlich": "Total male surplus/deficit"
        })

        # Get the base year values (2018)
        base_year = "2018"
        base_year_data = selected_data_renamed[selected_data_renamed["jahr"] == base_year]

        if not base_year_data.empty:
            base_year_data = base_year_data.iloc[0]

            # Calculate the percentage for each age group based on the base year
            for age_group in ["Total live births", "Total deaths", "Total surplus/deficit"]:
                selected_data_renamed[f'{age_group} (%)'] = (selected_data_renamed[age_group] / base_year_data[age_group]) * 100

            brt_fig = go.Figure()

            # Add traces for each age group percentage
            for age_group in ["Total live births (%)", "Total deaths (%)", "Total surplus/deficit (%)"]:
                brt_fig.add_trace(go.Scatter(x=selected_data_birth_death["jahr"], y=selected_data_renamed[age_group], mode='lines+markers', name=age_group))

            brt_fig.update_layout(
                title=f"Birth surplus (+) or deficit (-) in {selected_district}",
                xaxis_title="Year",
                yaxis_title="% (base year 2018 = 100%)",
                legend_title="Age Group",
                template='plotly_white',
                width=450,  
                height=300  
            )
          
            with chart_row2:
                st.plotly_chart(brt_fig)
        else:
            pass
            # st.warning(f"Select District to view the Birth Surplus/Deficit of the Base Year {base_year}")


        

             
        
           
        
        # <-----------The Population Pyramid chart in chart_row3---------------------------->
        with chart_row2_pyramid:
            landkreis_data = pop_since_2011_df[(pop_since_2011_df['landkreis'] == selected_district) & 
                                            (~pop_since_2011_df['im_alter_von'].str.contains('Insgesamt'))]

            if landkreis_data.empty:
                pass
                # st.warning(f"You have not yet selected a district to view the population pyramid: {selected_district}")
            else:
                # Separate the data for males and females
                male_data = landkreis_data[['im_alter_von', 'bev_maennlich']].copy()
                female_data = landkreis_data[['im_alter_von', 'bev_weiblich']].copy()

                # Check if male_data or female_data is empty
                if male_data.empty or female_data.empty:
                    st.error(f"No male or female population data available for the selected district: {selected_district}")
                else:
                    # Calculate the total population for each gender
                    total_male_population = male_data['bev_maennlich'].sum()
                    total_female_population = female_data['bev_weiblich'].sum()

                    # Normalize the populations to percentages
                    male_data['bev_maennlich'] = (male_data['bev_maennlich'] / total_male_population) * 100
                    female_data['bev_weiblich'] = (female_data['bev_weiblich'] / total_female_population) * 100

                    # Create a horizontal bar chart for males
                    pop_pyramid_fig = go.Figure()

                    pop_pyramid_fig.add_trace(go.Bar(
                        y=male_data['im_alter_von'],  # y-axis: Age groups
                        x=-male_data['bev_maennlich'],  # x-axis: Male population (negated percentages)
                        orientation='h',  # Horizontal orientation
                        name='Male',
                        text=male_data['bev_maennlich'].abs().round(2).astype(str) + '%',
                        textposition='outside',
                        hoverinfo='x'
                    ))

                    # Create a horizontal bar chart for females
                    pop_pyramid_fig.add_trace(go.Bar(
                        y=female_data['im_alter_von'],  # y-axis: Age groups
                        x=female_data['bev_weiblich'],  # x-axis: Female population (percentages)
                        orientation='h',  # Horizontal orientation
                        name='Female',
                        text=female_data['bev_weiblich'].round(2).astype(str) + '%',
                        textposition='outside',
                        hoverinfo='x'
                    ))

                    # Set layout for the chart
                    max_percentage = max(male_data['bev_maennlich'].max(), female_data['bev_weiblich'].max())
                    pop_pyramid_fig.update_layout(
                        title=f"Population Pyramid of {selected_district} Since 2011",
                        xaxis_title="Population Percentage",
                        yaxis_title="Age Group",
                        barmode='relative',  # Ensure bars are plotted relative to each other
                        xaxis=dict(
                            tickvals=[-max_percentage, 0, max_percentage],
                            ticktext=[f"{max_percentage:.2f}%", "0%", f"{max_percentage:.2f}%"],
                            tickfont=dict(size=14)  
                        ),
                        yaxis=dict(
                            tickfont=dict(size=14) 
                        ),
                        template='plotly_white',
                        width=450,  
                        height=300 
                    )
                    st.plotly_chart(pop_pyramid_fig)
        
        
        
    # <-------THIS SECTION IS FOR THE PROGRESS TABLE REPRESENTING TOTAL POPULATION--------->
        filtered_totalPop_df = totalPop_df[totalPop_df["jahr"] == selected_year].sort_values(by="insgesamt", ascending=False)
        with table_totalpop_district:
            table_totalpop_district.header("Total Population by District")
            table_totalpop_district.dataframe(filtered_totalPop_df,
                         column_order=("landkreis", "insgesamt"),
                         hide_index=True,
                         width=None,
                         column_config={
                             "landkreis": st.column_config.TextColumn(
                                 "District",
                             ),
                             "insgesamt": st.column_config.ProgressColumn(
                                 "Population",
                                 format="%f",
                                 min_value=0,
                                 max_value=max(filtered_totalPop_df.insgesamt),
                             )}
                         )
        
        
        
        
        


        
        
        
    elif page == "Simulation":
        
        # Load data
        result_totalPop = view_all_total_pop_data()
        totalPop_df = pd.DataFrame(result_totalPop, 
                                   columns=["landkreis", 
                                            "id", "jahr", 
                                            "insgesamt", "unter_15", 
                                            "von_15_bis_18",
                                            "von_18_bis_25",
                                            "von_25_bis_40", 
                                            "von_40_bis_65", 
                                            "ab_65", "primary_id"])    

        totalPop_df['jahr'] = totalPop_df['jahr'].str.extract('(\d{4})')
        totalPop_df['jahr'] = totalPop_df['jahr'].str.strip().astype(int)
    
    
    
    # <------------THIS SECTION IS FOR THE SIMUALTION OF A SINGLE DISTRICT----------------->
        
        # Sidebar for selecting simulation type
        st.sidebar.header("Simulation Type")
        simulation_type = st.sidebar.radio("Select Simulation Type", ("Single District", "Multiple Districts"))

        # Sidebar for selecting year
        year_options = sorted(totalPop_df['jahr'].unique(), reverse=True)
        selected_year = st.sidebar.selectbox("Select Year", year_options)

        if simulation_type == "Single District":
            # Sidebar for selecting district
            district_options = totalPop_df['landkreis'].unique()
            selected_district = st.sidebar.selectbox("Select District", district_options)
            
            # Filter the DataFrame for the selected year and district
            filtered_df = totalPop_df[(totalPop_df["jahr"] == selected_year) & (totalPop_df["landkreis"] == selected_district)]
            
            # Extract the initial population from the insgesamt column
            if not filtered_df.empty:
                initial_population_value = int(filtered_df["insgesamt"].values[0])
            else:
                st.warning("Sorry! There is either no data available for the selected district and year or you made a wrong choice.")
                initial_population_value = 0  # Default value if no data is found

            # Sidebar for simulation parameters
            st.sidebar.header("Simulation Parameters")
            initial_population = st.sidebar.number_input("Initial Population", value=initial_population_value, step=1)
            growth_rate = st.sidebar.slider("Annual Growth Rate (%)", min_value=0.0, max_value=10.0, value=2.0) / 100.0
            min_years = st.sidebar.number_input("Minimum Year", value=selected_year, step=1)
            max_years = st.sidebar.number_input("Maximum Year", value=selected_year + 28, step=1)
            
            # Simulate population growth
            population_values = simulate_population_growth(initial_population, growth_rate, min_years, max_years)
            
            # Create a Plotly line plot
            fig = px.line(x=range(min_years, max_years + 1), y=population_values, labels={"x": "Year", "y": "Population"})
            fig.update_xaxes(tickvals=list(range(min_years, max_years + 1)))
            fig.update_traces(mode="lines+markers", line=dict(color='green'))
            
            # Set axis ranges
            fig.update_xaxes(range=[min_years - 1, max_years + 1])
            fig.update_yaxes(range=[0, max(population_values) * 1.3])
            fig.update_layout(title=f'Simulated Population Growth for {selected_district} from {min_years} to {max_years}')
            
            # Display the plot in Streamlit
            st.plotly_chart(fig, use_container_width=True)

        elif simulation_type == "Multiple Districts":
            # Sidebar for selecting districts
            district_options = totalPop_df['landkreis'].unique()
            selected_districts = st.sidebar.multiselect("Select District(s)", district_options, default=district_options[0])
            
            # Sidebar for simulation parameters
            st.sidebar.header("Simulation Parameters")
            growth_rate = st.sidebar.slider("Annual Growth Rate (%)", min_value=0.0, max_value=10.0, value=2.0) / 100.0
            min_years = st.sidebar.number_input("Minimum Year", value=selected_year, step=1)
            max_years = st.sidebar.number_input("Maximum Year", value=max(year_options) + 28, step=1)
            
            # Create a Plotly figure
            fig = go.Figure()
            
            for selected_district in selected_districts:
                # Filter the DataFrame for the selected year and district
                filtered_df = totalPop_df[(totalPop_df["jahr"] == selected_year) & (totalPop_df["landkreis"] == selected_district)]
                
                # Extract the initial population from the insgesamt column
                if not filtered_df.empty:
                    initial_population_value = int(filtered_df["insgesamt"].values[0])
                    # Simulate population growth
                    population_values = simulate_population_growth(initial_population_value, growth_rate, min_years, max_years)
                    # Add trace to the figure
                    fig.add_trace(go.Scatter(x=list(range(min_years, max_years + 1)), y=population_values, mode="lines+markers",
                                            name=f"{selected_district} {selected_year}"))
                else:
                    st.warning(f"No data available for {selected_district} in {selected_year}. Skipping.")
            
            # Update layout and display the plot
            if fig.data:
                fig.update_layout(title=f'Simulated Population Growth from {min_years} to {max_years}')
                fig.update_xaxes(tickvals=list(range(min_years, max_years + 1)))
                fig.update_xaxes(range=[min_years - 1, max_years + 1])
                fig.update_yaxes(range=[0, max([max(trace.y) for trace in fig.data]) * 1.3])
                # Display the plot in Streamlit
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Ooops! Sorry, no data available for the selected parameters. Please select the appropriate ones to see the chart.")
                
                
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        # st.write("# Simulated Population")
        # result_totalPop = view_all_total_pop_data()
        # totalPop_df = pd.DataFrame(result_totalPop, columns=["landkreis", "id", "jahr", "insgesamt", "unter_15", "von_15_bis_18","von_18_bis_25","von_25_bis_40", "von_40_bis_65", "ab_65", "primary_id"] )    
        
        
        # # <------------THIS SECTION IS FOR THE SIMUALTION OF MULTIPLE DISTRICTS----------------->
        # totalPop_df['jahr'] = totalPop_df['jahr'].str.extract('(\d{4})')
        # totalPop_df['jahr'] = totalPop_df['jahr'].str.strip().astype(int)

        # # Sidebar for selecting districts and year
        # # Sidebar for selecting districts and year
        # st.sidebar.header("Selection Parameters")
        # district_options = totalPop_df['landkreis'].unique()
        # year_options = sorted(totalPop_df['jahr'].unique(), reverse=True)

        # selected_districts = st.sidebar.multiselect("Select District(s)", district_options, default=district_options[0])
        # selected_year = st.sidebar.selectbox("Select Year", year_options)

        # # Sidebar for simulation parameters
        # st.sidebar.header("Simulation Parameters")
        # growth_rate = st.sidebar.slider("Annual Growth Rate (%)", min_value=0.0, max_value=10.0, value=2.0) / 100.0
        # min_years = st.sidebar.number_input("Minimum Year", value=selected_year, step=1)
        # max_years = st.sidebar.number_input("Maximum Year", value=max(year_options) + 28, step=1)

        # # Create a plotly figure
        # fig = go.Figure()

        # for selected_district in selected_districts:
        #     # Filter the DataFrame for the selected year and district
        #     filtered_df = totalPop_df[(totalPop_df["jahr"] == selected_year) & (totalPop_df["landkreis"] == selected_district)]

        #     # Extract the initial population from the insgesamt column
        #     if not filtered_df.empty:
        #         initial_population_value = int(filtered_df["insgesamt"].values[0])
        #         # Simulate population growth
        #         population_values = simulate_population_growth(initial_population_value, growth_rate, min_years, max_years)
        #         # Add trace to the figure
        #         fig.add_trace(go.Scatter(x=list(range(min_years, max_years + 1)), y=population_values, mode="lines+markers",
        #                         name=f"{selected_district} {selected_year}"))
        #     else:
        #         st.warning(f"No data available for {selected_district} in {selected_year}. Skipping.")

        # # Update layout and display the plot
        # if fig.data:
        #     fig.update_layout(title=f'Simulated Population Growth from {min_years} to {max_years}')
        #     fig.update_xaxes(range=[min_years - 1, max_years + 1])
        #     fig.update_yaxes(range=[0, max([max(trace.y) for trace in fig.data]) * 1.3])
        #     # Display the plot in Streamlit
        #     st.plotly_chart(fig, use_container_width=True)
        # else:
        #     st.warning("Ooops! Sorry, no data available for the selected parameters. Please select the appropriate ones to see the chart.")
                    
                
            
            
    # <----------------THIS SECTION IS FOR THE DATA FOR OUR USERS------------------------------>        
            
            
            
    
    elif page == "Data":
        st.write("# Data Page")
        
        result_totalPop = view_all_total_pop_data()
        totalPop_df = pd.DataFrame(result_totalPop, columns=["landkreis", "id", "jahr", "insgesamt", "unter_15", "von_15_bis_18","von_18_bis_25","von_25_bis_40", "von_40_bis_65", "ab_65", "primary_id"] )
        
        result_popNationality = view_pop_by_nationality_data()
        popNationality_df = pd.DataFrame(result_popNationality, columns=["id", "landkreis", "jahr", "insgesamt", "maennlich_insgesamt", "zusammen_Deutsche", "maennlich_Deutsche", "zusammen_Auslaender", "maennlich_Auslaender"])

        result_projected_pop = view_projected_pop_data_2020_2040()
        projected_pop_df = pd.DataFrame(result_projected_pop, columns=["landkreis","id", "jahr", "insgesamt", "under_20", "von_20_bis_40", "von_40_bis_60", "von_60_bis_85", "ab_85", "primary_id"])

        result_migration_pop = view_migration_pop_data()
        migration_pop_df = pd.DataFrame(result_migration_pop, columns=["landkreis_code", "landkreis", "jahr", "zugezo_insgesamt", "zugezo_maennlich", "fortgezo_insgesamt", "fortgezo_maennlich", "wandersaldo_insgesamt", "wandersaldo_maennlich", "id"])

        result_birth_death_pop = view_birth_death_pop_data()
        birth_death_pop_df = pd.DataFrame(result_birth_death_pop, columns=["landkreis_code", "landkreis", "jahr", "lebendge_insgesamt", "lebendge_maennlich", "gestorb_insgesamt", "gestorb_maennlich", "geburten_uebersc_insgesamt", "geburten_uebersc_maennlich", "id"])
        st.write("## Total Population")
        st.dataframe(totalPop_df)
                
        st.write("## Population by Nationality")
        st.dataframe(popNationality_df)
        
        st.write("## Projected Population (2020-2040)")
        st.dataframe(projected_pop_df)
        
        st.write("## Migration Population Data")
        st.dataframe(migration_pop_df)
        
        st.write("## Birth and Death Population Data")
        st.dataframe(birth_death_pop_df)
        
        








    # <----------------THIS SECTION IS THE ABOUT SECTION OF OUR DASHBOARD------------------------->  

    elif page == "About":
        st.title("About the Population Dashboard Project of Stuttgart")
        st.write("The lack of a centralized platform for storing and accessing demographic data exacerbates the challenges associated with data management and integration. Without a robust database infrastructure in place, stakeholders face difficulties in aggregating, analyzing, and visualizing demographic data from multiple sources, hindering their ability to derive meaningful insights and inform decision-making processes effectively. Furthermore, the absence of user-friendly tools and interfaces for data visualization and analysis poses additional barriers to stakeholders’ engagement with demographic data. Existing methods for presenting demographic information, such as static reports or spreadsheets, fail to leverage the full potential of data visualization techniques to communicate complex patterns and trends effectively. Moreover, the dynamic nature of population dynamics, characterized by fluctuations in birth rates, mortality rates, and migration patterns, necessitates the implementation of automatic update mechanisms to ensure the ongoing relevance and accuracy of demographic data. Without real-time or near-real-time data updates, stakeholders risk basing decisions on outdated or incomplete information, compromising the effectiveness and efficiency of their interventions. In light of these challenges, there is a compelling need to develop an online population map dashboard for the Stuttgart Sub Region. This dashboard will serve as a centralized platform for accessing, analyzing, and visualizing demographic data in real time, empowering stakeholders with the insights needed to make informed decisions and address pressing challenges facing the sub-region. By harnessing the power of web crawling, database management, and interactive visualization technologies, this project aims to overcome existing barriers to data-driven decision-making and facilitate the sustainable development and well-being of the Stuttgart Sub Region and its residents")
       
        st.markdown("""
            <style>
             body {
                 background: #dae3dc; /* Set the background color to white */
                 color: #dae3dc; /* Set the default text color */
            }
            .centered-title {
                text-align: center;
                margin-top: 20px;
            }
            .centered-subtitle {
                text-align: center;
                margin-top: 10px;
            }
            .centered-text {
                text-align: center;
                margin-top: 5px;
            }
             .left-text {
                text-align: left;
                margin-top: 5px;
            }
            </style>
            <div class="centered-subtitle">
                <h3>Project Objectives</h3>
            </div>
            
            <div class="left-text">
                <p>1. The main aim of the project is to develop an online population map dashboard for the Stuttgart Sub Region. The specific tasks to achieve this include:</p>
            
            <div class="left-text">
                <p>2. Develop a Web crawling script with BeautifulSoup python library for extracting HTML data from the Baden-Wuertemberg Statistical Office website.</p>
            
            <div class="left-text">
                <p>3. Create a PostgreSQL database for the integration and storage of the project data seamlessly.</p>
            
            <div class="left-text">
                <p>4. Create a dashboard with Streamlit and Folium for the map visualization with automatic update features.</p>
            
            <div class="left-text">
                <p>5. Create statistical charts/graphs on the dashboard to show trends and distribution.</p>
                
            </div>
            

            
            
            
            <div class="centered-title">
                <h2>Master Photogrammetry and Geoinformatics</h2>
            </div>
            <div class="centered-subtitle">
                <h3>PG2: GIS Studio (GSS)</h3>
            </div>
            <div class="centered-subtitle">
                <h4>Professors:</h4>
            </div>
            <div class="centered-subtitle">
                <h5>Prof. Dr. Volker Coors</h5>
            </div>
            <div class="centered-subtitle">
                <h5>Mr. Hamidreza Ostadabbas</h5>
            </div>

            """, unsafe_allow_html=True)



    # Adding a footer
    footer_html = """
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f1f1f1;
        text-align: center;
        padding: 10px;
        font-size: 15px;
        color: #000;
    }
    
    .footer p {
        margin: 0;
        font-weight: bold;
        font-size: 20px
    }
    </style>
    <div class="footer">
        <p>Developed by | <a href="https://www.linkedin.com/in/abdulwfuseini/" target="_blank">Abdul-Karim Wumpini Fuseini</a>|<a href="https://www.linkedin.com/in/oseiprince/" target="_blank">Prince Osei Boateng</a> | <a href="https://www.linkedin.com/in/michael-aboagye-appiah-454858289/" target="_blank">Michael Aboagye Appiah</a></p>
    </div>
    """

    st.markdown(footer_html, unsafe_allow_html=True)





if __name__=="__main__":
    main()

