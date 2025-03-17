import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from pandas.tseries.holiday import USFederalHolidayCalendar

# GLOBALS
COLS_TO_DROP = ['Unique ID', 'Nature Code', 'Street Address',
                'State Plane Feet X', 'State Plane Feet Y',
                'FirstResponding', 'FirstArrival', 'FullComplement',
                'Shift', 'Battalion', 'Division', 'DispatchNature',
                'CauseCategory']


def data_import(df: pd.DataFrame) -> pd.DataFrame:
    """
    Import data from CSV
    """
    # Get EMS data
    ems_df = df[df['CauseCategory'] == 'EMS'].reset_index(drop=True)

    # Convert 'Dispatched' column to datetime format
    ems_df['Dispatched'] = pd.to_datetime(ems_df['Dispatched'])

    # Get Date from 'Dispatched'
    ems_df['Date'] = ems_df['Dispatched'].dt.date

    print("Data imported - filtered to EMS")
    return ems_df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans up dataframe by dropping unnecessary columns, renaming column names, adding dummy categories, and updating date/time with cyclical info

    Args:
        df: pandas Dataframe for EMS calls
    
    Returns:
        df: updated dataframe
    """
    if 'Cluster' in df.columns:
        df.drop(['Cluster'], axis=1, inplace=True)

    # Feature engineering
    # TODO: add additional features
    df['Date-Hr'] = pd.to_datetime(df['Date-Hr'])
    df['Year'] = df['Date-Hr'].dt.year
    df['Month'] = df['Date-Hr'].dt.month
    df['Day'] = df['Date-Hr'].dt.day  # Monday=0, Sunday=6
    df['Hour'] = df['Date-Hr'].dt.hour
    df['Day_of_Week'] = df['Date-Hr'].dt.weekday

    # Holidays
    cal = USFederalHolidayCalendar()
    us_holidays = cal.holidays(start=df['Date-Hr'].min(), end=df['Date-Hr'].max())
    df['is_holiday'] = df['Date-Hr'].isin(us_holidays).astype(int)

    # Weekend
    df['is_weekend'] = df['Day_of_Week'].isin([4, 5, 6]).astype(int)

    # Add cyclical date data
    df['Hour_sin'] = np.sin(2 * np.pi * df['Hour'] / 24)
    df['Hour_cos'] = np.cos(2 * np.pi * df['Hour'] / 24)
    df['Day_sin'] = np.sin(2 * np.pi * df['Day'] / 7)
    df['Day_cos'] = np.cos(2 * np.pi * df['Day'] / 7)
    df['Month_sin'] = np.sin(2 * np.pi * df['Month'] / 12)
    df['Month_cos'] = np.cos(2 * np.pi * df['Month'] / 12)

    return df


def k_means(df: pd.DataFrame, num_clusters: int):
    """
    Group coordinates into clusters using K-Means

    Params:
        df: pandas.DataFrame - set of all coordinates in historical data
        num_cluster: int - number of clusters to group coordinates by
    
    Returns:
        df: panadas.DataFrame - original df with additional 'Clusters' column
    """
    cluster_df = df[['Latitude', 'Longitude']]
    model = KMeans(n_clusters=num_clusters)
    y_kmeans = model.fit_predict(cluster_df)
    df['Cluster'] = y_kmeans

    print(f"{num_clusters} clusters created")
    return df


def split_by_cluster(df):
    """
    Split DataFrame by cluster

    Params:
        df: pandas.DataFrame - data on coordinates - must have 'Cluster' column
            (see k_means)
    
    Returns:
        dfs: dict - dictionary where key = cluster id, value = cluster's data
    """
    dfs = {key: value for key, value in df.groupby('Cluster')}
    return dfs


if __name__ == "__main__":
    ems_df = data_import()
    cluster_df = k_means(ems_df, 5)
    dfs = split_by_cluster(cluster_df)
