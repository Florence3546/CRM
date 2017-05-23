PT.namespace('CustomerList');
PT.CustomerList = function () {
    
    var refresh_datatable = function (){
        $('#data_table').dataTable({
        "bPaginate": false,
        "bFilter": false,
        "bInfo": false,
        "aoColumns": [{ "bSortable": false},
                    { "bSortable": true },
                    { "bSortable": true},
                    {"bSortable": true, "sSortDataType": "dom-text", "sType": "numeric"},
                    { "bSortable": false },
                    { "bSortable": true },
                    { "bSortable": true },
                    { "bSortable": true },
                    { "bSortable": false }]
        });
    };
    
    var init_dom = function(){
        PT.Base.set_nav_activ(2);
        refresh_datatable();
        $('.edit_danger').click(function(){
            var cid = $(this).attr('cid');
            var status = $(this).attr('status');
            var offestLeft=$(this).offset().left;
            var offestTop=$(this).offset().top;
            $('#danger_list').data('customer_id',cid);
            $('#id_danger'+parseInt(status)).attr('checked',true);
            $('#danger_list').css({'left':offestLeft,'top':offestTop}).show(); 
        });
        
        $('#id_modify_status').click(function(){
            var customer_id=$('#danger_list').data('customer_id');
            var status=$('#danger_list input[name="danger_status_radio"]:checked').val();
            PT.sendDajax({'function':'crm_change_danger',"customer_id":customer_id,'status':status}); 
        });
        
        $("#id_reset").click(function(){
            $("#id_shop_id").val('');
            $("#id_username").val('');
        });
    }

    
    
    return {
        init: init_dom,
        change_danger_callBack: function(status,customer_id,mode){
            if(status=='fail'){
                PT.alert('状态修改失败，请联系管理员');
                return false;   
            }
            if(status=='success'){
                $('#danger_'+customer_id+' div[class^="notification"]').hide();
                $('#danger_status_'+customer_id+'_'+mode).show();
            }
            $('#danger_list').hide();
        }
    };
}();
