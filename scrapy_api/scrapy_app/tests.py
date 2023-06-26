from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from .models import Chemicals


class ChemicalsListAPIViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("chemicals-list")
        self.numcas = "12345"


        Chemicals.objects.create(
            availability=True,
            company_name="Company A",
            product_url="https://example.com/productA",
            numcas="12345",
            name="Chemical A",
            qt_list=[1.0, 2.0, 3.0],
            unit_list=["g", "kg", "mg"],
            currency_list=["USD", "EUR", "GBP"],
            price_pack_list=["10", "20", "15"],
        )

    def test_get_chemicals_with_valid_numcas(self):
        response = self.client.get(self.url, {"numcas": self.numcas})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["data"][0]["name"], "Chemical A")
        self.assertEqual(response.json()["data"][0]["numcas"], self.numcas)

    def test_get_chemicals_with_invalid_numcas(self):
        response = self.client.get(self.url, {"numcas": "00000"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["error"], "No data found for the given CAS number.")

    def test_get_chemicals_without_numcas(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["error"], "No CAS number provided.")


class AveragePriceViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("average-price")
        self.numcas = "12345"

        # Create some sample Chemicals objects
        Chemicals.objects.create(
            availability=True,
            company_name="Company A",
            product_url="https://example.com/productA",
            numcas=self.numcas,
            name="Chemical A",
            qt_list=[1.0, 2.0, 3.0],
            unit_list=["g", "g", "mg"],
            currency_list=["USD", "EUR", "GBP"],
            price_pack_list=["100", "200", "300"],
        )

    def test_get_average_price_with_valid_numcas(self):
        response = self.client.get(self.url, {"numcas": self.numcas})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(int(response.json()["average_price_g"]), 199.0)
        self.assertEqual(response.json()["average_price_ml"], 0.0)

    def test_get_average_price_with_invalid_numcas(self):
        response = self.client.get(self.url, {"numcas": "00000"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["error"], "No data found for the given CAS number.")

    def test_get_average_price_without_numcas(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["error"], "No CAS number provided.")
