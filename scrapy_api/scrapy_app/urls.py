from django.urls import path
from scrapy_app import views

urlpatterns = [
    path("", views.ChemicalsListAPIView.as_view()),
    path("avg/", views.AveragePriceView.as_view()),
    path("run/", views.CompanySpiderAPIView.as_view()),
]
