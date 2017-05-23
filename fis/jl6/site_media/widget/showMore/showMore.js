define(["template","jquery"], function(template,$) {
    "use strict";

    var objs = $('[data-toggle=show_more]'),
        tpl = __inline('tpl.html');


    var getTpmData = function($element) {
        var data = [];
        $element.find('thead>tr:first th').each(function() {
            var $obj = $(this);
            if ($obj.is('[data-active]')) {
                data.push([$.trim($(this).text()), $(this).is(':visible'), $obj.data('active')])
            }
        });
        return data;
    }

    var getChooseData = function($element) {
        var data = [];

        $('input', $element).each(function() {
            data.push([this.value, this.checked]);
        });
        console.log(data)
        return data;
    }

    //绑定事件
    var bind_event = function(parent, target) {
        var that = this;

        console.log(target)

        $('input', this).on('change', function() {
            var obj = $('[data-name=' + $(this).val() + ']', that);
            if (this.checked) {
                obj.removeClass('hidden');
            } else {
                obj.addClass('hidden');
            }
        });

        $('.btn-default', this).on('click', function() {
            $(parent).removeClass('open');
        });

        $('.btn-primary', this).on('click', function() {
            var data;
            $(parent).removeClass('open');

            data = getChooseData(that);

            $(data).each(function() {
                if (this[0]) {
                    var index = $('thead>tr>th', target).index($('th[data-active=' + this[0] + ']', target));

                    if(this[1]){
                        $('tr',target).find('th:eq('+index+')').removeClass('hidden');
                        $('tr',target).find('td:eq('+index+')').removeClass('hidden');
                    }else{
                        $('tr',target).find('th:eq('+index+')').addClass('hidden');
                        $('tr',target).find('td:eq('+index+')').addClass('hidden');
                    }
                }
            });
        });
    }

    objs.each(function() {
        $(this).on('click.data.api', function(e) {
            var $parent = $(this).parent(),
                $target,
                $html;

            e.stopPropagation();

            $target = $('#' + $(this).data('target'));

            $html = $(template.compile(tpl)({
                data: getTpmData($target)
            }));


            if (!$parent.find('.show_more_modal').length) {
                $(this).after($html);

                bind_event.apply($html, [$parent, $target])

                $parent.find('.show_more_modal').on('click', function(e) {
                    e.stopPropagation();
                });
            }


            $parent.toggleClass('open');

        });
    });

    $(document).on('click.show_more.hide', function() {
        objs.parent().removeClass('open');
    })
});
