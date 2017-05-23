/**
 * Created by Administrator on 2016/1/11.
 */
define(['require','template','moment', 'dataTable', '../../widget/ajax/ajax'],function(require,template,moment, dataTable, ajax){

    var detail_table;
    var start_date = moment().subtract(7, 'days').format('YYYY-MM-DD'),
        end_date = moment().subtract(1, 'days').format('YYYY-MM-DD');

    var  hasInit = false;
    var init = function(){
        hasInit = true;
        getDetailList(start_date,end_date);

        $('#selectDetailDate').change(function(){
            var days = Number($(this).val());
            if(days==0){
                start_date = moment().subtract(0, 'days').format('YYYY-MM-DD'),
                end_date = moment().subtract(0, 'days').format('YYYY-MM-DD');
            }else{
                start_date = moment().subtract(days, 'days').format('YYYY-MM-DD'),
                end_date = moment().subtract(1, 'days').format('YYYY-MM-DD');
            }
            getDetailList(start_date,end_date);
        });
    };

    //获取计划列表数据
    var getDetailList=function(start,end) {
        /**
         * 在这里从后台取数据
         */
        ajax.ajax('get_rpt_detail',{'start_date':start, 'end_date':end},function(data){
            drawDataTable(data);
        });
    };

    var drawDataTable = function(data){
        if (detail_table) {
            detail_table.fnClearTable();
            detail_table.fnDestroy();
        }
        var html,
            tpl = __inline("account_detail_list.html");
        /**
         * 在这里从后台取数据
         */
        html = template.compile(tpl)({list: data.data.rpt_list});


        $('#detail_table tbody').html(html);

        detail_table = $('#detail_table').dataTable({
            "bRetrieve": true, //允许重新初始化表格
            "bPaginate": false,
            "bDestroy": true,
            "bFilter": true,
            "bInfo": false,
            "bAutoWidth": false,//禁止自动计算宽度
            "sDom": '',
            "language": {"emptyTable": "<div style='text-align:center'>暂无数据</div>"},
            "aoColumns": [
                {"bSortable": true,
                    "sType": 'custom',
                    "sSortDataType": "custom-text"
                },
                {"bSortable": true,
                    "sType": 'custom',
                    "sSortDataType": "custom-text"
                },
                {"bSortable": true,
                    "sType": 'custom',
                    "sSortDataType": "custom-text"
                },
                {"bSortable": true,
                    "sType": 'custom',
                    "sSortDataType": "custom-text"
                },
                {"bSortable": true,
                    "sType": 'custom',
                    "sSortDataType": "custom-text"
                },
                {"bSortable": true,
                    "sType": 'custom',
                    "sSortDataType": "custom-text"
                },
                {"bSortable": true,
                    "sType": 'custom',
                    "sSortDataType": "custom-text"
                },
                {"bSortable": true,
                    "sType": 'custom',
                    "sSortDataType": "custom-text"
                },
                {"bSortable": true,
                    "sType": 'custom',
                    "sSortDataType": "custom-text"
                },
                {"bSortable": true,
                    "sType": 'custom',
                    "sSortDataType": "custom-text"
                },
                {"bSortable": false}
            ]
        });
    };

    return {
        init:function(){
            init();
        },
        hasInit: function(){
            return hasInit;
        }
    }
});