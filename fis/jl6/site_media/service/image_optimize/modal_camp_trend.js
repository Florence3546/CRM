define(["require","template","../common/common"], function(require,template,common) {
    "use strict";

    var tpl;

    tpl = __inline('modal_camp_trend.html');

    var show=function(options,category_list, series_cfg_list){
        var html,
            obj;

        html = template.compile(tpl)(options);

        obj=$(html);

        $('body').append(obj);

        obj.modal();


        obj.on('shown.bs.modal',function(){
            common.chart.draw("camp_chart_warp",category_list, series_cfg_list);
        });

        obj.on('hidden.bs.modal',function(){
            obj.remove();
        });
    }

    return {
        show: show
    }
});
