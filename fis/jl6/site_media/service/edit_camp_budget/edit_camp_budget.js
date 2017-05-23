define(["template","../common/common"], function(template,common) {
    "use strict";

    var tpl;

    tpl = __inline('edit_camp_budget.html');

    var budgetArr = [[30,3000],[30,10000],[30,99999]];

    var show=function(options){
        var html,
            obj;
        var mnt_type = options.mnt_type;
        var cur_range = budgetArr[2];
        if(mnt_type==1||mnt_type==3){
            cur_range = budgetArr[0];
        }else if(mnt_type==2||mnt_type==4){
            cur_range = budgetArr[1];
        }else{
            cur_range = budgetArr[2];
        }
        options['budget_min'] = cur_range[0];
        options['budget_max'] = cur_range[1];
        html = template.compile(tpl)(options);

        obj=$(html);

        $('body').append(obj);

        obj.modal();

        obj.find('[name=budget]').focus(function(){
            $(this).tooltip('destroy');
        });

        obj.find('.btn-primary').on('click',function(){
            var budget,
                is_limit,
                is_smooth,
                error_msg;

            is_limit=obj.find('[name=is_limit]:checked').val();
            if (is_limit=='unlimit') {
                budget=20000000;
            }else{
                budget=Number(obj.find('[name=budget]').val());
            }
            is_smooth=obj.find('[name=is_smooth]:checked').val();

            if(isNaN(budget)||(parseInt(budget)!=budget)){
                error_msg = '日限额只能为整数';
            }else if(budget<cur_range[0]){
                error_msg = '日限额不能低于'+cur_range[0]+'元';
            }else if (is_limit=='limit' && budget>cur_range[1]){
                error_msg = '日限额不能高于'+cur_range[1]+'元';
            }

            if(error_msg){
                obj.find('[name=budget]').tooltip({title:error_msg,placement:'top',trigger:'manual'});
                obj.find('[name=budget]').tooltip('show');
                return false;
            }

            obj.modal('hide');

            options.onChange(budget,is_smooth);
        });

        obj.find('[name=is_limit]').on('change',function(){
            if($(this).val()=="unlimit"){
                obj.find('[name=is_smooth]').closest('div').hide();
                obj.find('[name=budget]').attr('disabled','disabled');
            }else{
                obj.find('[name=is_smooth]').closest('div').show();
                obj.find('[name=budget]').removeAttr('disabled');
            }
        });

        obj.on('hidden.bs.modal',function(){
            obj.remove();
        });

        obj.on('shown.bs.modal',function(){
            // obj.find('[name=is_limit]:checked').change();
            $('[data-toggle="tooltip"]').tooltip({html: true});
        });

    }

    return {
        show: show
    }
});
