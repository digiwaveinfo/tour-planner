from rest_framework import serializers
from .models import Country,Region
from django.conf import settings
import os

class CountrySerializer(serializers.ModelSerializer):
    images = serializers.ListField(child=serializers.ImageField(),write_only=True,required=False)
    image_urls = serializers.SerializerMethodField()

    class Meta:
        model = Country
        fields = "__all__"
        extra_fields = ["image_urls"]

    def get_image_urls(self, obj):
        request = self.context.get("request")
        if not obj.images:
            return []

        return [
            request.build_absolute_uri(settings.MEDIA_URL + img)
            for img in obj.images
        ]

    def create(self, validated_data):
        images = validated_data.pop("images", [])
        country = Country.objects.create(**validated_data)

        image_paths = []
        for image in images:
            path = f"country/{image.name}"
            full_path = os.path.join(settings.MEDIA_ROOT, path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "wb+") as f:
                for chunk in image.chunks():
                    f.write(chunk)
            image_paths.append(path)
        country.images = image_paths
        country.save()
        return country

class RegionSerializer(serializers.ModelSerializer):
    images = serializers.ListField(child=serializers.ImageField(),write_only=True,required=False)
    country_name = serializers.CharField(source="country.name", read_only=True)
    image_urls = serializers.SerializerMethodField()

    class Meta:
        model = Region
        fields = "__all__"
        extra_fields = ["image_urls"]

    def get_image_urls(self, obj):
        request = self.context.get("request")
        if not obj.images:
            return []

        return [
            request.build_absolute_uri(settings.MEDIA_URL + img)
            for img in obj.images
        ]

    def create(self, validated_data):
        images = validated_data.pop("images", [])
        region = Region.objects.create(**validated_data)
        image_paths = []
        for image in images:
            path = f"region/{image.name}"
            full_path = os.path.join(settings.MEDIA_ROOT, path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "wb+") as f:
                for chunk in image.chunks():
                    f.write(chunk)
            image_paths.append(path)
        region.images = image_paths
        region.save()
        return region