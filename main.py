# main.py
import streamlit as st
from PIL import Image
import pandas as pd
import geopandas as gpd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import folium
from folium.features import GeoJsonTooltip
from streamlit_folium import folium_static

#import bcrypt

# Configuration de la page
st.set_page_config(page_title="Baromètre EDH 2024", layout="wide")

# Fonction d'authentification
# def hash_password(password):
#     return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

# def check_password(password, hashed):
#     return bcrypt.checkpw(password.encode(), hashed.encode())

# def authenticate(username, password):
#     if username in st.secrets["users"]:
#         hashed_password = st.secrets["users"][username]
#         if check_password(password, hashed_password):
#             st.session_state["authenticated"] = True
#             st.session_state["username"] = username
#             return True
#     return False

# def login():
#     if "authenticated" not in st.session_state:
#         st.session_state["authenticated"] = False
    
#     if st.session_state["authenticated"]:
#         return True

#     st.title("Connexion")
#     username = st.text_input("Nom d'utilisateur")
#     password = st.text_input("Mot de passe", type="password")
#     if st.button("Se connecter"):
#         if authenticate(username, password):
#             st.success("Connexion réussie")
#             return True
#         else:
#             st.error("Échec de la connexion")
#     return False

# def logout():
#     st.session_state["authenticated"] = False
#     st.session_state["username"] = ""

# Chargement et prétraitement des données
@st.cache_data
def load_data():
    combined_data = pd.read_parquet('data/combined_data.parquet')
    provinces_data = pd.read_parquet('data/provinces.parquet')
    geojson_provinces = gpd.read_file('data/updated_provinces.json')
    geojson_regions = gpd.read_file('data/updated_maroc.geojson')
    grappes_regions = pd.read_parquet('data/grappes_regions.parquet')
    circles_data = pd.read_parquet('data/cercles.parquet')  # Ajouter les données des cercles
    return combined_data, provinces_data, geojson_provinces, geojson_regions, grappes_regions, circles_data

# Chargement des données une seule fois
combined_data, provinces_data, geojson_provinces, geojson_regions, grappes_regions, circles_data = load_data()


def generate_province_map(data, column, title):
    # Assurez-vous que toutes les provinces du geojson sont présentes dans les données
    all_provinces = pd.DataFrame({'name': geojson_provinces['name']})
    data = all_provinces.merge(data, left_on='name', right_on='Province', how='left')
    
    data[column] = pd.to_numeric(data[column], errors='coerce')
    
    # Créer une colonne d'étiquettes
    if 'Proportion' in column:
        data['label'] = data.apply(lambda row: f"{row[column]:.2f}%" if pd.notnull(row[column]) and row[column] != 0 else "Hors enquête", axis=1)
    else:
        data['label'] = data.apply(lambda row: f"{row[column]:,.0f}".replace(",", " ") if pd.notnull(row[column]) and row[column] != 0 else "Hors enquête", axis=1)
    
    fig = px.choropleth(
        data,
        geojson=geojson_provinces,
        locations='name',
        featureidkey="properties.name",
        color=column,
        hover_name='name',
        hover_data={'label': True, column: False},  # Afficher 'label' au lieu de la valeur numérique
        color_continuous_scale=px.colors.sequential.Blues,
        title=title
    )

    fig.update_traces(
        hovertemplate="<b>%{hovertext}</b><br>%{customdata[0]}<extra></extra>"
    )

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        coloraxis_colorbar=dict(title="Pourcentage (%)" if 'Proportion' in column else "Total"),
        title={
            'y': 0.9,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        margin={"r": 0, "t": 40, "l": 0, "b": 0}
    )

    # Ajouter les noms des provinces et les valeurs des indicateurs sur la carte
    for _, row in data.iterrows():
        centroid = geojson_provinces[geojson_provinces['name'] == row['name']].geometry.centroid.iloc[0]
        fig.add_annotation(
            x=centroid.x, y=centroid.y,
            text=f"<b>{row['name']}<br>{row['label']}</b>",
            showarrow=False,
            font=dict(size=10, color="black"),
            align="center",
            bgcolor="rgba(255,255,255,0.8)",
            xanchor="center",
            yanchor="middle"
        )

    return fig


def generate_fixed_map(data, column, title):
    # Assurez-vous que toutes les régions du geojson sont présentes dans les données
    all_regions = pd.DataFrame({'region': geojson_regions['region']})
    data = all_regions.merge(data, on='region', how='left')
    
    data[column] = pd.to_numeric(data[column], errors='coerce')
    
    # Créer une colonne d'étiquettes
    if "Proportion" in title:
        data['label'] = data.apply(lambda row: f"{row[column]:.2f}%".replace(',', ' ') if pd.notnull(row[column]) and row[column] != 0 else "Hors enquête", axis=1)
    else:
        data['label'] = data.apply(lambda row: f"{int(row[column]):,}".replace(',', ' ') if pd.notnull(row[column]) and row[column] != 0 else "Hors enquête", axis=1)
    
    fig = px.choropleth(
        data,
        geojson=geojson_regions,
        locations='region',
        featureidkey="properties.region",
        color=column,
        hover_name='region',
        hover_data={'label': True, column: False},  # Afficher 'label' au lieu de la valeur numérique
        color_continuous_scale=px.colors.sequential.Blues,
        title=title
    )

    fig.update_traces(
        hovertemplate="<b>%{hovertext}</b><br>%{customdata[0]}<extra></extra>"
    )

    fig.update_geos(fitbounds="locations", visible=False)
    
    # Définir le titre de la légende en fonction de l'indicateur
    if "Proportion" in title:
        colorbar_title = "Pourcentage (%)"
    else:
        colorbar_title = "Total"
    
    fig.update_layout(
        coloraxis_colorbar=dict(title=colorbar_title),
        title={
            'y': 0.9,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        width=1200,  # Augmenter la taille du plot
        height=900,  # Augmenter la taille du plot
        margin={"r": 0, "t": 40, "l": 0, "b": 0}
    )

    # Ajouter les noms des régions et les valeurs des indicateurs sur la carte
    for _, row in data.iterrows():
        centroid = geojson_regions[geojson_regions['region'] == row['region']].geometry.centroid.iloc[0]
        fig.add_annotation(
            x=centroid.x, y=centroid.y,
            text=f"<b>{row['region']}<br>{row['label']}</b>",
            showarrow=False,
            font=dict(size=10, color="black"),
            align="center",
            bgcolor="rgba(255,255,255,0.8)",
            xanchor="center",
            yanchor="middle"
        )

    return fig







# Fonction principale pour afficher les indicateurs
def display_indicators(level, view):
    if level == "Vision Macroscopique":
        st.title("Chiffres Clés")

        if view == "Tableau":
            st.subheader("")
            num_days = (combined_data['submission_date'].max() - combined_data['submission_date'].min()).days +1
            total_expra = combined_data['expra'].sum()
            total_recensement = (combined_data['expra'] == 0).sum()
            daily_expra = combined_data.groupby('submission_date')['expra'].sum()
            global_prog_enq = (total_expra/35000)*100
            total_grap = combined_data['grappe'].nunique()
            global_prog_grap = (total_grap/10225)*100

            
            national_indicators = {
                "Durée de l'opération": f"{num_days} jours",
                "Taux de réalisation des enquêtes ménage": f"{global_prog_enq:.2f}%",
                "Taux de couverture des grappes": f"{global_prog_grap:.2f}%",
                "Grappes enquêtées": f"{total_grap} grappes",
                "Enquêtes ménages": f"{total_expra} enquêtes",
                "Recensements": f"{total_recensement} enquêtes",
                "Cadence quotidienne moyenne": f"{daily_expra.mean():.0f} enquêtes ménage par jour",
                "Variation de la cadence (Écart-type)": f"{daily_expra.std():.2f}"
            }
            
            df = pd.DataFrame(national_indicators.items(), columns=["Indicateur", "Valeur"]).reset_index(drop=True)
            st.table(df)

        elif view == "Datavisualisation":
            #st.subheader("Focus Visuel")

            # Calcul des indicateurs
            total_enquetes_menage = combined_data['expra'].sum()
            total_recensement = (combined_data['expra'] == 0).sum()
            total_grappes = combined_data['grappe'].nunique()
            progress_global_enquetes_menage = (total_enquetes_menage / 35000) * 100  
            progress_global_grappes = (total_grappes / 10225) * 100  

            # Barres horizontales pour Progrès Globaux
            #st.write("### Progrès Globaux")
            progress_df = pd.DataFrame({
                'Indicateur': ['Taux de réalisation des enquêtes ménage', 'Taux de couverture des grappes'],
                'Pourcentage': [progress_global_enquetes_menage, progress_global_grappes],
                'Restant': [100 - progress_global_enquetes_menage, 100 - progress_global_grappes]
            })
            fig_progress = px.bar(progress_df, y='Indicateur', x=['Pourcentage', 'Restant'], orientation='h', title="Taux d'Atteinte des Objectifs", barmode='stack')
            fig_progress.update_traces(texttemplate='%{x:.2f}%', textposition='inside')
            fig_progress.update_layout(uniformtext_minsize=8, uniformtext_mode='hide', title={'x':0.35})
            st.plotly_chart(fig_progress)

            # Barres verticales pour Total Enquêtes Ménage et Total Recensement
            #st.write("### Total Enquêtes Ménage et Recensement")
            total_df = pd.DataFrame({
                'Indicateur': ['Enquêtes Ménage', 'Recensements'],
                'Valeur': [total_enquetes_menage, total_recensement]
            })
            fig_total = px.bar(total_df, x='Indicateur', y='Valeur', title="Bilan des Opérations : Enquêtes Ménage et Recensements")
            fig_total.update_traces(texttemplate='%{y}', textposition='outside')
            fig_total.update_layout(uniformtext_minsize=8, uniformtext_mode='hide', title={'x':0.35})
            st.plotly_chart(fig_total)

            # Evolution des enquêtes ménages, recensement et grappes par jour
            st.write("### Tendances Journalières")
            combined_data['submission_date'] = pd.to_datetime(combined_data['submission_date'])
            daily_data = combined_data.groupby('submission_date').agg({
                'expra': ['sum', lambda x: (x == 0).sum()],
                'grappe': 'nunique'
            }).reset_index()
            daily_data.columns = ['submission_date', 'Enquêtes Ménage', 'Recensements', 'Grappes']

            evolution_type = st.selectbox("Sélectionner l'Indicateur de Suivi", ['Enquêtes Ménage', 'Recensements', 'Grappes'])
            fig_evolution = px.line(daily_data, x='submission_date', y=evolution_type, title=f"Tendance Journalière : {evolution_type}", labels={'submission_date': 'Date', evolution_type: evolution_type})

            # Traduire les dates en français
            fig_evolution.update_layout(
                xaxis=dict(
                    tickformat="%d-%m-%Y"
                ),
                title={'x':0.35}
            )
            st.plotly_chart(fig_evolution)

        elif view == "Géo-intelligence":
            st.subheader("Disponible en Zoom Régional et Provincial")
            
            #st.plotly_chart(fig)

    elif level == "Zoom Régional":
        #st.title("Indicateurs par Région")

        region_data = combined_data.groupby('region_label').agg(
            expra_1=('expra', lambda x: (x == 1).sum()),
            expra_0=('expra', lambda x: (x == 0).sum()),
            unique_grappe=('grappe', pd.Series.nunique)
        ).reset_index()
        region_data = region_data.merge(grappes_regions, left_on='region_label', right_on='region')
        region_data['ratio_expra'] = (region_data['expra_1'] / region_data['expra_0']) * 100
        region_data['percent_unique_grappe'] = (region_data['unique_grappe'] / region_data['nb_grappes']) * 100
        region_data = region_data.replace([np.inf, -np.inf], np.nan).fillna(0)

        # Sélectionner les colonnes à afficher
        region_data = region_data[['region_label', 'expra_1', 'expra_0', 'unique_grappe', 'nb_grappes', 'ratio_expra', 'percent_unique_grappe']]
        region_data.columns = ['Région', 'ENQUMENAGE', 'Recensement', 'Nb grappes enquêtées', 'Nb grappes total', 'Proportion ENQUMENAGE/Recensement', 'Proportion de grappes enquêtées']

        # Formatage des colonnes
        region_data['ENQUMENAGE'] = region_data['ENQUMENAGE'].apply(lambda x: f"{x:,}".replace(",", " "))
        region_data['Recensement'] = region_data['Recensement'].apply(lambda x: f"{x:,}".replace(",", " "))
        region_data['Nb grappes enquêtées'] = region_data['Nb grappes enquêtées'].apply(lambda x: f"{x:,}".replace(",", " "))
        region_data['Nb grappes total'] = region_data['Nb grappes total'].apply(lambda x: f"{x:,}".replace(",", " "))
        region_data['Proportion ENQUMENAGE/Recensement'] = region_data['Proportion ENQUMENAGE/Recensement'].apply(lambda x: f"{x:.2f}%")
        region_data['Proportion de grappes enquêtées'] = region_data['Proportion de grappes enquêtées'].apply(lambda x: f"{x:.2f}%")

        region_data1 = region_data.copy(deep=True)

        # Définir les nouveaux noms de colonnes
        new_columns = [
            'Région',
            'Enquêtes Ménage',
            'Recensements',
            'Grappes Couvertes',
            'Taux Enquêtes Ménage/Recensements',
            'Taux de Couverture des Grappes'
        ]

        # Créer un dictionnaire de mapping entre anciens et nouveaux noms
        column_mapping = {
            'Région': 'Région',
            'ENQUMENAGE': 'Enquêtes Ménage',
            'Recensement': 'Recensements',
            'Nb grappes enquêtées': 'Grappes Couvertes',
            'Proportion ENQUMENAGE/Recensement': 'Taux Enquêtes Ménage/Recensements',
            'Proportion de grappes enquêtées': 'Taux de Couverture des Grappes'
        }
        # Renommer les colonnes
        region_data1 = region_data1.rename(columns=column_mapping)

        # Réorganiser les colonnes selon l'ordre spécifié
        region_data1 = region_data1[new_columns]

        if view == "Tableau":
            st.subheader("Matrice Comparative des Indicateurs Régionaux")
            st.dataframe(region_data1)

        elif view == "Datavisualisation":
            st.subheader("Aperçu Graphique des Indicateurs Régionaux")

            # Fonction pour nettoyer et convertir les valeurs en float
            def clean_and_convert(column):
                return column.str.replace(' ', '').str.replace('%', '').astype(float)

            # Nettoyer et convertir les colonnes en float
            region_data['ENQUMENAGE'] = clean_and_convert(region_data['ENQUMENAGE'])
            region_data['Recensement'] = clean_and_convert(region_data['Recensement'])
            region_data['Nb grappes enquêtées'] = clean_and_convert(region_data['Nb grappes enquêtées'])
            region_data['Nb grappes total'] = clean_and_convert(region_data['Nb grappes total'])
            region_data['Proportion ENQUMENAGE/Recensement'] = clean_and_convert(region_data['Proportion ENQUMENAGE/Recensement'])
            region_data['Proportion de grappes enquêtées'] = clean_and_convert(region_data['Proportion de grappes enquêtées'])

            # Utiliser les valeurs nettoyées et converties pour définir les limites de l'axe y
            y_lim_multiplier = 1.1

            # Filtre pour sélectionner l'indicateur à afficher
            indicateur = st.selectbox(
                "Sélectionner l'Indicateur de Suivi", 
                
                [
                    "Enquêtes Ménage",
                    "Recensements",
                    "Grappes Couvertes",
                    "Distribution des Grappes",
                    "Taux Enquêtes Ménage/Recensements",
                    "Taux de Couverture des Grappes"
                ]
            )

            # Affichage du graphique en fonction de l'indicateur sélectionné
            if indicateur == "Enquêtes Ménage":
                fig = px.bar(region_data, x='Région', y='ENQUMENAGE', title="Enquêtes Ménage par Région", labels={'ENQUMENAGE': 'ENQUMENAGE'})
                fig.update_traces(texttemplate='%{y:,.0f}', textposition='outside')
                fig.update_layout(
                    uniformtext_minsize=8, 
                    uniformtext_mode='hide', 
                    yaxis=dict(range=[0, region_data['ENQUMENAGE'].max() * y_lim_multiplier]),
                    title={'x':0.35},
                    separators=', '  # Corrigé ici
                )
                st.plotly_chart(fig)

            elif indicateur == "Recensements":
                fig = px.bar(region_data, x='Région', y='Recensement', title="Recensements par Région", labels={'Recensement': 'Recensement'})
                fig.update_traces(texttemplate='%{y:,.0f}', textposition='outside')
                fig.update_layout(
                    uniformtext_minsize=8, 
                    uniformtext_mode='hide', 
                    yaxis=dict(range=[0, region_data['Recensement'].max() * y_lim_multiplier]),
                    title={'x':0.35},
                    separators=', '  # Corrigé ici
                )
                st.plotly_chart(fig)

            elif indicateur == "Grappes Couvertes":
                fig = px.bar(region_data, x='Région', y='Nb grappes enquêtées', title="Grappes Couvertes par Région", labels={'Nb grappes enquêtées': 'Nb grappes enquêtées'})
                fig.update_traces(texttemplate='%{y:,.0f}', textposition='outside')
                fig.update_layout(
                    uniformtext_minsize=8, 
                    uniformtext_mode='hide', 
                    yaxis=dict(range=[0, region_data['Nb grappes enquêtées'].max() * y_lim_multiplier]),
                    separators=', '  # Corrigé ici
                )
                st.plotly_chart(fig)

            elif indicateur == "Distribution des Grappes":
                fig = px.bar(region_data, x='Région', y='Nb grappes total', title="Distribution des Grappes par Région", labels={'Nb grappes total': 'Nb grappes total'})
                fig.update_traces(texttemplate='%{y:,.0f}', textposition='outside')
                fig.update_layout(
                    uniformtext_minsize=8, 
                    uniformtext_mode='hide', 
                    yaxis=dict(range=[0, region_data['Nb grappes total'].max() * y_lim_multiplier]),
                    separators=', '  # Corrigé ici
                )
                st.plotly_chart(fig)

            elif indicateur == "Taux Enquêtes/Recensements":
                fig = px.bar(region_data, x='Région', y='Proportion ENQUMENAGE/Recensement', title="Taux Enquêtes Ménage/Recensements par Région", labels={'Proportion ENQUMENAGE/Recensement': 'Proportion ENQUMENAGE/Recensement (%)'})
                fig.update_traces(texttemplate='%{y:.2f}%', textposition='outside')
                fig.update_layout(
                    uniformtext_minsize=8, 
                    uniformtext_mode='hide', 
                    yaxis=dict(range=[0, region_data['Proportion ENQUMENAGE/Recensement'].max() * y_lim_multiplier]),
                    separators=', '  # Ajouté ici
                )
                st.plotly_chart(fig)

            elif indicateur == "Taux de Couverture des Grappes":
                fig = px.bar(region_data, x='Région', y='Proportion de grappes enquêtées', title="Taux de Couverture des Grappes par Région", labels={'Proportion de grappes enquêtées': 'Proportion de grappes enquêtées (%)'})
                fig.update_traces(texttemplate='%{y:.2f}%', textposition='outside')
                fig.update_layout(
                    uniformtext_minsize=8, 
                    uniformtext_mode='hide', 
                    yaxis=dict(range=[0, region_data['Proportion de grappes enquêtées'].max() * y_lim_multiplier]),
                    separators=', '  # Ajouté ici
                )
                st.plotly_chart(fig)




        elif view == "Géo-intelligence":
            st.subheader("Aperçu Cartographique des Indicateurs Régionaux")

            # Filtre pour sélectionner l'indicateur
            indicateur = st.selectbox(
                "Sélectionner l'Indicateur de Suivi", 
                [
                    "Enquêtes Ménage",
                    "Recensements",
                    "Grappes Couvertes",
                    "Taux Enquêtes Ménage/Recensements",
                    "Taux de Couverture des Grappes"
                ]
            )

            # Charger le fichier GeoJSON
            geojson_path = 'data/updated_maroc.geojson'
            geo_data = gpd.read_file(geojson_path)

            # Filtrer les données GeoJSON pour ne conserver que les régions du Maroc
            maroc_regions = geo_data[geo_data['region'].notnull()]

            # Assurer que toutes les régions soient incluses dans la fusion
            region_data_full = maroc_regions[['region', 'geometry']].merge(region_data, left_on='region', right_on='Région', how='left')

            # Convertir les colonnes en valeurs numériques si nécessaire et remplir les valeurs manquantes avec 0
            region_data_full['Enquêtes Ménage'] = pd.to_numeric(region_data_full['ENQUMENAGE'].str.replace(' ', ''), errors='coerce').fillna(0)
            region_data_full['Recensements'] = pd.to_numeric(region_data_full['Recensement'].str.replace(' ', ''), errors='coerce').fillna(0)
            region_data_full['Grappes Couvertes'] = pd.to_numeric(region_data_full['Nb grappes enquêtées'].str.replace(' ', ''), errors='coerce').fillna(0)
            region_data_full['Proportion ENQUMENAGE/Recensement'] = pd.to_numeric(region_data_full['Proportion ENQUMENAGE/Recensement'].str.replace('%', ''), errors='coerce').fillna(0)
            region_data_full['Taux de Couverture des Grappes'] = pd.to_numeric(region_data_full['Proportion de grappes enquêtées'].str.replace('%', ''), errors='coerce').fillna(0)

            # Générer la carte pour l'indicateur sélectionné
            title_map = {
                'Enquêtes Ménage': 'Répartition Régionale des Enquêtes Ménage',
                'Recensements': 'Répartition Régionale des Recensements',
                'Grappes Couvertes': 'Répartition Régionale des Grappes Enquêtées',
                'Taux Enquêtes Ménage/Recensements': 'Répartition Régionale du Taux Enquêtes/Recensements',
                'Taux de Couverture des Grappes': 'Répartition Régionale du Taux de Couverture des Grappes'
            }

            fig = generate_fixed_map(region_data_full, indicateur, title_map[indicateur])
            st.plotly_chart(fig)



    elif level == "Zoom Provincial":
        #st.title("Indicateurs par Province")

        province_data = combined_data.groupby('province_label').agg(
            expra_1=('expra', lambda x: (x == 1).sum()),
            expra_0=('expra', lambda x: (x == 0).sum()),
            unique_grappe=('grappe', pd.Series.nunique)
        ).reset_index()
        province_data = province_data.merge(provinces_data, left_on='province_label', right_on='province')
        province_data = province_data.merge(combined_data[['province_label', 'region_label']].drop_duplicates(), on='province_label', how='left')
        province_data['ratio_expra'] = (province_data['expra_1'] / province_data['expra_0']) * 100
        province_data['percent_unique_grappe'] = (province_data['unique_grappe'] / province_data['nb_grappe']) * 100
        province_data = province_data.replace([np.inf, -np.inf], np.nan).fillna(0)

        # Sélectionner les colonnes à afficher
        province_data = province_data[['province_label', 'region_label', 'expra_1', 'expra_0', 'unique_grappe', 'nb_grappe', 'ratio_expra', 'percent_unique_grappe']]
        province_data.columns = ['Province', 'Région', 'ENQUMENAGE', 'Recensement', 'Nb grappes enquêtées', 'Nb grappes total', 'Proportion ENQUMENAGE/Recensement', 'Proportion de grappes enquêtées']

        # Formatage des colonnes
        province_data['ENQUMENAGE'] = province_data['ENQUMENAGE'].apply(lambda x: f"{x:,}".replace(",", " "))
        province_data['Recensement'] = province_data['Recensement'].apply(lambda x: f"{x:,}".replace(",", " "))
        province_data['Nb grappes enquêtées'] = province_data['Nb grappes enquêtées'].apply(lambda x: f"{x:,}".replace(",", " "))
        province_data['Nb grappes total'] = province_data['Nb grappes total'].apply(lambda x: f"{x:,}".replace(",", " "))
        province_data['Proportion ENQUMENAGE/Recensement'] = province_data['Proportion ENQUMENAGE/Recensement'].apply(lambda x: f"{x:.2f}%")
        province_data['Proportion de grappes enquêtées'] = province_data['Proportion de grappes enquêtées'].apply(lambda x: f"{x:.2f}%")

        # Créer une copie profonde de province_data
        province_data1 = province_data.copy(deep=True)

        # Définir les nouveaux noms de colonnes
        new_columns = [
            'Province',
            'Région',
            'Enquêtes Ménage',
            'Recensements',
            'Grappes Couvertes',
            'Nombre Total de Grappes',
            'Taux Enquêtes Ménage/Recensements',
            'Taux de Couverture des Grappes'
        ]

        # Créer un dictionnaire de mapping entre anciens et nouveaux noms
        column_mapping = {
            'Province': 'Province',
            'Région': 'Région',
            'ENQUMENAGE': 'Enquêtes Ménage',
            'Recensement': 'Recensements',
            'Nb grappes enquêtées': 'Grappes Couvertes',
            'Nb grappes total': 'Nombre Total de Grappes',
            'Proportion ENQUMENAGE/Recensement': 'Taux Enquêtes Ménage/Recensements',
            'Proportion de grappes enquêtées': 'Taux de Couverture des Grappes'
        }

        # Renommer les colonnes
        province_data1 = province_data1.rename(columns=column_mapping)


        if view == "Tableau":
            st.subheader("Matrice Comparative des Indicateurs Provinciaux")
            st.dataframe(province_data1)


        elif view == "Datavisualisation":
            st.subheader("Aperçu Graphique des Indicateurs Provinciaux")

            # Fonction pour nettoyer et convertir les valeurs en float
            def clean_and_convert(column):
                return column.str.replace(' ', '').str.replace('%', '').astype(float)

            # Nettoyer et convertir les colonnes en float
            province_data['ENQUMENAGE'] = clean_and_convert(province_data['ENQUMENAGE'])
            province_data['Recensement'] = clean_and_convert(province_data['Recensement'])
            province_data['Nb grappes enquêtées'] = clean_and_convert(province_data['Nb grappes enquêtées'])
            province_data['Nb grappes total'] = clean_and_convert(province_data['Nb grappes total'])
            province_data['Proportion ENQUMENAGE/Recensement'] = clean_and_convert(province_data['Proportion ENQUMENAGE/Recensement'])
            province_data['Proportion de grappes enquêtées'] = clean_and_convert(province_data['Proportion de grappes enquêtées'])

            # Utiliser les valeurs nettoyées et converties pour définir les limites de l'axe y
            y_lim_multiplier = 1.1

            # Filtre pour sélectionner la région
            regions = ['Toutes les Régions'] + list(province_data['Région'].unique())
            selected_region = st.selectbox("Choisir une Région", regions)

            # Filtre pour sélectionner l'indicateur à afficher
            indicateur = st.selectbox(
                "Sélectionner l'Indicateur de Suivi", 
                
                [
                    "Enquêtes Ménage",
                    "Recensements",
                    "Grappes Couvertes",
                    "Nombre Total de Grappes",
                    "Taux Enquêtes Ménage/Recensements",
                    "Taux de Couverture des Grappes"
                ]
            )

            # Filtrer les données en fonction de la région sélectionnée
            if selected_region != 'Toutes les Régions':
                filtered_data = province_data[province_data['Région'] == selected_region]
            else:
                filtered_data = province_data

            # Affichage du graphique en fonction de l'indicateur sélectionné
            if indicateur == "Enquêtes Ménage":
                fig = px.bar(filtered_data, x='Province', y='ENQUMENAGE', title="Enquêtes Ménage par Province", labels={'ENQUMENAGE': 'ENQUMENAGE'})
                fig.update_traces(texttemplate='%{y:,.0f}', textposition='outside')
                fig.update_layout(
                    uniformtext_minsize=8, 
                    uniformtext_mode='hide', 
                    yaxis=dict(range=[0, filtered_data['ENQUMENAGE'].max() * y_lim_multiplier]),
                    title={'x':0.35},
                    separators=', '  # Corrigé ici
                )
                st.plotly_chart(fig)

            elif indicateur == "Recensements":
                fig = px.bar(filtered_data, x='Province', y='Recensement', title="Recensements par Province", labels={'Recensement': 'Recensement'})
                fig.update_traces(texttemplate='%{y:,.0f}', textposition='outside')
                fig.update_layout(
                    uniformtext_minsize=8, 
                    uniformtext_mode='hide', 
                    yaxis=dict(range=[0, filtered_data['Recensement'].max() * y_lim_multiplier]),
                    separators=', '  # Corrigé ici
                )
                st.plotly_chart(fig)

            elif indicateur == "Grappes Couvertes":
                fig = px.bar(filtered_data, x='Province', y='Nb grappes enquêtées', title="Grappes Couvertes par Province", labels={'Nb grappes enquêtées': 'Nb grappes enquêtées'})
                fig.update_traces(texttemplate='%{y:,.0f}', textposition='outside')
                fig.update_layout(
                    uniformtext_minsize=8, 
                    uniformtext_mode='hide', 
                    yaxis=dict(range=[0, filtered_data['Nb grappes enquêtées'].max() * y_lim_multiplier]),
                    separators=', '  # Corrigé ici
                )
                st.plotly_chart(fig)

            elif indicateur == "Nombre Total de Grappes":
                fig = px.bar(filtered_data, x='Province', y='Nb grappes total', title="Nombre Total de Grappes par Province", labels={'Nb grappes total': 'Nb grappes total'})
                fig.update_traces(texttemplate='%{y:,.0f}', textposition='outside')
                fig.update_layout(
                    uniformtext_minsize=8, 
                    uniformtext_mode='hide', 
                    yaxis=dict(range=[0, filtered_data['Nb grappes total'].max() * y_lim_multiplier]),
                    separators=', '  # Corrigé ici
                )
                st.plotly_chart(fig)

            elif indicateur == "Taux Enquêtes Ménage/Recensements":
                fig = px.bar(filtered_data, x='Province', y='Proportion ENQUMENAGE/Recensement', title="Taux Enquêtes Ménage/Recensements par Province", labels={'Proportion ENQUMENAGE/Recensement': 'Proportion ENQUMENAGE/Recensement (%)'})
                fig.update_traces(texttemplate='%{y:.2f}%', textposition='outside')
                fig.update_layout(
                    uniformtext_minsize=8, 
                    uniformtext_mode='hide', 
                    yaxis=dict(range=[0, filtered_data['Proportion ENQUMENAGE/Recensement'].max() * y_lim_multiplier]),
                    separators=', '  # Ajouté ici
                )
                st.plotly_chart(fig)

            elif indicateur == "Taux de Couverture des Grappes":
                fig = px.bar(filtered_data, x='Province', y='Proportion de grappes enquêtées', title="Taux de Couverture des Grappes par Province", labels={'Proportion de grappes enquêtées': 'Proportion de grappes enquêtées (%)'})
                fig.update_traces(texttemplate='%{y:.2f}%', textposition='outside')
                fig.update_layout(
                    uniformtext_minsize=8, 
                    uniformtext_mode='hide', 
                    yaxis=dict(range=[0, filtered_data['Proportion de grappes enquêtées'].max() * y_lim_multiplier]),
                    separators=', '  # Ajouté ici
                )
                st.plotly_chart(fig)



        elif view == "Géo-intelligence":
            st.subheader("Cartographie des Indicateurs par Provinciaux")

            # Filtre pour sélectionner la région
            regions = ['Toutes les Régions'] + list(province_data['Région'].unique())
            selected_region = st.selectbox("Sélectionnez une région", regions)

            # Filtre pour sélectionner l'indicateur
            indicateur = st.selectbox(
                "Sélectionnez un indicateur", 
                ['Enquêtes Ménage', 
                 'Recensements', 
                 'Grappes Couvertes', 
                 'Taux Enquêtes Ménage/Recensements', 
                 'Taux de Couverture des Grappes']
            )

            # Filtrer les données en fonction de la région sélectionnée
            if selected_region != 'Toutes les Régions':
                filtered_data = province_data[province_data['Région'] == selected_region]
            else:
                filtered_data = province_data.copy()

            # Convertir les colonnes en valeurs numériques si nécessaire et remplir les valeurs manquantes avec 0
            filtered_data['Enquêtes Ménage'] = pd.to_numeric(filtered_data['ENQUMENAGE'].str.replace(' ', ''), errors='coerce').fillna(0)
            filtered_data['Recensements'] = pd.to_numeric(filtered_data['Recensement'].str.replace(' ', ''), errors='coerce').fillna(0)
            filtered_data['Grappes Couvertes'] = pd.to_numeric(filtered_data['Nb grappes enquêtées'].str.replace(' ', ''), errors='coerce').fillna(0)
            filtered_data['Taux Enquêtes Ménage/Recensements'] = pd.to_numeric(filtered_data['Proportion ENQUMENAGE/Recensement'].str.replace('%', ''), errors='coerce').fillna(0)
            filtered_data['Taux de Couverture des Grappes'] = pd.to_numeric(filtered_data['Proportion de grappes enquêtées'].str.replace('%', ''), errors='coerce').fillna(0)

            # Générer la carte pour l'indicateur sélectionné
            title_map = {
                'Enquêtes Ménage': 'Répartition Provinciale des Enquêtes Ménage',
                'Recensements': 'Répartition Provinciale des Recensements',
                'Grappes Couvertes': 'Répartition Provinciale des Grappes Enquêtées',
                'Taux Enquêtes Ménage/Recensements': 'Répartition Provinciale du Taux Enquêtes/Recensements',
                'Taux de Couverture des Grappes': 'Répartition Provinciale du Taux de Couverture des Grappes'
                }

            fig = generate_province_map(filtered_data, indicateur, title_map[indicateur])
            st.plotly_chart(fig)


    elif level == "Zoom Cercles":
        # Analyse par cercles
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

        # Fusion avec combined_data pour obtenir la province
        circle_data = circle_data.merge(combined_data[['cldh_label', 'province_label']].drop_duplicates(), on='cldh_label', how='left')

        # Suppression des doublons de colonnes et renommage
        if 'province_label_x' in circle_data.columns and 'province_label_y' in circle_data.columns:
            circle_data['province_label'] = circle_data['province_label_x']
            circle_data = circle_data.drop(columns=['province_label_x', 'province_label_y'])

        # Calcul des ratios et pourcentages
        circle_data['ratio_expra'] = (circle_data['expra_1'] / circle_data['expra_0']) * 100
        circle_data['percent_unique_grappe'] = (circle_data['unique_grappe'] / circle_data['nb_grappe']) * 100
        circle_data = circle_data.replace([np.inf, -np.inf], np.nan).fillna(0)

        # Sélectionner les colonnes à afficher
        circle_data = circle_data[['cldh_label', 'province_label', 'expra_1', 'expra_0', 'unique_grappe', 'nb_grappe', 'ratio_expra', 'percent_unique_grappe']]
        circle_data.columns = ['Cercle', 'Province', 'ENQUMENAGE', 'Recensement', 'Nb grappes enquêtées', 'Nb grappes total', 'Proportion ENQUMENAGE/Recensement', 'Proportion de grappes enquêtées']

        # Formatage des colonnes
        circle_data['ENQUMENAGE'] = circle_data['ENQUMENAGE'].apply(lambda x: f"{x:,}".replace(",", " "))
        circle_data['Recensement'] = circle_data['Recensement'].apply(lambda x: f"{x:,}".replace(",", " "))
        circle_data['Nb grappes enquêtées'] = circle_data['Nb grappes enquêtées'].apply(lambda x: f"{x:,}".replace(",", " "))
        circle_data['Nb grappes total'] = circle_data['Nb grappes total'].apply(lambda x: f"{x:,}".replace(",", " "))
        circle_data['Proportion ENQUMENAGE/Recensement'] = circle_data['Proportion ENQUMENAGE/Recensement'].apply(lambda x: f"{x:.2f}%")
        circle_data['Proportion de grappes enquêtées'] = circle_data['Proportion de grappes enquêtées'].apply(lambda x: f"{x:.2f}%")


        # Créer une copie profonde de circle_data
        circle_data1 = circle_data.copy(deep=True)

        # Définir les nouveaux noms de colonnes
        new_columns = [
            'Cercle',
            'Province',
            'Enquêtes Ménage',
            'Recensements',
            'Grappes Couvertes',
            'Nombre Total de Grappes',
            'Taux Enquêtes Ménage/Recensements',
            'Taux de Couverture des Grappes'
        ]

        # Créer un dictionnaire de mapping entre anciens et nouveaux noms
        column_mapping = {
            'Cercle': 'Cercle',
            'Province': 'Province',
            'ENQUMENAGE': 'Enquêtes Ménage',
            'Recensement': 'Recensements',
            'Nb grappes enquêtées': 'Grappes Couvertes',
            'Nb grappes total': 'Nombre Total de Grappes',
            'Proportion ENQUMENAGE/Recensement': 'Taux Enquêtes Ménage/Recensements',
            'Proportion de grappes enquêtées': 'Taux de Couverture des Grappes'
        }

        # Renommer les colonnes
        circle_data1 = circle_data1.rename(columns=column_mapping)


        if view == "Tableau":
            st.subheader("Matrice Comparative des Indicateurs des Cercles")
            st.dataframe(circle_data1)
        
        elif view == "Datavisualisation":
            st.subheader("Aperçu Graphique des Indicateurs des Cercles")

            # Fonction pour nettoyer et convertir les valeurs en float
            def clean_and_convert(column):
                return column.str.replace(' ', '').str.replace('%', '').astype(float)

            # Nettoyer et convertir les colonnes en float
            circle_data['ENQUMENAGE'] = clean_and_convert(circle_data['ENQUMENAGE'])
            circle_data['Recensement'] = clean_and_convert(circle_data['Recensement'])
            circle_data['Nb grappes enquêtées'] = clean_and_convert(circle_data['Nb grappes enquêtées'])
            circle_data['Nb grappes total'] = clean_and_convert(circle_data['Nb grappes total'])
            circle_data['Proportion ENQUMENAGE/Recensement'] = clean_and_convert(circle_data['Proportion ENQUMENAGE/Recensement'])
            circle_data['Proportion de grappes enquêtées'] = clean_and_convert(circle_data['Proportion de grappes enquêtées'])

            # Utiliser les valeurs nettoyées et converties pour définir les limites de l'axe y
            y_lim_multiplier = 1.1

            # Filtre pour sélectionner la province
            provinces = ['Toutes les Provinces'] + list(circle_data['Province'].unique())
            selected_province = st.selectbox("Choisir une Province", provinces)

            # Filtre pour sélectionner l'indicateur à afficher
            indicateur = st.selectbox(
                "Sélectionner l'Indicateur de Suivi", 
                [
                    "Enquêtes Ménage",
                    "Recensements",
                    "Grappes Couvertes",
                    "Nombre Total de Grappes",
                    "Taux Enquêtes Ménage/Recensements",
                    "Taux de Couverture des Grappes"
                ]
            )

            # Filtrer les données en fonction de la province sélectionnée
            if selected_province != 'Toutes les Provinces':
                filtered_data = circle_data[circle_data['Province'] == selected_province]
            else:
                filtered_data = circle_data

            # Affichage du graphique en fonction de l'indicateur sélectionné
            if indicateur == "Enquêtes Ménage":
                fig = px.bar(filtered_data, x='Cercle', y='ENQUMENAGE', title="Enquêtes Ménage par Cercle", labels={'ENQUMENAGE': 'ENQUMENAGE'})
                fig.update_traces(texttemplate='%{y:,.0f}', textposition='outside')
                fig.update_layout(
                    uniformtext_minsize=8, 
                    uniformtext_mode='hide', 
                    yaxis=dict(range=[0, filtered_data['ENQUMENAGE'].max() * y_lim_multiplier]),
                    title={'x':0.35},
                    separators=', '  # Corrigé ici
                )
                st.plotly_chart(fig)

            elif indicateur == "Recensements":
                fig = px.bar(filtered_data, x='Cercle', y='Recensement', title="Recensements par Cercle", labels={'Recensement': 'Recensement'})
                fig.update_traces(texttemplate='%{y:,.0f}', textposition='outside')
                fig.update_layout(
                    uniformtext_minsize=8, 
                    uniformtext_mode='hide', 
                    yaxis=dict(range=[0, filtered_data['Recensement'].max() * y_lim_multiplier]),
                    separators=', '  # Corrigé ici
                )
                st.plotly_chart(fig)

            elif indicateur == "Grappes Couvertes":
                fig = px.bar(filtered_data, x='Cercle', y='Nb grappes enquêtées', title="Grappes Couvertes par Cercle", labels={'Nb grappes enquêtées': 'Nb grappes enquêtées'})
                fig.update_traces(texttemplate='%{y:,.0f}', textposition='outside')
                fig.update_layout(
                    uniformtext_minsize=8, 
                    uniformtext_mode='hide', 
                    yaxis=dict(range=[0, filtered_data['Nb grappes enquêtées'].max() * y_lim_multiplier]),
                    separators=', '  # Corrigé ici
                )
                st.plotly_chart(fig)

            elif indicateur == "Nombre Total de Grappes":
                fig = px.bar(filtered_data, x='Cercle', y='Nb grappes total', title="Nombre Total de Grappes par Cercle", labels={'Nb grappes total': 'Nb grappes total'})
                fig.update_traces(texttemplate='%{y:,.0f}', textposition='outside')
                fig.update_layout(
                    uniformtext_minsize=8, 
                    uniformtext_mode='hide', 
                    yaxis=dict(range=[0, filtered_data['Nb grappes total'].max() * y_lim_multiplier]),
                    separators=', '  # Corrigé ici
                )
                st.plotly_chart(fig)

            elif indicateur == "Taux Enquêtes Ménage/Recensements":
                fig = px.bar(filtered_data, x='Cercle', y='Proportion ENQUMENAGE/Recensement', title="Taux Enquêtes Ménage/Recensements par Cercle", labels={'Proportion ENQUMENAGE/Recensement': 'Proportion ENQUMENAGE/Recensement (%)'})
                fig.update_traces(texttemplate='%{y:.2f}%', textposition='outside')
                fig.update_layout(
                    uniformtext_minsize=8, 
                    uniformtext_mode='hide', 
                    yaxis=dict(range=[0, filtered_data['Proportion ENQUMENAGE/Recensement'].max() * y_lim_multiplier]),
                    separators=', '  # Ajouté ici
                )
                st.plotly_chart(fig)

            elif indicateur == "Taux de Couverture des Grappes":
                fig = px.bar(filtered_data, x='Cercle', y='Proportion de grappes enquêtées', title="Taux de Couverture des Grappes par Cercle", labels={'Proportion de grappes enquêtées': 'Proportion de grappes enquêtées (%)'})
                fig.update_traces(texttemplate='%{y:.2f}%', textposition='outside')
                fig.update_layout(
                    uniformtext_minsize=8, 
                    uniformtext_mode='hide', 
                    yaxis=dict(range=[0, filtered_data['Proportion de grappes enquêtées'].max() * y_lim_multiplier]),
                    separators=', '  # Ajouté ici
                )
                st.plotly_chart(fig)

        elif view == "Géo-intelligence":
            st.subheader("Disponible en Zoom Régional et Provincial")

# Fonction principale

def main():
    # if not login():
    #     return
    
    # Custom CSS to style the title
    st.markdown(
        """
        <style>
        .big-bold-font {
            font-size:50px !important;
            font-weight: bold !important;
        }
        .center-bold-font {
            text-align: center;
            font-weight: bold;
            font-size: 20px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    # Create a layout with two columns
    col1, col2 = st.columns([1, 3])

    # Load your logo
    logo = Image.open('ondh.png')

    # Display the logo in the left column
    with col1:
        st.image(logo, width=100)

    # You can use the right column for a title or other content
    with col2:
        st.markdown('<p class="big-bold-font">Baromètre EDH 2024</p>', unsafe_allow_html=True)
    
    st.markdown('<p class="center-bold-font">Pilotage Stratégique de l\'Enquête sur le Développement Humain auprès des Ménages 2024</p>', unsafe_allow_html=True)
    
    st.sidebar.title("Filtres")
    #niveau = st.sidebar.radio("Niveau", ["National", "Régions", "Provinces"])
    niveau = st.sidebar.radio("Échelle d'Analyse", ["Vision Macroscopique", "Zoom Régional", 
                                                    "Zoom Provincial", "Zoom Cercles"])
    vue = st.sidebar.radio("Mode de Visualisation", ["Tableau", "Datavisualisation", "Géo-intelligence"])
    
    # if st.sidebar.button("Se déconnecter"):
    #     logout()
    #     st.experimental_rerun()

    display_indicators(niveau, vue)


if __name__ == "__main__":
    main()
