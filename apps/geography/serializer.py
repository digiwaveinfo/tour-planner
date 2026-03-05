from rest_framework import serializers
from .models import Country,Region,CountryImage,RegionImage
from django.conf import settings
import os

class CountryImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CountryImage
        fields = ["id", "image"]

class CountrySerializer(serializers.ModelSerializer):
    images = serializers.ListField(child=serializers.ImageField(),write_only=True,required=False)
    country_images = CountryImageSerializer(many=True, read_only=True)

    class Meta:
        model = Country
        fields = "__all__"

    def create(self, validated_data):
        images = validated_data.pop("images", [])
        country = Country.objects.create(**validated_data)
        for image in images:
            CountryImage.objects.create(country=country,image=image)
        return country
    
    def update(self, instance, validated_data):
        images = validated_data.pop("images", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if images:
            for image in images:
                CountryImage.objects.create(country=instance, image=image)
        return instance

class RegionImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegionImage
        fields = ["id", "image"]

class RegionSerializer(serializers.ModelSerializer):
    images = serializers.ListField(child=serializers.ImageField(),write_only=True,required=False)
    region_images = RegionImageSerializer(many=True, read_only=True)
    country_name = serializers.CharField(source="country.name", read_only=True)

    class Meta:
        model = Region
        fields = "__all__"

    def create(self, validated_data):
        images = validated_data.pop("images", [])
        region = Region.objects.create(**validated_data)
        for image in images:
            RegionImage.objects.create(region=region,image=image)
        return region
    
    def update(self, instance, validated_data):
        images = validated_data.pop("images", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if images:
            for image in images:
                RegionImage.objects.create(region=instance, image=image)
        return instance