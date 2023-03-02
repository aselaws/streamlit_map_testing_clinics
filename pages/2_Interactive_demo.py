"""
Streamlit app template.

Because a long app quickly gets out of hand,
try to keep this document to mostly direct calls to streamlit to write
or display stuff. Use functions in other files to create and
organise the stuff to be shown. In this example, most of the work is
done in functions stored in files named container_(something).py

This folium code is directly copied from Elliot's HSMA exercise
https://github.com/hsma5/5b_geospatial_problems/blob/main/exercise/5B_Folium_map_Group-SOLUTION.ipynb
"""
# ----- Imports -----
import streamlit as st
from streamlit_folium import st_folium

# Importing libraries
import folium
from folium import plugins
from folium.features import GeoJsonPopup, GeoJsonTooltip
import pandas as pd
import json
import numpy as np
import pickle
# import cPickle

# For the colour bar:
import branca

# Custom functions:
from utilities_maps.fixed_params import page_setup

from datetime import datetime


def import_geojson(group_hospital):
    # Choose which geojson to open:
    geojson_file = 'LSOA_' + group_hospital.replace(' ', '~') + '.geojson'
    # geojson_file = './old/LSOA_2011.geojson'
    # geojson_file = 'LSOA_(Dec_2011)_Boundaries_Super_Generalised_Clipped_(BSC)_EW_V3.geojson'

    # lsoa geojson
    # with open('./data_maps/lhb_scn_geojson/' + geojson_file) as f:
    with open('./data_maps/lhb_stp_geojson/' + geojson_file) as f:
        geojson_ew = json.load(f)

    ## Copy the LSOA11CD code to features.id within geojson
    for i in geojson_ew['features']:
        i['id'] = i['properties']['LSOA11NMW']
    return geojson_ew



def import_hospital_geojson(hospital_postcode, MT=False):
    # Choose which geojson to open:
    geojson_file = 'lsoa_nearest_'
    if MT is True:
        geojson_file += 'MT_'
    else:
        geojson_file += 'to_'
    geojson_file += hospital_postcode
    geojson_file += '.geojson'

    # geojson_file = './old/LSOA_2011.geojson'
    # geojson_file = 'LSOA_(Dec_2011)_Boundaries_Super_Generalised_Clipped_(BSC)_EW_V3.geojson'

    # lsoa geojson
    # with open('./data_maps/lhb_scn_geojson/' + geojson_file) as f:
    with open('./data_maps/lsoa_nearest_hospital/' + geojson_file) as f:
        geojson_ew = json.load(f)

    # ## Copy the LSOA11CD code to features.id within geojson
    # for i in geojson_ew['features']:
    #     i['id'] = i['properties']['LSOA11NMW']
    return geojson_ew


def draw_map(lat_hospital, long_hospital, geojson_list, region_list, df_placeholder, df_hospitals, nearest_hospital_geojson_list, nearest_mt_hospital_geojson_list, choro_bins=6):
    # Create a map
    clinic_map = folium.Map(location=[lat_hospital, long_hospital],
                            zoom_start=9,
                            tiles='cartodbpositron',
                            # prefer_canvas=True,
                            # Override how much people can zoom in or out:
                            min_zoom=0,
                            max_zoom=18,
                            width=1200,
                            height=600
                            )

    # # Add markers
    # for (index, row) in df_clinics.iterrows():
    #     pop_up_text = f"The postcode for {row.loc['Name']} " + \
    #                     f"({row.loc['Clinic']}) is {row.loc['postcode']}"
    #     folium.Marker(location=[row.loc['lat'], row.loc['long']], 
    #                   popup=pop_up_text, 
    #                   tooltip=row.loc['Name']).add_to(clinic_map)
    # folium.features.GeoJsonTooltip(['travel_time_mins'])

    outcome_min = 0
    outcome_max = 1
    choro_bins = np.linspace(outcome_min, outcome_max, 7)

    # Make a new discrete colour map:
    # (colour names have to be #000000 strings or names)
    colormap = branca.colormap.StepColormap(
        vmin=outcome_min,
        vmax=outcome_max,
        colors=["red", "orange", "lightblue", "green", "darkgreen", 'blue'],
        caption='Placeholder',
        index=choro_bins
    )
    colormap.add_to(clinic_map)
    # fg.add_child(colormap)  # doesn't work


    # fg = folium.FeatureGroup(name="test")
    
    # Add choropleth
    for g, geojson_ew in enumerate(geojson_list):
        # a = folium.Choropleth(geo_data=geojson_ew,
        #                 name=region_list[g], # f'choropleth_{g}',
        #                 bins=choro_bins,
        #                 data=df_placeholder,
        #                 columns=['LSOA11NMW', 'Placeholder'],
        #                 key_on='feature.id',
        #                 fill_color='OrRd',
        #                 fill_opacity=0.5,
        #                 line_opacity=0.5,
        #                 legend_name='Placeholder',
        #                 highlight=True,
        #                 #   tooltip='travel_time_mins',
        #                 smooth_factor=1.5,
        #                 show=False if g > 0 else True
        #                 ).add_to(clinic_map)
        # st.write(g)
        # st.write(a)
        # st.write(' ')



        # # fg.add_child(
        folium.GeoJson(
            data=geojson_ew,
            tooltip=GeoJsonTooltip(
                fields=['LSOA11NMW'],
                aliases=[''],
                localize=True
                ),
            # lambda x:f"{x['properties']['LSOA11NMW']}",
            # popup=popup,
            name=region_list[g],
            style_function= lambda y:{
                # "fillColor": colormap(y["properties"]["Estimate_UN"]),
                "fillColor": colormap(df_placeholder[df_placeholder['LSOA11NMW'] == y['properties']['LSOA11NMW']]['Placeholder'].iloc[0]),
                # "fillColor": colormap(df_placeholder[df_placeholder['LSOA11NMW'] == y['geometries']['properties']['LSOA11NMW']]['Placeholder'].iloc[0]),
                'stroke':'false',
                'opacity': 0.5,
                'color':'black',  # line colour
                'weight':0.5,
                # 'dashArray': '5, 5'
            },
            highlight_function=lambda x: {'weight': 2.0},
            smooth_factor=1.5,  # 2.0 is about the upper limit here
            show=False if g > 0 else True
            ).add_to(clinic_map)
        # ))

        # folium.TopoJson(
        #     data=geojson_ew,
        #     # tooltip=GeoJsonTooltip(
        #     #     fields=['LSOA11NMW'],
        #     #     aliases=[''],
        #     #     localize=True
        #     #     ),
        #     # lambda x:f"{x['properties']['LSOA11NMW']}",
        #     # popup=popup,
        #     # name=region_list[g],
        #     object_path='LSOA_South~West',
        #     # style_function= lambda y:{
        #     #     # "fillColor": colormap(y["properties"]["Estimate_UN"]),
        #     #     # "fillColor": colormap(df_placeholder[df_placeholder['LSOA11NMW'] == y['properties']['LSOA11NMW']]['Placeholder'].iloc[0]),
        #     #     "fillColor": colormap(df_placeholder[df_placeholder['LSOA11NMW'] == y['geometries']['properties']['LSOA11NMW']]['Placeholder'].iloc[0]),
        #     #     'stroke':'false',
        #     #     'opacity': 0.5,
        #     #     'color':'black',  # line colour
        #     #     'weight':0.5,
        #     #     # 'dashArray': '5, 5'
        #     # },
        #     # highlight_function=lambda x: {'weight': 2.0},
        #     # smooth_factor=1.5,  # 2.0 is about the upper limit here
        #     # show=False if g > 0 else True
        #     ).add_to(clinic_map)

    # import matplotlib.colors
    # colours = list(matplotlib.colors.cnames.values())
    # # st.write(colours)
    # for g, geojson_ew in enumerate(nearest_hospital_geojson_list):
    #     colour_here = colours[g]


    #     # fg.add_child(
    #     folium.GeoJson(
    #         data=geojson_ew,
    #         # tooltip=GeoJsonTooltip(
    #         #     fields=['LSOA11NMW'],
    #         #     aliases=[''],
    #         #     localize=True
    #         #     ),
    #         # lambda x:f"{x['properties']['LSOA11NMW']}",
    #         # popup=popup,
    #         name='placeholder_'+str(g), #region_list[g],
    #         style_function= lambda y:{
    #             # "fillColor": , #f'{colour_here}',# 'rgba(0, 0, 0, 0)',
    #             'stroke':'false',
    #             'opacity': 0.5,
    #             'color':'black',  # line colour
    #             'weight': 3,
    #             'dashArray': '5, 5'
    #         },
    #         # highlight_function=lambda x: {'fillOpacity': 0.8},
    #         smooth_factor=1.5,  # 2.0 is about the upper limit here
    #         show=True, # if g > 0 else True
    #         overlay=False
    #     # ))
    #         ).add_to(clinic_map)


    # Problem - no way to set colour scale max and min,
    # get a new colour scale for each choropleth.


    # Add markers
    for (index, row) in df_hospitals.iterrows():
        # pop_up_text = f'{row.loc["Stroke Team"]}'

        if last_object_clicked_tooltip == row.loc['Stroke Team']:
            icon = folium.Icon(
                # color='black',
                # icon_color='white',
                icon='star', #'fa-solid fa-hospital',#'info-sign',
                # angle=0,
                prefix='glyphicon')#, prefix='fa')
        else:
            icon = None


        # fg.add_child(
        folium.Marker(location=[row.loc['lat'], row.loc['long']], 
                    # popup=pop_up_text, 
                    tooltip=row.loc['Stroke Team']
        # ))
                    ).add_to(clinic_map)
        # folium.Circle(
        #     radius=100, # metres
        #     location=[row.loc['lat'], row.loc['long']],
        #     popup=pop_up_text,
        #     color='black',
        #     tooltip=row.loc['Stroke Team'],
        #     fill=False,
        #     weight=1
        # ).add_to(clinic_map)
        # fg.add_child(
        #     folium.Marker(location=[row.loc['lat'], row.loc['long']], 
        #               popup=pop_up_text, 
        #               tooltip=row.loc['Name'],
        #               icon=icon
        #               )
        # )

    # # Add choropleth
    # fg.add_child(
    #     folium.Choropleth(geo_data=geojson_cornwall,
    #                     name='choropleth',
    #                     data=df_travel_times,
    #                     columns=['LSOA11CD', 'travel_time_mins'],
    #                     key_on='feature.id',
    #                     fill_color='OrRd',
    #                     fill_opacity=0.5,
    #                     line_opacity=0.5,
    #                     legend_name='travel_time_mins',
    #                     highlight=True
    #                     )
    #                     )#.add_to(clinic_map)


    # # This works for starting the map in this area
    # # with the max zoom possible.
    # folium.map.FitBounds(
    #     bounds=[(50, -4), (51, -3)],
    #     padding_top_left=None,
    #     padding_bottom_right=None,
    #     padding=None,
    #     max_zoom=None
    #     ).add_to(clinic_map)

    folium.map.LayerControl().add_to(clinic_map)
    # fg.add_child(folium.map.LayerControl())

    # Generate map
    # clinic_map
    output = st_folium(
        clinic_map,
        # feature_group_to_add=fg,
        returned_objects=[
            # 'bounds',
            # 'center',
            # "last_object_clicked", #_tooltip",
            # 'zoom'
        ],
        )
    st.write(output)
    # st.stop()


def draw_map_plotly(df_placeholder, geojson_ew, lat_hospital, long_hospital):
    import plotly.express as px

    fig = px.choropleth_mapbox(
        df_placeholder,
        geojson=geojson_ew, 
        locations='LSOA11NMW',
        color='Placeholder',
        color_continuous_scale="Viridis",
        # range_color=(0, 12),
        mapbox_style="carto-positron",
        zoom=9, 
        center = {"lat": lat_hospital, "lon": long_hospital},
        opacity=0.5,
        # labels={'unemp':'unemployment rate'}
    )
    # fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    # fig.show()
    st.plotly_chart(fig)



def draw_map_circles(lat_hospital, long_hospital, df_placeholder, df_hospitals, df_lsoa_regions):
    # Create a map
    # import leafmap.foliumap as leafmap

    # clinic_map = leafmap.Map(
    clinic_map = folium.Map(
        location=[lat_hospital, long_hospital],
        zoom_start=9,
        tiles='cartodbpositron',
        # prefer_canvas=True,
        # Override how much people can zoom in or out:
        min_zoom=0,
        max_zoom=18,
        width=1200,
        height=600
        )

    outcome_min = 0
    outcome_max = 1
    choro_bins = np.linspace(outcome_min, outcome_max, 7)

    # Make a new discrete colour map:
    # (colour names have to be #000000 strings or names)
    colormap = branca.colormap.StepColormap(
        vmin=outcome_min,
        vmax=outcome_max,
        colors=["red", "orange", "lightblue", "green", "darkgreen", 'blue'],
        caption='Placeholder',
        index=choro_bins
    )
    colormap.add_to(clinic_map)
    # fg.add_child(colormap)  # doesn't work

    # Add markers
    for (index, row) in df_hospitals.iterrows():
        # pop_up_text = f'{row.loc["Stroke Team"]}'

        if last_object_clicked_tooltip == row.loc['Stroke Team']:
            icon = folium.Icon(
                # color='black',
                # icon_color='white',
                icon='star', #'fa-solid fa-hospital',#'info-sign',
                # angle=0,
                prefix='glyphicon')#, prefix='fa')
        else:
            icon = None


        # fg.add_child(
        folium.Marker(location=[row.loc['lat'], row.loc['long']], 
                    # popup=pop_up_text, 
                    tooltip=row.loc['Stroke Team']
        # ))
                    ).add_to(clinic_map)

    marker_list = []
    for i, row in df_lsoa_regions.iterrows():
        # # folium.Circle(
        # # folium.PolyLine(
        #     # radius=100, # metres
        #     locations=[[row.loc['LSOA11LAT'], row.loc['LSOA11LONG']]],
        #     # popup=pop_up_text,
        #     color='black',
        #     tooltip=row.loc['LSOA11NM'],
        #     fill=True,
        #     weight=1
        # ).add_to(clinic_map)
        # pass
        marker_list.append(
        folium.Marker(
            [row.loc['LSOA11LAT'], row.loc['LSOA11LONG']],
        ))#.add_to(clinic_map)
    
    marker_list.add_to(clinic_map)
    
    # folium.plugins.FastMarkerCluster(
    #     np.transpose([df_lsoa_regions['LSOA11LAT'], df_lsoa_regions['LSOA11LONG']]),
    # ).add_to(clinic_map)
        
    # folium.plugins.HeatMap(
    #     np.transpose([df_lsoa_regions['LSOA11LAT'], df_lsoa_regions['LSOA11LONG']]),
    # ).add_to(clinic_map)

    folium.map.LayerControl().add_to(clinic_map)

    # Generate map
    output = st_folium(
        clinic_map,
        returned_objects=[
        ],
        )
    st.write(output)



def draw_map_leafmap(lat_hospital, long_hospital, geojson_list, region_list, df_placeholder, df_hospitals, nearest_hospital_geojson_list, nearest_mt_hospital_geojson_list, choro_bins=6):
    
    import leafmap.foliumap as leafmap

    # Create a map
    clinic_map = leafmap.Map(location=[lat_hospital, long_hospital],
                            zoom_start=9,
                            tiles='cartodbpositron',
                            # prefer_canvas=True,
                            # Override how much people can zoom in or out:
                            min_zoom=0,
                            max_zoom=18,
                            width=1200,
                            height=600
                            )


    outcome_min = 0
    outcome_max = 1
    choro_bins = np.linspace(outcome_min, outcome_max, 7)

    # Make a new discrete colour map:
    # (colour names have to be #000000 strings or names)
    colormap = branca.colormap.StepColormap(
        vmin=outcome_min,
        vmax=outcome_max,
        colors=["red", "orange", "LimeGreen", "green", "darkgreen", 'blue'],
        caption='Placeholder',
        index=choro_bins
    )
    colormap.add_to(clinic_map)
    # clinic_map.add_colormap(colormap)
    
    # Add choropleth
    for g, geojson_ew in enumerate(geojson_list):

        # style = {#lambda y:{
        #         # "fillColor": colormap(y["properties"]["Estimate_UN"]),
        #         # "fillColor": colormap(df_placeholder[df_placeholder['LSOA11NMW'] == y['properties']['LSOA11NMW']]['Placeholder'].iloc[0]),
        #         # "fillColor": colormap(df_placeholder[df_placeholder['LSOA11NMW'] == y['geometries']['properties']['LSOA11NMW']]['Placeholder'].iloc[0]),
        #         'fillColor': 'red',
        #         'stroke':'false',
        #         'fillOpacity': 0.5,
        #         'color':'black',  # line colour
        #         'weight':0.5,
        #         # 'dashArray': '5, 5'
        #     }

        # st.write(geojson_ew)

        # def style(y):
        #     # st.write(y)
        #     style_list=[]
        #     for x in y['features']:
        #         style_dict = {#lambda y:{
        #             # "fillColor": colormap(y["properties"]["Estimate_UN"]),
        #             "fillColor": colormap(
        #                 df_placeholder[
        #                     df_placeholder['LSOA11NMW'] == x['properties']['LSOA11NMW']
        #                     ]['Placeholder'].iloc[0]
        #                 ),
        #             # "fillColor": colormap(df_placeholder[df_placeholder['LSOA11NMW'] == y['geometries']['properties']['LSOA11NMW']]['Placeholder'].iloc[0]),
        #             # 'fillColor': 'red',
        #             'stroke':'false',
        #             'fillOpacity': 0.5,
        #             'color':'black',  # line colour
        #             'weight':0.5,
        #             # 'dashArray': '5, 5'
        #         }
        #         style_list.append(style_dict)
        #     # st.write(style_list)
        #     return style_list

        # st.write(geojson_ew)
        # colour_list = [
        #     colormap(
        #                 df_placeholder[
        #                     df_placeholder['LSOA11NMW'] == x['properties']['LSOA11NMW']
        #                     ]['Placeholder'].iloc[0]
        #                 )
        #     for x in geojson_ew['features']
        #     ]

        # ValueError: highlight_function should be a function that accepts items from data['features'] and returns a dictionary.


        # # fg.add_child(
        folium.GeoJson(
        # clinic_map.add_geojson(
            # in_geojson=geojson_ew,
            data=geojson_ew,
            tooltip=GeoJsonTooltip(
                fields=['LSOA11CD'],
                aliases=[''],
                localize=True
                ),
            # # lambda x:f"{x['properties']['LSOA11NMW']}",
            # # popup=popup,
            # name=region_list[g],
            # style=style(geojson_ew),
            style_function=lambda y:{  # style / style_function
                    # "fillColor": colormap(y["properties"]["Estimate_UN"]),
                    "fillColor": colormap(
                        df_placeholder[
                            df_placeholder['LSOA11CD'] == y['properties']['LSOA11CD']
                            ]['Placeholder'].iloc[0]
                        ),
                    # "fillColor": colormap(df_placeholder[df_placeholder['LSOA11NMW'] == y['geometries']['properties']['LSOA11NMW']]['Placeholder'].iloc[0]),
                    # 'fillColor': 'red',
                    # 'fillColor': colour_list,
                    # 'stroke':'false',
                    # 'fillOpacity': 0.5,
                    # 'color':'black',  # line colour
                    'weight':0.1,
                    # 'dashArray': '5, 5'
                },
            highlight_function=lambda y:{'weight': 2.0},  # highlight_function / hover_dict
            # smooth_factor=1.5,  # 2.0 is about the upper limit here
            # show=False if g > 0 else True
            ).add_to(clinic_map)
        # ))
        # )

    # for g, geojson_ew in enumerate(geojson_list):
    #     clinic_map.add_data(
    #         data=geojson_ew
    #     )



    fg = folium.FeatureGroup(name='hospital_markers')
    # Add markers
    for (index, row) in df_hospitals.iterrows():
        # pop_up_text = f'{row.loc["Stroke Team"]}'

        # if last_object_clicked_tooltip == row.loc['Stroke Team']:
        #     icon = folium.Icon(
        #         # color='black',
        #         # icon_color='white',
        #         icon='star', #'fa-solid fa-hospital',#'info-sign',
        #         # angle=0,
        #         prefix='glyphicon')#, prefix='fa')
        # else:
        #     icon = None


        fg.add_child(
        folium.Marker(
        # clinic_map.add_marker(
            location=[row.loc['lat'], row.loc['long']],
                    # popup=pop_up_text,
                    tooltip=row.loc['Stroke Team']
        ))
                    # )#.add_to(clinic_map)

    fg.add_to(clinic_map)

    # folium.map.LayerControl().add_to(clinic_map)
    clinic_map.add_layer_control()
    # fg.add_child(folium.map.LayerControl())

    # Generate map
    hello = clinic_map.to_streamlit()
    # hello = clinic_map.show_in_browser()

    # with open('pickle_test.p', 'wb') as pickle_file:
    #     pickle.dump(hello, pickle_file)

    # st.write(type(hello))
    # st.write(hello)
    # clinic_map
    # output = st_folium(
    #     clinic_map,
    #     # feature_group_to_add=fg,
    #     returned_objects=[
    #         # 'bounds',
    #         # 'center',
    #         # "last_object_clicked", #_tooltip",
    #         # 'zoom'
    #     ],
    #     )
    # st.write(output)
    # st.stop()


def draw_map_tiff(myarray, lat_hospital, long_hospital, geojson_list, region_list, df_placeholder, df_hospitals, nearest_hospital_geojson_list, nearest_mt_hospital_geojson_list, choro_bins=6):
    
    import leafmap.foliumap as leafmap
    import matplotlib.cm

    # Create a map
    clinic_map = leafmap.Map(
        location=[lat_hospital, long_hospital],
        zoom_start=9,
        tiles='cartodbpositron',
        # prefer_canvas=True,
        # Override how much people can zoom in or out:
        min_zoom=0,
        max_zoom=18,
        width=1200,
        height=600,
        draw_control=False,
        scale_control=False,
        search_control=False,
        measure_control=False
        )


    # leafmap.image_to_cog('./data_maps/LSOA_raster_test.tif', out_cog)



    # leafmap.plot_raster(out_cog, cmap='terrain', figsize=(15, 10))

    # st.write(leafmap.cog_validate(out_cog))#, verbose=True))

    # from PIL import Image
    # out_cog_rgb = Image.open(out_cog)
    # out_cog_rgb = out_cog_rgb.convert("RGB")

    # import rasterio as rio
    # with rio.open(out_cog) as src:
    #     out_cog_rgb = src.read()
    # st.write(out_cog_rgb.shape)

    # import os
    # os.environ['LOCALTILESERVER_CLIENT_PREFIX'] = 'proxy/{port}'


    # clinic_map.add_raster(out_cog,
    #                     #   cmap='terrain',
    #                     #    palette='inferno',
    #                        figsize=(15, 10)
    #                        )

    # import numpy as np
    # from osgeo import gdal
    # ds = gdal.Open(out_cog)
    # myarray = np.array(ds.GetRasterBand(1).ReadAsArray())

    # st.write(myarray)


    # def colour_func(x):
    #     vmin = 15
    #     vmax = 34740
    #     cmap = matplotlib.cm.get_cmap('inferno')
    #     val = (x - vmin) / (vmax - vmin)
    #     return cmap(val)


    folium.raster_layers.ImageOverlay(
        # name="Mercator projection SW",
        image=myarray,#out_cog,#out_cog,
        # bounds=[[49.8647411589999976, -6.4185476299999999], [55.8110685409999974, 1.7629415090000000]],
        bounds=[[49.6739854059999999, -6.6230848580000004], [56.0018242949999987, 1.9674787370000004]],
        # opacity=0.6,
        mercator_project=True,
        # colormap=colour_func,
        # interactive=True,
        # cross_origin=False,
        # zindex=1,
    ).add_to(clinic_map)

    # clinic_map.add_cog_layer(out_cog, bands=['Band 1'])# bands=bands, **vis_params)

    for geojson_ew in geojson_list:
        folium.GeoJson(
        # clinic_map.add_geojson(
            # in_geojson=geojson_ew,
            data=geojson_ew,
            tooltip=GeoJsonTooltip(
                fields=['LSOA11CD'],
                aliases=[''],
                localize=True
                ),
            # # lambda x:f"{x['properties']['LSOA11NMW']}",
            # # popup=popup,
            name='LSOAs',#region_list[g],
            # style=style(geojson_ew),
            style_function=lambda y:{  # style / style_function
                    # "fillColor": colormap(y["properties"]["Estimate_UN"]),
                    # "fillColor": colormap(
                    #     df_placeholder[
                    #         df_placeholder['LSOA11CD'] == y['properties']['LSOA11CD']
                    #         ]['Placeholder'].iloc[0]
                    #     ),
                    # "fillColor": colormap(df_placeholder[df_placeholder['LSOA11NMW'] == y['geometries']['properties']['LSOA11NMW']]['Placeholder'].iloc[0]),
                    'fillColor': 'rgba(0, 0, 0, 0)', #'red',
                    # 'fillColor': colour_list,
                    # 'stroke':'false',
                    # 'fillOpacity': 0.5,
                    # 'color':'black',  # line colour
                    'color': 'rgba(0, 0, 0, 0)',
                    'weight':0.1,
                    # 'dashArray': '5, 5'
                },
            highlight_function=lambda y:{'weight': 2.0, 'color': 'black'},  # highlight_function / hover_dict
            # smooth_factor=1.5,  # 2.0 is about the upper limit here
            # show=False if g > 0 else True
            ).add_to(clinic_map)
    


    fg = folium.FeatureGroup(name='hospital_markers')
    # Add markers
    for (index, row) in df_hospitals.iterrows():
        fg.add_child(
        folium.Marker(
        # clinic_map.add_marker(
            location=[row.loc['lat'], row.loc['long']],
                    # popup=pop_up_text,
                    tooltip=row.loc['Stroke Team']
        ))
                    # )#.add_to(clinic_map)

    fg.add_to(clinic_map)

    clinic_map.add_layer_control()

    # Generate map
    hello = clinic_map.to_streamlit()


# ###########################
# ##### START OF SCRIPT #####
# ###########################
page_setup()

# Title:
st.markdown('# Folium map test')


startTime = datetime.now()

try:
    last_object_clicked_tooltip = st.session_state['last_object_clicked_tooltip']
except KeyError:
    last_object_clicked_tooltip = ''


## Load data files
# Hospital info
df_hospitals = pd.read_csv("./data_maps/stroke_hospitals_22_reduced.csv")

# Select a hospital of interest
hospital_input = st.selectbox(
    'Pick a hospital',
    df_hospitals['Stroke Team']
)

# Find which region this hospital is in:
df_hospitals_regions = pd.read_csv("./data_maps/hospitals_and_lsoas.csv")
df_hospital_regions = df_hospitals_regions[df_hospitals_regions['Stroke Team'] == hospital_input]

long_hospital = df_hospital_regions['long'].iloc[0]
lat_hospital = df_hospital_regions['lat'].iloc[0]
region_hospital = df_hospital_regions['RGN11NM'].iloc[0]
if region_hospital == 'Wales':
    group_hospital = df_hospital_regions['LHB20NM'].iloc[0]
else:
    group_hospital = df_hospital_regions['STP19NM'].iloc[0]

# All hospital postcodes:
hospital_postcode_list = df_hospitals_regions['Postcode']

# travel times
# df_travel_times = pd.read_csv("./data_maps/clinic_travel_times.csv")
df_travel_matrix = pd.read_csv('./data_maps/lsoa_travel_time_matrix_calibrated.csv')
LSOA_names = df_travel_matrix['LSOA']
# st.write(len(LSOA_names), LSOA_names[:10])
placeholder = np.random.rand(len(LSOA_names))
table_placeholder = np.stack([LSOA_names, placeholder], axis=-1)
# st.write(table_placeholder)
df_placeholder = pd.DataFrame(
    data=table_placeholder,
    columns=['LSOA11NMW', 'Placeholder']
)
# st.write(df_placeholder)

# LSOA lat/long:

df_lsoa_regions = pd.read_csv('./data_maps/LSOA_regions.csv')



time2 = datetime.now()


# # geojson_ew = import_geojson(group_hospital)

region_list = [
    'Devon',
    'Dorset',
    'Cornwall and the Isles of Scilly',
    'Somerset'
]
# region_list = ['South West']

geojson_list = []
nearest_hospital_geojson_list = []
nearest_mt_hospital_geojson_list = []
# for region in region_list:
#     geojson_ew = import_geojson(region)
#     geojson_list.append(geojson_ew)

# # geojson_file = 'LSOA_South~West_t.geojson'
geojson_file = 'LSOA_(Dec_2011)_Boundaries_Super_Generalised_Clipped_(BSC)_EW_V3_reduced.geojson'
with open('./data_maps/' + geojson_file) as f:
    geojson_ew = json.load(f)

# Make a list of the order of LSOA codes in the geojson that made the geotiff
LSOA_names = []
for i in geojson_ew['features']:
    LSOA_names.append(i['properties']['LSOA11CD'])
# st.write(LSOA_names)

# st.write(LSOA_names[])

# st.write(len(LSOA_names), LSOA_names[:10])
# LSOA_names = df_travel_matrix['LSOA']
placeholder = np.random.rand(len(LSOA_names))
table_placeholder = np.stack(np.array([LSOA_names, placeholder], dtype=object), axis=-1)
# st.write(table_placeholder)
df_placeholder = pd.DataFrame(
    data=table_placeholder,
    columns=['LSOA11CD', 'Placeholder']
)

# st.write(df_placeholder)


# st.write(geojson_ew)

# # Copy the LSOA11CD code to features.id within geojson
# for i in geojson_ew['features']:
#     i['id'] = i['properties']['LSOA11NMW']

# for i in geojson_ew['objects']['LSOA_South~West']['geometries']:
#     i['id'] = i['properties']['LSOA11NMW']
geojson_list = [geojson_ew]

# for hospital_postcode in hospital_postcode_list:
#     try:
#         nearest_hospital_geojson = import_hospital_geojson(hospital_postcode)
#         nearest_hospital_geojson_list.append(nearest_hospital_geojson)
#     except FileNotFoundError:
#         pass

#     try:
#         nearest_mt_hospital_geojson = import_hospital_geojson(hospital_postcode, MT=True)
#         nearest_mt_hospital_geojson_list.append(nearest_mt_hospital_geojson)
#     except FileNotFoundError:
#         pass

# st.write(geojson_ew['features'][0])


time3 = datetime.now()
st.write('Time to import geojson:', time3 - startTime)

# st.stop()

time4 = datetime.now()

# draw_map(lat_hospital, long_hospital, geojson_list, region_list, df_placeholder, df_hospitals, nearest_hospital_geojson_list, nearest_mt_hospital_geojson_list)#, choro_bins)
# draw_map_plotly(df_placeholder, geojson_ew, lat_hospital, long_hospital)

# draw_map_circles(lat_hospital, long_hospital, df_placeholder, df_hospitals, df_lsoa_regions)

# with st.spinner(text='Drawing map'):
#     draw_map_leafmap(lat_hospital, long_hospital, geojson_list, region_list, df_placeholder, df_hospitals, nearest_hospital_geojson_list, nearest_mt_hospital_geojson_list)#, choro_bins)



# Import map tiff
out_cog = 'data_maps/LSOA_cog_colours.tif'
# out_cog = 'data_maps/LSOA_raster_test.tif'
import rasterio

with rasterio.open(out_cog, 'r') as ds:
    myarray_colours = ds.read()  # read all raster values

myarray_colours = np.transpose(myarray_colours, axes=(1, 2, 0))

# st.write(myarray)

# myarray = myarray[0, :, :]
# st.write(myarray.shape)
# # st.write(myarray)
# st.write(
#     len(
#         sorted(
#             list(
#                 set(
#                     myarray.ravel().tolist()
#                 )
#             )
#         )
#     )
# )
# st.write(len(LSOA_names) - 1) # minus 1 for the sea





# myarray_colours = np.full((*myarray.shape, 4), 0.0)
# # Alpha
# # Set this to non-zero for all valid pixels and zero for invalid
# # (e.g. the sea, bits of other countries)
# myarray_colours[:, :, 3] = np.full(myarray.shape, 0.6)
# myarray_colours[np.where(myarray == 0)[0], np.where(myarray == 0)[1], 3] = 0

# # for ind_LSOA, LSOA in enumerate(LSOA_names):
# #     # The value of this LSOA in the cog is +1
# #     # because the value of the sea (blank areas) is 0.
# #     value_in_cog = ind_LSOA + 1
# #     # Find where these values are in the image:
# #     inds_in_cog = np.where(myarray == value_in_cog)
# #     # Look up which colour to set this to:
# #     # TEMPORARY set to some colour:
# #     colour_rgb = [ind_LSOA / len(LSOA_names), 0, 0]
# #     # Update the colour array with these values:

# #     # Red
# #     myarray_colours[inds_in_cog[0], inds_in_cog[1], 0] = colour_rgb[0]
# #     # Green
# #     myarray_colours[inds_in_cog[0], inds_in_cog[1], 1] = colour_rgb[1]
# #     # Blue
# #     myarray_colours[inds_in_cog[0], inds_in_cog[1], 2] = colour_rgb[2]

# # Red
# myarray_colours[:, :, 0] = np.random.rand(*myarray.shape)
# # Green
# myarray_colours[:, :, 1] = np.random.rand(*myarray.shape)
# # Blue
# myarray_colours[:, :, 2] = np.random.rand(*myarray.shape)

# time5 = datetime.now()
# st.write('Time to make colours:', time5 - time4)

# st.write(myarray_colours.shape)
# st.write(myarray)
# st.stop()


# # myarray[np.where(myarray > 0)] = 1
# st.write(len(np.where(myarray > 0)[0]))
# st.write(len(np.where(myarray > 14)[0]))

with st.spinner(text='Drawing map'):
    draw_map_tiff(myarray_colours, lat_hospital, long_hospital, geojson_list, region_list, df_placeholder, df_hospitals, nearest_hospital_geojson_list, nearest_mt_hospital_geojson_list)#, choro_bins)


time5 = datetime.now()

st.write('Time to draw map:', time5 - time4)
st.stop()


import streamlit.components.v1 as components
with st.spinner(text='Loading map'):

    with open("data_maps/folium_EW_reduced2_placeholder.html", 'r', encoding='utf-8') as HtmlFile:
        source_code = HtmlFile.read()
        # print(source_code)

# st.write(source_code)

with st.spinner(text='Drawing map'):
    components.html(source_code, height=600)
    # components.iframe("data_maps/folium_EW_reduced_placeholder.html", height=600)

time5 = datetime.now()

st.write('Time to draw map:', time5 - time4)

# st.session_state['last_object_clicked_tooltip'] = output['last_object_clicked_tooltip']

# {
# "last_clicked":NULL
# "last_object_clicked":NULL
# "last_object_clicked_tooltip":NULL
# "all_drawings":NULL
# "last_active_drawing":NULL
# "bounds":{
#     "_southWest":{
#     "lat":39.94384773921137
#     "lng":-75.15805006027223
#     }
# "_northEast":{
#     "lat":39.9553624980935
#     "lng":-75.14249324798585
#     }
#     }
# "zoom":16
# "last_circle_radius":NULL
# "last_circle_polygon":NULL
# "center":{
# "lat":39.94961
# "lng":-75.150282
# }
# }

# st.write(output)


# st.stop()
# ----- The end! -----
