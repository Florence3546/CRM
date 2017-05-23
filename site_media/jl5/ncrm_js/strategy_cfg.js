PT.namespace('NcrmStgCfg');
PT.NcrmStgCfg = function(){
    var stg_table = $('#stg_cfg_table');

    var inited=false;

    var init_dom=function(){
        $(document).off('keypress.PT.search_instuction').on('keypress.PT.search_instuction', '#id_search_instrcn', function(e){
            var key=e.keyCode||e.which||e.charCode;
            switch(key){
                case 13:
                    var search_text = $(this).val();
                    var instrcn_selector = '#cmd_cfg_table>tbody>tr';
                    if(search_text==''||search_text==undefined||search_text==null){
                       $(instrcn_selector).each(function(){
                          $(this).show();
                       });
                   }else{
                       $(instrcn_selector).each(function(){
                          if($(this).attr('tag_name').indexOf(search_text)!=-1){
                              $(this).show();
                          }else{
                              $(this).hide();
                          }
                       });
                   }
                   break;
            }
        });

        $(document).on('click', '.save_stg', function(){
            var save_stg = function (cfg_id, update_dict) {
                PT.sendDajax({'function': 'ncrm_save_algcfg', 'cfg_id': cfg_id, 'update_dict': $.toJSON(update_dict), 'class_type': 'stg_cfg'});
                PT.show_loading('正在修改数据');
            };

            var cur_tr = $(this).parents('tr:first'),
                cfg_id = cur_tr.attr('id'),
                name = cur_tr.find('td').eq(0).text(),
                desc = cur_tr.find('td').eq(1).text(),
                kw_cmd_list = $.map(cur_tr.find('.instrcn_list li'), function(obj){ return $.trim($(obj).text());}),
                adg_cmd_list = $.map(cur_tr.find('.adg_cmd input:checked'), function(obj){ return $(obj).val();}),
                jq_impact_list = cur_tr.find('.impact_factor'),
                impact_factor_dict = {};
            for (var i = 0; i < jq_impact_list.length; i++) {
                var key = $(jq_impact_list[i]).attr('data'),
                    value = parseFloat($(jq_impact_list[i]).text(), 2);
                    if (isNaN(value)) {
                        PT.alert('影响系数只能为数字');
                        return;
                    }
                impact_factor_dict[key] = value;
            };

            if (name) {
                var update_dict = {'name': name, 'desc': desc, 'kw_cmd_list': kw_cmd_list, 'adg_cmd_list': adg_cmd_list, 'impact_factor_dict': impact_factor_dict};
                PT.confirm("确定要「修改」当前配置吗？", save_stg, [cfg_id, update_dict]);
            }else{
                PT.alert("配置项尚未完整输入！");
                return false;
            }
        });

        $(document).on('click', '.del_stg', function(){
            var del_stg = function(cfg_id) {
                PT.sendDajax({'function':'ncrm_del_algcfg', 'cfg_id':cfg_id, 'class_type': 'stg_cfg'});
                PT.show_loading('正在删除数据');
                return;
            };

            var cur_tr = $(this).parents('tr:first');
                cfg_id = cur_tr.attr('id');
            if (cfg_id) {
                PT.confirm("确定要「删除」当前配置吗？", del_stg, [cfg_id]);
                return;
            }
            cur_tr.remove();
        });


        $(document).on('click', '.save_cmd', function(){
            var save_cmd = function (cfg_id, update_dict) {
                PT.sendDajax({'function': 'ncrm_save_algcfg', 'cfg_id': cfg_id, 'update_dict': $.toJSON(update_dict), 'class_type': 'cmd_cfg'});
                PT.show_loading('正在修改数据');
            };

            var cur_tr = $(this).parents('tr:first'),
                cfg_id = cur_tr.attr('id'),
                key_list = ['name', 'desc', 'cond', 'operate'],
                update_dict = {};

            for (var i = 0; i < key_list.length; i++) {
                update_dict[key_list[i]] = $.trim(cur_tr.find('.' + key_list[i]).text());
            };

            if (update_dict.name && update_dict.cond && update_dict.operate) {
                PT.confirm("确定要「修改」当前配置吗？", save_cmd, [cfg_id, update_dict]);
            }else{
                PT.alert("配置项尚未完整输入！");
                return false;
            }
        });

        $(document).on('click', '.del_cmd', function(){
            var del_cmd = function(cfg_id) {
                PT.sendDajax({'function':'ncrm_del_algcfg', 'cfg_id':cfg_id, 'class_type': 'cmd_cfg'});
                PT.show_loading('正在删除数据');
                return;
            };

            var cur_tr = $(this).parents('tr:first');
                cfg_id = cur_tr.attr('id');
            if (cfg_id) {
                PT.confirm("确定要「删除」当前配置吗？", del_cmd, [cfg_id]);
                return;
            }
            cur_tr.remove();
        });

        $(document).on('click','.edit_instrcn', function(){
            $('ul.instrcn_list').removeClass('edit_style').addClass('view_style');
            var instrcn_obj = $(this).parent().find('ul.instrcn_list');
            instrcn_obj.removeClass('view_style').addClass('edit_style');

            var instrcn_list = [];
            var obj_list = $(instrcn_obj).find('li');
            for(var j=0;j<obj_list.length;j++){
                instrcn_list.push($(obj_list[j]).text());
            }
            var cb_list = $('input[name=instrcn_checkbox]');
            for(var i=0;i<cb_list.length;i++){
                var cur_tr = $(cb_list[i]).parents('tr');
                if(instrcn_list.indexOf($(cb_list[i]).attr('id'))!=-1){
                    $(cb_list[i]).attr('checked', 'checked');
                    cur_tr.show();
                }else{
                    $(cb_list[i]).removeAttr('checked');
                    cur_tr.hide();
                }
            }
        });

        $('#stg_cfg_table ul.instrcn_list').sortable({axis:'x', containment:'parent'});

        /*修改子项的顺序*/
        var change_order =function(org_index, new_index, all_obj){
            if(new_index >=$(all_obj).length || new_index <=-1){
                return false;
            }
            if(org_index >new_index){//提升顺序
                $(all_obj).filter(':eq('+org_index+')').after($(all_obj).filter(':eq('+new_index+')'));
            }else if(org_index < new_index){//降低顺序
                $(all_obj).filter(':eq('+org_index+')').before($(all_obj).filter(':eq('+new_index+')'));
            }else{//置顶
                $(all_obj).filter(':eq('+org_index+')').after($(all_obj));
            }
        };

        $(document).on('click', '.sort', function(){
            var tag_name = $(this).parent().parent().attr('name');
            var all_obj = $('div[name='+tag_name+']');
            var index = $(this).parent().parent().index();
            var new_index = index - parseInt($(this).attr('move'));
            change_order(index,new_index, all_obj);
        });

        $(document).on('onblur', '.impact_factor', function(){
            if (parseFloat($(this).text()) == NaN) {
                $(this).text(1.0);
                PT.light_msg('警告', '影响系数只能为数字');
            }
        })

    };


    var bind_event = function(selector){

        var selector = selector;
        $(document).off('click.PT.check_instrcn').on('click.PT.check_instrcn', 'input[name=instrcn_checkbox]', function(){

            function remove_instrcn(tag_name){
                var obj_list = $(editting_obj).find('li');
                for(var i=0;i<obj_list.length;i++){
                    if($(obj_list[i]).text() == tag_name){
                       $(obj_list[i]).remove();
                    }
                }
            }

            function add_instrcn(tag_name){
                var html = "<li>"+tag_name+"</li>";
                $(editting_obj).append(html);
            }

            var tag_name = $(this).attr('id');
            if(tag_name!=''&& tag_name!=undefined){
                var editting_obj = $(selector);
                if(editting_obj.length>0){
                    var is_in = $(editting_obj).text().indexOf(tag_name)!=-1?true:false;
                    if($(this).attr('checked') == 'checked'){
                        if(!is_in){add_instrcn(tag_name);}
                    }
                    else{
                        if(is_in){remove_instrcn(tag_name);}
                    }
                }
            }
        });

    };

    var init_table = function() {
            $('table[id=stg_cfg_table]').each(function() {
                $(this).dataTable({
                    'autoWidth': true,
                    'bDestroy': true,
                    'aaSorting': [
                        [0, 'asc']
                    ],
                    'iDisplayLength': 1000,
                    'sDom': "T<'row-fluid't<'row-fluid mt10'<'span12 pl10'i><'span12 pr10 tr'p>>",
                    'oLanguage': {
                        'sInfo': '总共_TOTAL_条记录',
                        'sInfoEmpty': '',
                        'sEmptyTable': '正在获取数据.......',
                        'sZeroRecords': '亲，没有找到匹配的关键词',
                        'sInfoFiltered': '(从 _MAX_ 条记录中过滤)',
                        'oPaginate': {
                            'sNext': '下一页',
                            'sPrevious': '上一页'
                        }
                    }
                    });
                    });
            }

    return {
        init:function(){
            init_dom();
            bind_event('.instrcn_list.edit_style');
        },
        del_cfg_back: function(result) {
            var cfg_id = result.cfg_id,
                error_str = result.error_str;
            PT.hide_loading();
            if (error_str) {
                PT.alert('删除失败：e=' + error_str);
            }else{
                $('tr[id=' + cfg_id + ']').remove();
            }
        }
    }
}();
