PT.namespace('EditCustomer');
PT.EditCustomer = function() {

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
                o[this.name] = this.value || '';
            }
        });
        return o;
    };

    var check_valid = function(org_data){

    	function not_int(value){
    		return isNaN(parseInt(value)) ?0:parseInt(value);
    	}

    	var check_mapping = {'credit':not_int,
    						 'acct_status':not_int,
    						 'info_status':not_int}

    	for(var key in check_mapping){
    		org_data[key] = check_mapping[key](org_data[key]);
    	}
    	return org_data;
    }

    var submit_customer = function(group_id){
    	var submit_obj = form_2obj($('#edit_customer_form'));
        submit_obj['note']=editors.value();
        submit_obj['is_b2c']=submit_obj.is_b2c=='on'?1:0;

        var error_msg = $.trim($('#edit_customer_form #id_nick').attr('error_msg'));
        if (error_msg) {
            PT.alert(error_msg);
        } else {
            var valid_obj = check_valid(submit_obj);
            PT.sendDajax({'function':'ncrm_save_customer', 'customer':$.toJSON(valid_obj), 'namespace':'EditCustomer.save_customer_callback', 'group_id':group_id});
        }
    };

    var init_dom = function() {
        require('pt/pt-editor-mini,node', function(editor, $) {
            editors = new editor({
                render: '#id_note',
                textareaAttrs: {
                    name: 'note'
                },
                height:'160px'
            });

            editors.initData($('#id_note').next('.init_data').html());
            editors.render();
        });

        $('#id_submit').click(function(){
            submit_customer(0);
        });

        $('#add_to_group').click(function(){
        	var group_id = parseInt($('#some_hidden_client_id').val());
        	submit_customer(group_id);
        });

        $('#edit_customer_form #id_nick').blur(function(){
	        if ($(this).attr('readonly')) {
		        return;
	        }
            var nick = $.trim($(this).val());
            if(nick){
	            PT.show_loading('正在检查nick');
                PT.sendDajax({'function':'ncrm_check_nick', 'nick':nick, namespace:'EditCustomer.check_nick_callback'});
            }else{
                $(this).attr('error_msg', '必须填写nick');
            }
        })
    };

    return {
        init: function() {
            init_dom();
        },
        check_nick_callback:function(result){
            if (result.shop_id) {
	            $('#edit_customer_form #id_shop_id').val(result.shop_id);
	            $('#edit_customer_form #id_nick').attr('error_msg', '');
            } else {
                $('#edit_customer_form #id_shop_id').val('');
                $('#edit_customer_form #id_nick').attr('error_msg', result.msg);
                PT.alert(result.msg);
            }
        },
        save_customer_callback:function(result){
        	if(result){
        		$('#customer_edit_layout').modal('hide');
        	}else{
        		PT.alert("保存失败，请联系管理员！")
        	}
        }

    }
}();
