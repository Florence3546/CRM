PT.namespace('new_CustomerList');
PT.new_CustomerList = function () {

  var add_remark_id, contral_table_id, temp_mark_content;

  //css3 animate动画发生器
  var css_animate = function (obj, animate) {
    obj.addClass(animate).addClass('animated');
    setTimeout(function () {
      obj.removeClass(animate).removeClass('animated');
    }, 1000);
  }

  //获取指定className里面的input信息并用它的className组成键值对
  var get_data_4input = function (obj) {
    var data = {};
    $('.post_data input', obj).each(function () {
      if (this.value !== '') {
        data[this.className] = this.value;
      }
    });
    $('.post_data textarea', obj).each(function () {
      if (this.value !== '') {
        data[this.className] = this.value;
      }
    });
    $('.post_data select', obj).each(function () {
      if (this.value !== '') {
        data[this.className] = this.value;
      }
    });
    return data;
  }

  var init_dom = function () {
    // 修改评价
    $('.comment_box input').click(function () {
      if(confirm('确定修改评价状态吗？')){
        PT.sendDajax({
          'function': 'crm_change_comment',
          "customer_id": this.name.split('_')[1],
          'status': this.value,
          'back_fuc': 'PT.new_CustomerList.change_comment_back',
          'is_manual': 1
        });
        return true;
      }
        return false;
    });

    //修改用户状态
    $('.dangerous_box input').click(function (e) {
      if (confirm('确定修改用户状态吗？')) {
        PT.sendDajax({
          'function': 'crm_change_dangerous',
          "customer_id": this.name.split('_')[1],
          'status': this.value,
          'back_fuc': 'PT.new_CustomerList.change_dangerous_back',
          'is_manual': 1
        });
        if(this.value=='4'){
          $('#refund_tip_' + this.name.split('_')[1]).show();
          PT.light_msg('提示','记得添加退款跟踪表哦')
        }
        this.checked=true;
        return true;
      }
      this.checked=false;
      return false;
    });

    //修改回访次数
    $('i[class^="icon-circle-arrow"]').click(function () {
      $(this).attr('disable', true);
      if ($(this).attr('disable') !== true) {
        var now = new Date(),
          mode = -1;
        nowStr = now.format("yyyy-MM-dd  hh:mm:ss"),
        customer_id = this.getAttribute('value');

        if (this.className.indexOf('up') !== -1) {
          mode = 1;
        }

        $('#revisit_count_' + customer_id).text(Number($('#revisit_count_' + customer_id).text()) + mode);

        $('#revisit_time_' + customer_id).text(nowStr.split(' ')[0]);
        PT.sendDajax({
          'function': 'crm_change_revisit',
          "customer_id": customer_id,
          "revisit_time": nowStr,
          "mode": mode,
          'back_fuc': 'PT.new_CustomerList.change_revisit_back',
          'is_manual': 1
        });
      }
    });

    //添加个备注
    $('.add_remark').click(function () {
      add_remark_id = this.getAttribute('value');
      $('#remark').val(''); //清空备注
    });

    //新增备注
    $('#add_remark_submit').click(function () {
      var remark = $.trim($('#remark').val());
      if (remark === '') {
        css_animate($('#add_remark'), 'shake');
        return;
      }
      $('#remark_close').click();
      PT.sendDajax({
        'function': 'crm_add_remark',
        "customer_id": add_remark_id,
        "remark": remark,
        'back_fuc': 'PT.new_CustomerList.add_remark_back',
        'is_manual': 1
      });
    });

    //查看历史备注
    $('.histary_remark').click(function () {
      PT.sendDajax({
        'function': 'crm_histary_remark',
        "customer_id": this.getAttribute('value'),
        'is_manual': 1
      });
    });
    
    //查看店铺数据
    $('.check_shopdata').click(function(){
    	var shop_id = parseInt($(this).attr('shop_id'));
    	var nick = $(this).attr('nick');
    	PT.sendDajax({'function':'crm_get_shop_data', 'shop_id':shop_id , 'nick':nick});
    });
    

    //表格操作列中的点击事件
    $('.contral_list a[ajax]').click(function () {
      var send_data, ajax_name = this.getAttribute('ajax'),
        ajax_status = this.getAttribute('ajax_status');
      contral_table_id = this.parentNode.getAttribute('value'); //记录当前管控表操作的id
      $('#add_' + ajax_name).find('.modal-body input[type="text"]').val(''); //清空页面中的表单
      $('.tooltip').remove(); //清空表单验证提示
      eval('get_' + ajax_name + '_before()'); //将页面上已经有的数据填充

      if (ajax_status == 'true') {
        send_data = {
          'function': 'crm_get_control_table',
          "table": ajax_name,
          "customer_id": contral_table_id,
          "back_fuc": 'PT.new_CustomerList.get_' + ajax_name + '_back',
          'is_manual': 1
        }

        PT.sendDajax(send_data);
      }
    });

    $('form.vaildataForm').vaildata({
      submit: false,
      call_back: PT.new_CustomerList.submit_control_table
    });

    $(document).keypress(function (e) {
      var key = e.keyCode || e.which || e.charCode
      switch (key) {
      case 13:
        $('#id_search_form').attr('action', '');
        $('#id_search_form').submit();
        break;
      }
    });

    $('#export_data').click(function(){
    	function export_data(){
    		$('#id_search_form').attr('action', '/crm/export_customer_data/');
    		$('#id_search_form').submit();
    	}
    	PT.confirm("确定要导出所有数据吗？", export_data, []);
    });
        
    $('#query_btn').click(function(){
       $('#id_search_form').attr('action', '');
       $('#id_search_form').submit(); 
    });

    $('.order_list_more').click(function () {
      var table, parent, i_dom;
      table = $(this).prev();
      parent = $(this).parent();
      i_dom = $('i', this);
      if (i_dom[0].className == 'icon-chevron-down') {
        parent.animate({
          height: table.height()
        }, 100);
        i_dom.attr('class', 'icon-chevron-up');
      } else {
        parent.animate({
          height: 110
        }, 100);
        i_dom.attr('class', 'icon-chevron-down');
      }
    });

    //历史备注修改
    $(document).on('click.PT.edit', '#histary_remark .accordion .edit', function (e) {
      var index = $(this).attr('index');
      if ($(this).text() == '修改') {
        var content = $('#mark_content_' + index).text();
        $(this).text('保存');
        temp_mark_content = content;
        $('#mark_content_' + index).html('<textarea>' + $('#mark_content_' + index).text() + '</textarea>');
      } else {
        var content = $('#mark_content_' + index).find('textarea').val();
        $(this).text('修改');

        if (content === '') {
          $('#mark_content_' + index).find('textarea').val(temp_mark_content);
          PT.alert('请填写修改内容。');
          return false;
        }

        if (content === temp_mark_content) { //判断是否有过修改
          $('#mark_content_' + index).html(content);
          return false;
        }

        PT.sendDajax({
          'function': 'crm_edit_remark',
          'remark_id': index,
          'content': content,
          'back_fuc': 'PT.new_CustomerList.edit_remark_back',
          'is_manual': 1
        });
      }
    });

    //删除历史备注
    $(document).on('click.PT.edit', '#histary_remark .accordion .delete', function (e) {
      var index = $(this).attr('index');
      PT.sendDajax({
        'function': 'crm_delete_remark',
        'remark_id': index,
        'back_fuc': 'PT.new_CustomerList.delete_remark_back',
        'is_manual': 1
      });
    });

    //管控表修改操作
    $('.control_table').on('click.PT.control_table.edit', 'a.edit', function () {
      var i = 0,
        s = 0,
        obj = $(this).parent().parent(),
        id = obj.children('td:first').text(),
        edit_able_td = obj.children('td.edit_able'),
        remove_disabled_select = obj.children('td.remove_disabled').find('select');

      if ($(this).text() === '修改') {
        $(this).text('保存');
        edit_able_td.attr('contenteditable', true).addClass('editing');
        remove_disabled_select.removeAttr('disabled');
      } else {
        var data = {};
        $(this).text('修改');
        edit_able_td.removeAttr('contenteditable').removeClass('editing');
        remove_disabled_select.attr('disabled', true);

        for (i; i < edit_able_td.length; i++) {
          var key = $(edit_able_td[i]).attr('filed'),
            value = $(edit_able_td[i]).text();
          data[key] = value;
        }

        for (s; s < remove_disabled_select.length; s++) {
          var key = $(remove_disabled_select[s]).attr('filed'),
            value = $(remove_disabled_select[s]).val();
          data[key] = value;
        }

        data['id'] = id;
        table = $(this).parents('fieldset:first').prev().find('.btn[ajax]').attr('ajax');

        PT.sendDajax({
          'function': 'crm_set_control_table',
          'table': table,
          'data': $.toJSON(data),
          'back_fuc': 'PT.new_CustomerList.set_control_table',
          'is_manual': 1
        });
      }
    });

    //删除管控表
    $('.control_table').on('click.PT.control_table.edit', 'a.delete', function () {
      var id = $(this).parent().parent().children('td:first').text(),
        table = $(this).parents('fieldset:first').prev().find('.btn[ajax]').attr('ajax');

      PT.sendDajax({
        'function': 'crm_delete_control_table',
        'table': table,
        'id': id,
        'back_fuc': 'PT.new_CustomerList.delete_control_table',
        'is_manual': 1
      });
    });
    
    // 店铺全选&单选
    $('#check_all_shop').click(function (event) {
	    event.stopPropagation();
	    var td_checkbox = $('#user_table>tbody>tr>td:first-child');
	    td_checkbox.children(':checkbox[name="shop_id"]').attr('checked', this.checked);
	    switch (this.checked) {
		    case true:
			    $(this).parent().add(td_checkbox).addClass('checked');
			    break;
		    case false:
			    $(this).parent().add(td_checkbox).removeClass('checked');
			    break;
	    }
    });
    
    $('#user_table>tbody>tr>td:first-child>:checkbox[name="shop_id"]').click(function (event) {
	    event.stopPropagation();
        switch (this.checked) {
            case true:
                $(this).parent().addClass('checked');
                break;
            case false:
                $(this).parent().removeClass('checked');
                break;
        }
    });
    
    $('#user_table>thead>tr>th:first-child, #user_table>tbody>tr>td:first-child').click(function () {
	    $(this).children(':checkbox').click();
    });
    
    $('#user_table>tbody>tr>td:first-child').mouseup(function (event) {
	    var event = window.event || event;
	    if (event.button==2 && event.target==this) {
		    $(this).children('[name="shop_id"]').triggerHandler({type:'mouseup', button:2});
	    }
	    this.oncontextmenu = function (e) {
		    if (document.all) {
			    window.event.returnValue = false;
		    } else {
			    e.preventDefault();
		    }
	    }
    });
    
    $select({name:'shop_id', callBack:function () {
	    $('#user_table>tbody>tr>td:first-child:has([name="shop_id"]:checked)').addClass('checked');
	    $('#user_table>tbody>tr>td:first-child>[name="shop_id"]:not(:checked)').parent().removeClass('checked');
    }});
    
    //分配顾问
    $('#btn_allocate_consult').click(function () {
	    var checked_count = $('#user_table>tbody>tr>td:first-child>[name="shop_id"]:checked').length;
	    if (checked_count>0) {
		    $('#modal_allocate_consult .checked_count').html(checked_count);
		    $('#modal_allocate_consult').modal('show');
	    } else {
		    PT.alert('还没有勾选任何店铺！');
	    }
    });
    
    $('#submit_allocate_consult').click(function () {
	    var psuser_id = Number($('#modal_allocate_consult select[name="consult"]').val());
	    if (psuser_id) {
	        var shop_id_list = $.map($('#user_table>tbody>tr>td:first-child>[name="shop_id"]:checked'), function (checked) {
	            return Number(checked.value);
	        });
	        PT.show_loading('正在分配顾问');
	        PT.sendDajax({'function':'crm_allocate_single_consult',
							        'shop_id_list':$.toJSON(shop_id_list),
							        'psuser_id':psuser_id
	        });
	    } else {
		    PT.alert('还没有选择要分配的顾问！');
	    }
    });
    
    // 关闭抽奖信息
    $('#user_table>tbody>tr>td:last-child .hide_lottery').click(function () {
	    PT.show_loading('正在关闭抽奖信息');
	    PT.sendDajax({'function':'crm_hide_lottery', 'shop_id':$(this).closest('tr').attr('id').replace(/tr_/, '')});
    });
  }

  var submit_control_table = function (obj) {
    var index = $('input[type="submit"]', obj).attr('ajax');
    post_data = get_data_4input($('#add_' + index));
    post_data['customer_id'] = contral_table_id;
    post_data['function'] = 'crm_set_' + index;
    post_data['back_fuc'] = 'PT.new_CustomerList.set_' + index + '_back';
    post_data['is_manual'] = 1;
    PT.sendDajax(post_data);
    $('.modal-header button[data-dismiss]', obj).click();
  }

  //获取订单信息last_order=0时表示查找最后一次续订
  var get_order_data = function (dom_tr, last_order) {
    var i = 0,
      data = {};
    dom_tr.find('table').find('tr').each(function () {
      //if ($(this).find('i').hasClass('icon-globe')) {
        if (last_order !== undefined || $(this).find('td:first').text().indexOf('续订') != -1) {
          data.order_cycle = $(this).find('td:eq(1)').text().replace('个月', '');
          data.order_cycle_start = $(this).find('td:eq(2)').text();
          data.order_cycle_end = $(this).find('td:eq(3)').text();
          data.fee = $(this).find('td:eq(4)').text();
          data.total_pay_fee = $(this).find('td:eq(5)').text();
          return false;
        }
      //}
    });
    return data
  }

  //获取最后一次订单信息
  var get_last_order_data = function (dom_tr) {
    return get_order_data(dom_tr, 0)
  }

  //获取当前行的所有信息
  var get_current_data = function () {
    var data;
    dom_tr = $('#tr_' + contral_table_id);
    eval('data=' + dom_tr.attr('data'));
//    data.order = get_order_data(dom_tr);
    data.last_order = get_last_order_data(dom_tr);
    return data;
  }

  //点击续订表时要填充基本信息
  var get_renewed_before = function () {
    var data, obj;
    data = get_current_data();
    obj = $('#add_renewed')
    $('.username', obj).text(data.nick);
    $('.consult', obj).val(data.consult);
//    $('.order_cycle_start', obj).val(data.order.order_cycle_start);
//    $('.order_cycle', obj).val(data.order.order_cycle);
//    $('.total_pay_fee', obj).val(data.order.total_pay_fee);
  }

  //点击水军表时填充基本信息
  var get_navy_before = function () {
    var data, obj;
    data = get_current_data();
    obj = $('#add_navy')
    $('.username', obj).text(data.nick);
    $('.consult', obj).val(data.consult);
    $('.order_cycle_end', obj).val(data.last_order.order_cycle_end);
  }

  //点击转介绍表时填充的信息
  var get_referrals_before = function () {
    var data, obj;
    data = get_current_data();
    obj = $('#add_referrals')
    $('.username', obj).text(data.nick);
    $('.consult', obj).val(data.consult);
  }

  //点击差评跟踪表时所填充的信息
  var get_appraisal_before = function () {
    var data, obj;
    data = get_current_data();
    obj = $('#add_appraisal')
    $('.username', obj).text(data.nick);
    $('.consult', obj).val(data.consult);
    //发送请求获取用户所在类目
    PT.sendDajax({
      'function':'crm_cat_name4id',
      'shop_id':data.shop_id,
      'back_fuc': 'PT.new_CustomerList.cat_name4id_back',
      'is_manual': 1
    });    
  }

  //点击退款表时所填充的信息
  var get_refund_before = function () {
    var data, obj;
    data = get_current_data();
    obj = $('#add_refund')
    $('.username', obj).text(data.nick);
    $('.consult', obj).val(data.consult);
    //发送请求获取用户所在类目
    PT.sendDajax({
      'function':'crm_cat_name4id',
      'shop_id':data.shop_id,
      'back_fuc': 'PT.new_CustomerList.cat_name4id_back',
      'is_manual': 1
    });
  }

  //点击修改用户信息所填充的东西
  var get_user_info_before = function() {
    var data;
    data = get_current_data();

    send_data = {
      'function': 'crm_get_user_info',
      "customer_id": data.shop_id,
      "back_fuc": 'PT.new_CustomerList.set_user_info_back',
      'is_manual': 1
    }

    PT.sendDajax(send_data);
  }

  //帮助setup_by_setup
  var init_help = function () {

    var help_list = [
      {
        element: 'fieldset:first',
        content: 'Step【1/5】这里和老版本区别不大，只是将回访次数默认设置了未回访，另外布局变了下，按下回车就可以进行条件搜索了',
        placement: 'bottom'
            },
      {
        element: '#user_table>tbody td:first',
        content: 'Step【2/5】点击店铺id可开启旺旺联系卖家，点击店铺名进入卖家店铺，最后一排可以登录软件后台',
        placement: 'right'
            },
      {
        element: '.comment_box:first',
        content: 'Step【3/5】直接修改用户状态，不会再有弹窗的干扰了',
        placement: 'bottom'
            },
      {
        element: '.revisit_box:first',
        content: 'Step【4/5】点击向上按钮直接修改回访次数，回访时间会自动同步到今天',
        placement: 'bottom'
            },
      {
        element: '.contral_list:first',
        content: 'Step【5/5】 你自己的管控表常规操作，在这里可以将这个用户添加到相应的管控表中哦。Thanks,enjoy it!',
        placement: 'left'
            }
        ];
    PT.help(help_list);
  }


  return {
    init: function () {
      PT.Base.set_nav_activ('customer_list');
      init_dom();
      init_help();
    },
    change_comment_back: function (json) {
      PT.light_msg('修改评价', '修改成功');
    },
    change_dangerous_back: function (json) {
      if (json.result.dangerous_status == '5') {
        $('#dangerous_tips_' + json.resu).show();
      } else {
        $('#dangerous_tips_' + json.result.customer_id).hide();
      }
      PT.light_msg('修改用户状态', '修改成功');

    },
    change_revisit_back: function (json) {
      PT.light_msg('修改回访次数', '修改成功');
      var mode = (json.result.mode == 1) ? 'up' : 'down';
      $('i[class^="icon-circle-arrow-' + mode + '"][value="' + json.result.customer_id + '"]').attr('disable', false);
    },
    add_remark_back: function (json) {
      var now = new Date(),
        nowStr = now.format("yyyy-MM-dd"),
        obj = $('#td_mark_' + json.result.customer_id),
        html = '<div class="newest_mark"><span>' + json.result.remark.slice(0, 25) + '</span><span class="fr"><span class="marr_6">' + json.result.mark_author + '</span><span class="s_color">' + nowStr + '</span></span></div>';

      if (obj.find('.newest_mark').length) {
        if (obj.find('.newest_mark').length > 2) {
          obj.find('.newest_mark:last').remove();
        }
        obj.find('.newest_mark:first').before(html);
      } else {
        obj.children('span,img').remove()
        obj.children('div:first').before(html);
      }
      PT.light_msg('添加备注', '添加成功');
    },
    get_renewed_back: function (json) {
      var i = 0,
        html = '';
      for (i; i < json.result.length; i++) {
        html += template.render('renewed_tr', json.result[i])
      }
      if (html !== '') {
        $('#add_renewed tbody').html(html);
      } else {
        $('#add_renewed tbody').html('<tr><td colspan="6" class="tac">暂时没有数据</td></tr>');
      }
    },
    set_renewed_back: function () {
      PT.light_msg('添加续签', '添加成功');
    },
    set_appraisal_back: function () {
      PT.light_msg('添加差评跟踪', '添加成功');
    },
    get_appraisal_back: function (json) {
      var i = 0,
          obj=$('#add_appraisal'),
          html = '';
      for (i; i < json.result.length; i++) {
        html += template.render('appraisal_tr', json.result[i])
      }
      if (html !== '') {
        obj.find('tbody').html(html);
      } else {
        obj.find('tbody').html('<tr><td colspan="13" class="tac">暂时没有数据</td></tr>');
      }
      
      
      $('.phone', obj).val(json.result[0].phone);
      $('.qq', obj).val(json.result[0].qq);
      $('.wangwang', obj).val(json.result[0].wangwang);      
    },
    get_refund_back: function (json) {
      var i = 0,
        html = '';
      for (i; i < json.result.length; i++) {
        html += template.render('refund_tr', json.result[i])
      }
      if (html !== '') {
        $('#add_refund tbody').html(html);
      } else {
        $('#add_refund tbody').html('<tr><td colspan="9" class="tac">暂时没有数据</td></tr>');
      }
    },
    set_refund_back: function (json) {
      $('#refund_tip_' + json.result.customer_id).show();
      $('input[name=dangerous_'+json.result.customer_id+'][value=4]').attr('checked',true);
      if(json.result.remark){
        PT.new_CustomerList.add_remark_back(json)
      }
      PT.light_msg('添加退款跟踪', '添加成功');
    },
    submit_control_table: submit_control_table,
    get_navy_back: function (json) {
      var obj, appraisal_times_list, select_options_html = '',
        i = 0;
      if (typeof (json.result[0]) !== 'undefined') {
        obj = $('#add_navy')
        $('.consult', obj).val(json.result[0].adviser);
        $('.order_cycle_end', obj).val(json.result[0].order_cycle_end);
        $('.phone', obj).val(json.result[0].phone);
        $('.qq', obj).val(json.result[0].qq);
        $('.wangwang', obj).val(json.result[0].wangwang);

        appraisal_times_list = json.result[0].appraisal_times_list.split(',');
        for (i; i < appraisal_times_list.length; i++) {
          select_options_html += '<option>' + appraisal_times_list[i] + '</option>';
        }
      } else {
        select_options_html = '<option>没有评价过</option>';
        appraisal_times_list = [];
      }
      $('.appraisal_times_list', obj).html(select_options_html);
      $('.navy_appraisal_times', obj).html(appraisal_times_list.length);

    },
    set_navy_back: function () {
      PT.light_msg('添加水军', '添加成功');
    },
    get_referrals_back: function (json) {
      var obj;
      if (typeof (json.result[0]) !== 'undefined') {
        obj = $('#add_referrals')
        $('.consult', obj).val(json.result[0].adviser);
        $('.time', obj).val(json.result[0].referrals);
        $('.phone', obj).val(json.result[0].phone);
        $('.qq', obj).val(json.result[0].qq);
        $('.wangwang', obj).val(json.result[0].wangwang);
      }
    },
    edit_remark_back: function (json) {
      var index = json.result.remark_id;
      var content = $('#mark_content_' + index).find('textarea').val();
      PT.light_msg('修改备注', '修改成功！');
      $('#mark_content_' + index).html(content);
      $('#mark_content_' + index).parent().parent().prev().find('span:first').text(content.slice(0, 25));
    },
    delete_remark_back: function (json) {
      var index = json.result.remark_id;
      PT.light_msg('删除备注', '删除成功！');
      $('#collapse_' + index).parent().remove();
      $('#newest_mark_' + index).remove();
    },
    set_control_table: function (json) {
      PT.light_msg('修改管控表', '修改成功！');
    },
    delete_control_table: function (json) {
      $('#' + json.result.table + '_tr_' + json.result.id).remove();
      PT.light_msg('删除管控表', '删除成功');
    },
    cat_name4id_back: function (json) {
      $('#add_refund input.cat_name').val(json.result.cat_name);
      $('#add_appraisal input.cat_name').val(json.result.cat_name);
    },
    set_user_info_back:function(json){
      $('#add_user_info').find('.phone').val(json.result&&json.result.phone||'');
      $('#add_user_info').find('.qq').val(json.result&&json.result.qq||'');
      $('#add_user_info').find('.wangwang').val(json.result&&json.result.wangwang||'');
      $('#add_user_info').find('.lz_id').val(json.result&&json.result.lz_id||'');
      $('#add_user_info').find('.lz_psw').val(json.result&&json.result.lz_psw||'');
    },
    show_shop_trend:function(nick, category_list, series_cfg_list, snap_list) {
		$('#shop_trend_title').text(nick);
		PT.draw_trend_chart( 'shop_trend_chart' , category_list, series_cfg_list);
		$('#id_shop_data_table>tbody').html(template.render('snap_list_template', {'snap_list':snap_list}));
		$('#modal_shop_trend').modal();
	},
	allocate_single_consult_callback: function () {
		PT.alert('分配成功，即将刷新页面！', undefined, function () {
	        $('#id_search_form').attr('action', '');
	        $('#id_search_form').submit();
		});
	}
  };
}();