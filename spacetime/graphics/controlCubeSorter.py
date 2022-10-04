# Sorting methods for control chart output.
import pandas
import pandas as pd
import numpy as np

from typing import Tuple, List


# Main Method
########################################################################################################################
def sort_cube_data(
        df: pandas.DataFrame,
        FLAGS,
        show_avg="all",
        show_deviations="all",
        deviation_coefficient=1,
        show_trends="updown",

) -> Tuple[pandas.DataFrame, List]:
    print("Sorting through data in cube.")

    df_sorted = df
    df_sorted.insert(loc=0, column='flag', value='base')

    if show_avg != 'none':
        df_sorted = sort_average(df, show_avg)
    if show_deviations != 'none':
        df_sorted = sort_deviations(df, show_deviations, coefficient=deviation_coefficient)
    if show_trends != 'none':
        segments = sort_trends(df)
    else:
        df_sorted = df

    return df_sorted, segments


# Helper methods
########################################################################################################################
def sort_average(df, show_avg) -> pandas.DataFrame:
    avg = get_avg(df)
    if show_avg != 'below':
        df.loc[(df['value'] > avg), 'flag'] = 'above_avg'
    if show_avg != 'above':
        df.loc[(df['value'] < avg), 'flag'] = 'below_avg'

    return df


def sort_deviations(df, show_deviations, coefficient) -> pandas.DataFrame:
    std = np.std(df['value'])
    avg = get_avg(df)
    if show_deviations != 'below':
        df.loc[(df['value'] - (std * coefficient) > avg), 'flag'] = 'deviation_above'
    if show_deviations != 'above':
        df.loc[(df['value'] - (-(std * coefficient)) < avg), 'flag'] = 'deviation_below'

    return df


def sort_trends(df) -> List:
    min_change = 10
    curr_changes = 0
    last_sign = 1
    last_change_idx = 0
    bounds_idx = [0]
    cumulative_slope = [0]

    df['row'] = np.arange(len(df))

    # for each data point, calculate the slope of the linear regression that includes all the data points before it
    for i in range(1, df.shape[0]):
        segment = df.iloc[0:i + 1, :]

        slope = calc_slope(segment)
        cumulative_slope.append(slope)

        # compare the current cumulative slope with the previous, and keep track of whether it increased or decreased
        # as well as how many times it has changed in that direction, and where it last changed direction
        if abs(cumulative_slope[i]) < abs(cumulative_slope[i - 1]):
            if last_sign == 1:
                curr_changes = 0
            if curr_changes == 0:
                last_change_idx = i
            curr_changes += 1
            last_sign = -1

        elif abs(cumulative_slope[i]) > abs(cumulative_slope[i - 1]):
            if last_sign == -1:
                curr_changes = 0
            if curr_changes == 0:
                last_change_idx = i
            curr_changes += 1
            last_sign = 1

        # if we meet the minimum amount of times the slope changes in a direction, mark the last time it changed
        # and reset the change counter
        if curr_changes == min_change:
            curr_changes = 0
            bounds_idx.append(last_change_idx)

    # add the last point in the dataset to the bounds just to ensure we encapsulate all points
    bounds_idx.append(df.shape[0] - 1)
    return bounds_idx


def get_avg(df):
    return np.average(df['value'])


def calc_slope(df):

    slope = np.polyfit(df['row'], df['value'], 1)
    return slope[0]
