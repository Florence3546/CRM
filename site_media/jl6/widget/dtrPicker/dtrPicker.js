define("jl6/site_media/widget/dtrPicker/dtrPicker",["jl6/site_media/plugins/moment/moment.min","jl6/site_media/plugins/jquery-ui-daterangepicker/jquery.comiseo.daterangepicker.min"],function(t){"use strict";$.datepicker.regional["zh-cn"]={clearText:"清除",clearStatus:"清除已选日期",closeText:"关闭",closeStatus:"不改变当前选择",prevText:"<上月",prevStatus:"显示上月",prevBigText:"<<",prevBigStatus:"显示上一年",nextText:"下月>",nextStatus:"显示下月",nextBigText:">>",nextBigStatus:"显示下一年",currentText:"今天",currentStatus:"显示本月",monthNames:["一月","二月","三月","四月","五月","六月","七月","八月","九月","十月","十一月","十二月"],monthNamesShort:["一","二","三","四","五","六","七","八","九","十","十一","十二"],monthStatus:"选择月份",yearStatus:"选择年份",weekHeader:"周",weekStatus:"年内周次",dayNames:["星期日","星期一","星期二","星期三","星期四","星期五","星期六"],dayNamesShort:["周日","周一","周二","周三","周四","周五","周六"],dayNamesMin:["日","一","二","三","四","五","六"],dayStatus:"设置 DD 为一周起始",dateStatus:"选择 m月 d日, DD",dateFormat:"yy-mm-dd",firstDay:1,initStatus:"请选择日期",isRTL:!1},$.datepicker.setDefaults($.datepicker.regional["zh-cn"]);var e=[{text:"今日实时",dateStart:function(){return t()},dateEnd:function(){return t()}},{text:"昨天",dateStart:function(){return t().subtract(1,"days")},dateEnd:function(){return t().subtract(1,"days")}},{text:"过去3天",dateStart:function(){return t().subtract(3,"days")},dateEnd:function(){return t().subtract(1,"days")}},{text:"过去7天",dateStart:function(){return t().subtract(7,"days")},dateEnd:function(){return t().subtract(1,"days")}},{text:"过去15天",dateStart:function(){return t().subtract(15,"days")},dateEnd:function(){return t().subtract(1,"days")}},{text:"过去30天",dateStart:function(){return t().subtract(30,"days")},dateEnd:function(){return t().subtract(1,"days")}},{text:"上个月",dateStart:function(){return t().subtract(1,"month").startOf("month")},dateEnd:function(){return t().subtract(1,"month").endOf("month")}}],a=function(t){var a,r;a="0"==t.attr("rt_rpt")?e.slice(1):"1"==t.attr("rt_rpt")?e.slice(1,-1):e,r=Number(t.attr("months"))||3,t.daterangepicker({presetRanges:a,initialText:t.data().initText||"过去7天",rangeSplitter:"&emsp;至&emsp;",dateFormat:"mm-dd",altFormat:"yy-mm-dd",applyOnMenuSelect:!1,applyButtonText:"确定",cancelButtonText:"取消",datepickerOptions:{numberOfMonths:r+1,minDate:30*-r,maxDate:0}})};return $("[data-toggle=dtr_picker]").each(function(){a($(this))}),{init:a}});