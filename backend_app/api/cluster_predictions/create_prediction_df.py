import numpy as np
import pandas as pd
from backend_app.api.cluster_predictions.preprocess import clean


def create_prediction_df(cluster, new_week_data_file_path=None):
    """
    Creates the final prediction dataframe for a given cluster.

    Parameters:
        cluster (Cluster): 
            The Cluster object containing historical data.
        new_week_data_file_path (str, optional): 
            Path to the newest week of data.

    Returns:
        pd.DataFrame: The final prediction dataframe combining past and future data.
    """
    cols_to_drop = ["Cluster", "Date-Hr", "Count"]
    # Get the latest week of real data
    latest_week_data = create_prediction_input_df(cluster, new_week_data_file_path)

    # Create an empty dataframe for next week's predictions
    future_week_data = create_new_prediction_df()

    # Drop unnecessary columns
    for col in cols_to_drop:
        if col in latest_week_data.columns:
            latest_week_data.drop(col, axis=1, inplace=True)
        # if col in future_week_data.columns:
        #     future_week_data.drop(col, axis=1, inplace=True)

    # Combine both datasets
    # final_prediction_df = pd.concat([latest_week_data, future_week_data], ignore_index=True)

    final_prediction_df = future_week_data
    return final_prediction_df


def create_prediction_input_df(cluster, new_week_data_file_path=None):
    """
    Creates a new prediction input dataframe for a specific cluster.
    Uses the newest week of data to generate inputs for prediction.

    Parameters:
        cluster (Cluster): 
            The Cluster object containing historical data.
        new_week_data_file_path (str, optional): 
            The file path to the newest week of data. If None, extracts the last week from cluster's data.

    Returns:
        pd.DataFrame: The prediction input dataframe for the cluster.
    """
    if new_week_data_file_path:
        # Load new data from file
        cluster_data = pd.read_csv(new_week_data_file_path)
        
        # TODO: Before cleaning, need to aggregate by 'Date-Hr' and 'Cluster'
        # Need to also create 'Count' and 'Date-Hr' columns
        
        
        # TODO: Implement more cleaning steps to get the data in right format
        # Need to drop a lot of columns
        
        cluster_data = clean(cluster_data)
    else:
        # Extract most recent week from the cluster's stored data
        cluster_data = cluster.data.copy()
        
    cluster_data["Date-Hr"] = pd.to_datetime(cluster.data["Date-Hr"])
    last_week_start = cluster.data["Date-Hr"].max() - pd.Timedelta(days=7)
    new_data = cluster.data[cluster.data["Date-Hr"] >= last_week_start].copy()
    
    return new_data


def create_new_prediction_df():
    """
    Creates an empty prediction DataFrame for the new week of data.
    Generates hourly timestamps for the next week.

    Parameters:
        cluster (Cluster): 
            The Cluster object containing historical data and lat_lng_dist.

    Returns:
        pd.DataFrame: The new prediction DataFrame.
    """

    # Generate timestamps for the next week by the hour
    future_dates = pd.date_range(start=pd.Timestamp.today().normalize(), periods=7 * 24, freq='h')
    future_df = pd.DataFrame({"Date-Hr": future_dates})

    # Pass DataFrame through clean() to get it in the right format
    future_df = clean(future_df)
    future_df["Count"] = np.nan

    return future_df
