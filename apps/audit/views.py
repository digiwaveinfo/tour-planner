from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated
from .models import AuditLog
from .serializer import AuditLogSerializer

class AuditLogViewSet(ReadOnlyModelViewSet):

    queryset = AuditLog.objects.all().order_by("-created_at")
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()

        user = self.request.query_params.get("user")
        action = self.request.query_params.get("action")
        entity = self.request.query_params.get("entity_type")
        start = self.request.query_params.get("start")
        end = self.request.query_params.get("end")

        if user:
            qs = qs.filter(user_id=user)
        if action:
            qs = qs.filter(action__iexact=action)
        if entity:
            qs = qs.filter(entity_type__iexact=entity)
        if start and end:
            qs = qs.filter(created_at__range=[start, end])

        return qs