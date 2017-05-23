PT.namespace('WorkbenchPhoneSaler');
PT.WorkbenchPhoneSaler = function() {

    var init_dom = function() {

        //日期时间选择器
        require(['dom', 'gallery/datetimepicker/1.1/index'], function(DOM, Datetimepicker) {
            var b, c;
            b = new Datetimepicker({
                start: '#id_subscribe_start_time',
                timepicker: false,
                closeOnDateSelect : true
            });
            c = new Datetimepicker({
                start: '#id_subscribe_end_time',
                timepicker: false,
                closeOnDateSelect : true
            });

            new Datetimepicker({
                start: '.time',
                timepicker: false,
                closeOnDateSelect : true
            });

        });

        $("#workbanch_search_form .search_submit").click(function(){
            var form_obj = $("#workbanch_search_form");
            var search_flag = $(this).attr('search_flag');
            if(search_flag == 1){
                var is_all_null = true;
                var form_attrs = ['nick','shop_id','qq','phone','address','note'];
                var form_obj = $("#workbanch_search_form");
                for(var i = 0 ; i < form_attrs.length ; i ++){

                    var form_attr = form_obj.find('[name='+form_attrs[i]+']');
                    if(form_attr.length > 0){
                        var val = form_attr.val().replace(/\s/g,'');
                        if(val != ""){
                            is_all_null = false;
                        }
                    }
                }

                if ( is_all_null ){
                    PT.alert("应用全局搜索时，请填写必要参数....");
	                return false;
                }
            }
            form_obj.find('input[name=search_global_swith]').val(search_flag);
            form_obj.submit();
        });

        var insert_prev_tr = function(tr_obj,template_id, data){
            var html = template.render(template_id,data);
            tr_obj.before(html);
            var last_obj = tr_obj.prev();

            last_obj.find('.remove_currow').click(function(){
               var obj = $(this);
               var i = 7;
               for( var i = 7 ; i > 0 ; i --){
                   obj = obj.parent();
                    if( obj[0].tagName == "TR" && obj.find("td[colspan=5]").length >0){
                       obj.remove();
                       break;
                    }
               }
            });

            last_obj.find(".auto_genarate_note").click(function(){
                var obj = $(this);
                var note_title = $(this).val();

                var opar_obj = obj.parent().parent().parent().parent().find(".contact_note_textarea");
                var cur_text = opar_obj.val();
                var is_checked = obj.attr('checked');
                if(is_checked == undefined){
                   cur_text = cur_text.replace(note_title,"");
                   opar_obj.val(cur_text);
                } else {
                   opar_obj.val(cur_text+note_title);
                }
            });

            // 提交事件
            last_obj.find('.submid_qq').click(function(){
               var cur_obj = $(this).parent();
               var shop_id = cur_obj.attr('shop_id');
               var qq = cur_obj.find('.qq_text').val().replace(/\s/g,"");
               var old_qq = cur_obj.parent().parent().next().find('.qq_flag').text().replace(/\s/g,"");
               if(qq==""){
                   PT.alert("请输入QQ不能为空！");
               } else if (!/^\d+$/.test(qq)){
                   PT.alert("QQ号码必须为数字,不能含有其他字符");
               } else if (qq == old_qq){
                   PT.alert("您输入的QQ号为改变，请重新输入。");
               }else {
                   var note = ""
                   if( old_qq == "-" ){
                        note = "初始化 QQ 号为: "+qq;
                   } else {
                        note = "将 QQ 号由 "+old_qq+" 改变成 : "+qq;
                   }
                   PT.sendDajax({
                        'function': 'ncrm_update_customer',
                        'customer': $.toJSON({'shop_id':shop_id,'qq':qq}),
                        'record_type':"qq",
                        'record_note': note,
                        'call_back': 'PT.WorkbenchPhoneSaler.update_customer_back'
                    });
                }
             });

             last_obj.find('.submit_contact_new').click(function(){
                var obj = $(this);
                var tr_obj = obj.parent().parent();
                var note = tr_obj.parent().find('.contact_note_textarea').val();
                if(note == ""){
                    PT.alert("请备注一下");
                } else {
	                var submit_obj = new Object();
		            submit_obj.shop_id = parseInt(obj.attr('shop_id'));
		            submit_obj.contact_type = obj.parent().find('input[name=contact_type]:checked').val();
		            //submit_obj.create_time = $('#id_contact_time').val();
		            //submit_obj.end_time = $('#id_contact_end_time').val();
		            submit_obj.is_initiative = 1;
		            submit_obj.note = tr_obj.find("input[name=contact_type]:checked").parent().text()+ " : "+note;
		            submit_obj.intention = "";
		            submit_obj.visible = $('input[name=contact_visible]:checked').val();
		            console.log(submit_obj);
		            PT.sendDajax({
		                'function': 'ncrm_save_contact_bak',
		                'contact': $.toJSON(submit_obj),
		                'call_back': "PT.WorkbenchPhoneSaler.save_contact_back"
		            });
                }
             });
        };

        $(".contact_new").click(function(){
            var obj = $(this);
            var tr_obj = obj.parent().parent();
            var shop_id = tr_obj.attr('shop_id');

            PT.WorkbenchPhoneSaler.clear_last_tr(tr_obj);
            insert_prev_tr(tr_obj,'workbench_table_contact_tr',{'shop_id':shop_id});

        });

        $(".qq_recrod").click(function(){
            var obj = $(this);
            var tr_obj = obj.parent().parent();
            var shop_id = tr_obj.attr('shop_id');

            // 插入行
            PT.WorkbenchPhoneSaler.clear_last_tr(tr_obj);
            insert_prev_tr(tr_obj,'workbench_table_qq_record_tr',{'shop_id':shop_id});
        });

        //展开隐藏订单
        $('.show_order_more').on('click',function(){
            $(this).closest('.ovh').removeClass('h100');
            $(this).remove();
        });

        $('.tips').tooltip();
    }

    return {
        init: function() {
            init_dom();
        },

        clear_last_tr : function(tr_obj){
	        var last_obj_tds = tr_obj.prev().find('td[colspan=5]');
	        if (last_obj_tds.length > 0 ){
	            last_obj_tds.remove();
	        }
	    },

	    add_event_tonote : function(cur_tr,json){
	       var html = template.render('note_record_p',json);
	       if(cur_tr.find(".note_all p").length > 0){
	           cur_tr.find(".note_all p:eq(0)").before(html);
	       } else {
	           cur_tr.find(".note_all").append(html);
	       }
	    },

        save_subscribe_call_back:function(data){
            if (data.status==true){
                $("#id_add_subscribe_layout .subscribe_btn").click();
                PT.alert('订单保存成功');
            }  else {
                PT.alert('保存订单出错了');
            }
        },

        showreintro_callback:function(user_list){
            var html_str = template.render('id_user_selector_template', {'user_list':user_list});
            $('#id_select_receiver').html(html_str);
            $('#id_add_reintro_layout').modal();
        },

        update_customer_back:function(json){
            if ( json.error == ""){
                var cur_tr = $("#workbench_table tr[shop_id="+json.shop_id+"]");
                var qq_text  = cur_tr.prev().find('.qq_text').val();
                cur_tr.find(".qq_flag").text(qq_text);

                PT.WorkbenchPhoneSaler.clear_last_tr(cur_tr);
                PT.WorkbenchPhoneSaler.add_event_tonote(cur_tr,json);
            } else {
                PT.alert(json.error);
            }
        },

        save_contact_back:function(json){
            if ( json.error == ""){
                var cur_tr = $("#workbench_table tr[shop_id="+json.shop_id+"]");
                PT.WorkbenchPhoneSaler.clear_last_tr(cur_tr);
                PT.WorkbenchPhoneSaler.add_event_tonote(cur_tr,json);
            } else {
                PT.alert(json.error);
            }
        }
    }
}();
