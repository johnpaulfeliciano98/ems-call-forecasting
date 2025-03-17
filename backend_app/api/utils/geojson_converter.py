import pandas as pd

def predictions_to_json(df: pd.DataFrame) -> dict:
    """
    Prediction data to a structured GeoJSON format for visualization.

    Params:
        df: pandas.DataFrame - prediction data

    Returns:
        dict - GeoJSON formatted data
    """
    features = {}

    for index, row in df.iterrows():
        # Convert to Unix timestamp 
        timestamp = int(pd.Timestamp(year=int(row['Year']), 
                                    month=int(row['Month']), 
                                    day=int(row['Day'])).timestamp() * 1000)

        # Normalize call volume
        # We can use this if we want to scale the volume of calls instead of using the raw value
        # It basically scales the volume of calls to a range of 0-10
        # This is useful if we want to see the density of calls rather than the raw volume
    
        # max_calls = df['Count'].max() if 'Count' in df.columns and df['Count'].max() > 0 else 1
        # volume = row['Count'] / max_calls * 10 if 'Count' in row else 1
        volume = row['Count']

        # Construct feature object
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [row['Long'], row['Lat']]
            },
            "properties": {
                "time": timestamp,
                "volume": round(volume, 5),
                "cluster_id": row.get('Cluster', -1),
                "cluster_volume": round(row.get('Cluster_Count', -1), 5)
            }
        }
        features[index] = feature

    return {"features": features}


def boundaries_to_geojson(boundaries_dict):
    """
    Convert cluster boundary data to GeoJSON format.

    Params:
        boundaries_dict: dict - dictionary where key = cluster_id, value = list of boundary coordinates

    Returns:
        dict - GeoJSON formatted boundaries data
    """
    features = {}

    for cluster_id, boundary in boundaries_dict.items():
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",  
                "coordinates": [boundary] 
            },
            "properties": {
                "cluster_id": cluster_id, 
            }
        }
        features[cluster_id] = feature

    # Return GeoJSON format
    return {
        "type": "FeatureCollection",
        "features": features
    }
