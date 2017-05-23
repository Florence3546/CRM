/* =========================================================
   * jquery弹层静态方法，用于很少重复，不需记住状态的弹层，可方便的直接调用，最简单形式就是$.alert('我是alert')
   * 若弹层内容是复杂的Dom结构， 建议将弹层html结构写到模版里，用$(xx).modal(options) 调用
   * 
   * example
   * $.alert({
   *  title: '自定义标题'
   *  body: 'html' //必填
   *  okBtn : '好的'
   *  cancelBtn : '雅达'
   *  width: {number|string(px)|'small'|'normal'|'large'}推荐优先使用后三个描述性字符串，统一样式
   *  height: {number|string(px)} 高度
   *  show:     fn --------------function(e){}
   *  shown:    fn
   *  hide:     fn
   *  hidden:   fn
   *  okHide:   function(e){alert('点击确认后、dialog消失前的逻辑,
   *            函数返回true（默认）则dialog关闭，反之不关闭;若不传入则默认是直接返回true的函数
   *            注意不要人肉返回undefined！！')}
   *  okHidden: function(e){alert('点击确认后、dialog消失后的逻辑')}
   *  cancelHide: fn
   *  cancelHidden: fn
   * })
   *
   *  auther:钟进峰  ，本模块模仿千牛sui插件，经过修改而成，感谢千牛sui的大神
   * ========================================================= */

!function($){
  
  "use strict";
  
  var template=function(options){
      var TPL='<div class="modal fade hide" id="<%id%>" tabindex="-1" data-hidetype="remove">'
            +'<div class="modal-header">'
              +'<button type="button" class="close"></button>'
              +'<h5 class="tac"><%title%></h5>'
            +'</div>'
            +'<div class="modal-body"><%body%></div>'
            +'<div class="modal-footer">'
              +'<button class="btn btn-primary" data-ok="modal" action="confirm"><%okBtn%></button>'
              +(options.cancelBtn?'<button class="btn" data-dismiss="modal" aria-hidden="true"><%cancelBtn%></button>':'')
            +'</div>'
          +'</div>';
            
      var element=$(TPL.replace('<%id%>',options.id)
                       .replace('<%title%>',options.title)
                       .replace('<%body%>',options.body)
                       .replace('<%okBtn%>',options.okBtn)
                       .replace('<%cancelBtn%>',options.cancelBtn));
    $('body').append(element);
  }

  $.extend({
      _modal: function(dialogCfg, customCfg){
        var modalId = +new Date()
          ,finalCfg = $.extend({}, $.fn.modal.defaults
            , dialogCfg
            , {id: modalId, okBtn: '确定'}
            , (typeof customCfg == 'string' ? {body: customCfg} : customCfg))
        
        template(finalCfg); //生成dom
        
        var dialog = new $.fn.modal.Constructor($('#'+modalId), finalCfg)
          , $ele = dialog.$element 
        
        function _bind(id, eList){
          var eType = ['show', 'shown', 'hide', 'hidden', 'okHidden', 'cancelHide', 'cancelHidden']
          $.each(eType, function(k, v){
            if (typeof eList[v] == 'function'){
              $(document).on(v, '#'+id, $.proxy(eList[v], $('#' + id)[0]))
            }
          })
        }
        
        _bind(modalId, finalCfg)
        $ele.data('modal', dialog).modal('show')
        
        //静态方法对话框返回对话框元素的jQuery对象
        return $ele
      }
      //为最常见的alert，confirm建立$.modal的快捷方式，
      ,alert: function(customCfg){
        var dialogCfg = {
          type: 'alert'
          ,title: '注意'
        }
        if($('.modal-backdrop').length){
          dialogCfg.backdrop=false;
        }
        return $._modal(dialogCfg, customCfg)
      }
      ,confirm: function(customCfg){
        var dialogCfg = {
          type: 'confirm'
          ,title: '请选择'
          ,cancelBtn: '取消'
        }
        if($('.modal-backdrop').length){
          dialogCfg.backdrop=false;
        }        
        return $._modal(dialogCfg, customCfg)
      }
    })
  
}(window.jQuery)