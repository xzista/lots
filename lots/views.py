import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.views.generic import ListView, DetailView
from .models import Lot


class LotListView(ListView):
    model = Lot
    template_name = "lot_list.html"
    context_object_name = "lots"
    paginate_by = 12

    def get_queryset(self):
        qs = super().get_queryset().filter(is_active=True)

        # параметры фильтрации из GET-запроса
        q = self.request.GET.get("q", "").strip()
        tag = self.request.GET.get("tag", "").strip().lower()
        category = self.request.GET.get("category", "").strip()

        # фильтры
        if q:
            qs = qs.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(tags__icontains=q)
            )

        if tag:
            # поиск тега содержался в CSV
            qs = qs.filter(tags__icontains=tag)

        if category:
            qs = qs.filter(category__iexact=category)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # добавляем параметры фильтрации в контекст
        context["q"] = self.request.GET.get("q", "").strip()
        context["selected_tag"] = self.request.GET.get("tag", "").strip()
        context["selected_category"] = self.request.GET.get("category", "").strip()

        context["page_obj"] = context.get("page_obj")

        return context


class LotDetailView(DetailView):
    model = Lot
    template_name = "lots/lot_detail.html"
    context_object_name = "lot"

    def get_queryset(self):
        # фильтр по активным лотам
        return super().get_queryset().filter(is_active=True).prefetch_related("images")


def tag_suggestions(request):
    q = request.GET.get("q", "").strip().lower()

    if len(q) < 2:
        return JsonResponse([], safe=False)

    all_tags = set()

    for lot in Lot.objects.exclude(tags="").values_list("tags", flat=True):
        for tag in lot.split(","):
            tag = re.sub(r"\s+", " ", tag.strip().lower())
            if tag:
                all_tags.add(tag)

    result = [t for t in all_tags if q in t]

    return JsonResponse(sorted(result)[:15], safe=False)