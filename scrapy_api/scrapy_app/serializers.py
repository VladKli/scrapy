from rest_framework import serializers
from .models import Chemicals


class ChemicalsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chemicals
        fields = '__all__'


class AvgChemicalsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chemicals
        fields = '__all__'