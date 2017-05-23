PT.namespace('Feedback');
PT.Feedback = function() {

        var init_dom = function() {
            //日期时间选择器
            require(['dom', 'gallery/datetimepicker/1.1/index'], function(DOM, Datetimepicker) {
                var b, c;
                b = new Datetimepicker({
                    start: '#start_time',
                    timepicker: false,
                    closeOnDateSelect: true
                });
                c = new Datetimepicker({
                    start: '#end_time',
                    timepicker: false,
                    closeOnDateSelect: true
                });
            });
            
            //初始化表格
            $('#table_feedback').dataTable({
                sDom: '<"#pagination_bar" ip>t',
                bLengthChange: false,
                bDestroy: true,
                iDisplayLength: 20,
                oLanguage: {
                    sZeroRecords: "没有反馈记录",
                    sInfo: "第 _START_ 至 _END_ 条（共_TOTAL_条）",
                    sInfoEmpty: "0 条记录",
                    oPaginate: {
                        sFirst: "首页",
                        sLast: "末页",
                        sNext: "下一页",
                        sPrevious: "上一页"
                    }
                },
                aaSorting: [[0, 'desc']]
            });
        }

    return {
        init: function() {
            init_dom();
        }
    }
}();
