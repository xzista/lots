import os
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile
from pillow_heif import register_heif_opener

register_heif_opener()

def process_image(image_field, size=1920, quality=88):
    """
    Универсальная обработка изображения:
    - Поддерживает форматы: HEIC, JPEG, PNG
    - Конвертирует всё в качественный JPEG
    - Делает ресайз до указанного размера 'size' по длинной стороне
    - Оптимизирует размер файла
    """
    try:
        img = Image.open(image_field)

        # конвертация в RGB
        if img.mode != "RGB":
            img = img.convert("RGB")

        # ресайз с использованием LANCZOS
        img.thumbnail((size, size), Image.Resampling.LANCZOS)

        buffer = BytesIO()
        # optimize=True подбирает оптимальную таблицу сжатия
        img.save(buffer, format="JPEG", quality=quality, optimize=True)

        return ContentFile(buffer.getvalue())
    except Exception as e:
        # логирование ошибки, если файл битый или формат не поддерживается
        print(f"Ошибка при обработке изображения: {e}")
        return None


def compress_and_save_pair(instance, image_field, preview_field, base_size=2560, thumb_size=800):
    """
    Универсальный обработчик для любой пары 'Оригинал + Превью'
    """
    if not image_field:
        return

    filename = os.path.basename(image_field.name)
    base_name = os.path.splitext(filename)[0]

    # создаем превью 800px
    thumb_data = process_image(image_field, size=thumb_size, quality=75)
    if thumb_data:
        preview_field.save(f"{base_name}_thumb.jpg", thumb_data, save=False)

    # создаем качественный оригинал 2560px
    main_data = process_image(image_field, size=base_size, quality=90)
    if main_data:
        image_field.save(f"{base_name}.jpg", main_data, save=False)