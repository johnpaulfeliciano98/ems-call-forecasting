from django.urls import path
from .views import (
    get_heatmap, train_model, get_boundaries, make_predictions
)

urlpatterns = [
    # API endpoints in use
    path('heatmap/', get_heatmap, name='get_heatmap'),
    path('train/', train_model, name='train_model'),
    path('boundaries/', get_boundaries, name='get_boundaries'),
    path('predict/', make_predictions, name='make_predictions')
]