PT.namespace('NcrmAdvanceQuery');
PT.NcrmAdvanceQuery = function() {
    
    var loading_client_group = function(){
        if($("#id_subscribe_sale_user option").length > 1){
            var psuser_id = $("#psuser_id").val();
            var obj = $("#id_subscribe_sale_user");
            obj.val(psuser_id);
            obj.change();
        } else {
            setTimeout(function(){
                loading_client_group();
            }
            ,400);
        }
    }
    var init_dom = function() {
            loading_client_group();
            
            $("#id_group_client").change(function(){
                var group_client_id = $(this).val();
                $("#id_list_textarea").attr("client_group_id",group_client_id);
            });
            
            $("#create_client_group_submit").click(function(){
                var psuser_id = $("#client_group_psuser_id").attr('psuser_id'); // 此处一定会有psuser_id 因而无需判断
                var title = $("#client_group_title").val();
                PT.sendDajax({
                    'function': 'ncrm_creaete_client_group',
                    'psuser_id': psuser_id,
                    'title': title,
                    'call_back': 'PT.NcrmAdvanceQuery.creaete_client_group_back'
                });
            });
            
            $("#create_client_group").click(function(){
                var select_obj = $("#id_subscribe_sale_user option:checked");
                var title_obj = $("#client_group_psuser_id");
                $("#client_group_title").val("");
                if(parseInt(select_obj.val())>0){
	                title_obj.attr('psuser_id',select_obj.val());
	                title_obj.text(select_obj.text());
	                $("#id_create_client_group_layout").modal();
                } else {
                    PT.alert('请选择需要创建客户群的员工');
                }
            });
            
            $("#id_subscribe_sale_user").bind('change',function(){
                var obj = $(this);
                var user_id = parseInt(obj.val());
                if(user_id > 0){
                      PT.sendDajax({
                        'function': 'ncrm_get_client_group_info',
                        'user_id': user_id,
                        'call_back': 'PT.NcrmAdvanceQuery.client_group_info_back'
                    });
                } 
            });
            
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
                form_obj.attr('action',"/ncrm/allocate_client/1/");
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
                        'call_back': 'PT.NcrmAdvanceQuery.save_query_call_back'
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
                        'call_back': 'PT.NcrmAdvanceQuery.generate_id_list_call_back'
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
                    client_group_id = $("#id_group_client option:checked").val();
                if (parseInt(client_group_id) > 0) {
	                if (ids.length) {
	                    PT.show_loading('正在添加');
	                    PT.sendDajax({
	                        'function': 'ncrm_save_id_list',
	                        'id_list': $.toJSON(ids),
	                        'client_group_id': client_group_id,
	                        'call_back': 'PT.NcrmAdvanceQuery.save_ids_call_back'
	                    });
	                } else {
	                    PT.alert('请选择要保存用户');
	                }
                } else {
                    PT.alert('请选择客户群');
                }
            });
            
            // 提交所有查询结果
            $('#submit_all_ids').click(function(){
                var last_search_type = $("#last_search_type").val();
                var client_group_id = $("#id_group_client option:checked").val();
                if (parseInt(client_group_id) > 0) {
	                if(last_search_type == 'query'){
	                   PT.sendDajax({
                            'function': 'ncrm_add_all_query_customer',
                            'client_group_id': client_group_id,
                            'call_back': 'PT.NcrmAdvanceQuery.submit_all_customer_back'
                        });
	                } else if (last_search_type == 'unquery'){
	                   var shop_id = $("#condition_search input[name='shop_id']").val();
	                   if(parseInt(shop_id) > 0 ){
	                       PT.sendDajax({
	                            'function': 'ncrm_add_all_unquery_customer',
	                            'shop_id': shop_id,
	                            'nick': $("#condition_search input[name='nick']").replace(/\s/g,'').val(),
	                            'qq': $("#condition_search input[name='qq']").replace(/\s/g,'').val(),
	                            'phone': $("#condition_search input[name='phone']").replace(/\s/g,'').val(),
	                            'id_list_textarea': $("#condition_search textarea[name='id_list_textarea']").replace(/\s/g,'').val(),
	                            'client_group_id': client_group_id,
	                            'call_back': 'PT.NcrmAdvanceQuery.submit_all_customer_back'
                            });
	                   } else {
	                       PT.alert("ID 必须为数字！")
	                   }
	                } else {
	                    PT.alert("无任何数据用于提交！");
	                }
	            } else {
	               PT.alert('请选择客户群');
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
                        'call_back': 'PT.NcrmAdvanceQuery.del_ids_call_back'
                    });
                } else {
                    PT.alert('请选择要保存用户')
                }
            });

            //单个提交
            $('.singel_add').on('click', function() {
                var ids = [],
                     client_group_id = $("#id_group_client option:checked").val();
                
                if(parseInt(client_group_id) > 0){
                    ids.push($(this).closest('tr').attr('shop_id'));
	                PT.show_loading('正在添加');
	                PT.sendDajax({
	                    'function': 'ncrm_save_id_list',
	                    'id_list': $.toJSON(ids),
	                    'client_group_id': client_group_id,
	                    'call_back': 'PT.NcrmAdvanceQuery.singel_save_ids_call_back'
	                });
                } else {
                    PT.alert("请选择客户群！");
                }
                
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
                    'call_back': 'PT.NcrmAdvanceQuery.singel_del_ids_call_back'
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
                PT.alert('添加完成！');
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
        singel_del_ids_call_back: function(json) {
            if (json.error) {
                PT.alert(json.error);
            } else {
                window.location.reload();
            }
        },
        client_group_info_back:function(json){
             if (json.error) {
                PT.alert(json.error);
            } else {
                var client_group_infos = json.infos;
                var title = "--- 无客服群 ---";
                if(client_group_infos.length){
                    title = "--- 客户群列表 ---";
                }
                var html = template.render('group_client_option',{'id':0,'title':title});
                for(var i = 0 ; i < client_group_infos.length ; i ++){
	                html += template.render('group_client_option',client_group_infos[i]);
                }
                var aim_obj = $("#id_group_client");
                aim_obj.html(html);
                aim_obj.show();
                
                var client_group_id = $("#client_group_id").val();
                if (aim_obj.find("option[value="+client_group_id+"]").length > 0 ){
                    aim_obj.val(client_group_id);
                }
                
            }
        },
        creaete_client_group_back:function(json){
            if (json.error) {
                PT.alert(json.error);
            } else {
                var html = template.render('group_client_option',json.data);
                $("#id_group_client").append(html);
                $("#id_create_client_group_layout .close_model").click();
            }
        },
        submit_all_customer_back:function(json){
            if (json.error) {
                PT.alert(json.error);
            } else {
                PT.alert('添加完成！');
            }
        }
    }
}();
