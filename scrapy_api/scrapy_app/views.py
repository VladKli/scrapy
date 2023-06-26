from django.http import JsonResponse
from rest_framework.views import APIView
from .models import Chemicals
from .serializers import ChemicalsSerializer
import requests


class ChemicalsListAPIView(APIView):
    def get(self, request):
        numcas = request.query_params.get('numcas')

        if not numcas:
            return JsonResponse({'error': 'No CAS number provided.'}, status=400)

        queryset = Chemicals.objects.filter(numcas=numcas)

        if not queryset:
            return JsonResponse({'error': 'No data found for the given CAS number.'}, status=404)

        return JsonResponse({'data': ChemicalsSerializer(queryset, many=True).data})


class AveragePriceView(APIView):
    def get(self, request, cas_number):
        chemicals = Chemicals.objects.filter(numcas=cas_number)

        if not chemicals:
            return JsonResponse({'error': 'No data found for the given CAS number.'}, status=404)

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
                if unit == 'mg':
                    qt = qt / 1000
                    unit = 'g'
                elif unit == 'kg':
                    qt = qt * 1000
                    unit = 'g'
                elif unit == 'ml':
                    qt = qt
                    unit = 'ml'
                elif unit == 'l':
                    qt = qt * 1000
                    unit = 'ml'

                if unit == 'g':
                    total_price_g += float(price)
                    total_quantity_g += float(qt)
                elif unit == 'ml':
                    total_price_ml += float(price)
                    total_quantity_ml += float(qt)

        if total_quantity_g == 0 and total_quantity_ml == 0:
            return JsonResponse({'error': 'No valid data found for the given CAS number.'}, status=404)

        average_price_g = total_price_g / total_quantity_g if total_quantity_g != 0 else 0
        average_price_ml = total_price_ml / total_quantity_ml if total_quantity_ml != 0 else 0

        return JsonResponse({'average_price_g': average_price_g, 'average_price_ml': average_price_ml})


class CompanySpiderAPIView(APIView):
    def post(self, request):
        company_name = request.query_params.get('company_name')

        if not company_name:
            return JsonResponse({'error': 'No company name provided.'}, status=400)

        company_names = {
            'AstaTech': 'astatechinc_com',
        }

        # Удаление существующих продуктов для данной компании
        Chemicals.objects.filter(company_name=company_name).delete()

        # Запуск спайдера для сбора продуктов
        spider_url = 'http://localhost:6800/schedule.json'
        data = {
            'project': 'chemicals',
            'spider': company_names[company_name],
        }
        response = requests.post(spider_url, data=data)

        if response.status_code == 200:
            return JsonResponse({'success': 'Spider for company {} has been launched.'.format(company_name)})
        else:
            return JsonResponse({'error': 'Failed to launch spider.'}, status=500)
