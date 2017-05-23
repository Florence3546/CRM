/**
 * Created by Administrator on 2015/10/6.
 */
define(['jl6/site_media/widget/alert/alert','jl6/site_media/widget/confirm/confirm',
    'jl6/site_media/widget/loading/loading','jl6/site_media/widget/ajax/ajax',
    "jl6/site_media/widget/tagEditor/tagEditor"],function(alert,confirm,loading,ajax,tagEditor){
    var item_id = 0;
    var adgroup_id = 0;
    var campaign_id = $('#campaign_id').val();
    var prdtword,blackword;
    var init = function(){

        $(document).on('click', '.open_manage_elemword', function () {
            $('#div_manage_elemword').modal();
            var data = $(this).data('init_data');
            if (data===undefined) {
                item_id = $(this).attr('id').split('_')[2];
                adgroup_id = $(this).attr('adg_id');
                if (Number(item_id) === undefined) {
                    alert.show({'backdrop':false,'body':'请刷新页面重试'});
                    return;
                }

                ajax.ajax('manage_elemword',{ 'item_id':item_id},manage_elemword_callback);
               // PT.sendDajax({'function':'web_manage_elemword', 'item_id':item_id});
            }else{
                item_id = $(this).attr('id').split('_')[2];
                adgroup_id = $(this).attr('adg_id');
                var cur_word = data.prdtword;
                var cur_tags = prdtword.getTags();
                for(var i=0;i<cur_tags.length;i++){
                    if(cur_word.indexOf(cur_tags[i])<0){
                        prdtword.removeTag(cur_tags[i]);
                    }
                }
               // init_data(data);
            }
        });

        var manage_elemword_callback = function(data){
            var datas = data.data;
            $('#manage_elemword_'+item_id).data('init_data', datas);
            var words = datas['prdtword'].split(',');
            $("#old_m_prdtword").val(datas['prdtword']);
            var prdtword_options = {
                placeholder: '输入产品词，回车确定',
                initialTags:words,
                onChange:function(field, editor, tags){
                    var old_m_prdtword = $("#old_m_prdtword").val();
                    var new_m_prdtword = tags;
                    if(new_m_prdtword.toString() == old_m_prdtword){
                        $('#save_m_prdtword').addClass('disabled');
                    }else{
                        $('#save_m_prdtword').removeClass('disabled');
                    }
                }
            }
            prdtword = tagEditor.tagEditor($('#m_prdtword'),prdtword_options);

            $("#old_m_blackword").val(datas['blackword']);
            words = datas['blackword'].split(',');
            var blackword_options = {
                placeholder: '输入屏蔽词，回车确定',
                initialTags:words,
                onChange:function(field, editor, tags){
                    var old_m_blackword = $("#old_m_blackword").val();
                    var new_m_blackword = tags;
                    if(new_m_blackword.toString() == old_m_blackword){
                        $('#save_m_blackword').addClass('disabled');
                    }else{
                        $('#save_m_blackword').removeClass('disabled');
                    }
                }
            }
            blackword = tagEditor.tagEditor($('#m_blackword'),blackword_options);
        };

        // 保存产品词
        $('#save_m_prdtword').click(function () {
            var old_m_prdtword = $("#old_m_prdtword").val();
            var new_m_prdtword = prdtword.getTags();
            if(new_m_prdtword.toString() == old_m_prdtword){
                alert.show({'backdrop':false,'body':'您还未做出任何修改！'});
                return false;
            }
            var elemword_dict = {prdtword:new_m_prdtword};
            save_modifed_data(elemword_dict);
            loading.show('正在保存产品词');
            ajax.ajax('save_prdtword',{'item_id':item_id,
                    'adgroup_id':adgroup_id,
                    'campaign_id':campaign_id,
                    'prdtword':new_m_prdtword.toString()},
                    function(data){
                        loading.hide();
                        if (data.result==1) {
                            alert.show({'backdrop':false,'body':'保存成功！'});
                            $("#old_m_prdtword").val(new_m_prdtword.toString());
                            $('#save_m_prdtword').addClass('disabled');
                        }
                    });
        });

        // 恢复产品词默认值
        $('#restore_elemword_ps').click(function () {
            loading.show('正在恢复默认值');
            ajax.ajax('restore_elemword',{'item_id':item_id},function(data){
                if (data.result==1) {
                    loading.hide();
                    alert.show({'backdrop':false,'body':'恢复成功！'});
                    $('#m_prdtword').tagEditor('destroy');
                    $('#old_m_prdtword').val(data.prdtword_data_str);

                    var prdtword_options = {
                        placeholder: '输入产品词，回车确定',
                        initialTags:data.prdtword_data_str.split(','),
                        onChange:function(field, editor, tags){
                            var old_m_prdtword = $("#old_m_prdtword").val();
                            var new_m_prdtword = tags;
                            if(new_m_prdtword.toString() == old_m_prdtword){
                                $('#save_m_prdtword').addClass('disabled');
                            }else{
                                $('#save_m_prdtword').removeClass('disabled');
                            }
                        }
                    }
                    prdtword = tagEditor.tagEditor($('#m_prdtword'),prdtword_options);

                    update_init_data({'prdtword': data.prdtword_data_str});
                    $('#save_m_prdtword').addClass('disabled');

                }
            });
        });

        // 屏蔽词
        $('#save_m_blackword').click(function () {
            var old_m_blackword = $("#old_m_blackword").val();
            var new_m_blackword = blackword.getTags();
            if(new_m_blackword.toString() == old_m_blackword){
                alert.show({'backdrop':false,'body':'您还未做出任何修改！'});
                return false;
            }
            confirm.show({
                body:"注意：如果宝贝在其他计划下推广，包含屏蔽词的关键词也会被删除，确定要删除吗？",
                backdrop:false,
                okHidden:function(){
                    var elemword_dict = {blackword:new_m_blackword};
                    save_modifed_data(elemword_dict);
                    loading.show('正在保存屏蔽词');
                    ajax.ajax('save_bword',{
                            'item_id':item_id,
                            'campaign_id':campaign_id,
                            'adgroup_id':adgroup_id,
                            'save_or_update':0,
                            'common_table_flag':$('#common_table').length,
                            'blackwords':new_m_blackword.toString()},
                            function(data){
                                loading.hide();
                                if(!data.result){
                                    alert.show({'backdrop':false,'body':data.error_msg});
                                    return false;
                                }
                                $("#old_m_blackword").val(new_m_blackword.toString());
                                alert.show({'backdrop':false,'body':'保存成功！'});
                                $('#save_m_blackword').addClass('disabled');
                            });
                }
            });
        });
    };

    var save_modifed_data = function(obj) {
        var jq_data = $('#manage_elemword_'+item_id),
         modifed_data = jq_data.data('init_data');
        for (var prop in obj) {
            modifed_data[prop] = obj[prop];
        }
        jq_data.data('modifed_data', modifed_data);
    };

    var update_init_data = function(obj) {
        if (obj !== undefined) {
            save_modifed_data(obj);
        }
        var jq_data = $('#manage_elemword_'+item_id),
            modifed_data = jq_data.data('modifed_data');
        jq_data.data('init_data', modifed_data);
    };
    return {
        init:init
    }
});