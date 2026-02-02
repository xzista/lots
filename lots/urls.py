from django.urls import path
from .views import LotListView, LotDetailView, tag_suggestions

app_name = "lots"

urlpatterns = [
    path("", LotListView.as_view(), name="lot_list"),
    path("<int:pk>/", LotDetailView.as_view(), name="lot_detail"),
    path("tag-suggestions/", tag_suggestions, name="tag_suggestions"),
]