# Table of Contents
- [Project Overview](#project-overview)
- [Tech Stack](#tech-stack)
- [Setup Instructions](#setup-instructions)
- [Additional Model Research](#additional-model-research)
- [Contributors](#contributors)

## Project Overview
Emergency call volumes vary based on time and location. 
This project currently features: 
- A forecast for 911 EMS call volumes using with XGBoost, a regressive gradient boosting forecasting model.
- A prediction forcast for the next 7 days.
- Clustering of predictions into 5 distinct cluster zones. Each cluster of data points is used to train a unique prediction model.
- Data preprocessing and feature engineering for variables such as ```day_of_week, is_holiday, and is_weekend```.
- Interactive Mapbox heatmap for each daily prediction. 

## Tech Stack
- **Backend**
   - Python
   - Django
   - XGBoost
   - K-Means Clustering
   - Pandas
   - Numpy
     
- **Frontend**
   - Vite
   - React
   - Vitest
   - Typescript
   - prettier
   - SWC
   - ESLint
   - Mapbox
     
- **Data Processing**
   - Pandas
   - GeoJSON
     
- **Version Control**
   - Git
   - GitHub
 
## Setup Instructions  
### Frontend Setup Instructions using CLI
To develop the application or run the app in 'dev' mode:

1. ```npm install```
2. ```npm run test```

After running the 'test' script, the App test should pass, along with any additional tests created during development.

This repository uses a Test Driven Development approach.

3. Add .env file and update the missing credentials.
   The following will be needed:

   - ```VITE_MAPBOX_TOKEN```

4. ```npm run dev```

### Backend Setup Instructions using CLI
**Notes: The following tutorial is for Windows machines. Some commands may differ depending on the OS. (Ex: macOS may need to use pip3 instead of pip)**

1. Open Command Prompt in the 911-prediction directory.
2. Clone the Repository:
   - ```git clone https://github.com/Levrum-Capstones/911-prediction.git```
3. Navigate to the Project Directory:
   - ```cd 911-prediction```
4. Create a Virtual Environment:
   - ```python -m venv venv```
5. Activate the Virtual Environment:
   - ```venv\Scripts\activate```
6. Verify Your Python Version (should be at least 3.10):
   - ```python --version```
   (Alternatively, check the pyenv.cfg file in the virtual environment folder.)
7. Install Dependencies:
   - ```pip install -r requirements.txt```
8. Place Your Call Data:
   - Copy your call data file into the directory:
    - ```911-prediction/backend_app/data```
   - Ensure that the file is named ```data.csv```
9. Apply Database Migrations:
   - ```python manage.py migrate```
10. Start the Django Development Server:
    - ```python manage.py runserver```

The server should now be running at http://localhost:8000/

### Backend Setup Instructions using Conda Package Manger (recommended for macOS)
1. Install the miniconda package manager
   - Docs: https://www.anaconda.com/docs/getting-started/miniconda/install
2. Navigate to the project folder's directory in the terminal
3. Within the folder, run the following in the terminal to create a virtual environment with the needed dependencies:
   - ```conda create --name ./venv --file spec-file.txt```
4. Then, to activate the virtual environment, run:
   - ```conda activate ./venv```
5. You can view a list of your installed dependencies and versions by running:
   - ```conda list```
8. Place Your Call Data:
   - Copy your call data file into the directory:
    - ```911-prediction/backend_app/data```
   - Ensure that the file is named ```data.csv```
9. Apply Database Migrations:
   - ```python manage.py migrate```
10. Start the Django Development Server:
    - ```python manage.py runserver```
    
The server should now be running at http://localhost:8000/

## Additional Model Research
Additional research into the following algorithms are present in the ```/model-research``` folder:
- LSTM (with and without H3)
- Exponential Smoothing (Holt Winters)
- LSTM-Exponential Smoothing Hybrid
- XGBoost with H3
- Recurrent GNN

## Contributors
- [@evanjliu](https://github.com/evanjliu)
- [@annaleexjohnson](https://github.com/annaleexjohnson)
- [@Gomurmamma](https://github.com/Gomurmamma)
- [@ryjn](https://github.com/ryjn)
- [@johnpaulfeliciano98](https://github.com/johnpaulfeliciano98)
