define("site_media/service/rob_rank/real_time",["site_media/plugins/artTemplate/template","site_media/widget/ajax/ajax","site_media/plugins/moment/moment.min","site_media/plugins/highcharts/highcharts"],function(i,t,e){"use strict";var a,n='<div style="width: 600px; margin-left: -300px; left:50%;" tabindex="-1" role="dialog" data-hasfoot="false" class="sui-modal hide fade"  id="real_time">\n    <div class="modal-dialog">\n        <div class="modal-content">\n            <div class="modal-header">\n                <button type="button" data-dismiss="modal" aria-hidden="true" class="sui-close">×</button>\n                <h4 class="modal-title">“{{word}}”抢排名趋势，<span class="finished_status">正在抢......，请勿关闭窗口</span></h4>\n            </div>\n            <div class="modal-body">\n                <table class="main_info">\n                    <tr>\n                        <td><span class="img">&emsp;</span>{{if platform == \'pc\'}}计算机{{else}}移动{{/if}}出价：<span class="price">--</span>&ensp;元</td>\n                        <td class="msg">&emsp;</td>\n                        <td>\n                            <div class="show_model">\n                                <a class="active" data-type="rob_chat"><i class="iconfont b">&#xe60d;</i></a>\n                                <a data-type="rob_sub_info"><i class="iconfont b">&#xe60e;</i></a>\n                            </div>\n                        </td>\n                    </tr>\n                </table>\n                <div id="rob_chat" class="mt10" style="min-width:300px;height:240px"></div>\n                <div class="sub_info hide" id="rob_sub_info">\n                    <ol>\n                    </ol>\n                </div>\n                <div class="gray f12" style="margin-top:10px;">\n                    当前设置：{{if method == \'manual\'}}手动{{else}}自动{{/if}}，{{if platform == \'pc\'}}计算机{{else}}移动{{/if}}，{{rank_start_name}}~{{rank_end_name}}\n                </div>\n                <div class="red f12 mt5 hide" id="rob_tips">设置抢排名成功，正在测试</div>\n            </div>\n            <div class="modal-footer">\n                <button type="button" class="sui-btn btn-bordered btn-xlarge btn-primary reset">重新设置</button>\n                <button type="button" class="sui-btn btn-xlarge btn-primary submit" data-dismiss="modal">关闭</button>\n            </div>\n        </div>\n    </div>\n</div>\n',s=function(t){var e,a,s=!1;e=i.compile(n)(t),a=$(e),$("body").append(a),a.modal({backdrop:"static"}),"auto"==t.method&&a.find("#rob_tips").removeClass("hide"),a.on("shown.bs.modal",function(){var i=this;r(t),c(),$(this).find(".reset").on("click",function(){s=!0,$(i).modal("hide")})}),a.on("hidden.bs.modal",function(){s&&$("#"+t.keywordId).trigger("get.rob_set",[t]),$(this).remove(),l()}),a.find(".show_model a").on("click",function(){var i=$(this).data().type;a.find(".show_model a").removeClass("active"),$(this).addClass("active"),$("#rob_chat,#rob_sub_info").addClass("hide"),$("#"+i).removeClass("hide")})},r=function(i){var t,e;t="ws://"+window.location.host+"/websocket/?keyword_id="+i.keywordId,e=new WebSocket(t),e.onmessage=function(t){if(""!=t&&void 0!=t){if("ready"==t.data)return d(i),!1;var a=$.evalJSON(t.data);o(i,a,e)}}},d=function(i){t.ajax("manual_rob_rank",{keyword_id:i.keywordId,adgroup_id:i.adgroupId,exp_rank_start:i.rank_start,exp_rank_end:i.rank_end,limit_price:parseInt(100*i.limit+.5),platform:i.platform,nearly_success:i.nearly_success},function(i){if(""!=i.limitError){var t,e;"version_limit"==i.limitError&&(t="Sorry!当前版本不支持",e='亲，您订购的版本不支持手动抢排名哦，请升级到双引擎版！&emsp;&emsp;<a href="/web/upgrade_suggest/" target="_blank">立即升级</a></div></div>'),"others"==i.limitError&&(t="Sorry，自动抢排名失败",e="亲，请刷新页面重试"),$.alert({title:t,closeBtn:!1,body:e,okBtn:"知道了",height:"60px",backdrop:"static",keyboard:!1})}})},o=function(i,t,a){var n=$("#real_time"),s=$("#"+i.keywordId),r="doing";("ok"==t.result_flag||"nearly_ok"==t.result_flag)&&(n.find(".main_info").addClass("success"),n.find(".finished_status").text("抢排名成功"),n.find("#rob_tips").text("设置抢排名成功：系统将在您 指定的时间段内每隔15~30分钟自动为关键词抢排名"),s.trigger("update.rank",[t.cur_rank_dict.pc,t.cur_rank_dict.yd,t.cur_rank_dict.pc_desc,t.cur_rank_dict.yd_desc]),"rank"!=i.target&&s.trigger("update.rob_rank",["success",Number(t.price).toFixed(2),t.platform]),r="finish",a.close()),("done"==t.result_flag||"failed"==t.result_flag)&&(n.find(".main_info").addClass("fail"),n.find(".finished_status").text("抢排名失败"),n.find("#rob_tips").text("测试抢排名失败：建议你重新设置提高限价"),s.trigger("update.rank",[t.cur_rank_dict.pc,t.cur_rank_dict.yd,t.cur_rank_dict.pc_desc,t.cur_rank_dict.yd_desc]),"rank"!=i.target&&s.trigger("update.rob_rank",["fail"]),r="finish",a.close()),c(t),n.find("ol").append("<li class='"+r+"''><span>"+e(t.rob_time).format("H:mm:ss")+"<span class='r'>"+Number(t.price).toFixed(2)+"元</span></span><span>"+t.msg+"</span></li>"),n.find(".main_info .price").text(Number(t.price).toFixed(2)),n.find(".main_info .msg").text(t.msg)},l=function(){a=void 0},c=function(i){if(a){var t={y:Number(i.price),data:i.msg};("ok"==i.result_flag||"nearly_ok"==i.result_flag)&&(t.marker={fillColor:"#1ede20",states:{hover:{fillColor:"#1ede20",lineColor:"#1ede20"}}}),("done"==i.result_flag||"failed"==i.result_flag)&&(t.marker={fillColor:"#fd5726",states:{hover:{fillColor:"#fd5726",lineColor:"#fd5726"}}}),$("#rob_chat").highcharts().series[0].addPoint(t),$("#rob_chat").highcharts().series[1].addPoint({y:i.cur_rank_dict.pc,data:i.msg})}else a=$("#rob_chat").highcharts({chart:{type:"spline"},title:{text:""},subtitle:{text:""},legend:{enabled:!0},credits:{text:""},xAxis:{type:"linear",minTickInterval:1,formatter:function(){return this.value+1}},yAxis:[{title:{text:""},min:0,gridLineColor:"#ddd",gridLineDashStyle:"Dash",gridLineWidth:1},{title:{text:""},opposite:!0,min:0,gridLineColor:"#ddd",gridLineDashStyle:"Dash",gridLineWidth:1,labels:{formatter:function(){return""}}}],plotOptions:{spline:{marker:{radius:4,lineColor:"#666666",lineWidth:1}}},series:[{name:"出价",lineColor:"#76a0c6",marker:{lineWidth:0,width:8,height:8,symbol:"circle",fillColor:"#1a8bf1"}},{name:"排名",yAxis:1,lineColor:"#ccc",marker:{lineWidth:0,width:8,height:8,symbol:"circle",fillColor:"#aaa"}}],tooltip:{crosshairs:!0,shared:!0,formatter:function(){return"当前出价:"+this.y.toFixed(2)+"<br/>"+this.points[0].point.data}}})};return{show:s}});