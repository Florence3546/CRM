PT.namespace('InstructionList');
PT.MntCfg = function(){

    return {
        init_dom:function(){
            PT.sendDajax({'function':'crm_get_mnt_cfg'});
        },

        display_info:function(instrcn_list, mnt_cfg_list, stgy_cfg_list, cycle_cfg_list, opt_cfg_list){
            var mnt_html = template.render('id_base_taskcfg_template', {'cfg_list':mnt_cfg_list, 'cfg_type':'mnt'});
            var cycle_html = template.render('id_base_taskcfg_template', {'cfg_list':cycle_cfg_list, 'cfg_type':'cycle'});
            var opt_html = template.render('id_base_taskcfg_template', {'cfg_list':opt_cfg_list, 'cfg_type':'opt'});
            var stgy_html = template.render('id_base_taskcfg_template', {'cfg_list':stgy_cfg_list, 'cfg_type':'stgy'});
            $('#id_taskcfg_list_layer').html(mnt_html+cycle_html+opt_html+stgy_html);
            PT.TaskCfgList.init_dom();

            $('#id_instrcn_list_layer').html(template.render('id_instrcn_porlet_template', {'instrcn_list':instrcn_list}));
            $('#id_instrcn_list_div .portlet-body').css('display','block');
            $('#id_instrcn_list_div .tools a').removeClass('expand');
            $('#id_instrcn_list_div .tools a').addClass('collapse');
            PT.InstructionList.bind_event('.instrcn_list.edit_style');
            $('#cycle_cfg_table, #opt_cfg_table, #stgy_cfg_table').find('input[type="radio"]').remove();

        }
    };
}();
