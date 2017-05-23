define(['require', 'template', '../keyword/keyword_list', 'moment'],
    function(require,template,keywordList,moment) {

    var start_date = moment().subtract(7, 'days').format('YYYY-MM-DD'),
         end_date = moment().subtract(1, 'days').format('YYYY-MM-DD');
    var initDom=function(){
        if($("#version_limit").val()=="False"){
            keywordList.init('rank');
            keywordList.getKeywordList(start_date, end_date);
        }

        /**
         * 刷新列表
         */
        $('#refresh_list').click(function(){
            keywordList.getKeywordList(start_date, end_date);
        });

        /**
         * 按天数选择
         */
        var oldDays = Number($('#select_date').val());
        $('#select_date').change(function(){
            var days = Number($(this).val());
            if(oldDays == days){
                return;
            }
            oldDays = days;
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
