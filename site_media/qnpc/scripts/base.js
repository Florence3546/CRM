//PT是paithink的缩写，以此缩写开创一个命名空间
var PT = function() {
    return {
        namespace: function(ns) {
            var parts = ns.split("."),
                object = this,
                i, len;
            for (i = 0, len = parts.length; i < len; i++) {
                if (!object[parts[i]]) {
                    object[parts[i]] = {};
                }
                object = object[parts[i]];
            }
            return object;
        },
        alert: function(msg, color , call_back , argv ,that, millsec) {
        //自定义Alert()信息
          var alert_conf={
           backdrop:'static',
            bgColor:'#000',
            keyboard:true,
            title:'精灵提醒',
            body:'<span>'+msg+'</span>'
          }
          if(call_back != undefined && call_back instanceof Function){
            alert_conf.okHidden=function(){return function(){call_back.apply(that,argv)}()};
          }
          $.alert(alert_conf);
        },
        confirm: function(msg, call_back, argv, that, cancel_call_back, cancel_argv, cancel_that, btn_text_list) {
        //自定义confirm()信息
          var confirm_conf={
           backdrop:'static',
            bgColor:'#000',
            keyboard:true,
            title:'精灵提醒',
            body:'<span>'+msg+'</span>'
          }
          if(call_back != undefined && call_back instanceof Function){
            confirm_conf.okHidden=function(){return function(){call_back.apply(that,argv)}()};
          }
          $.confirm(confirm_conf);
        },
        sendDajax: function(jdata) {
        //统一ajax请求接口,发起ajax请求jdata中至少要有一个参数且名字为function,例:sendDajax({'function':'test'})
        //如果有别的参数直接传jsaon 例子:sendDajax({'function':'test','day':1})
            if (!jdata.hasOwnProperty('function')) {
                $('#center_tip_popup').hide();
                PT.alert('sendDajax:缺少必要参数[function]','red');
                return false;
            }
            var q, data = {}, mArray = jdata['function'].split('_');
            for (q in jdata) {
                data[q] = jdata[q];
            }
            data['function'] = mArray.slice(1).join('_');
            Dajax.dajax_call(mArray[0], 'route_dajax', data);
        },
        show_loading: function(msg,lock){
        //显示全屏tip消息，并锁定屏幕，禁止滚屏
            var obj=$('#full_screen_tips');
            obj.find('span').text(msg+'，请稍候...');
            if(lock){
                $('body').addClass('modal-open'); //锁定屏幕，禁止滚屏
            }
            obj.show();
        },
        hide_loading: function(msg){
        //隐藏全屏tip消息
            $('body').removeClass('modal-open');
            $('#full_screen_tips').hide();
        },
        initDashboardDaterange: function (){
        //日期插件
        $('.dashboard-date-range').daterangepicker({
                ranges: {
                    '昨天': [1],
                    '过去2天': [2],
                    '过去3天': [3],
                    '过去5天': [5],
                    '过去7天': [7],
                    '过去10天': [10],
                    '过去14天': [14],
                    '过去15天': [15]
                },
                call_back:function(value,form) {
                //这里相当于select的change事件
                    //PT.show_loading('正在查询');
                    if(form.attr('post_mode')=='ajax'){
                        var post_fuc=form.attr('post_fuc');
                        var fuc_arr=post_fuc.split(".");
                        setTimeout(function(){
                            window[fuc_arr[0]][fuc_arr[1]][fuc_arr[2]](value);
                        },17);

                    }else{
                    form[0].submit();
                    }
                }
            })
        },
        light_msg:function(title,text,time,direction,class_name) {
        /**
        * class_name: gritter-light 白色
        * direction: 控制方向
        */
            !time?time=8000:'';
            !class_name?class_name='my-sticky-class':'';
            !direction?direction='top-right':'';
            $.extend($.gritter.options, {
                position: direction
            });
            var comm_gritter=$.gritter.add({
                title: title,
                text: text,
                sticky: true,
                class_name: class_name
            });
            setTimeout(function () {
                $.gritter.remove(comm_gritter, {
                    fade: true,
                    speed: 'slow'
                });
            }, time);
        },
        true_length:function (str){
        //获取中英混合真实长度
            var l = 0;
            for (var i = 0; i < str.length; i++) {
                if (str[i].charCodeAt(0) < 299) {
                    l++;
                }
                else {
                    l += 2;
                }
            }
            return l;
        },
        console:function (msg){
            //浏览器控制台输出信息，便于调试和测试
            //var dt=new Date();
            //console.log(msg+' time:'+dt.getTime());
        },
        get_yaxis_4list:function (data) {
            var yaxis_list=[];
            for (var i=0; i<data.length; i++) {
                if (data[i].is_axis==0) {
                    continue;
                }
                yaxis_list.push({'gridLineWidth' : 1,
                                'title' : { 'text':'', 'style':{'color': data[i].color } },
                                'labels' : { 'formatter': function() {var temp_unit=data[i].unit;return function(){return this.value+temp_unit};}(), 'style': {'color': data[i].color}},
                                'opposite' : data[i].opposite
                                    });
            }
            return yaxis_list;
        },
        get_series_4list:function (data) {
            var series_list=[];
            for (var i=0; i<data.length; i++) {
                series_list.push({ 'name' : data[i].name,
                                            'color': data[i].color,
                                            'type': 'line',
                                            'yAxis' : data[i].yaxis,
                                            'data': data[i].value_list,
                                            'visible' : data[i].visible
                                        });
            }
            return series_list;
        },
        draw_trend_chart:function (id_container,category_list,series_cfg_list) {
            var chart = new Highcharts.Chart({
                chart: {renderTo: id_container,zoomType: 'xy',animation:true},
                title: {text: ''},
                subtitle: {text: ''},
                xAxis: [{categories: category_list}],
                yAxis: PT.get_yaxis_4list(series_cfg_list),
                tooltip: {
                    formatter: function() {
                        var obj_list = chart.series;
                        var result = this.x +'日 '+"<br/>";
                        for(var i = 0;i<obj_list.length;i++){
                            if(obj_list[i].visible){
                                result = result+(obj_list[i].name)+" "+obj_list[i].data[this.point.x].y+(series_cfg_list[i].unit)+"<br/>"
                            }
                        }
                        return result;
                    }
                },
                legend: {backgroundColor: '#FFFFFF'},
                series: PT.get_series_4list(series_cfg_list)
            });
        },
        get_events_namespace:function(dom,type){
            var events=$(dom).data('events')[type],i,name_list=[];
            for(i in events){
                name_list.push(events[i].namespace);
            }
            return name_list;
        },
        help:function(msg_list){
            return;
        }
    }
}();

PT.namespace('Base');
PT.Base = function () {
    var url='';

    var init_dom=function() {

        $('#contact_consult').hover(function(){
            $('#contact_telephone').stop().animate({'marginLeft':0},300);
        },function(){
            $('#contact_telephone').stop().animate({'marginLeft':-181},100);
        });

        $('a[name=upgrade]').click(function(){
            //这里只好将url固定了
            PT.confirm("您当前的版本需要升级后才可以开通该引擎，要升级吗？", function(){window.open("https://fuwu.taobao.com/ser/detail.html?spm=a1z13.1113643.51940006.43.RmTuNs&service_code=FW_GOODS-1921400&tracelog=category&scm=1215.1.1.51940006", '_blank');},[],this,null,[],this, ['升级'])
        });

        $('#duplicate_check_id').click(function() {
            PT.sendDajax({'function': 'web_to_duplicate_check'});
        });

        $('#attention_check_id').click(function() {
            PT.sendDajax({'function': 'web_to_attention_list'});
        });

        $('#sync_increase_data').click(function() {
            PT.show_loading('正在下载增量数据');
            PT.sendDajax({'function':'web_sync_increase_data'});
        });

        $('#sync_rpt_data').click(function(){
            PT.show_loading(sync_all(1,15));
        });

        $('#sync_base_data').click(function(){
            PT.show_loading(sync_all(2));
        });

        $('.open_qnpc_feedback_dialog').click(function(){

            $('#feedback_modal_dialog').modal();
        });

        $(document).on('click','#open_msg',function() {
            PT.sendDajax({'function':'web_open_msg_dialog'});
        });

        $(document).on('click','.dialog_close_msg',function() {
            eval("var data="+$(this).attr("data"));
            var is_common=data.is_common,msg_id=data.msg_id,type=is_common==1? 'common' : 'user',jq_count=$('#'+type+'_prompt_count'),prompt_count=jq_count.text().slice(1,-1);
            if ( prompt_count > 1) {
                jq_count.text('（'+(prompt_count-1)+'）');
            }   else {
                jq_count.addClass('hide');
            }
            $('#'+msg_id+'_'+is_common).parents('.accordion-group:first').remove();//删除首页相对应的公告
            PT.Base.change_msg_count();
            $('#dot_'+msg_id).removeClass('r_color').addClass('s_color');
            PT.sendDajax({'function':'web_close_msg','msg_id':msg_id,"is_common":is_common});
        });

        $(document).on('click','#submit_btn',function(){
            var content=$('#id_content').val();

            if(content==''){
                PT.alert('麻烦您不吝赐教，输入您的建议');
                return false;
            }
            PT.show_loading('感谢您的反馈');
            PT.sendDajax({'function':'web_submit_feedback','score_str':'[["health_check","qnpc"]]','content':content});
        });

        $(document).on('click', '#id_submit_info', function(){
            var qq = $('#id_qq').val(),
                phone = $('#id_phone').val();
            if(isNaN(phone) || !(/^1[3|4|5|7|8]\d{9}$/.test(phone))){
                PT.light_msg("提示", "手机号码填写不正确！");
                return false;
            }
            PT.sendDajax({'function':'qnyd_submit_phone', 'phone':phone, 'qq':qq, 'namespace':'PT', 'auto_hide': 0});
            PT.show_loading('正在提交手机号');
        });


        //当鼠标经过该元素时，加上hover这个class名称，修复ie中css的hover动作
        if(!$.browser.msie||Number($.browser.version)>8){
            $(document).on('mouseover.PT.e','*[fix-ie="hover"]',function(){
                $(this).addClass('hover');
                $(this).mouseout(function(){
                    $(this).removeClass('hover');
                });
            });
        }

        //关联td和里面的checkbox事件
        $(document).on('click','.link_inner_checkbox',function(e){
            e.stopPropagation();
            if(this==e.target){
                $(this).find('input[type="checkbox"]').click();
            }
        });

        !function(){
            var obj=$('.page-sidebar-menu');
            if(!obj.length){
                return;
            }
            var elem_top=obj.offset()['top'];
            var ele_height=obj.height();
            var visible_height=$(window).height();
            var temp=0;

            if(visible_height>=ele_height){
                //可正常显示内容
                obj.addClass('pof');
            }else{
                //滚动差
                $(window).scroll(function(){
                    var v_elem_top=obj.offset()['top'];
                    var elem_true_top=v_elem_top+ele_height-visible_height;
                    var base_top= document.body.scrollTop | document.documentElement.scrollTop;
                    if(base_top>temp){//向下滚动
                        if(temp==base_top){
                            return;
                        }
                        temp=base_top;
                        if(base_top>(elem_true_top)){//到达导航底部
                            if(!obj.hasClass('pof')){
                                obj.addClass('pof').removeClass('poa').css({'marginTop':visible_height-ele_height,top:0});
                                return;
                            }
                        }
                        if(base_top==obj.offset()['top']){//向上滚动后,又向下滚动
                                var temp1=obj.offset()['top']-elem_top;
                                obj.removeClass('pof').addClass('poa').css({'top':temp1,'marginTop':0});
                        }
                    }else{//向上滚动
                        if(temp==base_top){
                            return;
                        }
                        temp=base_top;
                        if((base_top>obj.offset()['top'])){//当在底部时
                            var temp1=obj.offset()['top'];
                            obj.addClass('poa').removeClass('pof').css({'top':temp1,'marginTop':0});
                        }else{//到达底部时
                            if(base_top<elem_top){//到达最顶部
                                obj.removeClass('pof');
                            }else{
                                obj.addClass('pof').removeClass('poa').css({'top':0});
                            }
                        }
                    }
                });
            }
        }();

        $('.call_wangwang').on('click.pt',function(){
            var nick="派生科技";
            QN.wangwang.invoke({
                 category: 'wangwang',
                 cmd: 'chat',
                 param: {'uid':"cntaobao"+nick},
                 success: function (rsp) {
                    QN.wangwang.invoke({
                        "cmd": "insertText2Inputbox",
                        "param": {
                           uid:"cntaobao"+nick,
                           text:"\\C0x0000ff\\T来自千牛pc版：",
                           type:1
                        }
                    });
                     return false;
                 },
                 error: function (msg) {
                    PT.alert('打开失败,请联系['+nick+']');
                 }
             });
        });
    };

    //扩展sui表单验证
    var check_max_price=function(value, element, param){
      if(element.attr('disabled')==='disabled'){
        return true;
      }
      max_price_msg='';
      var temp_min=!isNaN(Number(element.attr('min')))?Number(element.attr('min')):undefined;
      var temp_max=!isNaN(Number(element.attr('max')))?Number(element.attr('max')):undefined;
      if(Number(value)<temp_min){
        max_price_msg='必须大于'+temp_min;
      }
      if(Number(value)>temp_max){
        max_price_msg='必须小于'+temp_max;
      }
      if(max_price_msg!==''){
        if (this.errors[element.attr('name')]!==undefined&&this.errors[element.attr('name')]['custom']!==undefined){
          this.errors[element.attr('name')]['custom'].find('.msg-con span').text(max_price_msg); //刷新suiJs中表单信息
        }
        return false;
      }
      return true;
    };

    var max_price_msg_func=function(){
      return max_price_msg;
    };

    var duplicate_check=function () {
        PT.show_loading("正在下载关键词报表");
        window.location.href = "/web/duplicate_check";
    };

    var sync_all=function(data_type,rpt_days) {
        var tips='';
        if (data_type==1) {
            tips = '正在下载' + rpt_days + '天报表数据，可能耗时较长';
        } else if (data_type==2) {
            tips = '正在重新下载所有结构数据，耗时较长';
        }
        PT.sendDajax({'function':'web_sync_all_data','data_type':data_type,'rpt_days':rpt_days});
        return tips;
    };

    var attention_check=function(){
        PT.show_loading("正在下载关键词报表");
        window.location.href = "/qnpc/attention_list";
    };

    return {
        init: function (){
            init_dom();
        },

        change_msg_count:function() {
            var jq_count=$('#prompt_msg_count'),msg_count=jq_count.text();
            if(msg_count>1){
                jq_count.text(msg_count-1);
            }else{
                jq_count.remove();
            }
        },

        submit_feedback_back: function(result_flag) {
            PT.hide_loading();
            if (result_flag===0) {
                PT.alert('亲，提交失败，非常抱歉，麻烦将意见发给您的顾问');
            } else {
                $('#feedback_modal_dialog').modal('hide');
                PT.alert('提交成功，感谢您的参与！我们会及时处理您的意见' );
            }
        },

        'submit_phone_back': function (is_success) {
            PT.hide_loading();
            if (is_success) {
                PT.light_msg('提交成功','感谢您的信任和支持');
            }
            $('#modal_phone').modal('hide');
        },

        duplicate_check_confirm:function () {
            PT.confirm('关键词报表尚未下载完，会影响系统推荐的删词级别，现在就下载报表并排重吗？',duplicate_check,[],this);
        },
        //跳转到直通车后台的函数
        goto_ztc:function (type, campaign_id, adgroup_id, word) {
            var baseUrl = "http://new.subway.simba.taobao.com/#!/";
            var url = '';
            switch (type) {
                case 1: //添加计划
                    url = baseUrl + 'campaigns/standards/add';
                    break;
                case 2: //添加广告组
                    url = baseUrl + 'campaigns/standards/adgroups/items/add?campaignId=' + campaign_id;
                    break;
                case 3: //添加推广创意
                    url = baseUrl + 'campaigns/standards/adgroups/items/creative/add?adGroupId=' + adgroup_id + '&campaignId=' + campaign_id;
                    break;
                case 4: //管理推广创意
                    url = baseUrl + 'campaigns/standards/adgroups/items/detail?tab=creative&campaignId='+ campaign_id + '&adGroupId=' + adgroup_id;
                    break;
                case 5: //关键词流量解析
                    url = baseUrl + 'tools/insight-old/queryresult?kws=' + encodeURIComponent(word);
                    break;
                case 6://直通车充值
                    url = baseUrl + 'account/recharge';
                    break;
            }

            if (url != ''){
                if (type != 5 && type != 2){
                    PT.alert('亲，如果在后台作了修改，请记得同步到精灵哟!');
                }
                window.open(url, '_blank');
            }
        },
        set_nav_activ:function(index,next){
            //$('.page-sidebar-menu>li').removeClass('active');
            $('.page-sidebar-menu>li:eq('+index+')').addClass('active');
            $('.page-sidebar-menu>li:eq('+index+') .sub-menu li:eq('+next+')').addClass('active')
        },
        sync_result:function(msg){
            PT.hide_loading();
            msg+='即将刷新页面';
            PT.confirm(msg,function(){window.location.reload();});
        },
        attention_check_confirm:function () {
            //PT.confirm('关键词报表尚未下载完，是否现在下载数据？',attention_check,[],this);
            attention_check();
        },
        attention_check_redirect:function(){
            window.location.href="/qnpc/attention_list";
        },
        check_max_price:check_max_price,
        max_price_msg_func:max_price_msg_func
    }
}();



Validate.setRule("custom", PT.Base.check_max_price, PT.Base.max_price_msg_func);

//shift多选用法 1:带回调函数:$select(checkBoxName) 2:带回调 $select({name:checkBoxName,[callBack:fn]})
(function() {
    var arrList = {};
    var $select = window.$select = function(obj) {
        var checkboxName;
        if (typeof (obj) == 'string') {
            checkboxName = obj;
        }
        if (typeof (obj) == 'object') {
            checkboxName = obj.name;
        }

        // Meet the condition of 'checkbox' save into array
        arrList[checkboxName] = getCheckboxArray(checkboxName);

        // Add event for meet the condition of 'checkbox'
        for (var i=0,i_end=arrList[checkboxName].length;i<i_end;i++){
            // Left mouse and shift button event
            !function(){
                var current=arrList[checkboxName][i];
                current.onclick = function() {
                    var afterClickStatus = current.checked ? true : false;
                    mainFunc(current, arrList[current.name], afterClickStatus, obj);
                }

                // Right mouse event
                current.onmouseup = function(e) {
                    var e = window.event || e;
                    if (e.button == 2) {
                        var afterClickStatus = current.checked ? false : true;
                        pressShift = true;
                        mainFunc(current, arrList[current.name], afterClickStatus, obj);
                        pressShift = false;
                    }
                }

                // (For IE) Right mouse event
                current.oncontextmenu = function(event) {
                    if (document.all) {
                        window.event.returnValue = false;
                    } else {
                        event.preventDefault();
                    }
                }
            }();
        }

        // 当checkbox顺序变了之后调用此函数更新
        selectRefresh = function() {
            setTimeout(function() {
                for (var a in arrList)
                    arrList[a] = getCheckboxArray(a);
            }, 1);
            initSelect();
        }
        //表头变化后重置起止位置
        initSelect = function() {
            startEnd = [null, null];
        }
    }
    function getCheckboxArray(checkboxName) {
        var arr = [];
        var inputs = document.getElementsByTagName("input");
        for (var i = 0; i < inputs.length; i++) {
            if (inputs[i].name == checkboxName && inputs[i].type == "checkbox") {
                arr.push(inputs[i]);
            }
        }
        return arr;
    }

    function getIndex(arr,obj){
        for (var i = 0, index = 0; i < arr.length; i++, index++) {
            if (arr[i] == obj) {
                return index;
            }
        }
    }

    var pressShift = false;
    var startEnd = [null, null];

    function mainFunc(current, arr, afterClickStatus, obj) {
        // Get the index which click element in the 'checkbox' array
        var index = getIndex(arr,current);

        if (startEnd[0] == null)
            startEnd[0] = index;
        // 'shift button' whether is press
        if (pressShift) {
            startEnd[1] = index;
            // If select the 'checkbox' from the down top, reverse the array
            if (startEnd[0] > startEnd[1]) {
                startEnd.reverse();
            }

            // Select the 'checkbox'
            for (var j = startEnd[0]; j <= startEnd[1]; j++) {
                if(!arr[j].disabled){
                    arr[j].checked = afterClickStatus;
                }
            }
            startEnd[0] = startEnd[1];
        }
        startEnd[0] = index;
        if (obj.hasOwnProperty('callBack')) {
            obj.callBack.call(obj.that);
        }
    }
    /*<For left mouse and shift button event>*/
    document.onkeydown = function(e) {
        var e = window.event || e;
        if (e.keyCode == 16) {
            pressShift = true;
        } else {
            pressShift = false;
        }
    }
    document.onkeyup = function() {
        pressShift = false;
    }
})();

/*
//使用方法
var now = new Date();
var nowStr = now.format("yyyy-MM-dd hh:mm:ss");
//使用方法2:
var testDate = new Date();
var testStr = testDate.format("YYYY年MM月dd日hh小时mm分ss秒");
alert(testStr);
//示例：
alert(new Date().Format("yyyy年MM月dd日"));
alert(new Date().Format("MM/dd/yyyy"));
alert(new Date().Format("yyyyMMdd"));
alert(new Date().Format("yyyy-MM-dd hh:mm:ss"));
*/

Date.prototype.format = function(format){
    var o = {
        "M+" : this.getMonth()+1, //month
        "d+" : this.getDate(), //day
        "h+" : this.getHours(), //hour
        "m+" : this.getMinutes(), //minute
        "s+" : this.getSeconds(), //second
        "q+" : Math.floor((this.getMonth()+3)/3), //quarter
        "S" : this.getMilliseconds() //millisecond
    }

    if(/(y+)/.test(format)) {
        format = format.replace(RegExp.$1, (this.getFullYear()+"").substr(4 - RegExp.$1.length));
    }

    for(var k in o) {
        if(new RegExp("("+ k +")").test(format)) {
            format = format.replace(RegExp.$1, RegExp.$1.length==1 ? o[k] : ("00"+ o[k]).substr((""+ o[k]).length));
        }
    }
    return format;
}
