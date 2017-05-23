/**
 * Created by Administrator on 2015/10/21.
 */
define(["require","template","../common/common"], function(require,template,common) {
    "use strict";

    var tpl;

    tpl = __inline('mnt_camp_rpt.html');

    var show=function(options){
        var html,
            obj;
        html = template.compile(tpl)(options);
        obj=$(html);

        $('body').append(obj);

        obj.modal();


        obj.on('shown.bs.modal',function(){
            common.chart.draw("mnt_camp_chart",options.category_list, options.series_cfg_list);

            obj.find('.detailed_table').dataTable({
                "bPaginate": false,
                "bFilter": false,
                "bInfo": false,
                "aaSorting":[[0,'desc']],
                "sDom":"",
                "oLanguage": {
                    "sZeroRecords": "暂无数据！",
                    "sInfoEmpty": "暂无数据！"
                    },
                "aoColumns":[null, null, null, null, null, null,
                                        {"sSortDataType":"td-text", "sType":"numeric"},
                                        {"sSortDataType":"td-text", "sType":"numeric"},
                                        {"sSortDataType":"td-text", "sType":"numeric"},
                                        null, null]
            });
        });

        obj.on('hidden.bs.modal',function(){
            obj.remove();
        });
    }

    return {
        show: show
    }
});
