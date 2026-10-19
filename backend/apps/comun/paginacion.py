from rest_framework.pagination import PageNumberPagination


class Paginacion(PageNumberPagination):
    """20 elementos por página (RNF-09). Los selectores pueden pedir más con ?tamano=, hasta 200."""

    page_size = 20
    page_size_query_param = "tamano"
    max_page_size = 200
