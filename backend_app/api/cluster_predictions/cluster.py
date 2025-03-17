import xgboost as xgb
from sklearn.model_selection import train_test_split


class Cluster:
    """
    A class representing a cluster/zone of historical coordinates.

    Attributes:
        id (int): Cluster identification.
        data (pandas.DataFrame): Historical data for the specified cluster.
        lat_lng_dist (pandas.DataFrame): Coordinates present in historical
        data for the cluster.
            - Lat/Long: Coordinates.
            - Cluster: Cluster ID.
            - Count: Sum of counts at the coordinate.
            - Distribution: Distribution of historical call 
              volume.
        boundary (list): Set of coordinates defining the cluster boundary.
        X_train (pandas.DataFrame): Training features data.
        X_test (pandas.DataFrame): Testing features data.
        y_train (pandas.Series): Training targets data.
        y_test (pandas.Series): Testing targets data.
        model (xgb.XGBRegressor): Trained model for the cluster.
    """

    def __init__(
            self,
            id,
            data,
            lat_lng_dist,
            boundary,
            X_train=None,
            X_test=None,
            y_train=None,
            y_test=None,
            model=None
    ):
        self.id = id
        self.data = data
        self.lat_lng_dist = lat_lng_dist
        self.boundary = boundary
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test
        self.model = model

    def train_test(self):
        """
        Splits the cluster's data into training and testing datasets.

        Returns:
            tuple: (X_train, X_test, y_train, y_test)
        """
        if not {'Date-Hr', 'Count'}.issubset(self.data.columns):
            raise ValueError(
                "Data must contain 'Date-Hr' and 'Count' columns.")

        X = self.data.drop(columns=['Date-Hr', 'Count'])
        y = self.data['Count']

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, random_state=104, test_size=0.2, shuffle=True)

        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test

        return X_train, X_test, y_train, y_test

    def create_model(self):
        """
        Creates and trains an XGBoost regressor using the training data.

        Returns:
            xgb.XGBRegressor: The trained model.
        """
        if self.X_train is None or self.y_train is None:
            raise ValueError(
                "Training data not found. Please run train_test() first.")

        model = xgb.XGBRegressor(
            objective='reg:squarederror',
            n_estimators=100,
            learning_rate=0.1,
            max_depth=6,
            random_state=42
        )
        model.fit(self.X_train, self.y_train)
        self.model = model
        return model

    def make_predict(self, input):
        """
        Makes predictions using the trained model.

        Parameters:
            input (pandas.DataFrame): Input features for prediction.

        Returns:
            numpy.ndarray: Predicted values.
        """
        if self.model is None:
            raise ValueError(
                "Model has not been trained. Call create_model() first.")
        return self.model.predict(input)
