from django.http import JsonResponse
from rest_framework.views import APIView
from .models import Chemicals
from .serializers import ChemicalsSerializer
import requests


class ChemicalsListAPIView(APIView):
    """
    API view for retrieving a list of Chemicals based on CAS number.
    """
    def get(self, request):
        """
        Handle GET request to retrieve Chemicals based on CAS number.

        Args:
            request: The GET request object.

        Returns:
            A JSON response containing the Chemicals data or an error message.
        """
        numcas = request.query_params.get("numcas")

        if not numcas:
            return JsonResponse({"error": "No CAS number provided."}, status=400)

        queryset = Chemicals.objects.filter(numcas=numcas)

        if not queryset:
            return JsonResponse(
                {"error": "No data found for the given CAS number."},
                status=404
            )

        data = ChemicalsSerializer(queryset, many=True).data
        return JsonResponse({"data": data})


class AveragePriceView(APIView):
    """
    API view for calculating the average price of Chemicals based on CAS number.
    """
    def get(self, request):
        """
        Handle GET request to calculate the average price of Chemicals based on CAS number.

        Args:
            request: The GET request object.
            cas_number (str): The CAS number of the Chemicals.

        Returns:
            A JSON response containing the average prices.
        """

        numcas = request.query_params.get("numcas")

        if not numcas:
            return JsonResponse({"error": "No CAS number provided."}, status=400)

        chemicals = Chemicals.objects.filter(numcas=numcas)

        if not chemicals:
            return JsonResponse(
                {"error": "No data found for the given CAS number."}, status=404
            )

        total_price_g = 0
        total_quantity_g = 0
        total_price_ml = 0
        total_quantity_ml = 0

        for chemical in chemicals:
            qt_list = chemical.qt_list
            unit_list = chemical.unit_list
            price_pack_list = chemical.price_pack_list

            if not qt_list or not unit_list or not price_pack_list:
                continue

            for qt, unit, price in zip(qt_list, unit_list, price_pack_list):
                if unit == "mg":
                    qt = qt / 1000
                    unit = "g"
                elif unit == "kg":
                    qt = qt * 1000
                    unit = "g"
                elif unit == "ml":
                    qt = qt
                    unit = "ml"
                elif unit == "l":
                    qt = qt * 1000
                    unit = "ml"

                if unit == "g":
                    total_price_g += float(price)
                    total_quantity_g += float(qt)
                elif unit == "ml":
                    total_price_ml += float(price)
                    total_quantity_ml += float(qt)

        if total_quantity_g == 0 and total_quantity_ml == 0:
            return JsonResponse(
                {"error": "No valid data found for the given CAS number."}, status=404
            )

        average_price_g = (
            total_price_g / total_quantity_g if total_quantity_g != 0 else 0
        )
        average_price_ml = (
            total_price_ml / total_quantity_ml if total_quantity_ml != 0 else 0
        )

        return JsonResponse(
            {"average_price_g": average_price_g, "average_price_ml": average_price_ml}
        )


class CompanySpiderAPIView(APIView):
    """
    API view for launching a spider to collect products for a specific company.
    """
    def post(self, request):
        """
        Handle POST request to launch a spider for a specific company and collect products.

        Args:
            request: The POST request object.

        Returns:
            A JSON response indicating the success or failure of the spider launch.
        """
        company_name = request.query_params.get("company_name")

        if not company_name:
            return JsonResponse({"error": "No company name provided."}, status=400)

        company_names = {
            "AstaTech": "astatechinc_com",
        }

        Chemicals.objects.filter(company_name=company_name).delete()

        spider_url = "http://localhost:6800/schedule.json"
        data = {
            "project": "chemicals",
            "spider": company_names[company_name],
        }
        response = requests.post(spider_url, data=data)

        if response.status_code == 200:
            return JsonResponse(
                {
                    "success": "Spider for company {} has been launched.".format(
                        company_name
                    )
                }
            )
        else:
            return JsonResponse({"error": "Failed to launch spider."}, status=500)
