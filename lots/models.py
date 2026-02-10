import os
import re
from django.db import models
from django.utils import timezone
from django.utils.html import mark_safe
from .utils.images import process_image, compress_and_save_pair


class Lot(models.Model):
    title = models.CharField("Название", max_length=255)
    price = models.IntegerField(verbose_name="Цена", help_text="Укажите цену")
    description = models.TextField("Описание", blank=True)

    main_image = models.ImageField("Основное изображение", upload_to="lots/images/", blank=True, null=True)
    preview_image = models.ImageField("Превью для списка", upload_to="lots/previews/", blank=True, null=True,
                                      editable=False)
    created_at = models.DateTimeField("Дата создания", default=timezone.now)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)
    is_active = models.BooleanField("Активен", default=True)
    category = models.CharField("Категория", max_length=100, blank=True, help_text="Например: Иконы, Живопись")
    tags = models.CharField("Теги (через запятую)", max_length=255, blank=True,
                            help_text="Введите теги через запятую")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Лот"
        verbose_name_plural = "Лоты"

    def __str__(self):
        return self.title

    # Нормализация тегов
    def normalize_tags(self):
        result = []

        for t in self.tags.split(","):
            t = re.sub(r"\s+", " ", t.strip().lower())
            if t and t not in result:
                result.append(t)

        return ", ".join(result)

    # Нормализация категории
    def normalize_category(self):
        return " ".join(
            word.capitalize()
            for word in re.sub(r"\s+", " ", self.category.strip()).split(" ")
        )

    def save(self, *args, **kwargs):
        # текстовая нормализация
        if self.tags:
            self.tags = self.normalize_tags()

        if self.category:
            self.category = self.normalize_category()

        if self.main_image:
            is_new = not self.pk or Lot.objects.filter(pk=self.pk).exclude(main_image=self.main_image).exists()
            if is_new:
                compress_and_save_pair(self, self.main_image, self.preview_image)

        super().save(*args, **kwargs)

    def tags_list(self):
        return [t.strip() for t in self.tags.split(",") if t.strip()]

    def image_preview(self):
        # в админке показываем маленькое превью, чтобы она работала быстро
        display_img = self.preview_image if self.preview_image else self.main_image
        if display_img:
            return mark_safe(f'<img src="{display_img.url}" style="max-height:100px;"/>')
        return "(Нет изображения)"

    image_preview.short_description = "Превью"


class LotImage(models.Model):
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField("Доп. фото", upload_to="lots/gallery/")
    preview_image = models.ImageField("Доп. фото (превью)", upload_to="lots/gallery_previews/", editable=False, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.image:
            is_new = not self.pk or LotImage.objects.filter(pk=self.pk).exclude(image=self.image).exists()
            if is_new:
                compress_and_save_pair(self, self.image, self.preview_image)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Image for {self.lot.title}"