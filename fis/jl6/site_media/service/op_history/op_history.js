/**
 * Created by tianjh on 2015.10.6
 */
define(['require','moment','../common/common','op_row','template',
'dataTable','jl6/site_media/widget/ajax/ajax'],function(require,moment,common,
op_row,template,dataTable,ajax) {
    "use strict"

    //查询 条件
    var obj = {
        camp_id: -1,
        op_type: -1,
        opter: -1,
        start_date: moment().subtract(2,'days').format('YYYY-MM-DD'),
        end_date: moment().subtract(0,'days').format('YYYY-MM-DD'),
        pageIdx: 1,
        search_word:''
    }

    var init = function(){

//        initSelect();

        bindEvent();

        op_row.init(obj);

        setTimeout(delaySign,2000);
    };

    //加载页面后默认显示上次优化时间，3秒后隐藏，隐藏后需启动hover动画样式
    var delaySign = function(){
        $('.width100').animate({width:24},1000,function(){
            $('.width100').removeAttr('style');
            $('.width100').removeClass('width100');
            $('.sign-left>a').addClass('sign-content');
        });
    }

    //初 始化计划下拉列表
    var initSelect=function(){
        var camp_id = GetUrlParam('camp_id');
        if(camp_id)
            obj.camp_id = camp_id;
        ajax.ajax('get_camp_list', {}, function(data){
            var html = ''
            $.each(data.camp_list, function(idx, item){
                if(item.camp_id == obj.camp_id){
                    $('#select_camp .tip').text(item.camp_title);
                    html += '<li data-value="' + item.camp_id + '"><span class="active">' + item.camp_title + '</span></li>'
                }else{
                    html += '<li data-value="' + item.camp_id + '"><span>' + item.camp_title + '</span></li>'
                }
            });
            $('#select_camp').find('ul').html(html)
        });
    }

    //绑定事件
    var bindEvent=function(){
        //切换计划
        $('#select_camp').on('change',function(e, v){
            obj.camp_id = v;
            op_row.init(obj);
        });

        //切换数据类型
        $('#select_optype').on('change',function(e, v){
            obj.op_type = v;
            op_row.init(obj);
        });

        //切换操作人
        $('#select_opter').on('change',function(e, v){
            obj.opter = v;
            op_row.init(obj);
        });

         //选择天数
        $('#select_days').on('change',function(){
            obj.start_date = moment($(this).daterangepicker('getRange').start).format('YYYY-MM-DD');
            obj.end_date = moment($(this).daterangepicker('getRange').end).format('YYYY-MM-DD');
            op_row.init(obj);
        });

        //搜索按钮
        $('#search_btn').click(function (){
            var sSearch = $.trim($('#search_val').val());
            obj.search_word = sSearch;
            op_row.init(obj);
            //if(search_word == '')
                //return;
            //var oTable = $('#op_table').dataTable();
            //oTable.fnFilter(sSearch);
        });

        //搜索栏
        $('#search_val').keyup(function(e){
            if (e.keyCode==13) {
                var sSearch = $.trim($('#search_val').val());
                obj.search_word = sSearch;
                op_row.init(obj);
            }
        });

       //关闭详细的浮层
        $('#op_table').on('click','.btnx', function() {
            $('.his_item').removeClass('open');
        });

    }

    //获取URL参数
    function GetUrlParam(name) {
        var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)"); //构造一个含有目标参数的正则表达式对象
        var r = window.location.search.substr(1).match(reg);  //匹配目标参数
        if (r != null) return unescape(r[2]); return null; //返回参数值
    }

    //修改URL参数值
    function ChangeUrlArg(url, arg, arg_val){
        var pattern=arg+'=([^&]*)';
        var replaceText=arg+'='+arg_val;
        if(url.match(pattern)){
            var tmp='/('+ arg+'=)([^&]*)/gi';
            tmp=url.replace(eval(tmp),replaceText);
            return tmp;
        }else{
            if(url.match('[\?]')){
                return url+'&'+replaceText;
            }else{
                return url+'?'+replaceText;
            }
        }
        return url+'\n'+arg+'\n'+arg_val;
    }

    return {
        init:init
    }
});
