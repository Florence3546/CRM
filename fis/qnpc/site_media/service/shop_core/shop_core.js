define(['require', 'template', '../keyword/keyword_list', 'moment', '../../widget/ajax/ajax'],
    function(require,template,keywordList,moment, ajax) {

    var start_date = moment().subtract(7, 'days').format('YYYY-MM-DD'),
         end_date = moment().subtract(1, 'days').format('YYYY-MM-DD');
    var initDom=function(){

        if($("#version_limit").val()=="False"){
            ajax.ajax('calc_shop_core',{},function(data){
                if(data.condition=="ok"){
                    $('.func').removeClass('hide');
                    $('.submit-div').removeClass('hide');
                    keywordList.init('core');
                    keywordList.getKeywordList(start_date, end_date);
                }else{
                    var trHtml = '<td colspan="19"><div class="text-center"><span>正在分析核心词，请稍后再来查看或手动刷新该页面（第一次使用时需要下载大量数据，平均每100个宝贝约需要等待6分钟）</span></div></td>';
                    $("#keyword_table tbody tr").html(trHtml);
                }
            });
        }

        /**
         * 按天数选择
         */
        var oldDays = Number($('#select_date').val());
        $('#select_date').change(function(){
            var days = Number($(this).val());
            if(oldDays == days){
                return;
            }oldDays = days;

            if(days==0){
                start_date = moment().subtract(0, 'days').format('YYYY-MM-DD'),
                end_date = moment().subtract(0, 'days').format('YYYY-MM-DD');
            }else{
                start_date = moment().subtract(days, 'days').format('YYYY-MM-DD'),
                end_date = moment().subtract(1, 'days').format('YYYY-MM-DD');
            }
            keywordList.getKeywordList(start_date, end_date);
        });
    };

    return {
        init: function() {
            initDom();
        }
    }

});
