PT.namespace('UpfradeSuggest');

PT.InviteFriend=PT.UpfradeSuggest = function () {

    var statue=0; //兑换状态
    
    var init_dom = function () {

        $('.suggest .btn').click(function () {
            
            if ($(this).text() === '立即兑换') {
              //=================老的弹出逻辑========================
              //var jq_modal = $('#modal_confirm_redeem');
              //jq_modal.find('#discount_submit').attr('discount_id', $(this).attr('index'));
              //jq_modal.find('#redeem_info_2, #error_msg, #loading_tips').hide();
              //jq_modal.find('#redeem_info_1, #discount_submit').fadeIn();
              //jq_modal.modal();
              //return false;
              //========================================================
              
              PT.sendDajax({
              'function':'web_generate_wait_point',
              'discount_id':$(this).attr('index'),
              });
              return false;
            }
          return true;
        });

        $(document).on('click', '#discount_submit', function () {
            var nick = $('#input_nick').val();
            if (nick) {
                $('#discount_submit,#error_msg').hide();
                $('#loading_tips').fadeIn();
                statue=1
                PT.sendDajax({
                    'function': 'web_get_sale_link',
                    'nick': nick,
                    'discount_id': $(this).attr('discount_id')
                });
            } else {
                $('#error_msg').text('请输入店铺主旺旺！').fadeIn();
                $('#input_nick').blur();
            }
        });
        
		$(document).on('click','#close_confrim_redeem',function(){
            if (statue){
                PT.confirm('请确定您已经记下优惠链接，确定后将会刷新页面！',function(){
                    window.location.reload();
                });
                return false;
            }
			if($(this).attr('is_refresh')){
				$('#close_redeem_point').attr('is_refresh',1);
				$(this).attr('is_refresh',0);
			}
			$('#modal_confirm_redeem').modal('hide');
		});
        
        
    }

    
    return {
        'init': function () {
            init_dom();
        },
		get_sale_link_back:function(result){
			var jq_modal=$('#modal_confirm_redeem');
			jq_modal.find('#loading_tips').hide();
			if (result.is_success){
				jq_modal.find('#redeem_info_1').hide();
				jq_modal.find('#sale_link_user').text($('#input_nick').val());
				jq_modal.find('#sale_link').attr('href',result.sale_link).text(result.sale_link);
				jq_modal.find('#link_details').html(result.link_details);
				jq_modal.find('#redeem_info_2').fadeIn();
				jq_modal.find('#close_confrim_redeem').attr('is_refresh',1);
			}else{
				jq_modal.find('#error_msg').text(result.error_msg).fadeIn();
				jq_modal.find('#discount_submit').fadeIn();
			}
		}
    }
}();