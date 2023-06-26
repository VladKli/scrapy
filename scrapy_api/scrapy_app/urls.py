from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from scrapy_app import views

urlpatterns = [
    path("", views.ChemicalsListAPIView.as_view()),
    path("avg/<str:cas_number>/", views.AveragePriceView.as_view()),
    path("run/", views.CompanySpiderAPIView.as_view()),
]
