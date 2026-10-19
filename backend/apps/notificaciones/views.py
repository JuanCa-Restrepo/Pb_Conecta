from rest_framework import generics, serializers
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from .models import Notificacion


class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
        fields = ["id", "tipo", "titulo", "mensaje", "url_destino", "leida", "creado_en"]


class NotificacionesView(generics.ListAPIView):
    serializer_class = NotificacionSerializer

    def get_queryset(self):
        return Notificacion.objects.filter(usuario=self.request.user)


@api_view(["GET"])
def conteo_no_leidas(request):
    return Response({"no_leidas": Notificacion.objects.filter(usuario=request.user, leida=False).count()})


@api_view(["POST"])
def marcar_leida(request, pk):
    notificacion = get_object_or_404(Notificacion, pk=pk, usuario=request.user)
    notificacion.leida = True
    notificacion.save(update_fields=["leida"])
    return Response(NotificacionSerializer(notificacion).data)


@api_view(["POST"])
def marcar_todas_leidas(request):
    total = Notificacion.objects.filter(usuario=request.user, leida=False).update(leida=True)
    return Response({"marcadas": total})
