from .models import Lot

def categories_processor(request):
    categories = Lot.objects.order_by().values_list("category", flat=True).distinct()
    categories = [c for c in categories if c]
    return {"site_categories": categories}

def search_form_processor(request):
    # для доступа к полям поиска в любом шаблоне
    return {
        "search_q": request.GET.get("q", ""),
        "search_tag": request.GET.get("tag", ""),
        "search_category": request.GET.get("category", ""),
    }