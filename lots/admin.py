from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from .models import Lot, LotImage


class LotImageInline(admin.TabularInline):
    model = LotImage
    extra = 3


@admin.register(Lot)
class LotAdmin(admin.ModelAdmin):
    list_display = ("title", "price", "category", "is_active", "created_at", "image_preview")
    inlines = [LotImageInline]
    list_filter = ("is_active", "category", "price")
    search_fields = ("title", "description", "tags")
    readonly_fields = ("image_preview",)
    fields = (
    "title", "price", "description", "main_image", "image_preview", "category", "tags", "is_active", "created_at",
    "updated_at")
    readonly_fields = ("created_at", "updated_at", "image_preview")

    def get_urls(self):
        urls = super().get_urls()

        # Добавляем кастомный URL для автокомплита
        # Путь будет: /lot_add/lots/lot/tag-suggestions/
        custom_urls = [
            path('tag-suggestions/', self.admin_site.admin_view(self.tag_suggestions_view),
                 name='%s_%s_tag_suggestions' % (self.model._meta.app_label, self.model._meta.model_name)),
        ]
        return custom_urls + urls

    def tag_suggestions_view(self, request):
        query = request.GET.get("q", "").strip().lower()
        input_text = request.GET.get("input", "").strip()

        parts = []
        if input_text:
            parts = [p.strip() for p in input_text.split(",") if p.strip()]
            if parts:
                query = parts[-1].lower()

        if len(query) < 1:
            return JsonResponse([], safe=False)

        all_tags = set()

        for lot in Lot.objects.exclude(tags__isnull=True).exclude(tags="").only("tags"):
            for tag in lot.tags.split(","):
                tag = tag.strip()
                if tag:
                    all_tags.add(tag)

        suggestions = [
            t for t in all_tags
            if query in t.lower() and t.lower() not in [p.lower() for p in parts[:-1]]
        ]

        suggestions.sort(key=lambda x: (
            not x.lower().startswith(query),
            len(x),
            x.lower()
        ))

        return JsonResponse(suggestions[:10], safe=False)

    class Media:
        css = {
            'all': ('assets/css/autocomplete.css',)
        }
        js = (
            'admin/js/vendor/jquery/jquery.min.js',  # Загружаем jQuery явно
            'admin/js/jquery.init.js',  # Инициализируем jQuery для Django
            'assets/js/autocomplete.js',
        )