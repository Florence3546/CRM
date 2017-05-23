/* ===========================================================
 * @version			0.0.1
 * @since			2014.08.04
 * @author			钟进峰
 * @function        单选开关
 * @package			jQuery.js
 */

! function ($) {

  "use strict";

  var Switch = function (element, options) {
    this.$element = $(element);
    this.options = $.extend({}, this.$element.data());
  }

  Switch.prototype = {
    constructor: Switch,
    toggle: function () {
      this[!this.$element.hasClass('on') ? 'show' : 'hide']();
    },
    show: function () {
      if (!this.$element.hasClass('on')){
        this.$element.addClass('on');
        this.$element.find('input').attr('checked',true).trigger('change',[true]);
      }

    },
    hide: function () {
      if (this.$element.hasClass('on')){
        this.$element.removeClass('on');
        this.$element.find('input').attr('checked',false).trigger('change',[false]);
      }      
    }
  }


  $(document).on('click.switch.data-api', '[data-toggle="switch"]', function (e) {
     var $this = $(this)
        , data = $this.data('Switch')
      if (!data) $this.data('Switch', (data = new Switch(this)))    
      data.toggle();
  })
}(window.jQuery)