/**
 * Created by Administrator on 2015/9/18.
 */
define(['require','moment','../common/common','../goods_list/goods_table'],function(require,moment,common,goods_table) {
    "use strict"
    
    var list_type = -1,
        start_date = moment().subtract(7,'days').format('YYYY-MM-DD'),
        end_date = moment().subtract(1,'days').format('YYYY-MM-DD'),
        campaign_id = $('#campaign_id').val(),
        opt_type = -1,
        status_type = '',
        is_follow = -1;

    var init = function(){
    
        goods_table.init(list_type, start_date, end_date,campaign_id);

        //计划选择天数
        $('#select_days').on('change',function(){
            start_date = moment($(this).daterangepicker('getRange').start).format('YYYY-MM-DD');
            end_date = moment($(this).daterangepicker('getRange').end).format('YYYY-MM-DD');
            filterData();
        });

        //搜索栏
        $('#search_btn').click(function (){
            filterData();
        });

        $('#search_val').keyup(function(e){
            if (e.keyCode==13) {
                filterData();
            }
        });

        //根据优化状态查询宝贝
        $('#search_opt_type').on('change',function(e,value){
            opt_type = value;
            filterData();
        });

        //根据推广状态查询宝贝
        $('#search_status_type').on('change',function(e,value){
            status_type = value;
            filterData();
        });

        //根据关注状态查询宝贝
        $('#search_follow_type').on('change',function(e,value){
            is_follow = value;
            filterData();
        });

        //查询列表
        var filterData = function(){
            var search_word = $('#search_val').val();
            goods_table.filterData(start_date,end_date,campaign_id,search_word,opt_type,status_type,is_follow);
        };
    };

    return {
        init:init
    }
});
