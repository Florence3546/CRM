PT.namespace('AddPoint');
PT.AddPoint = function () {
    
    var init_dom = function(){
        $('#id_reset').click(function(){
            $('#input_nick').val('');
            $('#input_point').val('');
        });
        
        $('#id_submit_btn').click(function(){
           var nick = $('#input_nick').val();
           var point = parseInt($('#input_point').val()); 
           
           if(nick==''||nick==undefined||nick==null){
               PT.alert("店铺ID填写有误！");
               return false;
           }
           if(point==NaN||point<=0){
               PT.alert("精灵币数字填写错误！");
               return false;
           } 
           PT.sendDajax({'function':'crm_add_jlpoint', 'nick':nick, 'point':point}); 
        });
    };
    
    
    var append_history = function(nick, point){
        $('#id_reset').click();//清空，以免误点
        
        if($('#add_history').hasClass('hide')){
            $('#add_history').removeClass('hide');
        }
        var date_str = new Date().format('yyyy-M-d h:m:s');
        $('#add_history tbody').append(
            "<tr class='tac'><td>"+nick+"</td><td>"+point+"</td><td>"+date_str+"</td></tr>"
        );
    };
    
    return {
        init:init_dom,
        append_history:append_history
    };
}();