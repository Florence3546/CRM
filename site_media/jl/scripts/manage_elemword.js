PT.namespace('ManageElemword');
PT.ManageElemword = function () {
    var item_id = $('#item_id').val();
    var adgroup_id = $('#adgroup_id').val();
    var campaign_id = $('#campaign_id').val();
    var init_dom = function () {
        // 初始化 inputtags
        $('#m_prdtword').tagsInput({
            width: 800,
            height: 40,
            defaultText:'以回车键确定一个词根，不要输入任何符号'
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
            height: 105,
            defaultText:'以回车键确定一个词根，不要输入任何符号'
        });
        // 打开fancybox
        $('#manage_elemword').click(function () {
            $.fancybox.open([{href:'#div_manage_elemword'}], {helpers:{
                title : {type : 'outside'},
                overlay : {closeClick: false}
            }});
            var loaded = $('#div_manage_elemword').attr('loaded');
            if (loaded=='0') {
                PT.show_loading('正在加载');
                PT.sendDajax({'function':'web_manage_elemword', 'item_id':item_id});
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
                PT.sendDajax({'function':'web_submit_bwords',
                                         'item_id':item_id,
                                         'blackwords':blackword,
                                         'save_or_update':0,
                                         'common_table_flag':$('#common_table').length,
                                         'namespace':'ManageElemword'
                                         });
            };
            if (blackword==org_blackword) {
                PT.alert('您还未做出任何修改！');
            } else if (blackword) {
                PT.confirm('注意：如果宝贝在其他计划下推广，包含屏蔽词的关键词也会被删除，确认删除吗？', submit_bwords, [], null, null, [], null, ['确定删除', '返回']);
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
      $('#m_prdtword').change(function(){
        var obj=$('#save_elemword_ps');
        if($('#m_prdtword').val()!==$('#org_m_prdtword').val()||$('#m_saleword').val()!==$('#org_m_saleword').val()){
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
    };

    return {
        init: init_dom,
        save_bword_callback: function (result) {
            if (result==1) {
                $('#org_m_blackword').val($('#m_blackword').val());
                PT.alert('保存成功！');
            } else {
                PT.alert('保存失败，请联系顾问！');
            }
        },
        submit_bwords_callback: function () {
            $('#org_m_blackword').val($('#m_blackword').val());
            PT.alert('设置成功！');
        },
        save_elemword_callback: function (result, wordtype) {
            if (result==1) {
                $('#org_m_'+wordtype).val($('#m_'+wordtype).val());
                PT.alert('保存成功！');
            } else {
                PT.alert('保存失败，请联系顾问！');
            }
        },
        restore_elemword_callback: function (result, prdtword_data_str,sale_data_str) {
            if (result==1) {
                $('#m_prdtword').importTags(prdtword_data_str);
                $('#org_m_prdtword').val(prdtword_data_str);

                $('#m_saleword').importTags(sale_data_str);
                $('#org_m_saleword').val(sale_data_str);

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
            for (var wordtype in data) {
                $('#org_m_'+wordtype).val(data[wordtype]);
            }
            //zhongjinfeng 分开写是应为importTags会触发change,而org_m_%s里的值还没赋值上去，会出现保存按钮状态问题
            for (var wordtype in data) {
                $('#m_'+wordtype).importTags(data[wordtype]);
            }
            $('#div_manage_elemword').attr('loaded', '1');
        }
    };
} ();
