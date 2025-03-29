from django.urls import path
from .views import (
    PlotViewSet,
    LotViewSet,
    SoilTypeListCreateView,
    SoilTypeRetrieveUpdateDestroyView,
)

urlpatterns = [
    # Rutas para predios
    path(
        "plots/register",
        PlotViewSet.as_view({"post": "create"}),
        name="registrar-predio",
    ),
    path("plots/list", PlotViewSet.as_view({"get": "list"}), name="listar-predios"),
    path(
        "plots/<str:id_plot>",
        PlotViewSet.as_view({"get": "retrieve"}),
        name="detalle-predio",
    ),
    path(
        "plots/<str:id_plot>/update",
        PlotViewSet.as_view({"put": "update", "patch": "partial_update"}),
        name="actualizar-predio",
    ),
    path(
        "plots/<str:id_plot>/inhabilitar",
        PlotViewSet.as_view({"post": "inactive"}),
        name="inhabilitar-predio",
    ),
    path(
        "plots/<str:id_plot>/habilitar",
        PlotViewSet.as_view({"post": "active"}),
        name="habilitar-predio",
    ),
    # Rutas para lotes
    path("lots/register", LotViewSet.as_view({"post": "create"}), name="lot-create"),
    path("lots/list", LotViewSet.as_view({"get": "list"}), name="lot-list"),
    path(
        "lots/<str:id_lot>",
        LotViewSet.as_view({"get": "retrieve"}),
        name="detalle-lote",
    ),
    path(
        "lots/<str:id_lot>/update",
        LotViewSet.as_view({"put": "update", "patch": "partial_update"}),
        name="lot-update",
    ),
    path(
        "lots/<str:id_lot>/desactivate",
        LotViewSet.as_view({"post": "inactive"}),
        name="deactivate-lot",
    ),
    path(
        "lots/<str:id_lot>/activate",
        LotViewSet.as_view({"post": "active"}),
        name="activate-lot",
    ),
    # Rutas para lotes
    path(
        "soil-types", SoilTypeListCreateView.as_view(), name="soil-type-list-create"
    ),  # Metodos del endpoint Get lista todos, post Crea
    path(
        "soil-types/<int:pk>",
        SoilTypeRetrieveUpdateDestroyView.as_view(),
        name="soil-type-detail",
    ),  # Metodos del endpoint Get lista ,PUT modifica,DELETE elimina al ID que se pase
]
