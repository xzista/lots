(function($) {
    'use strict';

    $(document).ready(function() {
        setTimeout(initAutocomplete, 500);
    });

    function initAutocomplete() {
        const $field = $('.field-tags input, .field-tags textarea').first();
        if (!$field.length) return;

        if ($field.data('autocomplete-initialized')) return;
        $field.data('autocomplete-initialized', true);

        const datalistId = 'tags-datalist';
        const $datalist = $('<datalist id="' + datalistId + '"></datalist>');
        $('body').append($datalist);

        $field.attr('list', datalistId);
        $field.attr('autocomplete', 'off');

        let timer;

        function updateSuggestions() {
            const text = $field.val() || '';
            const parts = text.split(',').map(t => t.trim()).filter(Boolean);
            const last = parts.length ? parts[parts.length - 1] : '';

            if (last.length < 1) {
                $datalist.empty();
                return;
            }

            $.get('/lot_add/lots/lot/tag-suggestions/', {
                q: last,
                input: text
            }, function(data) {
                $datalist.empty();

                let prefix = parts.length > 1
                    ? parts.slice(0, -1).join(', ') + ', '
                    : '';

                data.forEach(tag => {
                    $datalist.append(`<option value="${prefix}${tag}">`);
                });
            });
        }

        $field.on('input', function() {
            clearTimeout(timer);
            timer = setTimeout(updateSuggestions, 300);
        });

        $field.on('change', function() {
            let val = $(this).val().trim();
            if (val && !val.endsWith(',')) {
                $(this).val(val + ', ');
            }
        });
    }
})(django.jQuery);