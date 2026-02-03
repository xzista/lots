from django.urls import path
from .views import LotListView, LotDetailView

app_name = "lots"

urlpatterns = [
    path("", LotListView.as_view(), name="lot_list"),
    path("<int:pk>/", LotDetailView.as_view(), name="lot_detail"),
]