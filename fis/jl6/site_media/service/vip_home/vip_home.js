define(['require','widget/lightMsg/lightMsg','widget/ajax/ajax'],function(require,lightMsg,ajax){

    var init=function(){

        //积分详情
        $('#point_detial').on('click',function(){
            require(['../point_detial/point_detial'],function(modal){
                modal.show()
            });
            return false;
        });

        //填写资料
        $('#complete_user_info').on('click',function(){
            require(['../complete_user_info/complete_user_info'],function(modal){
                modal.show({type:'fill'})
            });
            return false;
        });

        //验证手机号
         if($('#is_need_phone').val()=='1'){
            require(['../perfect_phone/perfect_phone'],function(modal){
                modal.show({
                    type:'init'
                });
            });
         }

         //修改验证信息
        $('#verify_phone').on('click',function(){
            require(['../perfect_phone/perfect_phone'],function(modal){
                modal.show({
                    type:'edit'
                });
            });
            return false;
        });

        //冻结积分
        $('.freeze_point').on('click',function(){
            ajax.ajax('freeze_point',{},function(data){
                lightMsg.show('操作成功，在'+data.freeze_point_deadline+'之前系统将会保留您的积分');
            });
        });

        require(['../perfect_promotion/perfect_promotion'],function(modal){
            modal.show();
        });
    }

    return {
        init:init
    }
});
