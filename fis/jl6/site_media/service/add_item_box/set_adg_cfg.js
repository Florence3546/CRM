/**
 * Created by Administrator on 2015/10/16.
 */
define(["template"], function(template) {
    "use strict";

    var show = function(options){

        var config = {
            avg_price:1.00,
            default_price_pc:1.00,
            default_price_yd:1.00,
            min_price:0.05,
            opt_adgroup:false,
            suggest_price:'1.00~2.00',
            use_camp_limit:1,
            mnt_opt_type:1,
            customer_price_pc:1.00,
            customer_price_yd:1.00,
            onChange:function(data){}
        };
        config = $.extend({}, config, options);

        var html,obj,tpl=__inline("set_adg_cfg.html");
            html = template.compile(tpl)({options:config});
        obj=$(html);
        $('body').append(obj);

        obj.modal();
        $("[data-toggle='tooltip']").tooltip({html:true});

        //获取宝贝行业均价
        $('#modal_set_adg_cfg').on('click', '#set_adg_cfg', function () {
            var customer_price_pc = obj.find('[name=customer_price_pc]').val();
            var customer_price_yd = obj.find('[name=customer_price_yd]').val();
            var mnt_opt_type = obj.find('[name=mnt_opt_type]:checked').val();
            var use_camp_limit = obj.find('[name=use_camp_limit]:checked').val();
            if(use_camp_limit=='0'){
                if(isNaN(customer_price_pc)){
                    obj.find('[name=customer_price_pc]').tooltip({title:'请输入数字',placement:'top',trigger:'manual'});
                    obj.find('[name=customer_price_pc]').tooltip('show');
                    setTimeout("javascript: $('[name=customer_price]').tooltip('hide');",5000);
                    return false;
                }

                if(customer_price_pc<Number(options['min_price'])||customer_price_pc>99.99){
                    obj.find('[name=customer_price_pc]').tooltip({title:'关键词限价最低'+Number(options['min_price'])+'元，最高99.99元',placement:'top',trigger:'manual'});
                    obj.find('[name=customer_price_pc]').tooltip('show');
                    setTimeout("javascript: $('[name=customer_price_pc]').tooltip('hide');",5000);
                    return false;
                }

                if(isNaN(customer_price_yd)){
                    obj.find('[name=customer_price_yd]').tooltip({title:'请输入数字',placement:'top',trigger:'manual'});
                    obj.find('[name=customer_price_yd]').tooltip('show');
                    setTimeout("javascript: $('[name=customer_price_yd]').tooltip('hide');",5000);
                    return false;
                }

                if(customer_price_yd<Number(options['min_price'])||customer_price_yd>99.99){
                    obj.find('[name=customer_price_yd]').tooltip({title:'关键词限价最低'+Number(options['min_price'])+'元，最高99.99元',placement:'top',trigger:'manual'});
                    obj.find('[name=customer_price_yd]').tooltip('show');
                    setTimeout("javascript: $('[name=customer_price_yd]').tooltip('hide');",5000);
                    return false;
                }
            }else{
                customer_price_pc = config.default_price_pc;
                customer_price_yd = config.default_price_yd;
            }

            $('#modal_set_adg_cfg').modal('hide');
            var result = {use_camp_limit:use_camp_limit,mnt_opt_type:mnt_opt_type,customer_price_pc:customer_price_pc, customer_price_yd:customer_price_yd};
            options.onChange(result);
        });

        $('[name=use_camp_limit]').on('change',function(){
            var use_camp_limit = obj.find('[name=use_camp_limit]:checked').val();
            if(use_camp_limit=='0'){
                obj.find('.set_customer_price').removeClass('hide');
            }else{
                obj.find('[name=customer_price_pc]').val(config.customer_price_pc);
                obj.find('[name=customer_price_yd]').val(config.customer_price_yd);
                obj.find('.set_customer_price').addClass('hide');
            }
        });

        obj.on('hidden.bs.modal',function(){
            obj.remove();
        });

        var use_camp_limit = obj.find('[name=use_camp_limit]:checked').val();
        if(use_camp_limit=='0'){
            obj.find('[name=customer_price]').attr('disabled',false);
        }else{
            obj.find('[name=customer_price]').attr('disabled',true);
        }

        /**
         * 点击区域，选中checkbox 和 radio
         */
        obj.on('click', '.select_div :radio,:checkbox', function (e) {
            //停止事件冒泡,当点击的是checkbox时,就不执行父div的click
            e.stopPropagation();
        });
        obj.on('click','.select_div',function(){
            $(this).find(':radio,:checkbox').click();
        });
    }

    return {
        show:show
    }
});