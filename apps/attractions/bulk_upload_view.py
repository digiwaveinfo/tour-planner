import pandas as pd
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Attraction
from apps.geography.models import Region

class AttractionBulkUpload(APIView):
    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "File required"}, status=400)
        df = pd.read_excel(file) if file.name.endswith("xlsx") else pd.read_csv(file)
        created = 0
        for _, row in df.iterrows():
            region = Region.objects.filter(id=row.get("region")).first()
            if not region:
                continue
            Attraction.objects.create(
                region=region,
                reference_no=row.get("reference_no"),
                name=row.get("name"),
                latitude=row.get("latitude"),
                longitude=row.get("longitude"),
                is_active=True
            )
            created += 1
        return Response({
            "message": f"{created} attractions uploaded"
        })