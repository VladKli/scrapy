from django.http import JsonResponse
from rest_framework.views import APIView
from .models import Chemicals
from .serializers import ChemicalsSerializer
import requests
from django.db.models import Case, FloatField, F, Value, When
from django.db.models.functions import Cast, Coalesce
from django.db.models.aggregates import Avg

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
                {"error": "No data found for the given CAS number."}, status=404
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

        average_price_per_gram = (
            chemicals
            .annotate(
                price_per_gram=Case(
                    When(
                        unit_list__0='mg',
                        then=Coalesce(Cast(F('price_pack_list__0'), FloatField()), Value(0.0)) / (
                                    Coalesce(Cast(F('qt_list__0'), FloatField()), Value(1.0)) * 0.001)
                    ),
                    When(
                        unit_list__0='kg',
                        then=Coalesce(Cast(F('price_pack_list__0'), FloatField()), Value(0.0)) / (
                                    Coalesce(Cast(F('qt_list__0'), FloatField()), Value(1.0)) * 1000)
                    ),
                    default=Coalesce(Cast(F('price_pack_list__0'), FloatField()), Value(0.0)) / Coalesce(
                        Cast(F('qt_list__0'), FloatField()), Value(1.0)),
                    output_field=FloatField()
                )
            )
            .filter(currency_list__0='$')
            .aggregate(average_price=Avg('price_per_gram'))
        )

        average_price = average_price_per_gram['average_price']

        return JsonResponse(
            {"average_price_g": average_price}
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
