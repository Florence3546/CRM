define("site_media/widget/ajax/ajax",["site_media/widget/loading/loading"],function(e){"use strict";var t=function(t,n){""!=t.errMsg?($.alert({title:"错误",closeBtn:!1,body:t.errMsg,okBtn:"确定",height:"60px"}),e.hide()):n&&n(t)},n=function(n,a,i,d,o){var r={url:"/qnyd/ajax/",type:"post",dataType:"json",data:$.extend({},{"function":n||"undefined"},a),timeout:6e4,cache:!1,success:function(e){t(e,i)},error:d||function(){e.hide()}};r=$.extend({},r,o),$.ajax(r)};return{ajax:n}});