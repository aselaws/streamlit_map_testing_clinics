import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import os
import geopandas
from geojson_rewind import rewind
import pyproj  # for crs conversion

from datetime import datetime

from utilities_maps.fixed_params import page_setup


def import_geojson(region_type: 'str'):
    """
    Import a geojson file as GeoDataFrame.

    The crs (coordinate reference system) is set to British National
    Grid.

    Inputs
    ------
    region_type - str. Lookup name for selecting a geojson file.
                  This should be one of the column names from the
                  various regions files.

    Returns
    -------
    gdf_boundaries - GeoDataFrame. One row per region shape in the
                     file. Expect columns for region name and geometry.
    """
    # Select geojson file based on input region type:
    geojson_file_dict = {
        'LSOA11NM': 'LSOA.geojson',
        'SICBL22NM': 'SICBL.geojson',
        'LHB20NM': 'LHB.geojson'
    }

    # Import region file:
    file_input = geojson_file_dict[region_type]
    # Relative import from package files:
    # path_to_file = files('stroke_maps.data').joinpath(file_input)
    path_to_file = os.path.join('data_maps', file_input)
    gdf_boundaries = geopandas.read_file(path_to_file)

    if region_type == 'LSOA11NM':
        index_col = 'LSOA11CD'
        # Only keep these columns.
        geo_cols = ['LSOA11NM', 'BNG_E', 'BNG_N',
                    'LONG', 'LAT', 'GlobalID', 'geometry']

    else:
        index_col = 'region_code'
        # Only keep these columns:
        geo_cols = ['region', 'BNG_E', 'BNG_N',
                    'LONG', 'LAT', 'GlobalID', 'geometry']

        # Find which columns to rename to 'region' and 'region_code'.
        if (region_type.endswith('NM') | region_type.endswith('NMW')):
            region_prefix = region_type.removesuffix('NM')
            region_prefix = region_prefix.removesuffix('NMW')
            region_code = region_prefix + 'CD'
        elif (region_type.endswith('nm') | region_type.endswith('nmw')):
            region_prefix = region_type.removesuffix('NM')
            region_prefix = region_prefix.removesuffix('NMW')
            region_code = region_prefix + 'cd'
        else:
            # This shouldn't happen.
            # TO DO - does this need a proper exception or can
            # we just change the above to if/else? ------------------------------
            region_code = region_type[:-2] + 'CD'

        try:
            # Rename this column:
            gdf_boundaries = gdf_boundaries.rename(columns={
                region_type: 'region',
                region_code: 'region_code'
            })
        except KeyError:
            # That column doesn't exist.
            # Try finding a column that has the same start and end
            # as requested:
            prefix = region_type[:3]
            suffix = region_type[-2:]
            success = False
            for column in gdf_boundaries.columns:
                # Casefold turns all UPPER into lower case.
                match = ((column[:3].casefold() == prefix.casefold()) &
                         (column[-2:].casefold() == suffix.casefold()))
                if match:
                    # Rename this column:
                    col_code = column[:-2] + region_code[-2:]
                    gdf_boundaries = gdf_boundaries.rename(columns={
                        column: 'region',
                        col_code: 'region_code'
                        })
                    success = True
                else:
                    pass
            if success is False:
                pass
                # TO DO - proper error here --------------------------------

    # Set the index:
    gdf_boundaries = gdf_boundaries.set_index(index_col)
    # Only keep geometry data:
    gdf_boundaries = gdf_boundaries[geo_cols]

    # If crs is given in the file, geopandas automatically
    # pulls it through. Convert to National Grid coordinates:
    if gdf_boundaries.crs != 'EPSG:27700':
        gdf_boundaries = gdf_boundaries.to_crs('EPSG:27700')
    return gdf_boundaries


def _load_geometry_lsoa(df_lsoa):
    """
    Create GeoDataFrames of new geometry and existing DataFrames.

    Inputs
    ------
    df_lsoa - pd.DataFrame. LSOA info.

    Returns
    -------
    gdf_boundaries_lsoa - GeoDataFrame. LSOA info and geometry.
    """

    # All LSOA shapes:
    gdf_boundaries_lsoa = import_geojson('LSOA11NM')
    crs = gdf_boundaries_lsoa.crs
    # Index column: LSOA11CD.
    # Always has only one unnamed column index level.
    gdf_boundaries_lsoa = gdf_boundaries_lsoa.reset_index()
    gdf_boundaries_lsoa = gdf_boundaries_lsoa.rename(
        columns={'LSOA11NM': 'lsoa', 'LSOA11CD': 'lsoa_code'})
    gdf_boundaries_lsoa = gdf_boundaries_lsoa.set_index(['lsoa', 'lsoa_code'])

    # ----- Prepare separate data -----
    # Set up column level info for the merged DataFrame.
    # Everything needs at least two levels: scenario and property.
    # Sometimes also a 'subtype' level.
    # Add another column level to the coordinates.
    col_level_names = df_lsoa.columns.names
    cols_gdf_boundaries_lsoa = [
        gdf_boundaries_lsoa.columns,                 # property
        ['any'] * len(gdf_boundaries_lsoa.columns),  # scenario
    ]
    if 'subtype' in col_level_names:
        cols_gdf_boundaries_lsoa.append([''] * len(gdf_boundaries_lsoa.columns))

    # Make all data to be combined have the same column levels.
    # Geometry:
    gdf_boundaries_lsoa = pd.DataFrame(
        gdf_boundaries_lsoa.values,
        index=gdf_boundaries_lsoa.index,
        columns=cols_gdf_boundaries_lsoa
    )

    # ----- Create final data -----
    # Merge together all of the DataFrames.
    gdf_boundaries_lsoa = pd.merge(
        gdf_boundaries_lsoa, df_lsoa,
        left_index=True, right_index=True, how='right'
    )
    # Name the column levels:
    gdf_boundaries_lsoa.columns = (
        gdf_boundaries_lsoa.columns.set_names(col_level_names))

    # Sort the results by scenario:
    gdf_boundaries_lsoa = gdf_boundaries_lsoa.sort_index(
        axis='columns', level='scenario')

    # Convert to GeoDataFrame:
    col_geo = find_multiindex_column_names(
        gdf_boundaries_lsoa, property=['geometry'])
    gdf_boundaries_lsoa = geopandas.GeoDataFrame(
        gdf_boundaries_lsoa,
        geometry=col_geo,
        crs=crs
        )
    return gdf_boundaries_lsoa


def find_multiindex_column_names(gdf, **kwargs):
    """
    Find the full column name to match a partial column name.

    Example usage:
    find_multiindex_column_name(gdf, scenario='any', property='geometry')

    Inputs
    ------
    gdf    - GeoDataFrame.
    kwargs - in format level_name=column_name for column level names
             in the gdf column MultiIndex.

    Returns
    -------
    cols - list or str or tuple. The column name(s) matching the
           requested names in those levels.
    """
    masks = [
        gdf.columns.get_level_values(level).isin(col_list)
        for level, col_list in kwargs.items()
    ]
    mask = np.all(masks, axis=0)
    cols = gdf.columns[mask]
    if len(cols) == 1:
        cols = cols.values[0]
    elif len(cols) == 0:
        cols = ''  # Should throw up a KeyError when used to index.
    return cols


def plotly_big_map(gdf, column_colour, column_geometry):
    gdf = gdf.copy()
    crs = gdf.crs
    gdf = gdf.reset_index()

    col_lsoa = find_multiindex_column_names(
        gdf, property=['lsoa'])

    # Only keep the required columns:
    gdf = gdf[[col_lsoa, column_colour, column_geometry]]
    # Only keep the 'property' subheading:
    gdf = pd.DataFrame(
        gdf.values,
        columns=['lsoa', 'outcome', 'geometry']
    )
    gdf = gdf.set_index('lsoa')
    gdf = geopandas.GeoDataFrame(gdf, geometry='geometry', crs=crs)

    # Has to be this CRS to prevent Picasso drawing:
    gdf = gdf.to_crs(pyproj.CRS.from_epsg(4326))

    fig = go.Figure()

    fig.update_layout(
        width=1200,
        height=1200
        )

    fig.add_trace(go.Choropleth(
        # gdf,
        geojson=gdf.geometry.__geo_interface__,
        locations=gdf.index,
        z=gdf.outcome,
        # featureidkey='properties.LSOA11NM',
        coloraxis="coloraxis",
        # colorscale='Inferno',
        # autocolorscale=False
    ))

    fig.update_layout(
        geo=dict(
            scope='world',
            projection=go.layout.geo.Projection(type='airy'),
            fitbounds='locations',
            visible=False
        ))
    # Remove LSOA borders:
    fig.update_traces(marker_line_width=0, selector=dict(type='choropleth'))

    # The initial colour map setting can take very many options,
    # but the later update with the drop-down menu only has a small list
    # of about ten coded in. You can't even provide a list of colours instead.
    # The available options are:
    # Blackbody, Bluered, Blues, Cividis, Earth, Electric, Greens, Greys,
    # Hot, Jet, Picnic, Portland, Rainbow, RdBu, Reds, Viridis, YlGnBu, YlOrRd.
    # As listed in: https://plotly.com/python-api-reference/generated/
    # plotly.graph_objects.Choropleth.html

    # fig.update_layout(
    #     coloraxis_colorscale='Electric',
    #     coloraxis_colorbar_title_text='Added utility',
    #     coloraxis_cmin=outcome_vmin,
    #     coloraxis_cmax=outcome_vmax,
    #     )

    # fig.update_layout(title_text='<b>Drip and Ship</b>', title_x=0.5)

    # fig.update_layout(
    #     updatemenus=[go.layout.Updatemenu(
    #         x=0, xanchor='right', y=1.15, type="dropdown",
    #         pad={'t': 5, 'r': 20, 'b': 0, 'l': 30},
    #         # ^ around all buttons (not indiv buttons)
    #         buttons=list([
    #             dict(
    #                 args=[
    #                     {
    #                         'z': [df_outcomes[
    #                             'drip_ship_lvo_mt_added_utility']],
    #                     },
    #                     {
    #                         'coloraxis.colorscale': 'Electric',
    #                         'coloraxis.reversescale': False,
    #                         'coloraxis.cmin': outcome_vmin,
    #                         'coloraxis.cmax': outcome_vmax,
    #                         'title.text': '<b>Drip and Ship</b>'
    #                     }],
    #                 label='Drip & Ship',
    #                 method='update'
    #             ),
    #             dict(
    #                 args=[
    #                     {
    #                         'z': [df_outcomes[
    #                             'mothership_lvo_mt_added_utility']],
    #                     },
    #                     {
    #                         'coloraxis.colorscale': 'Electric',
    #                         'coloraxis.reversescale': False,
    #                         'coloraxis.cmin': outcome_vmin,
    #                         'coloraxis.cmax': outcome_vmax,
    #                         'title.text': '<b>Mothership</b>'
    #                     }],
    #                 label='Mothership',
    #                 method='update'
    #             ),
    #             dict(
    #                 args=[
    #                     {
    #                         'z': [df_outcomes['diff_lvo_mt_added_utility']],
    #                     },
    #                     {
    #                         'coloraxis.colorscale': 'RdBu',
    #                         'coloraxis.reversescale': True,
    #                         'coloraxis.cmin': diff_vmin,
    #                         'coloraxis.cmax': diff_vmax,
    #                         'title.text': '<b>Difference</b>'
    #                     }],
    #                 label='Diff',
    #                 method='update'
    #             )
    #             ])
    #     )]
    # )
    fig.update_traces(hovertemplate='%{z}<extra>%{location}</extra>')

    # fig.write_html('data_maps/plotly_test.html')

    st.plotly_chart(fig)


# ###########################
# ##### START OF SCRIPT #####
# ###########################
page_setup()

# Title:
st.markdown('# Geopandas')

startTime = datetime.now()

# Load outcome data
time_o_start = datetime.now()
# Load data files
df_lsoa = pd.read_csv(
    os.path.join('data_maps', 'df_lsoa.csv'),
    index_col=[0, 1],
    header=[0, 1, 2],
)
time_o_end = datetime.now()
st.write(f'Time to load outcomes: {time_o_end - time_o_start}')

# # Load geography
# time_g_start = datetime.now()
# gdf_boundaries_lsoa = import_geojson('LSOA11NM')
# time_g_end = datetime.now()
# st.write(f'Time to load geography: {time_g_end - time_g_start}')

# Merge outcome and geography:
time_m_start = datetime.now()
gdf_boundaries_lsoa = _load_geometry_lsoa(df_lsoa)

# st.write(type(gdf_boundaries_lsoa))
# st.write('')
# st.write(gdf_boundaries_lsoa.info())
# st.write(gdf_boundaries_lsoa.crs)
time_m_end = datetime.now()
st.write(f'Time to merge geography and outcomes: {time_m_end - time_m_start}')

# Plot map:
time_p_start = datetime.now()
with st.spinner(text='Drawing map'):
    col_col = find_multiindex_column_names(
        gdf_boundaries_lsoa,
        property=['mRS shift'],
        scenario=['mothership'],
        subtype=['mean']
        )
    col_geo = find_multiindex_column_names(
        gdf_boundaries_lsoa, property=['geometry'])
    gdf_boundaries_lsoa = gdf_boundaries_lsoa.set_geometry(col_geo)
    plotly_big_map(
        gdf_boundaries_lsoa,
        column_colour=col_col,
        column_geometry=col_geo
        )
time_p_end = datetime.now()
st.write(f'Time to draw map: {time_p_end - time_p_start}')