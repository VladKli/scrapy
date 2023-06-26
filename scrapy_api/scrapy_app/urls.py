from django.urls import path
from scrapy_app import views

urlpatterns = [
    path("", views.ChemicalsListAPIView.as_view(), name='chemicals-list'),
    path("avg/", views.AveragePriceView.as_view(), name='average-price'),
    path("run/", views.CompanySpiderAPIView.as_view(), name='run-campaign'),
]
