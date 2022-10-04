import numpy as np
import pandas as pd
import plotly_express as px
import plotly.graph_objects as go

from typing import Optional, Union

import statsmodels.api as sm
import datetime

from spacetime.graphics.controlCubeSorter import sort_cube_data
from spacetime.operations.cubeToDataframe import cube_to_dataframe


# Style color presets
COLOR_STYLES = {
    "chart_background": "#222831",
    "chart_grid": "#41434a",
    "tick_font": "#bbbbbb",
    "font": "#bbbbbb",
    "line_colors": [
        "#777777"
    ],
    "marker_colors": [
        "#FF00FF",
        "#00FFFF",
        "#0000FF",
        "#FFFF00",
        "#00FF00",
        "#FF0000",
    ]
}

# flags for sorting the selected data, Currently unused.
FLAGS = {
    "base"              : ["Base", COLOR_STYLES["line_colors"][0]],
    "below_avg"         : ["Below Average", COLOR_STYLES["marker_colors"][0]],
    "above_avg"         : ["Above Average", COLOR_STYLES["marker_colors"][1]],
    "deviation_above"   : ["Deviation Below", COLOR_STYLES["marker_colors"][2]],
    "deviation_below"   : ["Deviation Above", COLOR_STYLES["marker_colors"][3]],
    "trending_up"       : ["Trending Up", COLOR_STYLES["marker_colors"][4]],
    "trending_down"     : ["Trending Down", COLOR_STYLES["marker_colors"][5]],
}


# Main cube plotting method
########################################################################################################################
def plot_cube(
        cube,
        plot_type: str = "timeseries",
        variable: Optional[Union[str, int]] = None,
        summary: str = "mean",
        show_avg: str = "all",
        show_deviations: str = "all",
        deviation_coefficient: int = 1,
        show_trends: str = "updown",
        histo_type: str = "value",
        show_plot: bool = True,
) -> None:

    df_plot = organize_dataframe(cube, plot_type, variable, summary)

    fig = go.Figure
    if plot_type == 'space':
        fig = plot_spatial(cube, df_plot)

    if plot_type == 'timeseries':
        fig = plot_timeseries(df_plot)

    if plot_type == 'control':
        fig = plot_control(df_plot, show_avg, show_deviations, deviation_coefficient, show_trends)

    if plot_type == 'histogram':
        fig = plot_histogram(df_plot, histo_type)

    if show_plot:
        fig.show()


# Secondary cube plotting methods
########################################################################################################################
# Plot a spatial choropleth chart
def plot_spatial(cube, df) -> go.Figure:

    time = df["timeChar"]
    maxVal = np.nanmax(df["value"])

    coords = cube.get_UL_corner()

    fig = px.scatter_mapbox(
        df,
        lat='lat',
        lon='lon',
        color='value',
        animation_frame=time,
        range_color=(0, maxVal),
        color_continuous_scale='Viridis',
        opacity=0.5,
    )

    fig.update_layout(
        mapbox_style='carto-darkmatter',
        mapbox_zoom=3,
        mapbox_center={'lat': coords[0], 'lon': coords[1]},
    )  # Spatial chart specific layout options.

    fig = update_fig_layout(fig)

    return fig


# Plot a time series chart
def plot_timeseries(df) -> go.Figure:\

    time = df['time']

    if 'variables' in list(df.columns):
        fig = px.line(df, x=time, y="value", color='variables')
    else:
        fig = px.line(df, x=time, y="value")

    fig = update_fig_layout(fig)

    return fig


# Plot a control chart
def plot_control(df, show_avg, show_deviations, deviation_coefficient, show_trends) -> go.Figure:

    # Additional processing necessary for control chart plotting.
    df_plot, segments = sort_cube_data(df, FLAGS, show_avg='all', show_deviations='all', show_trends='updown')

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_plot['time'],
        y=df_plot['value'],
        mode='lines',
        line=dict(color=FLAGS['base'][1]),
        showlegend=False,
    ))  # Base line plot

    for key in FLAGS.keys():
        summ_df = df_plot[df_plot.flag == key]
        if show_avg != 'none':
            if key == 'above_avg' and show_avg != 'below':
                marker_name = FLAGS[key][0]
                marker_color = FLAGS[key][1]
                fig = add_markers(summ_df, fig, marker_name, marker_color)
            if key == 'below_avg' and show_avg != 'above':
                marker_name = FLAGS[key][0]
                marker_color = FLAGS[key][1]
                fig = add_markers(summ_df, fig, marker_name, marker_color)

        if show_deviations != 'none':
            if key == 'deviation_above' and show_avg != 'below':
                marker_name = FLAGS[key][0]
                marker_color = FLAGS[key][1]
                fig = add_markers(summ_df, fig, marker_name, marker_color)
            if key == 'deviation_below' and show_avg != 'above':
                marker_name = FLAGS[key][0]
                marker_color = FLAGS[key][1]
                fig = add_markers(summ_df, fig, marker_name, marker_color)

    if show_trends != 'none':
        for start_idx, end_idx in zip(segments[:-1], segments[1:]):
            segment = df_plot.iloc[start_idx:end_idx + 1, :].copy()

            segment['serial_time'] = [(d - datetime.datetime(1970, 1, 1)).days for d in segment['time']]

            x = sm.add_constant(segment['serial_time'])
            model = sm.OLS(segment['value'], x).fit()
            segment['fitted_values'] = model.fittedvalues

            fit_color = COLOR_STYLES['marker_colors'][4] if model.params['serial_time'] > 0 \
                else COLOR_STYLES['marker_colors'][5]

            trend_name = "Trending Up" if model.params['serial_time'] > 0 else "Trending Down"

            print_trend = False

            if show_trends == 'all':
                print_trend = True
            else:
                if model.f_pvalue < 0.05:
                    if show_trends == 'up' and model.params['serial_time'] > 0:
                        print_trend = True
                    elif show_trends == 'down' and model.params['serial_time'] <= 0:
                        print_trend = True
                    elif show_trends == 'updown':
                        print_trend = True
                    else:
                        pass
                else:
                    pass

            if print_trend:
                fig.add_trace(go.Scatter(
                    x=segment['time'],
                    y=segment['fitted_values'],
                    mode='lines',
                    line=dict(color=fit_color),
                    name=trend_name,
                ))

        # Ensure duplicate legend items get filtered
        legend_names = set()
        fig.for_each_trace(
            lambda trace:
                trace.update(showlegend=False) if (trace.name in legend_names) else legend_names.add(trace.name)
        )

    return fig


# Plot a Histogram of the chart data
def plot_histogram(df_plot, histo_type) -> go.Figure:
    fig = go.Figure()

    # We like having the distribution rug plot on the chart, but it's only easily done with plotly_express
    fig = px.histogram(df_plot, x='value', marginal='rug', color='variables')

    # I would like to have a couple ways to make Histograms, based on the distribution of values numerically,
    #   as well as the distribution of values geographically. Have to figure out how to enable the distribution chart
    #   without effectively just writing out two histograms if I don't have to.
    #
    # if histo_type == 'value':
    #     for variable in pd.unique(df_plot['variables']):
    #         fig.add_trace(
    #             go.Histogram(x=df_plot['value'].loc[df_plot['variables'] == variable], name=("variable: " + variable))
    #         )
    #
    #     fig.update_layout(barmode='stack')
    #
    # if histo_type == 'geographic':

    # TODO: gonna have to fix aggregation functions in order to solve how to categorize the data geographically.
    #       This is easy enough to do for Min, Max, and Median, which all look for existing values, but for Mean it may
    #       become complicated.

    return fig


# Helper methods
########################################################################################################################
# Process Cube data for chart plotting
def organize_dataframe(cube, plot_type, variable, summary) -> pd.DataFrame:
    df = cube_to_dataframe(cube)
    shape_val = cube.get_shapeval()

    if shape_val == 4:

        if plot_type == "space":
            if variable == None:
                df_plot = df[df['variables'] == df['variables'][0]]
            else:
                df_plot = df[df['variables'] == variable]
        else:
            df_plot = df
    else:
        df_plot = df

    df_plot = df_plot.where(df_plot != cube.get_nodata_value())
    summ_df = pd.DataFrame

    if plot_type != 'space':
        if shape_val == 4:
            if summary == "mean":
                summ_df = df_plot.groupby(["time", "variables"]).mean().reset_index()
            if summary == "median":
                summ_df = df_plot.groupby(['time', "variables"]).median().reset_index()
            if summary == "min":
                # summ_df = df_plot.groupby(['time', 'variables']).apply(lambda x: x[x['value'] == x['value'].min()])
                summ_df = df_plot.groupby(['time', "variables"]).min().reset_index()
            if summary == "max":
                # summ_df = df_plot.groupby(['time', 'variables']).apply(lambda x: x[x['value'] == x['value'].max()])
                summ_df = df_plot.groupby(['time', "variables"]).max().reset_index()
        else:
            if summary == "mean":
                summ_df = df_plot.groupby('time').mean().reset_index()
            if summary == "median":
                summ_df = df_plot.groupby('time').median().reset_index()
            if summary == "min":
                summ_df = df_plot.groupby('time').min().reset_index()
            if summary == "max":
                summ_df = df_plot.groupby('time').max().reset_index()
    else:
        summ_df = df_plot

    summ_df.insert(loc=0, column='timeChar', value=summ_df['time'].astype(str))

    return summ_df


# Add trace
def add_markers(df, fig, marker_name, marker_color):
    fig.add_trace(go.Scatter(
        x=df['time'],
        y=df['value'],
        mode='markers',
        name=marker_name,
        marker_color=marker_color,
    ))

    return fig


# Chart Figure layout update
def update_fig_layout(fig) -> go.Figure:
    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 20, "b": 0},
        plot_bgcolor='#252e3f',
        paper_bgcolor='#252e3f',
        font=dict(color='#7fafdf'),
    )

    return fig
