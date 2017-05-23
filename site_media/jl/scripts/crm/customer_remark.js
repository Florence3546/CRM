PT.namespace('CustomerRemark');
PT.CustomerRemark = function () {
    
    var init_dom = function(){
        PT.Base.set_nav_activ(6);
        
        $("#submit_remark").click(function(){
            if ($.trim($('#remark').val())==''){
                PT.alert('备注为空');
                return false;   
            }
            add_remark.submit();
        });
        
        $(".del_remark").click(function(){
            var remark_id = $(this).attr('remark_id');
            PT.sendDajax({'function': 'crm_del_remark',"remark_id":remark_id});
        });
        
        $(".modify_count").click(function(){
            var oper = parseInt($(this).attr('oper'));
            var org_value = parseInt($('#id_revisit_count_bak').val());
            var new_value = parseInt($('#id_revisit_count').val())+oper;
            if(Math.abs(new_value-org_value)>=2){
                return false;
            }else{
                $('#id_revisit_count').val(new_value);
            }
        });
        
        
        $('#submit_data_btn').click(function(){
            var revisit_time = $('#id_revisit_time').val();
            if (revisit_time == ''){
            	PT.alert('请填写回访时间....');
            	return 
            }
            var cid=parseInt($('#customer_id').val());
            var revisit_count = $('#id_revisit_count').val(); 
            var revisit_detail = $('#id_revisit_detail').val();
            var refund_status = $('input:radio[name=refund_status_radio]:checked').val()
            var introduce_status = $('input:radio[name=introduce_status_radio]:checked').val();
            var ban_status = $('input:radio[name=ban_status_radio]:checked').val();
            var relation_status = $('input:radio[name=relation_status_radio]:checked').val();
            var comment_status = $('input:radio[name=comment_status_radio]:checked').val();
            PT.sendDajax({'function': 'crm_submit_status','id':cid,'revisit_count':revisit_count,'revisit_time':revisit_time,'revisit_detail':revisit_detail,'comment_status':comment_status,'refund_status':refund_status,'introduce_status':introduce_status,'ban_status':ban_status,'relation_status':relation_status})
        });
    };

    
    return {
        init: init_dom,
        
        del_remark_callBack:function(status,remrak_id){
            if(status=='fail'||status==undefined){
                PT.alert('删除失败，请联系管理员!');
                return false;
            }
            if(status=='success'){
                $('#remrak_'+remrak_id).fadeOut(300).queue(function(next){
                    $(this).remove();
                    $(this).dequeue();  
                });
            }
        }
    };
}();
