/**
 * Created by Administrator on 2015/10/14.
 */
define(["template",'jl6/site_media/widget/alert/alert'], function(template,alert) {
    "use strict";

    var tpl;

    tpl = __inline('edit_camp_price.html');

    var show=function(options){
        var html,
            obj;

        html = template.compile(tpl)(options);

        obj=$(html);

        $('body').append(obj);

        obj.find("[data-toggle='tooltip']").tooltip({html: true});
        obj.modal();

        $('.input_price_pc').on('focus', function(){
            obj.find('.input_price_pc').tooltip('hide');
        });

        $('.input_price_yd').on('focus', function(){
            obj.find('.input_price_yd').tooltip('hide');
        });

        $('.input_price_pc').on('blur', function(){
            var newPricePc=obj.find('.input_price_pc').val();
            newPricePc = parseFloat(newPricePc).toFixed(2);
            if(isNaN(newPricePc)){
                obj.find('.input_price_pc').tooltip({title:'请输入数字',placement:'right',trigger:'manual'});
                obj.find('.input_price_pc').tooltip('show');
            }
            if(newPricePc<options.min_price||newPricePc>options.max_price){
                obj.find('.input_price_pc').tooltip({title:'最低'+options.min_price+'元，最高'+options.max_price+'元',placement:'right',trigger:'manual'});
                obj.find('.input_price_pc').tooltip('show');
            }
        });

         $('.input_price_yd').on('blur', function(){
            var newPriceYd=obj.find('.input_price_yd').val();
            newPriceYd = parseFloat(newPriceYd).toFixed(2);
            if(isNaN(newPriceYd)){
                obj.find('.input_price_yd').tooltip({title:'请输入数字',placement:'right',trigger:'manual'});
                obj.find('.input_price_yd').tooltip('show');
            }
            if(newPriceYd<options.min_price||newPriceYd>options.max_price){
                obj.find('.input_price_yd').tooltip({title:'最低'+options.min_price+'元，最高'+options.max_price+'元',placement:'right',trigger:'manual'});
                obj.find('.input_price_yd').tooltip('show');
            }
        });

        obj.find('.btn-primary').on('click',function(){
            var newPricePc=obj.find('.input_price_pc').val();
            var newPriceYd=obj.find('.input_price_yd').val();
            if(newPricePc==options.default_price_pc&&newPriceYd==options.default_price_yd){
                obj.modal('hide');
                return false;
            }
            newPricePc = parseFloat(newPricePc).toFixed(2);
            if(isNaN(newPricePc)){
                return false;
            }

            newPriceYd = parseFloat(newPriceYd).toFixed(2)
            if(isNaN(newPriceYd)){
                return false;
            }
            if(newPricePc<options.min_price||newPricePc>options.max_price){
                return false;
            }
            if(newPriceYd<options.min_price||newPriceYd>options.max_price){
                return false;
            }
            obj.modal('hide');
            options.onChange(newPricePc, newPriceYd);
        });

        obj.on('hidden.bs.modal',function(){
            obj.remove();
        });

    }

    return {
        show: show
    }
});
