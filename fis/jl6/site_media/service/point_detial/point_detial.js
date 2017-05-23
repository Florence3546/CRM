define(["require","template",'widget/alert/alert','widget/ajax/ajax','widget/templateExt/templateExt'], function(require,template,alert,ajax) {
    "use strict";

    var modalTpl,
        tableTpl,
        obj;

    modalTpl = __inline('point_detial.html');
    tableTpl = __inline('point_table.html');

    var show=function(){
        var html;

        html = template.compile(modalTpl)();

        obj=$(html);

        $('body').append(obj);

        obj.modal();

        obj.on('shown.bs.modal',function(){
            getDate(1);
        });

        obj.on('hidden.bs.modal',function(){
            obj.remove();
        });

    }

    var getDate=function(page){
        ajax.ajax('point_detial',{page:page},function(data){
            layOutTable(data.data.detial_list);
            layOutPageBar(data.data.page_info);
        });
    }

    var layOutTable = function(data){
        var html;

        html = template.compile(tableTpl)({list:data});

        obj.find('.content').html(html);
    }

    var layOutPageBar = function(data){
        require(['widget/pageBar/pageBar'],function(pageBar){
            var dom = pageBar.show({
                data:data,
                onChange:function(page){
                    getDate(page)
                }
            });

            obj.find('.page').html(dom)
        });
    }

    return {
        show: show
    }
});
