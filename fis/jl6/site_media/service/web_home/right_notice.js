/**
 * Created by Administrator on 2015/9/17.
 */
define(['template'],function(template){

   var init = function(){



       var main_ad_event = require('../common/main_poster_event');
       //公告点击事件
       $('.right_notice_link').click(function(){
           var a = $(this).find("a");
           var ad_content = $(this).find("input[type=hidden]");
           var ad_title = $(this).find('.right_notice_title').text();
           var obj,
               tpl=__inline('right_notice.html');

           template.config('escape', false)
           var html = template.compile(tpl)({ad_content:ad_content.val(),ad_title:ad_title});

           obj=$(html);
           $('body').append(obj);
           if(a.attr('href')=='javascript:;'){
               obj.modal();
           }

           obj.on('hide.bs.modal',function(){
                obj.remove();
           });

           //点击公告后需要将公告点击次数加1
           main_ad_event.addClickTimes($(this).attr('ad_id'));
       });

       $('.right_notice_link').each(function(){
           main_ad_event.addViewTimes($(this).attr('ad_id'));
       });
   };

   return {
       init:function(){
           init();
       }
   }
});