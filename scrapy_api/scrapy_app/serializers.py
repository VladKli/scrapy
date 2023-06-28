from rest_framework import serializers
from .models import Chemicals


class ChemicalsSerializer(serializers.ModelSerializer):
    """
    Serializer for the Chemicals model.
    """

    class Meta:
        """
        Meta class for specifying serializer options.
        """

        model = Chemicals
        fields = "__all__"
