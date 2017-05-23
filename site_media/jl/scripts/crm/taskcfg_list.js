PT.namespace('CrmCampaign');
PT.TaskCfgList = function () {

    var init_dom=function(){

        $(document).on('focus.PT.edit_cfg', '.before_edit', function(){
            $(this).removeClass('before_edit').addClass('edit_cfg');
        });

        $(document).on('blur.PT.lost_focus', '.edit_cfg', function(){
            $(this).removeClass('edit_cfg').addClass('before_edit');
        });

        $('#id_taskcfg_list_layer').find('input').addClass('desc_input');
        $('#id_taskcfg_list_layer').on('mouseenter', 'input', function(){
            $(this).removeClass('desc_input');
        });

        $('#id_taskcfg_list_layer').on('mouseleave', 'input', function(){
            $(this).addClass('desc_input');
        });

        $(document).on('click.PT.addcfg', '.add_new_cfg', function(){
           var cfg_type =$(this).attr('cfg_type');
           if($('#id_new_'+cfg_type).length>0){
               return false;
           }
           var html = template.render('base_taskcfg_tbody_template', {'cfg_type':cfg_type, 'cfg':{'name':'', 'cfg_detail':{}}});
           $('#'+cfg_type+'_cfg_table>tbody').append(html);
        });

        $(document).on('click.PT.save_cfg', '.save_cfg', function(){
            var tag_name = $(this).parent().parent().attr('tag_name');
            if((tag_name===''|| tag_name===undefined)){//如果是新的，配置项从输入框中取出
                tag_name=$(this).parent().siblings('td:first').find('input').val();
            }
            var div_list = $(this).parents('tr:first').find('div'),
                cfg_type = $(this).parents('table:first').attr('cfg_type'),
                cfg_list = [],
                cfg_detail = null;
            for(var i=0;i<div_list.length;i++){
                var temp_cfg = {};
                var input_list = $(div_list[i]).find('input');
                for(var j=0;j<input_list.length;j++){
                    var temp_keyname = $(input_list[j]).attr('key_name');
                    if(temp_keyname=='instrcn_list'){
                        var instrcn_list = [];
                        $(input_list[j]).siblings('ul').find('li').each(function(){
                           instrcn_list.push($(this).text());
                        });
                        temp_cfg[temp_keyname] = instrcn_list;
                    }else{
                        temp_cfg[temp_keyname] = $(input_list[j]).val();
                    }
                }
                cfg_list.push(temp_cfg);
            }
            if (cfg_type === 'mnt') {
                cfg_detail = cfg_list[0];
                var error_msg = check_mnt_cfg(cfg_detail);
                if (error_msg) {
                    PT.alert(error_msg);
                    return false;
                }
            }else{
                cfg_detail = cfg_list;
            }
            if(cfg_list.length>0 && tag_name!=='' && tag_name!==undefined){
                PT.sendDajax({'function':'crm_save_cfg', 'tag_name':tag_name, 'cfg_detail':$.toJSON(cfg_detail), 'cfg_type':cfg_type});
            }else{
                PT.alert("配置项尚未完整输入！");
                return false;
            }
        });

        $(document).on('click.PT.delete_cfg', '.delete_cfg', function(){
            var delete_cfg = function(obj){
                var tag_name = $(obj).attr('tag_name');
                if(tag_name!==''&& tag_name!==undefined){
                    PT.sendDajax({'function':'crm_delete_cfg', 'tag_name':tag_name});
                }
                $(obj).remove();
            };
            PT.confirm("确定要删除当前配置吗？关联问题尚未处理哦！", delete_cfg, [$(this).parent().parent()]);
        });

        $(document).on('click.PT.add_cfg', '.add_cfg', function(){
            var tag_name = $(this).parent().parent().attr('tag_name');
            var cfg_type = $(this).parent().parent().parent().parent().attr('cfg_type');
            var cfg_detail = {};
            if(cfg_type=='stgy'){
                cfg_detail['instrcn_list'] = [];
            }
            var html = template.render('base_cfgdetail_template', {'name':tag_name, 'cfg_type':cfg_type, 'cfg_detail':cfg_detail});
            $(this).parent().siblings('td:eq(-1)').append(html);
        });

        $(document).on('click.PT.edit_instruction','.edit_instrcn', function(){
            $('ul.instrcn_list').removeClass('edit_style').addClass('view_style');
            var instrcn_obj = $(this).parent().find('ul.instrcn_list');
            instrcn_obj.removeClass('view_style').addClass('edit_style');
            instrcn_obj.sortable({axis:'x', containment:'parent'});

            var expand_obj = $('#id_instrcn_list_div .expand');
            if(expand_obj.length>0){
                $('#id_instrcn_list_div .portlet-body').css('display','block');
                $('#id_instrcn_list_div .tools a').removeClass('expand');
                $('#id_instrcn_list_div .tools a').addClass('collapse');
            }

            var instrcn_list = [];
            var obj_list = $(instrcn_obj).find('li');
            for(var j=0;j<obj_list.length;j++){
                instrcn_list.push($(obj_list[j]).text());
            }
            var cb_list = $('input[name=instrcn_checkbox]');
            for(var i=0;i<cb_list.length;i++){
                if(instrcn_list.indexOf($(cb_list[i]).attr('id'))!=-1){
                    $(cb_list[i]).attr('checked', 'checked');
                }else{
                    $(cb_list[i]).removeAttr('checked');
                }
            }
        });

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

        $(document).on('click.PT.sort_up', '.sort', function(){
            var tag_name = $(this).parent().parent().attr('name');
            var all_obj = $('div[name='+tag_name+']');
            var index = $(this).parent().parent().index();
            var new_index =index - parseInt($(this).attr('move'));
            change_order(index,new_index, all_obj);
        });

    };


    var check_mnt_cfg = function (cfg_dict) {
        var msg_dict = {'cycle':'周期', 'opt':'操作', 'stgy':'策略'};
        for (var prop in cfg_dict) {
            var jq_table = $('#'+prop+'_cfg_table');
                // jq_tds = jq_table.find('tbody>tr').find('td:first'),
                // t_list = $.map(jq_tds, function(obj){return obj.text();});
            if (jq_table.find('tr[tag_name="'+cfg_dict[prop]+'"]').length === 0){
                return msg_dict[prop] + '填写错误';
            }
        }
        return '';
    };

    return {

        init_dom:init_dom,

        display_cfg_dialog:function(result_dict){
            var content = template.render('task_config_template', {'stgy_cfg_list':result_dict.stgy_cfg_list, 'cycle_cfg_list':result_dict.cycle_cfg_list, 'opt_cfg_list':result_dict.opt_cfg_list,
                                                                   'instrcn_list':result_dict.instrcn_list, 'shop_id':result_dict.shop_id, 'campaign_id':result_dict.campaign_id});
            $('#task_config_layer').html(content);
            $.fancybox.open([{href:'#task_config_layer'}], {helpers:{
                title : {type : 'outside'},
                overlay : {closeClick: false},
            }});
            $('#'+result_dict.stgy_cfg).attr('checked', 'checked');
            $('#'+result_dict.cycle_cfg).attr('checked', 'checked');
            $('#'+result_dict.opt_cfg).attr('checked', 'checked');
            PT.InstructionList.bind_event('.instrcn_list.edit_style');
        },
        persistent_new_cfg:function(cfg_type){
            var tag_name = $('#id_new_'+cfg_type).val();
            var obj = $('#id_new_'+cfg_type).parent().parent();
            $(obj).find('td:first input').remove();
            $(obj).find('td:first').text(tag_name);
            $(obj).attr('tag_name', tag_name);
        },

    };
}();
