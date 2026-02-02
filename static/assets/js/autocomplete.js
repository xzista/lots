(function($) {
    'use strict';

    $(document).ready(function() {
        // Функция для создания автокомплита
        function initAutocomplete($input) {
            var field = $input.data('field');
            var $hiddenInput = $('#' + $input.attr('id').replace('_autocomplete', ''));

            // Создаем datalist
            var datalistId = 'datalist-' + field;
            if (!$('#' + datalistId).length) {
                $('body').append('<datalist id="' + datalistId + '"></datalist>');
            }

            $input.attr('list', datalistId);

            // Загружаем популярные значения
            var popularValues = [];
            switch(field) {
                case 'artist':
                    popularValues = POPULAR_ARTISTS || [];
                    break;
                case 'material':
                    popularValues = POPULAR_MATERIALS || [];
                    break;
                case 'technique':
                    popularValues = POPULAR_TECHNIQUES || [];
                    break;
            }

            // Добавляем опции в datalist
            var $datalist = $('#' + datalistId);
            $datalist.empty();

            popularValues.forEach(function(value) {
                $datalist.append('<option value="' + value + '">');
            });

            // Обработчик изменения значения
            $input.on('input', function() {
                var value = $(this).val();
                $hiddenInput.val(value);

                // Динамическая подгрузка предложений
                if (value.length >= 2) {
                    $.get('/admin/lots/lot/suggestions/', {
                        field: field,
                        q: value
                    }, function(data) {
                        $datalist.empty();
                        data.forEach(function(item) {
                            $datalist.append('<option value="' + item + '">');
                        });
                    });
                }
            });
        }

        // Инициализируем автокомплиты
        $('.autocomplete-input').each(function() {
            initAutocomplete($(this));
        });

        // Обработчик для быстрого добавления тегов
        $('select[name="tags"]').on('select2:select', function(e) {
            var data = e.params.data;
            if (data._resultId && data._resultId.startsWith('new:')) {
                var tagName = data.text;
                var fieldType = prompt('Выберите тип тега:\n1 - Автор\n2 - Материал\n3 - Техника\n4 - Стиль\n5 - Сюжет', '1');

                var fieldMap = {
                    '1': 'artist',
                    '2': 'material',
                    '3': 'technique',
                    '4': 'style',
                    '5': 'subject'
                };

                if (fieldType && fieldMap[fieldType]) {
                    // Отправляем AJAX запрос для создания тега
                    $.ajax({
                        url: '/admin/lots/tag/add/',
                        method: 'POST',
                        data: {
                            name: tagName,
                            field_type: fieldMap[fieldType],
                            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val()
                        },
                        success: function(response) {
                            if (response.success) {
                                // Обновляем список тегов
                                var $select = $('select[name="tags"]');
                                var newOption = new Option(tagName, response.id, true, true);
                                $select.append(newOption).trigger('change');
                            }
                        }
                    });
                }
            }
        });
    });
})(django.jQuery);

(function($) {
    $(document).ready(function() {

        const $input = $('input[name="tags"]');
        if (!$input.length) return;

        const listId = 'tags-datalist';
        if (!$('#' + listId).length) {
            $('body').append(`<datalist id="${listId}"></datalist>`);
        }

        $input.attr('list', listId);

        $input.on('input', function() {
            let value = this.value;
            let parts = value.split(',');
            let last = parts[parts.length - 1].trim();

            if (last.length < 2) return;

            fetch(`/tag-suggestions/?q=${encodeURIComponent(last)}`)
                .then(r => r.json())
                .then(data => {
                    const dl = $('#' + listId);
                    dl.empty();
                    data.forEach(tag => {
                        dl.append(`<option value="${tag}">`);
                    });
                });
        });

        $input.on('change', function() {
            let parts = this.value.split(',');

            let selected = parts.pop().trim();
            let prefix = parts.map(p => p.trim()).filter(Boolean);

            prefix.push(selected);

            this.value = prefix.join(', ') + ', ';
        });

    });
})(django.jQuery);