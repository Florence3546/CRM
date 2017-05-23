PT.namespace('NcrmAddClient');
PT.NcrmAddClient = function() {

    var init_dom = function() {

            $(".form_search_url").click(function(){
                var last_search_type = $("#last_search_type").val();
                var form_id = "#condition_search";
                if( last_search_type == "query" ){
                    form_id = "#query_form"
                }
                
                var obj = $(this);
                var form_obj = $(form_id);
                var submit_url = obj.attr('submit_url');
                form_obj.attr('action',submit_url);
                form_obj.submit();
            });

            $("#search_cond_btn").click(function(){
                var form_obj = $("#condition_search");
                var client_group_id = $("#client_group_id").val();
                form_obj.attr('action',"/ncrm/add_client/"+client_group_id+"/1/");
                form_obj.submit();
            });

            $("#id_list_btn").click(function(event){
                var obj = $("#search_id_list");
                if ( obj.css('display') == 'none' ){
                    obj.show();
                } else {
                    obj.hide();
                }
                event.preventDefault();
            });

            $('#search_query').on('click', function(event) {
                event.preventDefault();
                PT.confirm('该操作比较耗时，请耐心等待',function(){
                    PT.show_loading('正在查询');
                    $('#search_area_box form').submit();
                })
            });

            $('#save_query').on('click', function() {
                var query = $.trim($('#query').val()),
                    client_group_id = $('#client_group_id').val(),
                    data;
                if (query != '') {

                    data = {
                        'function': 'ncrm_save_query',
                        'client_group_id': client_group_id,
                        'query': query,
                        'call_back': 'PT.NcrmAddClient.save_query_call_back'
                    }
                    PT.sendDajax(data);
                } else {
                    PT.alert('查询条件不能为空');
                }
            });

            $('#generate_id_list').on('click', function() {
                var query = $.trim($('#query').val()),
                    client_group_id = $('#client_group_id').val(),
                    data;

                if (query != '') {
                    data = {
                        'function': 'ncrm_generate_id_list',
                        'client_group_id': client_group_id,
                        'query': query,
                        'call_back': 'PT.NcrmAddClient.generate_id_list_call_back'
                    }
                    PT.sendDajax(data);
                } else {
                    PT.alert('查询条件不能为空');
                }
            });

            // 复选框事件
            $('input.father_box').on('change', function(e) {
                var ev = e || window.event,
                    area_id = $(this).attr('link'),
                    there = this;
                ev.stopPropagation();
                if (area_id != undefined) {
                    $('#' + area_id).find('.kid_box').attr('checked', there.checked);
                }
                calc_checkbox();
            });

            //子复选框事件
            $('input.kid_box').on('change', function() {
                calc_checkbox();
            });

            //批量提交id
            $('#bluk_submit_ids').on('click', function() {
                var ids = get_checked_ids(),
                    client_group_id = $('#client_group_id').val();
                if (ids.length) {
                    PT.show_loading('正在添加');
                    PT.sendDajax({
                        'function': 'ncrm_save_id_list',
                        'id_list': $.toJSON(ids),
                        'client_group_id': client_group_id,
                        'call_back': 'PT.NcrmAddClient.save_ids_call_back'
                    });
                } else {
                    PT.alert('请选择要保存用户')
                }
            });

            // 打开手动批量添加页面
            $('#open_manual_layout').on('click', function() {
                // $("#id_list_textarea").val(""); 暂不做清理工作
                $("#id_manual_add_customer_layout").modal();
            });

            $('#manual_submit_ids').on('click', function() {
                var id_list_text = $("#id_list_textarea").val();
                var id_list = id_list_text.replace(/\s/g,'').replace(/，/g,',');

                //if(id_list.split(',').length> 1000){
//                    PT.alert("添加用户ID太多了，请适当的删减"); 暂不提供该校验
//                }

                if(id_list == ""){
                    PT.alert('客户ID列表 不能为空');
                } else {
	                if (/^[\d,]+$/.test(id_list)){
	                    var client_group_id = $("#client_group_id").val();
	                    PT.show_loading('正在批量添加客户到当前用户群');
	                    PT.sendDajax({
	                        'function': 'ncrm_manual_add_customers',
	                        'id_list': id_list,
	                        'client_group_id': client_group_id,
	                        'call_back': 'PT.NcrmAddClient.manual_add_customers_bak'
	                    });
	                } else {
	                    PT.alert("客户列表基本验证无效");
	                }
                }
            });

            //批量删除
            $('#bluk_del_submit_ids').on('click', function() {
                var ids = get_checked_ids(),
                    client_group_id = $('#client_group_id').val();
                if (ids.length) {
                    PT.show_loading('正在删除');
                    PT.sendDajax({
                        'function': 'ncrm_del_id_list',
                        'id_list': $.toJSON(ids),
                        'client_group_id': client_group_id,
                        'call_back': 'PT.NcrmAddClient.del_ids_call_back'
                    });
                } else {
                    PT.alert('请选择要保存用户')
                }
            });

            //单个提交
            $('.singel_add').on('click', function() {
                var ids = [],
                    client_group_id = $('#client_group_id').val();

                ids.push($(this).closest('tr').attr('shop_id'));
                PT.show_loading('正在添加');
                PT.sendDajax({
                    'function': 'ncrm_save_id_list',
                    'id_list': $.toJSON(ids),
                    'client_group_id': client_group_id,
                    'call_back': 'PT.NcrmAddClient.singel_save_ids_call_back'
                });
            });

            //单个删除
            $('.singel_del').on('click', function() {
                var ids = [],
                    client_group_id = $('#client_group_id').val();

                ids.push($(this).closest('tr').attr('shop_id'));
                PT.show_loading('正在删除');
                PT.sendDajax({
                    'function': 'ncrm_del_id_list',
                    'id_list': $.toJSON(ids),
                    'client_group_id': client_group_id,
                    'call_back': 'PT.NcrmAddClient.singel_del_ids_call_back'
                });
            });

            //显示帮助文档
            $('#show_help').on('click',function(){
                $('#help_content').toggleClass('hide');
            });


            $('.tips').tooltip();

        },

        //计算选中的用户
        calc_checkbox = function() {
            $('#checked_num').text($('input.kid_box:checked').length);
        },
        get_checked_ids = function() {
            var ids = [];
            $('input.kid_box:checked').each(function() {
                ids.push($(this).closest('tr').attr('shop_id'))
            });

            return ids;
        };

    return {
        init: function() {
            init_dom();
        },
        save_query_call_back: function(json) {
            if (json.error) {
                PT.alert(json.error);
            } else {
                PT.alert('保存成功');
            }
        },
        generate_id_list_call_back: function(json) {
            if (json.error) {
                PT.alert(json.error);
            } else {
                PT.alert('生成成功');
            }
        },
        save_ids_call_back: function(json) {
            if (json.error) {
                PT.alert(json.error);
            } else {
                for (var i=0;i<json.id_list.length;i++){
                    $('#singel_add_'+json.id_list[i]).replaceWith('<span class="gary">已添加</span>')
                }
            }
        },
        singel_save_ids_call_back:function(json){
            if (json.error) {
                PT.alert(json.error);
            } else {
                for (var i=0;i<json.id_list.length;i++){
                    $('#singel_add_'+json.id_list[i]).replaceWith('<span class="gary">已添加</span>')
                }
            }
        },
        del_ids_call_back: function(json) {
            if (json.error) {
                PT.alert(json.error);
            } else {
                window.location.reload();
            }
        },
        manual_add_customers_bak: function(json) {
            if (json.error) {
                PT.alert(json.error);
            } else {
                $("#id_manual_add_customer_layout .close_model").click();
                var no_exsited = json.data[0];
                var is_exsited = json.data[1];
                var success  = json.data[2];
                PT.alert("已成功导入客户 "+success+" 人,   其中无效客户 "+no_exsited+"人,   已存在客户"+is_exsited+" 人.");
            }
        },
        singel_del_ids_call_back: function(json) {
            if (json.error) {
                PT.alert(json.error);
            } else {
                window.location.reload();
            }
        },


    }
}();
