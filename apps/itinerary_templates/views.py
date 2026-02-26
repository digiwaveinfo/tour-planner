from rest_framework.viewsets import ModelViewSet
from .models import *
from .serializer import *
from rest_framework.decorators import action
from rest_framework.response import Response
from common.permissions import DayTourPermission

class ItineraryTemplateViewSet(ModelViewSet):
    queryset = ItineraryTemplate.objects.all()
    serializer_class = ItineraryTemplateSerializer
    permission_classes = [DayTourPermission]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


    @action(detail=True, methods=["post"])
    def add_day(self, request, pk=None):
        template = self.get_object()
        serializer = ItineraryTemplateDaySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(template=template)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def attach_inclusion(self, request, pk=None):
        template = self.get_object()
        incl_id = request.data.get("incl_excl")
        obj, created = ItineraryTemplateInclExcl.objects.get_or_create(
            template=template,incl_excl_id=incl_id)

        return Response({
            "attached": created
        })    
    
    @action(detail=True, methods=["post"])
    def remove_inclusion(self, request, pk=None):
        template = self.get_object()
        incl_id = request.data.get("incl_excl")
        deleted, _ = ItineraryTemplateInclExcl.objects.filter(
            template=template,incl_excl_id=incl_id).delete()

        return Response({
            "deleted": deleted
        })

class ItineraryTemplateDay(ModelViewSet):
    queryset = ItineraryTemplateDay.objects.all()
    serializer_class = ItineraryTemplateDaySerializer
    permission_classes = [DayTourPermission]

class ItineraryTemplateInclExclViewSet(ModelViewSet):
    queryset = ItineraryTemplateInclExcl.objects.all()
    serializer_class = ItineraryTemplateInclExclSerializer
    permission_classes = [DayTourPermission]