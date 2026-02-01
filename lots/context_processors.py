from collections import Counter
from .models import Lot

def categories_processor(request):
    lots = Lot.objects.filter(is_active=True)

    # категории + частота
    categories_counter = Counter(
        lots.exclude(category__isnull=True)
             .exclude(category__exact="")
             .values_list("category", flat=True)
    )

    categories = [c for c, _ in categories_counter.most_common()]

    # теги + частота
    tags_counter = Counter()
    for tags in lots.exclude(tags="").values_list("tags", flat=True):
        for t in [x.strip() for x in tags.split(",") if x.strip()]:
            tags_counter[t] += 1

    tags = [t for t, _ in tags_counter.most_common()]

    return {
        "site_categories": categories,
        "site_tags": tags,
    }

def search_form_processor(request):
    # для доступа к полям поиска в любом шаблоне
    return {
        "search_q": request.GET.get("q", ""),
        "search_tag": request.GET.get("tag", ""),
        "search_category": request.GET.get("category", ""),
    }