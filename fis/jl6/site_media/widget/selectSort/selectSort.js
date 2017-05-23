define(['jquery', 'template'], function($, template) {
    "use strict";

    var selecter = 'table th[data-toggle=selectSort]';

    $.fn.selectSort = function(options) {
        var options = $.extend({}, $(this).data(), options),
            obj,
            self = this,
            oldSelecter;

        obj = $(template.compile(__inline("selectSort.html"))({
            data: options.nameList
        }));

        self.append(obj);

        self.on('mouseover', function() {
            $(this).addClass('active');
        });

        self.on('mouseout', function() {
            $(this).removeClass('active');
        });

        obj.find('li').on('click', function() {
            var selecter = $(this).data().selecter,
                thObj = $(this).parents('th:first'),
                dataTable,
                index = options.index,
                sortValue,
                rows;


            obj.find('li').removeClass('active');
            $(this).addClass('active');

            thObj.removeClass('active');

            dataTable = $('#' + options.table).dataTable();
            rows = dataTable.fnSettings().aoData;

            for (var i = 0; i < rows.length; i++) {
                var temp = $(rows[i].nTr).find('.' + selecter),
                    sortValue,
                    matchValue;

                if (temp.length) {
                    matchValue=temp.text().match(/\d+(\.\d+)?/);
                    sortValue = matchValue?matchValue[0]:undefined;
                    temp.parents('td:first').find('>span:first').text(sortValue);
                }
            }

            if (oldSelecter == selecter) { //默认点击一次为降序，点击两次则升降序交替
                if (dataTable.fnSettings().aaSorting[0][1] === "asc") {
                    dataTable.fnSort([
                        [index, 'desc']
                    ]);
                } else {
                    dataTable.fnSort([
                        [index, 'asc']
                    ]);
                }
            } else {
                dataTable.fnSort([
                    [index, 'desc']
                ]);
            }


            oldSelecter = selecter;
        });
    }


    $(selecter).each(function() {
        var data = $(this).data();
        $(this).selectSort(data);
    });
});
