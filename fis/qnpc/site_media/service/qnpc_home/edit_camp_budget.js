define(["template"], function(template) {
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

        $('body').append($(html));

        $("#editBudgetModal").modal({backdrop:"static", keyboard:false});
        $("#editBudgetModal").modal('show');

        $("#editBudgetModal .btn-primary").on('click', function(){

            var budget, is_limit, is_smooth, error_msg;

            is_limit=$("#editBudgetModal").find('[name=is_limit]:checked').val();
            if (is_limit=='unlimit') {
                budget=20000000;
            }else{
                budget=Number($("#editBudgetModal").find('[name=budget]').val());
            }
            is_smooth=$("#editBudgetModal").find('[name=is_smooth]:checked').val();

            if(isNaN(budget)||(parseInt(budget)!=budget)){
                error_msg = '日限额只能为整数!';
            }else if(budget<cur_range[0]){
                error_msg = '日限额不能低于'+cur_range[0]+'元!';
            }else if (is_limit=='limit' && budget>cur_range[1]){
                error_msg = '日限额不能高于'+cur_range[1]+'元!';
            }

            if(error_msg){
                $.alert({title:'提示', body: error_msg, okBtn:"确定", height:"30px"});
                return false;
            }

            $("#editBudgetModal").modal('hide');

            options.onChange(budget,is_smooth);
        });

        $("#editBudgetModal").find('[name=is_limit]').on('change',function(){
            if($(this).val()=="unlimit"){
                $("#editBudgetModal").find('[name=is_smooth]').closest('label').hide();
                $("#editBudgetModal").find('[name=budget]').attr('disabled','disabled');
            }else{
                $("#editBudgetModal").find('[name=is_smooth]').closest('label').show();
                $("#editBudgetModal").find('[name=budget]').removeAttr('disabled');
            }
        });

        $("#editBudgetModal").on('hidden', function () {
           $("#editBudgetModal").remove();
        });

    };

    return {
        show: show
    }
});
