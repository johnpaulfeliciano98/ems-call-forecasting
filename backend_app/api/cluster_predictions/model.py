import pandas as pd
from backend_app.api.cluster_predictions.preprocess import data_import, clean, k_means
from backend_app.api.cluster_predictions.cluster import Cluster
from backend_app.api.cluster_predictions.create_prediction_df import create_prediction_df

from scipy.spatial import ConvexHull


# Globals
LAT, LNG = 35.227085, -80.843124    # Charlotte, NC coordinates


def coord_dist(df):
    """
    Create latitude/longitude distribution from historical data
    Round coordinates to 3 decimal places reduce granularity

    Params:
        df: pandas.DataFrame - dataframe with historical coordinate data

    Returns:
        df: pandas.DataFrame - same dataframe as params but with additional 'Distribution' column
    """
    clusters = df['Cluster'].unique()   # Get unique clusters in df

    # Round coordinate to 2 decimal places
    df['Lat'] = round(df['Latitude'], 2)
    df['Long'] = round(df['Longitude'], 2)

    # Aggregate by coordinate and cluster
    df = df.groupby(['Lat', 'Long', 'Cluster']).size().reset_index(name='Count')

    # Get total calls per cluster
    cluster_totals = df.groupby("Cluster")["Count"].sum()

    # Calculate distribution for each coordinate by iterating through each row
    df["Distribution"] = 0.0
    for i in range(len(df)):
        cluster_id = df.loc[i, "Cluster"]
        total_count = cluster_totals.get(cluster_id, 0) 

        # Calculate distribution and assign to 'Distribution' column
        if total_count > 0:
            df.loc[i, "Distribution"] = df.loc[i, "Count"] / total_count
        else:
            df.loc[i, "Distribution"] = 0

    return df


def get_boundaries(df):
    """
    Given coordinates, determine the boundaries of the coordinates using Convex Hull for the purpose of creating zones on heatmap

    Params:
        df: pandas.DataFrame - coordinates and their respective cluster number

    Returns:
        boundary_dict: dictionary - key = cluster number, value = boundary of cluster
    """
    boundary_dict = {}
    for cluster_id, group in df.groupby('Cluster'):
        coords = group[['Lat', 'Long']].values
        hull = ConvexHull(coords)
        boundary = coords[hull.vertices].tolist()
        boundary_dict[cluster_id] = boundary

    return boundary_dict


def create_models(cluster_list):
    """
    Create models and trains for each cluster. Creates prediction dataframes
    for each cluster.

    Params:
        cluster_list: list - list of Cluster objects

    Returns:
        prediction_df_list: list - list of prediction dataframes for each cluster
    """
    for cluster in cluster_list:
        cluster.train_test()    # Train/test split
        cluster.create_model()  # Create model
    return


def create_prediction_dataframes(cluster_list):
    """
    Create prediction dataframes for each cluster.

    Params:
        cluster_list: list - list of Cluster objects

    Returns:
        prediction_df_list: list - list of empty prediction dataframes for each cluster
    """
    prediction_df_list = []

    for cluster in cluster_list:
        prediction_df = create_prediction_df(cluster)
        prediction_df_list.append(prediction_df)

    return prediction_df_list


def make_predictions(prediction_dfs, clusters):
    """
    Makes predictions on each cluster model.
    
    Params:
        predictions_dfs: pandas.DataFrames - list of empty prediction dataframes for each cluster
        clusters: Cluster - list of all clusters

    Returns:
        final_predictions: List - List of prediction dataframes from each cluster
    """
    final_predictions = {}
    for cluster, df_pred in zip(clusters, prediction_dfs):
        if cluster.model is None:
            raise ValueError(f"Model for cluster {cluster.id} has not been trained.")

        # Ensure df_pred has the correct columns
        df_pred = df_pred[cluster.X_train.columns].copy()

        # Convert to NumPy for predictions
        df_pred_array = df_pred.to_numpy()

        # Make predictions
        predictions = cluster.model.predict(df_pred_array)
        df_pred["Count"] = predictions
        
        final_predictions[cluster.id] = df_pred
    
    return final_predictions


def aggregate_daily_data(predictions):
    """
    Aggregates predictions into daily data.

    Params:
        predictions: dict - Dictionary of prediction dataframes assigned to a specific cluster id

    Returns:
        daily_predictions: dict - Dictionary where key = cluster ID, value = daily aggregated predictions DataFrame.
    """
    daily_predictions = {}

    for cluster_id, pred_df in predictions.items():
        # Aggregate predictions to daily totals
        # Only groups columns specified in .agg()
        daily_df = pred_df.groupby(["Year", "Month", "Day"], as_index=False).agg({
            "Count": "sum",  # Sum up predicted calls per day
            "is_holiday": "max",
            "is_weekend": "max"
        })

         # Store results in dictionary
        daily_predictions[cluster_id] = daily_df 

    return daily_predictions


def assign_call_distribution(daily_predictions, clusters):
    """
    Distributes daily call predictions back to each lat/long coordinate based on historical distribution.

    Params:
        daily_predictions: dict - cluster_id with daily aggregated DataFrame with total predicted calls per day
        clusters: list - List of Cluster objects, each holding lat_lng_dist.

    Returns:
        distributed_predictions: dict - cluster_id with DataFrame with lat/lng and distributed counts
    """
    distributed_predictions = {}

    for cluster in clusters:
        cluster_id = cluster.id
        lat_lng_dist = cluster.lat_lng_dist.copy()
        
        dist_sum = lat_lng_dist["Distribution"].sum()

        if cluster_id not in daily_predictions:
            continue 

        # Get the prediction DataFrame for this cluster
        daily_df = daily_predictions[cluster_id].copy()

        # Rename "Count" to "Cluster_Count" to store total calls per day
        daily_df.rename(columns={"Count": "Cluster_Count"}, inplace=True)

        # Get lat/lng distribution for this cluster
        lat_lng_dist = cluster.lat_lng_dist.copy()

        # Merge daily predictions with lat/lng distribution
        # Uses cross join to apply distribution to all dates
        daily_df["key"] = 1 
        lat_lng_dist["key"] = 1
        distributed_df = pd.merge(daily_df, lat_lng_dist, on="key").drop(columns=["key"])

        # Assign the distributed count as new Count column
        distributed_df["Count"] = distributed_df["Cluster_Count"] * distributed_df["Distribution"]

        # Store in dictionary
        distributed_predictions[cluster_id] = distributed_df

    return distributed_predictions


# ----------------------------------------------------------------------------------------------
# Main Model Workflow
# ----------------------------------------------------------------------------------------------
def prepare_and_train_model(data):
    """
    Prepare data and train model. Saves each model to pickle file.
    Saves boundary data to JSON file.
    Saves cluster data to JSON file.

    Parameters:
        data: Pandas dataframe
    Returns:
        clusters: List of Cluster objects
    """
    # Prepares the dataframe for clustering
    df = data_import(data)

    # Create clusters
    cluster_df = k_means(df, 5)
    lat_lng_dist = cluster_df.copy()    # To determine coordinate distribution for each cluster

    # Group by Date-Hr and Cluster
    cluster_df['Dispatched'] = pd.to_datetime(cluster_df['Dispatched'])
    cluster_df['Date-Hr'] = cluster_df['Dispatched'].dt.strftime("%Y-%m-%d %H")
    cluster_count = cluster_df.groupby(['Date-Hr', 'Cluster']).size().reset_index(name='Count')

    # Store cluster dataframes in dictionary
    df_dict = {key: value for key, value in cluster_count.groupby('Cluster')}

    # Coordinate distribution
    lat_lng_dist = coord_dist(lat_lng_dist)
    
    # Get boundaries of each cluster
    boundary_dict = get_boundaries(lat_lng_dist)

    # Create cluster objects
    clusters = []
    for cluster_id, cluster_data in df_dict.items():
        cluster_data = clean(cluster_data)
        cluster = Cluster(
            cluster_id,
            cluster_data,
            lat_lng_dist[lat_lng_dist['Cluster'] == cluster_id],
            boundary_dict[cluster_id]
        )
        clusters.append(cluster)
    
    # Create models and train models
    print("Creating models...\n\n")
    create_models(clusters)
       
    return clusters, boundary_dict


def predict_model(clusters):
    """
    Makes predictions on each cluster model.
    
    Params:
        predictions_dfs: pandas.DataFrames - list of empty prediction dataframes for each cluster
        
    """
    # Make prediction dataframes for each cluster
    prediction_df_list = create_prediction_dataframes(clusters)

    # Make predictions for each cluster into a dictionary.
    print("Making predictions...\n\n")
    final_predictions_dict = make_predictions(prediction_df_list, clusters)

    # Aggregate data into daily data into a dictionary.
    print("Aggregating daily data...\n\n")
    agg_predictions_dict = aggregate_daily_data(final_predictions_dict)

    # Assign call distribution to each lon/lat coordinate in each cluster
    print("Assigning call distribution...\n\n")
    distributed_predictions_dict = assign_call_distribution(agg_predictions_dict, clusters)

    return distributed_predictions_dict


# ----------------------------------------------------------------------------------------------
# Test the model workflow
# ----------------------------------------------------------------------------------------------
import os
import pickle

if __name__ == "__main__":
    # Define file paths
    data_path = "backend_app/data/data.csv"
    model_folder = "backend_app/data/model"
    cluster_path = os.path.join(model_folder, "clusters.pkl")

    # Ensure model folder exists
    os.makedirs(model_folder, exist_ok=True)

    # Load data
    data = pd.read_csv(data_path)

    # Train models and save clusters
    clusters, boundaries = prepare_and_train_model(data)

    # Save clusters using pickle
    with open(cluster_path, "wb") as f:
        pickle.dump(clusters, f)

    # Load clusters from pickle
    with open(cluster_path, "rb") as f:
        clusters = pickle.load(f)

    # Run predictions
    distributed_predictions_dict = predict_model(clusters)

    # Save predictions to CSV files
    output_folder = "backend_app/data/predictions"
    os.makedirs(output_folder, exist_ok=True)

    for cluster_id, df in distributed_predictions_dict.items():
        output_file = os.path.join(output_folder, f"cluster_{cluster_id}.csv")
        df.to_csv(output_file, index=False)
        print(f"Saved predictions for cluster {cluster_id} to {output_file}")
