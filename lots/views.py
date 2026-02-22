from django.db.models import Q
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
        sort = self.request.GET.get("sort", "-created_at")

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

        # логика сортировки
        if sort == "price_asc":
            qs = qs.order_by("price")
        elif sort == "price_desc":
            qs = qs.order_by("-price")
        elif sort == "oldest":
            qs = qs.order_by("created_at")
        else:
            qs = qs.order_by("-created_at")
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # добавляем параметры фильтрации в контекст
        context["q"] = self.request.GET.get("q", "").strip()
        context["selected_tag"] = self.request.GET.get("tag", "").strip()
        context["selected_category"] = self.request.GET.get("category", "").strip()
        context["current_sort"] = self.request.GET.get("sort", "-created_at")

        return context


class LotDetailView(DetailView):
    model = Lot
    template_name = "lots/lot_detail.html"
    context_object_name = "lot"

    def get_queryset(self):
        # фильтр по активным лотам
        return super().get_queryset().filter(is_active=True).prefetch_related("images")
