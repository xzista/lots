from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Lot
from django.db.models import Q

def lot_list(request):
    qs = Lot.objects.filter(is_active=True)

    q = request.GET.get("q", "").strip()
    tag = request.GET.get("tag", "").strip()
    category = request.GET.get("category", "").strip()

    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q) | Q(tags__icontains=q))

    if tag:
        # ищем, чтобы тег содержался в CSV
        qs = qs.filter(tags__icontains=tag)

    if category:
        qs = qs.filter(category__iexact=category)

    paginator = Paginator(qs, 12)  # 12 на страницу
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "q": q,
        "selected_tag": tag,
        "selected_category": category,
    }
    return render(request, "lots/lot_list.html", context)

def lot_detail(request, pk):
    lot = get_object_or_404(Lot, pk=pk, is_active=True)
    context = {"lot": lot}
    return render(request, "lots/lot_detail.html", context)