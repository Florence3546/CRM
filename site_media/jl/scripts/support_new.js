PT.namespace("SupportNew");
PT.SupportNew = function(){
    
    var display_link = function (url_dict){
        $('#id_sale_link').html(template.render('id_url_template', {'url_dict':url_dict}));
        $('#id_sale_link').removeClass('hide');
    };
    
    var init_dom = function(){
        
        $(document).on('click', '#id_check_ww', function (){
            $('#id_sale_link').html('');
            var ww = $.trim($('#id_ww').val());
            if(ww!=''&&ww!=undefined&&ww!=null){
                   $.ajax({
                      url:'/web/check_ww',
                      data:{'ww':ww},
                      dataType:'json',
                      cached:true,
                      success:function(data, status){
                          if(data.result){
                              display_link(data.url_dict);
                          }else{
                              $('#id_result_msg').text(data.msg);
                              $('#modal-custom-confirm').modal();
                          }
                      },
                      error:function(){
                          PT.alert('验证失败！');
                      }
                   }); 
            }else{
                $('#id_ww').val('');
            }
        });
    };
    
    return {
        init:init_dom
    };
}();
