PT.namespace('EditSubscribe');
PT.EditSubscribe = function() {

    var editors;

    var form_2obj = function(form){
        var o = {};
        var a = $(form).serializeArray();
        $.each(a, function () {
            if (o[this.name] !== undefined) {
                if (!o[this.name].push) {
                    o[this.name] = [o[this.name]];
                }
                o[this.name].push(this.value || '');
            } else {
                if (!this.value || this.value == 'None'){
                    o[this.name] = '';
                }else{
                    o[this.name] = this.value;
                }
            }
        });
        return o;
    };

    var submit_subscribe = function () {

    	var submit_obj = form_2obj($('#edit_subscribe_form'));
    	if ($('#order_id')!='0' || submit_obj['category']) {
	        submit_obj['note']=editors.value();
            if (submit_obj.hasOwnProperty('pay')) {
	           submit_obj['pay'] = parseInt(Number(submit_obj['pay'])*100);
            }
	        submit_obj['article_code'] = $('#edit_subscribe_form [name=category] option:selected').attr('article_code');
	        submit_obj['item_code'] = submit_obj['article_code'];
            if (!isNaN(submit_obj['pay_type'])) {
                submit_obj['pay_type'] = parseInt(submit_obj['pay_type']);
            }
            submit_obj['pay_type_no'] = $.trim(submit_obj['pay_type_no']);
            if (submit_obj['pay_type']>=2 && submit_obj['pay_type']<=4 && !submit_obj['pay_type_no']) {
                PT.alert('支付宝和银行付款时必须填写付款信息');
                return false;
            }
	        PT.show_loading('正在处理');
	        PT.sendDajax({'function':'ncrm_save_subscribe', 'subscribe':$.toJSON(submit_obj), 'namespace':'EditSubscribe.save_subscribe_callback'});
    	} else {
    	    PT.alert('请选择订单类型');
    	}
    };

    var init_dom = function () {

    	require(['dom', 'gallery/datetimepicker/1.1/index'], function(DOM, Datetimepicker) {
            new Datetimepicker({
                start: '#id_start_date',
                timepicker: false,
                closeOnDateSelect : true
            });
            new Datetimepicker({
                start: '#id_end_date',
                timepicker: false,
                closeOnDateSelect : true
            });
        });


        require('pt/pt-editor-mini,node', function(editor, $) {
            editors = new editor({
                render: '#id_subscribe_note',
                textareaAttrs: {
                    name: 'note'
                },
                height:'200px'
            });

            editors.initData($('#id_subscribe_note').next('.init_data').html());
            editors.render();
        });

        if(PT.NcrmBase.has_psuser_cache()){
        	PT.NcrmBase.psuser_select_callBack();
        }else{
        	PT.sendDajax({'function': 'ncrm_get_psuser_list','namespace': 'NcrmBase.psuser_select_callBack'});
        }

        $('#submit_subscribe').click(function(){
        	submit_subscribe();
        });

        /***************文件上传下载**************/
         // 聊天文件选择事件绑定
        $("#id_chat_file_path").on('click',function () {
            $("#up_chat_file").click();//触发文件选择
        });
        // 文件选择后，将当前文件路径显示到输入框
        $("#up_chat_file").on("change",function(event){
            $("#id_chat_file_path").val($("#up_chat_file").val());
        });
        // ajax文件上传
        $("#edit_chat_btn").on("click",function(){
            var obj_id = $("#sb_subscribe_id").val();
            if(!PT.DBCLICK_ENABLED) {
                //禁止重复点击
                return fe;
            }
            var form_data = new FormData(), file = $("#up_chat_file")[0].files[0];
            if(file == undefined ){
                PT.alert('请先选择要上传的文件');
                $("#up_chat_file").val('');
                $("#id_chat_file_path").val('');
                return false;
            }
            // 验证文件相关参数
            if (file.size > 1024 * 1024 * 10) {
                PT.alert('文件大小不能超过10M');
                $("#up_chat_file").val('');
                $("#id_chat_file_path").val('');
                return false;
            }
            var extStart = file.name.lastIndexOf(".");
            var ext = file.name.substring(extStart, file.name.length).toUpperCase();
            if (ext == ".EXE"){
                PT.alert('请不要上传可执行文件');
                $("#up_chat_file").val('');
                $("#id_chat_file_path").val('');
                return false;
            }
            // 上传文件[编辑人工签单]
            form_data.append('up_file', file);
            form_data.append('up_path', "chat_file/");
            form_data.append('obj_id', obj_id);
            PT.show_loading('正在上件文件');
            $.ajax({
                url: '/ncrm/edit_sb_upload_file/',
                type: 'POST',
                cache: false,
                data: form_data,
                processData: false,
                contentType: false,
                success: function(data) {
                     PT.hide_loading();
                     if(data.status==1){
                         $("#id_chat_file_path").val(data.file_path);
                         $("#id_chat_file_path").removeClass("w160");
                         $("#id_chat_file_path").addClass("w100");
                         $("#down_sub_file").attr("href","/ncrm/download_file/?file_path="+data.file_path);
                         $("#down_sub_file").removeAttr("style");
                         $("#del_chat_btn").removeAttr("style");
                         PT.alert(data.msg);
                     }else{
                          PT.alert(data.msg);
                     }
                },
                error: function() {
                    PT.hide_loading();
                    PT.alert('上传聊天文件失败');
                    $("#up_chat_file").val('');
                    $("#id_chat_file_path").val('');
                    return false;
                }
            });
        });

         // 清除聊天文件
        $("#del_chat_btn").on("click",function(){
            var obj_id = $("#sb_subscribe_id").val();
            if(!PT.DBCLICK_ENABLED) {
                //禁止重复点击
                return false;
            }
            PT.show_loading('正在删除文件');
            $.ajax({
                url: '/ncrm/del_chat_file/',
                type: 'POST',
                cache: false,
                data: {
                    'obj_id': obj_id
                },
                success: function(data) {
                     PT.hide_loading();
                     if(data.status==1){
                         $("#id_chat_file_path").val('');
                         $("#id_chat_file_path").removeClass("w100");
                         $("#id_chat_file_path").addClass("w160");
                         $("#down_sub_file").css("display","none");
                         $("#del_chat_btn").css("display","none");
                         PT.alert(data.msg);
                     }else{
                          PT.alert(data.msg);
                     }
                },
                error: function() {
                    PT.hide_loading();
                    PT.alert("网络异常，请稍后重试!");
                    return false;
                }
            });
        });

    };

    return {
        init: function() {
            init_dom();
        },
        save_subscribe_callback:function(json){
            var obj;
        	if(json.flag){
                obj=$('#'+json.data.id)
                obj.find('.category').text(json.data.category);
                obj.find('.item_code').text(json.data.item_code);
                obj.find('.create_time').text(json.data.create_time);
                obj.find('.start_date').text(json.data.start_date);
                obj.find('.end_date').text(json.data.end_date);
                obj.find('.pay').text(json.data.pay);
                obj.find('.biz_type').text(json.data.biz_type);
                obj.find('.source_type').text(json.data.source_type);
                obj.find('.psuser').text(json.data.psuser);
                obj.find('.operater').text(json.data.operater);
                obj.find('.consult').text(json.data.consult);
                obj.find('.approval_status>.text').text(json.data.approval_status);

        		$('#subscribe_edit_layout').modal('hide');
        	}else{
        		PT.alert("无法保存，只有负责人和签单人才能编辑哦，如果还有问题，请联系管理员！")
        	}
        }

    }
}();
