import pandas as pd
import os
import json
import pickle
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .utils import geojson_converter
from .cluster_predictions import model

# ----------------------------------------------------------------------------------------------
# Global File Paths
# ----------------------------------------------------------------------------------------------
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "data.csv")
MODEL_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "model")
CLUSTER_PATH = os.path.join(MODEL_FOLDER, "clusters.pkl")
PREDICTIONS_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "predictions")
GEOJSON_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "geojson")


# ----------------------------------------------------------------------------------------------
# Heatmap API
# ----------------------------------------------------------------------------------------------
@api_view(['GET'])
def get_heatmap(request):
    """
    Retrieve heatmap data for a given time range with optional query parameters.

    Query Parameters:
        start_date: str (YYYY-MM-DD) - The beginning of the time range.
        end_date: str (YYYY-MM-DD) - The end of the time range (max 7 days difference).

    Returns:
        JSON response containing a single combined GeoJSON heatmap object.
    """
    # Get all prediction files
    prediction_files = []
    for file in os.listdir(PREDICTIONS_FOLDER):
        if file.startswith("cluster_") and file.endswith(".csv"):
            prediction_files.append(file)

    # If no prediction files exist, return error
    if not prediction_files:
        return Response({"error": "No prediction data found. Please run /predict first."}, status=404)

    # geojson requires a list/array for the features rather than a dict/obj
    combined_geojson = {"type": "FeatureCollection", "features": []}

    # Get query date parameters
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    json_index = 0

    # Loop through each prediction file
    for file in prediction_files:
        # Extract cluster ID from filename
        cluster_id = file.split("_")[1].split(".")[0]  
        file_path = os.path.join(PREDICTIONS_FOLDER, file)

        try:
            # Read cluster prediction data
            df = pd.read_csv(file_path)

            # Convert date columns to datetime if filtering is needed
            if start_date and end_date:
                try:
                    df["date"] = pd.to_datetime(df[["Year", "Month", "Day"]])
                    start_dt = pd.to_datetime(start_date)
                    end_dt = pd.to_datetime(end_date)

                    # Ensure the time range is valid (max 7 days)
                    if (end_dt - start_dt).days > 7 or (end_dt - start_dt).days < 0:
                        return Response({"error": "Time range is not at or within 7 day range."}, status=400)

                    # Filter data within the time range
                    df = df[(df["date"] >= start_dt) & (df["date"] <= end_dt)]

                except Exception as e:
                    return Response({"error": f"Invalid date format: {e}"}, status=400)

            # Convert DataFrame to GeoJSON and add "Cluster" property
            geojson_features = geojson_converter.predictions_to_json(df)["features"]
                
            # Append to combined GeoJSON
            for feature in geojson_features.values():
                # combined_geojson["features"][json_index] = feature
                # json_index += 1
                combined_geojson["features"].append(feature)

        except Exception as e:
            return Response({"error": f"Failed to process cluster {cluster_id}: {e}"}, status=500)

    return Response(combined_geojson, status=200)



@api_view(['GET'])
def get_boundaries(request):
    """
    Retrieve boundaries for each cluster.

    Returns:
        GeoJSON response containing cluster boundaries as a polygon feature type.
    """
    boundaries_path = os.path.join(MODEL_FOLDER, "boundaries.json")

    # Check if boundaries file exists
    if not os.path.exists(boundaries_path):
        return Response({"error": "Cluster boundaries not found"}, status=404)

    # Load boundaries JSON file
    try:
        with open(boundaries_path, "r") as f:
            boundaries = json.load(f)
    except Exception as e:
        return Response({"error": f"Failed to load boundaries: {e}"}, status=500)

    # Convert boundaries to GeoJSON
    geojson_boundaries = geojson_converter.boundaries_to_geojson(boundaries)
    return Response(geojson_boundaries, status=200)


# ----------------------------------------------------------------------------------------------
# Model Workflow API
# ----------------------------------------------------------------------------------------------
@api_view(['POST'])
def train_model(request):
    """
    Trigger workflow to retrain the model using all current data in backend_app/data/data.csv.

    Returns:
        JSON response indicating the success of the model training process.
    """
    try:
        # Ensure model and predictions directories exist
        os.makedirs(MODEL_FOLDER, exist_ok=True)
        os.makedirs(PREDICTIONS_FOLDER, exist_ok=True)

        # Check if the dataset exists
        if not os.path.exists(DATA_PATH):
            return Response({"error": "Training data file not found."}, status=404)

        # Load data
        try:
            input_df = pd.read_csv(DATA_PATH)
            if input_df.empty:
                return Response({"error": "Training data is empty."}, status=400)
        except Exception as e:
            return Response({"error": f"Error reading CSV: {e}"}, status=500)

        # Train the model
        try:
            clusters, boundaries = model.prepare_and_train_model(input_df)

            # Dump the trained model into a pickle file
            with open(CLUSTER_PATH, "wb") as f:
                pickle.dump(clusters, f)
            
            # Dump the boundaries into a JSON file
            with open(os.path.join(MODEL_FOLDER, "boundaries.json"), "w") as f:
                json.dump(boundaries, f)
        except Exception as e:
            return Response({"error": f"Model training failed: {e}"}, status=500)

        return Response({"message": "Model training completed successfully."}, status=200)

    except Exception as e:
        return Response({"error": f"An error occurred: {e}"}, status=500)


@api_view(['GET'])
def make_predictions(request):
    """
    Load the trained clusters and run predictions.

    Returns:
        JSON response indicating the success of the prediction process.
    """
    try:
        # Ensure model exists
        if not os.path.exists(CLUSTER_PATH):
            return Response({"error": "Trained model not found. Run training first."}, status=404)

        # Load trained clusters
        try:
            with open(CLUSTER_PATH, "rb") as f:
                clusters = pickle.load(f)
        except Exception as e:
            return Response({"error": f"Failed to load model: {e}"}, status=500)

        # Delete existing prediction files
        for file in os.listdir(PREDICTIONS_FOLDER):
            if file.startswith("cluster_") and file.endswith(".csv"):
                os.remove(os.path.join(PREDICTIONS_FOLDER, file))

        # Make predictions
        try:
            predictions_dict = model.predict_model(clusters)
        except Exception as e:
            return Response({"error": f"Prediction process failed: {e}"}, status=500)

        # Save predictions to CSV
        try:
            for cluster_id, df in predictions_dict.items():
                output_file = os.path.join(PREDICTIONS_FOLDER, f"cluster_{cluster_id}.csv")
                df.to_csv(output_file, index=False)

            return Response({"message": "Predictions completed and saved successfully."}, status=200)

        except Exception as e:
            return Response({"error": f"Failed to save predictions: {e}"}, status=500)

    except Exception as e:
        return Response({"error": f"An error occurred: {e}"}, status=500)
