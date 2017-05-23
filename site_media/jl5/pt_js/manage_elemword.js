PT.namespace('ManageElemword');
PT.ManageElemword = function () {
    var item_id = 0;
    var adgroup_id = 0;
    var campaign_id = $('#campaign_id').val();
    var init_dom = function () {

        // 初始化 inputtags
        $('#m_prdtword').tagsInput({
            width: 800,
            height: 100,
            defaultText:'输入产品词，回车确定',
            onChange:function(){$('#m_prdtword').trigger('change');}
        });
        $('#m_propword').tagsInput({
            width: 800,
            height: 105,
            defaultText:'以回车键确定一个词根，不要输入任何符号'
        });
        $('#m_dcrtword').tagsInput({
            width: 800,
            height: 105,
            defaultText:'以回车键确定一个词根，不要输入任何符号'
        });
        $('#m_saleword').tagsInput({
            width: 800,
            height: 40,
            defaultText:'以回车键确定一个词根，不要输入任何符号'
        });
        $('#m_blackword').tagsInput({
            width: 800,
            height: 100,
            defaultText:'输入屏蔽词，回车确定'
        });
        $(document).on('click', '.open_manage_elemword', function () {
            // $.fancybox.open([{href:'#div_manage_elemword'}], {helpers:{
            //     title : {type : 'outside'},
            //     overlay : {closeClick: false}
            // }});
            $('#div_manage_elemword').modal({width:850});
            var data = $(this).data('init_data');
            if (data===undefined) {
                item_id = $(this).attr('id').split('_')[2];
                adgroup_id = $(this).attr('adg_id');
                if (Number(item_id) === undefined) {
                    PT.alert('请刷新页面重试');
                    return;
                }
                PT.show_loading('正在加载');
                PT.sendDajax({'function':'web_manage_elemword', 'item_id':item_id});
            }else{
                item_id = $(this).attr('id').split('_')[2];
                adgroup_id = $(this).attr('adg_id');
                init_data(data);
            }
        });
        // 保存词根
        $('#save_elemword_ps').click(function () {
            var wordtype_list = ['prdtword', 'saleword'];
            var elemword_dict = {};
            var is_modified = false;
            for (var i in wordtype_list) {
                var wordtype = wordtype_list[i];
                var elemword = $('#m_'+wordtype).val();
                var org_elemword = $('#org_m_'+wordtype).val();
                if (elemword!=org_elemword) {
                    elemword_dict[wordtype] = elemword;
                    is_modified = true;
                }
            }
            if (is_modified) {
                PT.show_loading('正在保存词根');
                save_modifed_data(elemword_dict);
                PT.sendDajax({'function':'web_save_all_elemword',
                    'item_id':item_id,
                    'adgroup_id':adgroup_id,
                    'campaign_id':campaign_id,
                    'elemword_dict':$.toJSON(elemword_dict),
                    'namespace':'ManageElemword'
                    });
            } else {
                PT.alert('您还未做出任何修改！');
            }
        });

        // 恢复词根默认值
        $('#restore_elemword_ps').click(function () {
            PT.show_loading('正在恢复默认值');
            PT.sendDajax({'function':'web_restore_elemword',
                'item_id':item_id,
                'namespace':'ManageElemword'
                });
        });
        // 屏蔽词
        $('#save_m_blackword').click(function () {
            var blackword = $('#m_blackword').val();
            var org_blackword = $('#org_m_blackword').val();
            if (blackword!=org_blackword) {
                save_modifed_data({'blackword':blackword});
                PT.show_loading('正在保存屏蔽词');
                PT.sendDajax({'function':'web_save_bword',
                    'item_id':item_id,
                    'blackwords':blackword,
                    'namespace':'ManageElemword'
                    });
            } else {
                PT.alert('您还未做出任何修改！');
            }
        });
        $('#save_del_m_blackword').click(function () {
            var blackword = $('#m_blackword').val();
            var org_blackword = $('#org_m_blackword').val();
            var submit_bwords = function () {
                PT.show_loading('正在保存屏蔽词并删除相关关键词');
                save_modifed_data({'blackword':blackword});
                PT.sendDajax({'function':'web_submit_bwords',
                                         'campaign_id':campaign_id,
                                         'adgroup_id':adgroup_id,
                                         'item_id':item_id,
                                         'blackwords':blackword,
                                         'save_or_update':0,
                                         'common_table_flag':$('#common_table').length,
                                         'namespace':'ManageElemword'
                                         });
            };
            $('#div_manage_elemword').modal('shadeIn');
            if (blackword==org_blackword) {
                PT.alert('您还未做出任何修改！');
            } else if (blackword) {
                PT.confirm('注意：如果宝贝在其他计划下推广，包含屏蔽词的关键词也会被删除，确认删除吗？', submit_bwords, [], null, function(){$('#div_manage_elemword').modal('shadeOut');}, [], null, ['确定删除', '返回']);
            } else {
                submit_bwords();
            }
        });
        // 保存所有词根
        $('#save_all_elemword').click(function () {
            var wordtype_list = ['prdtword', 'propword', 'dcrtword', 'saleword', 'blackword'];
            var elemword_dict = {};
            var is_modified = false;
            for (var i in wordtype_list) {
                var wordtype = wordtype_list[i];
                var elemword = $('#m_'+wordtype).val();
                var org_elemword = $('#org_m_'+wordtype).val();
                if (elemword!=org_elemword) {
                    elemword_dict[wordtype] = elemword;
                    is_modified = true;
                }
            }
            if (is_modified) {
                PT.show_loading('正在保存词根');
                PT.sendDajax({'function':'web_save_all_elemword',
                    'item_id':item_id,
                    'adgroup_id':adgroup_id,
                    'campaign_id':campaign_id,
                    'elemword_dict':$.toJSON(elemword_dict),
                    'namespace':'ManageElemword'
                    });
            } else {
                PT.alert('您还未做出任何修改！');
            }
        });

      //判断产品词是否为空改变保存按钮状态
      $('#m_prdtword').on('change',function(){
        var obj=$('#save_elemword_ps');
        if($('#m_prdtword').val()!==$('#org_m_prdtword').val()){
          obj.removeClass('disabled');
        }else{
          obj.addClass('disabled');
        }
      });

      //判断卖点词是否为空改变按钮状态
      $('#m_saleword').change(function(){
        var obj=$('#save_elemword_ps');
        if($('#m_prdtword').val()!==$('#org_m_prdtword').val()||$('#m_saleword').val()!==$('#org_m_saleword').val()){
          obj.removeClass('disabled');
        }else{
          obj.addClass('disabled');
        }
      });

      $('.tooltips').tooltip({html:true});
    };

    var init_data = function (data) {
        for (var wordtype in data) {
            $('#org_m_'+wordtype).val(data[wordtype]);
        }
        //zhongjinfeng 分开写是应为importTags会触发change,而org_m_%s里的值还没赋值上去，会出现保存按钮状态问题
        for (var wordtype in data) {
            $('#m_'+wordtype).importTags(data[wordtype]);
        }
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
        init: function() {
            init_dom();
        },
        save_bword_callback: function (result) {
            if (result==1) {
                $('#org_m_blackword').val($('#m_blackword').val());
                update_init_data();
                PT.alert('保存成功！');
            } else {
                PT.alert('保存失败，请联系顾问！');
            }
        },
        submit_bwords_callback: function (data) {
            $('#org_m_blackword').val($('#m_blackword').val());
            update_init_data();
            PT.alert('设置成功！');
        },
        save_elemword_callback: function (result, wordtype) {
            if (result==1) {
                $('#org_m_'+wordtype).val($('#m_'+wordtype).val());
                update_init_data();
                PT.alert('保存成功！');
            } else {
                PT.alert('保存失败，请联系顾问！');
            }
        },
        restore_elemword_callback: function (result, prdtword_data_str,sale_data_str) {
            if (result==1) {
                $('#m_prdtword').importTags(prdtword_data_str);
                $('#org_m_prdtword').val(prdtword_data_str);

                // $('#m_saleword').importTags(sale_data_str);
                // $('#org_m_saleword').val(sale_data_str);
                update_init_data({'prdtword': prdtword_data_str});
                $('#save_elemword_ps').addClass('disabled');
                PT.alert('恢复成功！');
            } else {
                PT.alert('恢复失败，请联系顾问！');
            }
        },
        save_all_elemword_callback: function (result, wordtype_list) {
            if (result==1) {
                for (var i in wordtype_list) {
                    var wordtype = wordtype_list[i];
                    $('#org_m_'+wordtype).val($('#m_'+wordtype).val());
                }
                PT.alert('保存成功！');
                $('#save_elemword_ps').addClass('disabled');
            } else {
                PT.alert('保存失败，请联系顾问！');
            }
        },
        manage_elemword_callback: function (data) {
            $('#manage_elemword_'+item_id).data('init_data', data);
            init_data(data);
        }
    };
} ();
