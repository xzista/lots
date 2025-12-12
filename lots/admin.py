from django.contrib import admin
from .models import Lot, LotImage


class LotImageInline(admin.TabularInline):
    model = LotImage
    extra = 3


@admin.register(Lot)
class LotAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "is_active", "created_at", "image_preview")
    inlines = [LotImageInline]
    list_filter = ("is_active", "category",)
    search_fields = ("title", "description", "tags")
    readonly_fields = ("image_preview",)
    fields = ("title", "description", "main_image", "image_preview", "category", "tags", "is_active", "created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at", "image_preview")