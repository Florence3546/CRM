PT.namespace('NcrmClinetGroup');
PT.NcrmClinetGroup = function() {

    var init_dom = function() {
        $('#create_form').vaildata({
            placement: 'top',
            call_back: function() {
                $('#create_form')[0].submit();
            }
        });
    },

    //调用父级显示客户群列表
    call_parent=function(){
        if(window.opener&&(window.opener.location.href.indexOf('create_plan')!=-1||window.opener.location.href.indexOf('edit_plan')!=-1)){
            var client_group=[];
            $('#client_group_table tbody tr').each(function(){
                var title=$(this).find('td:first').text(),
                    id=$(this).attr('cgid');

                if(id){
                    client_group.push([id,title]);
                }
            });
            window.opener.PT.NcrmCreatePlan.add_or_change_client_group(client_group);
        }
    }

    return {
        init: function() {
            init_dom();
            call_parent();
        }
    }
}();
