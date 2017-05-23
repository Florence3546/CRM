define(["jquery","bootstrap"],function($) {
    "use strict";

      var popoverList = function (element, options) {
        this.init('popoverList', element, options);
      }

      popoverList.DEFAULTS = $.extend({}, $.fn.popover.Constructor.DEFAULTS, {
        placement: 'right',
        trigger: 'click',
        content: '',
        template: '<div class="popover" role="tooltip"><div class="arrow"></div><div class="popover-content list"></div></div>'
      });

      popoverList.prototype = $.extend({}, $.fn.popover.Constructor.prototype)

      popoverList.prototype.constructor = popoverList;

      popoverList.prototype.getDefaults = function (options) {
        popoverList.DEFAULTS.container=this.$element;
        return popoverList.DEFAULTS
      }

      popoverList.prototype.getOptions = function (options) {
        options = $.extend({}, this.getDefaults(options), this.$element.data(), options)

        if (options.delay && typeof options.delay == 'number') {
          options.delay = {
            show: options.delay,
            hide: options.delay
          }
        }

        return options
      }

      popoverList.prototype.setContent = function () {
        var $tip    = this.tip()
        var title   = this.getTitle()
        var content = this.getContent()
        var self=this

        $tip.find('.popover-title')[this.options.html ? 'html' : 'text'](title)
        $tip.find('.popover-content').children().detach().end()[ // we use append for html objects to maintain js events
          this.options.html ? (typeof content == 'string' ? 'html' : 'append') : 'text'
        ](content)

        $tip.removeClass('fade top bottom left right in')

        // IE8 doesn't accept hiding via the `:empty` pseudo selector, we have to do
        // this manually by checking the contents.
        if (!$tip.find('.popover-title').html()) $tip.find('.popover-title').hide()

        //注入ul选中的代码
        $tip.find('.list ul>li').on('click',function(){
          self.options.onChange&&self.options.onChange($(this).data());
        });
      }

      popoverList.prototype.hide = function (callback) {
        var that = this
        var $tip = $(this.$tip)
        var e    = $.Event('hide.bs.' + this.type)

        function complete() {
          if (that.hoverState != 'in') $tip.detach()
          that.$element
            .removeAttr('aria-describedby')
            .trigger('hidden.bs.' + that.type)
          callback && callback()
        }

        this.$element.trigger(e)

        if (e.isDefaultPrevented()) return

        $tip.removeClass('in')

        $.support.transition && $tip.hasClass('fade') ?
          $tip
            .one('bsTransitionEnd', complete)
            .emulateTransitionEnd(popoverList.TRANSITION_DURATION) :
          complete()

        this.hoverState = null

        //what a fuck 强制隐藏后把点击改为false,以免再次点击时不起作用
        this.inState['click']=false;

        return this
      }

      function Plugin(option) {
        return this.each(function () {
          var $this   = $(this)
          var data    = $this.data('bs.popoverList')
          var options = typeof option == 'object' && option

          if (!data && /destroy|hide/.test(option)) return
          if (!data) $this.data('bs.popoverList', (data = new popoverList(this, options)))
          if (typeof option == 'string') data[option]()
        })
      }

      function clearM(e){
        $('.popover').each(function(){
          if($(e.target).find('>div').attr('id')==this.id) return
          $(this).popoverList('hide');
        });
      }

      $.fn.popoverList=Plugin;

      $.fn.popoverList.Constructor = popoverList;

      $(document).on('click.bs.popoverList.data-api', clearM);

});
