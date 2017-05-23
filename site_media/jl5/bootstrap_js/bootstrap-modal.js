/* =========================================================
 * bootstrap-modal.js v2.3.2
 * http://getbootstrap.com/2.3.2/javascript.html#modals
 * =========================================================
 * Copyright 2013 Twitter, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * ========================================================= */


!function ($) {

  "use strict";


 /* MODAL CLASS DEFINITION
  * ====================== */

  var Modal = function (element, options) {
    var $container
    this.options = options
    this.$element = $(element)

    if(!this.$element.data('hidetype')){
      $container = $('<div class="modal-scrollable">').append(this.$element)
      $('body').append($container)
    }

    if (this.options.remote){
      (this.$element.find('.modal-body').length?this.$element.find('.modal-body'):this.$element).load(this.options.remote,$.proxy(this.show, this))
    }

    this.$element.delegate('[data-dismiss="modal"]', 'click.dismiss.modal', $.proxy(this.hide, this))
    this.$element.delegate(':not(.disabled)[data-ok="modal"]', 'click.ok.modal', $.proxy(this.okHide, this))
  }

  Modal.prototype = {

      constructor: Modal

    , toggle: function () {
        return this[!this.isShown ? 'show' : 'hide']()
      }

    , show: function () {
        var that = this
          , e = $.Event('show')

        this.$element.trigger(e)

        if (this.isShown || e.isDefaultPrevented()) return

        this.isShown = true

        this.escape()

        this.$element
          .parent().removeClass('hide')

        if (this.options.backdrop || this.options.backdrop == 'static'){
          $('html').addClass('page-overflow')
          // $('html').css({'overflow':'hidden','height':'100%'})
        }

        this.backdrop(function () {
          var transition = $.support.transition && that.$element.hasClass('fade')

          if (!that.$element.parent().length) {
            that.$element.appendTo(document.body) //don't move modals dom position
          }

          that.$element.show()
          that.layout()

          if (transition) {
            that.$element[0].offsetWidth // force reflow
          }

          that.$element
            .addClass('in')

          that.enforceFocus()

          transition ?
            that.$element.one($.support.transition.end, function () { that.$element.focus().trigger('shown') }) :
            that.$element.focus().trigger('shown')

        })
      }

    , hide: function (e) {
        e && e.preventDefault()

        var that = this

        e = $.Event('hide')

        this.hideReason != 'ok' && this.$element.trigger('cancelHide')

        this.$element.trigger(e)

        if (!this.isShown || e.isDefaultPrevented()) return

        this.isShown = false

        this.escape()

        $(document).off('focusin.modal')

        this.$element
          .removeClass('in')

        $.support.transition && this.$element.hasClass('fade') ?
          this.hideWithTransition() :
          this.hideModal()
      }

    ,layout: function () {

            if(this.options.width!==""&&this.options.width!==undefined){
              this.$element.removeClass('small'|'normal'|'large');

              if(isNaN(Number(this.options.width))){
                this.$element.addClass(this.options.width);
                this.options.width=this.$element.width();
              }

              this.$element.css('width', this.options.width);

              var that = this;
              this.$element.css('margin-left', function () {
                  if (/%/ig.test(that.options.width)){
                      return -(parseInt(that.options.width) / 2) + '%';
                  } else {
                      return -($(this).width() / 2) + 'px';
                  }
              });
            }

            if(this.options.height!==""&&this.options.height!==undefined){
              this.$element.find('.modal-body').css('height',this.options.height);
            }

            var modalOverflow = $(window).height() - 10 < this.$element.outerHeight();

            if (modalOverflow || this.options.modalOverflow) {
                this.$element.css('top', 0);
            }else{
                if(!this.$element.attr('style')||this.$element.attr('style').toLowerCase().match(/.*margin-top.*/)===null){
                  this.$element.css('margin-top',-this.$element.outerHeight() / 2)
                }
            }
		}

    , okHide: function(e){

        function hideWithOk (){
          self.hideReason = 'ok'
          self.hide(e)
        }

        var self = this
        // 如果e为undefined而不是事件对象，则说明不是点击确定按钮触发的执行，而是手工调用，
        // 那么直接执行hideWithOk
        if (!e) {
          hideWithOk()
          return
        }
        var fn = this.options.okHide
          , ifNeedHide = true
        if (!fn) {
            var eventArr = $._data(this.$element[0], 'events').okHide
            if (eventArr && eventArr.length) {
                fn = eventArr[eventArr.length - 1].handler;
            }
        }
        typeof fn == 'function' && (ifNeedHide = fn.call(this))
        //显式返回false，则不关闭对话框
        if (ifNeedHide !== false){
          hideWithOk()
        }

        return self.$element
    }
    //对话框内部遮罩层
    , shadeIn: function () {
        var $ele = this.$element
        if ($ele.find('.shade').length) return
        var $shadeEle = $('<div class="shade in"></div>')
        $shadeEle.appendTo($ele)
        this.hasShaded = true
        return this.$element
    }
    , shadeOut: function () {
        this.$element.find('.shade').remove()
        this.hasShaded = false
        return this.$element
    }
    , shadeToggle: function () {
        return this[!this.hasShaded ? 'shadeIn' : 'shadeOut']()
    }
    , enforceFocus: function () {
        var that = this
        //防止多实例循环触发focus事件
        $(document).off('focusin.modal').on('focusin.modal', function (e) {
          if (that.$element[0] !== e.target && !that.$element.has(e.target).length) {
            that.$element.focus()
          }
        })
      }

    , escape: function () {
        var that = this
        if (this.isShown && this.options.keyboard) {
//          this.$element.on('keyup.dismiss.modal', function ( e ) {
//            e.which == 27 && that.hide()
//          })
          $(document).on('keyup.dismiss.modal', this.$element, function (e) {
            e.which == 27 && that.hide();
          })
        } else if (!this.isShown) {
//          this.$element.off('keyup.dismiss.modal')
          $(document).off('keyup.dismiss.modal', this.$element);
        }
      }

    , hideWithTransition: function () {
        var that = this
          , timeout = setTimeout(function () {
              that.$element.off($.support.transition.end)
              that.hideModal()
            }, 500)

        this.$element.one($.support.transition.end, function () {
          clearTimeout(timeout)
          that.hideModal()
        })
      }

    , hideModal: function () {
        var that = this
        this.$element.hide()
        this.backdrop(function () {
          that.removeBackdrop()
          that.$element.trigger(that.hideReason == 'ok' ? 'okHidden' : 'cancelHidden')
          that.hideReason = null
          that.$element.trigger('hidden')
          //销毁静态方法生成的dialog元素 , 默认只有静态方法是remove类型
          that.$element.data('hidetype') == 'remove' && that.$element.remove()
          if(!that.$element.data('hidetype')){
            that.$element.parent().addClass('hide')
          }
          if(!that.hasOpenModal()){
            $('html').removeClass('page-overflow')
          }
        })
      }

    , removeBackdrop: function () {
        this.$backdrop && this.$backdrop.remove()
        this.$backdrop = null
      }

    , backdrop: function (callback) {
        var that = this
          , animate = this.$element.hasClass('fade') ? 'fade' : ''

        if (this.isShown && this.options.backdrop) {
          var doAnimate = $.support.transition && animate

          this.$backdrop = $('<div class="modal-backdrop ' + animate + '" />')
            .appendTo(document.body)

          this.$backdrop.click(
            this.options.backdrop == 'static' ?
              $.proxy(this.$element[0].focus, this.$element[0])
            : $.proxy(this.hide, this)
          )

          if (doAnimate) this.$backdrop[0].offsetWidth // force reflow

          this.$backdrop.addClass('in')

          if (!callback) return

          doAnimate ?
            this.$backdrop.one($.support.transition.end, callback) :
            callback()

        } else if (!this.isShown && this.$backdrop) {
          this.$backdrop.removeClass('in')

          $.support.transition && this.$element.hasClass('fade')?
            this.$backdrop.one($.support.transition.end, callback) :
            callback()

        } else if (callback) {
          callback()
        }
      }
    , hasOpenModal: function () {
      return $('.modal.in').length;
    }
  }


 /* MODAL PLUGIN DEFINITION
  * ======================= */

  var old = $.fn.modal

  $.fn.modal = function (option) {
    return this.each(function () {
      var $this = $(this)
        , data = $this.data('modal')
        , options = $.extend({}, $.fn.modal.defaults, $this.data(), typeof option == 'object' && option)
      if (!data) $this.data('modal', (data = new Modal(this, options)))
      if (typeof option == 'string') data[option]()
      else if (options.show && !(typeof option !=='undefined'&&/#/.test(option.remote))) data.show()
    })
  }

  $.fn.modal.defaults = {
      backdrop: true
    , keyboard: true
    , show: true
  }

  $.fn.modal.Constructor = Modal


 /* MODAL NO CONFLICT
  * ================= */

  $.fn.modal.noConflict = function () {
    $.fn.modal = old
    return this
  }


 /* MODAL DATA-API
  * ============== */

  $(document).on('click.modal.data-api', '[data-toggle="modal"]', function (e) {
    var $this = $(this)
      , href = $this.attr('href')
      , $target = $($this.attr('data-target') || (href && href.replace(/.*(?=#[^\s]+$)/, ''))) //strip for ie7
      , option = $target.data('modal') ? 'toggle' : $.extend({ remote:!/#/.test(href) && href }, $target.data(), $this.data())

    e.preventDefault()

    $target
      .modal(option)
//      .one('hide', function () {
//        $this.focus()
//      })
  })

}(window.jQuery);
