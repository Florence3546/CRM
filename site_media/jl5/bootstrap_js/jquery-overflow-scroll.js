/* ===========================================================
 * @version         0.0.1
 * @since           2014.09.19
 * @author          钟进峰
 * @function        自定义滚动条
 * @package         jQuery.js
 */

! function($) {

  "use strict";

  var OverflowScroll = function(element, options) {
    this.$element = $(element);
    this.options = $.extend({}, this.$element.data());
    this.show();
  }

  OverflowScroll.prototype = {
    constructor: OverflowScroll,
    show: function() {
      this.get_info();

      if (this.scroll_h <= 0) {
        this.hide();
        return false;
      }

      this.addScrollBarDom();

      this.setScrollBar();

      this.changeClass();

      this.addEvent();

    },
    hide: function() {
      if (this.$element.data().OverflowScroll) {
        this.$element.find('.scroll-bar-box').remove();
      }
      this.target.removeAttr('style');
      this.$element.off('mousewheel.Bootstrap.api');
    },
    get_info: function() {
      this.target = $(this.options.target);
      this.chird_h = this.target.height();
      this.chird_t = Number(this.target.css('top').replace('px', '')) || 0;
      this.h = this.$element.outerHeight();
      this.scroll_h = this.chird_h - this.h;
    },
    changeClass: function() {
      $(this.options.target).css({
        'position': 'absolute'
      });
      this.$element.css({
        'position': 'relative'
      })
    },
    addEvent: function() {
      var that = this,
        scrollBar = this.$element.find('.scroll-bar'),
        scrollBarBox = this.$element.find('.scroll-bar-box');

      this.scrollBarBoxH = scrollBarBox.height();

      this.$element.off('mousewheel.Bootstrap.api').on('mousewheel.Bootstrap.api', function(e) {
        var current_top = Number(that.target.css('top').replace('px', '')) || 0,
          lastDeltaY = current_top + e.deltaY * 20;

        if (Math.abs(lastDeltaY) > that.scroll_h) {
          lastDeltaY = that.scroll_h * e.deltaY;
        }

        if (e.deltaY > 0 && lastDeltaY > 0) {
          lastDeltaY = 0;
        }

        that.target.css({
          'top': lastDeltaY
        });

        scrollBar.css('marginTop', Math.max((-lastDeltaY / that.chird_h) * that.scrollBarBoxH - 2, 2))

        that.target.trigger('scroll',[-lastDeltaY,that.scroll_h]);

        if ((e.deltaY > 0 && lastDeltaY === 0) || (e.deltaY < 0 && Math.abs(lastDeltaY) === that.scroll_h)) {
          return true;
        }

        e.stopPropagation();
        e.preventDefault();
      });

      this.$element.on('mouseover', function() {
        scrollBarBox.css('visibility', 'visible');
      });

      this.$element.on('mouseout', function() {
        scrollBarBox.css('visibility', 'hidden');
      })
    },
    setScrollBar: function() {
      var that = this,
        lastScrollY,
        scrollBar = this.$element.find('.scroll-bar'),
        scrollBarBox = this.$element.find('.scroll-bar-box');

      scrollBar.css('height', this.h * 100 / this.chird_h + '%');

      this.initscrollBarBoxH = scrollBarBox.offset().top;
      this.scrollBarH = scrollBar.height();
      this.maxScrollH = scrollBarBox.height() - this.scrollBarH;

      scrollBar.css('marginTop', -this.chird_t / this.chird_h * this.h);

      scrollBar.on('mousedown', function(e) {
        that.initscrollBarH = e.offsetY;
        that.scrollBarHodle = true;
        return false;
      });

      $(document).on('mouseup', function() {
        that.scrollBarHodle = false;
        return false;
      });

      $(document).on('mousemove', function(e) {
        if (that.scrollBarHodle) {
          lastScrollY = e.pageY - that.initscrollBarH - that.initscrollBarBoxH;

          if (lastScrollY < 2) {
            lastScrollY = 2;
          }

          if (lastScrollY > that.maxScrollH) {
            lastScrollY = that.maxScrollH - 2;
          }

          scrollBar.css('marginTop', lastScrollY);

          that.target.css({
            'top': -(lastScrollY / that.scrollBarH) * that.h
          });

          that.target.trigger('scroll',[(lastScrollY / that.scrollBarH) * that.h,that.scroll_h]);
        }
      });
    },
    addScrollBarDom: function() {
      var template = document.createElement('div');
      template.className='scroll-bar-box';
      template.innerHTML='<div class="scroll-bar"></div>';
      this.$element[0].appendChild(template);
    }
  }

  $.fn.OverflowScroll = function(option) {
    return this.each(function() {
      var $this = $(this),
        data = $this.data('OverflowScroll'),
        options = $.extend({}, $this.data(), typeof option == 'object' && option);
      if (!data) $this.data('OverflowScroll', (data = new OverflowScroll(this, options)));
      if (typeof option == 'string') data[option]();
    });
  }
}(window.jQuery)
