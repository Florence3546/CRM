PT.namespace('Control_table');
PT.Control_table = function () {

  var add_remark_id, PAGE = 1;
  var init_table_select = $('#table_tab').val();
  var adviser = $('#adviser').val();

  //css3 animate动画发生器
  var css_animate = function (obj, animate) {
    obj.addClass(animate).addClass('animated');
    setTimeout(function () {
      obj.removeClass(animate).removeClass('animated');
    }, 1000);
  }

  var init_dom = function () {
    //提价备注
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
        'back_fuc': 'PT.Control_table.add_remark_back'
      });
    });

    //查看历史备注
    $('table').on('click.PT.e', '.histary_remark', function () {
      PT.sendDajax({
        'function': 'crm_histary_remark',
        "customer_id": this.getAttribute('value')
      });
    });

    //添加个备注
    $('table').on('click.PT.e', '.add_remark', function () {
      add_remark_id = this.getAttribute('value');
      $('#remark').val(''); //清空备注
    });

    //搜索
    $('.search_btn').click(function () {
      init_table_select = this.getAttribute('ajax');
      clear_table();
      init_table();
    });

    $(document).keypress(function (e) {
      var key = e.keyCode || e.which || e.charCode
      switch (key) {
      case 13:
        clear_table();
        init_table();
        break;
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
          'back_fuc': 'PT.Control_table.edit_remark_back',
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
        'back_fuc': 'PT.Control_table.delete_remark_back',
        'is_manual': 1
      });
    });

    //导出csv表格
    $('.get_csv').click(function () {
      var field_dict, table = $(this).attr('ajax');

      PT.sendDajax({
        'function': 'crm_get_csv',
        'table': table,
        'back_fuc': 'PT.Control_table.get_csv_back',
        'is_manual': 1
      });
    });
  }

  var get_where_str = function () {
    var where_str = '';

    $('#' + init_table_select).find('.select_ul li').each(function () {
      switch ($(this).find('input').length || $(this).find('select').length) {
      case 0:
        break;
      case 1:
        var adviser_select = $(this).find('select').val();
        if (adviser_select !== '') {
          adviser = adviser_select;
        } else {
          adviser = $('#adviser').val();
        }
        break;
      case 2:
        var data_min, data_max, field;
        field = $(this).find('input:first').attr('field');
        data_min = $(this).find('input')[0].value;
        data_max = $(this).find('input')[1].value;
        if (data_min !== '') {
          if (where_str !== '') {
            where_str += ' and '
          }
          where_str += field + '>="' + data_min + '"';
        }

        if (data_max !== '') {
          if (where_str !== '') {
            where_str += ' and '
          }
          where_str += field + '<="' + data_max + '"';
        }
        break;
      }
    });

    return where_str;
  }

  var clear_table = function () {
    $('#' + init_table_select).removeClass('no_data').addClass('loading');
    $('#' + init_table_select + '_dynamic_pager').html('');
  }

  var init_table = function () {
    var where_string = get_where_str()
    PT.sendDajax({
      'function': 'crm_get_control_table',
      'adviser': adviser,
      'table': init_table_select,
      'page': PAGE,
      'where_string': where_string,
      'back_fuc': 'PT.Control_table.layout_table'
    });
  }

  //初始化datetable
  var init_datetable = function () {
    $('#' + init_table_select + '_table').dataTable({
      "bRetrieve": true, //允许重新初始化表格
      "bPaginate": false,
      "bFilter": false,
      "bInfo": false,
      "bAutoWidth": false, //禁止自动计算宽度
      "sDom": ''
    });
  }

  //点击tabs初始化table
  $('#nav_tabs a').click(function () {
    init_table_select = this.href.match(/\#.*/)[0].replace('#', '');
    PAGE = 1;

    init_table();
  });

  var navy_after = function (json) {
    var i = 0;
    for (i; i < json.result.length; i++) {
      json.result[i].appraisal_count = json.result[i].appraisal_times_list?json.result[i].appraisal_times_list.split(',').length:0;
    }
    return json
  }

  var handle_page = function (page_count, page_no) {
    $('#' + init_table_select + '_dynamic_pager').off('page');
    $('#' + init_table_select + '_dynamic_pager').bootpag({
      total: page_count,
      page: page_no,
      leaps: false,
      prev: '上一页',
      next: '下一页',
      maxVisible: 10
    }).on('page', function (event, num) {
      PAGE = num;
      init_table();
    });
  }


  return {
    init: function () {
      PT.Base.set_nav_activ('control_table');
      init_dom();
      init_table();
    },
    layout_table: function (json) {
      var i = 0,
        html = '';

      if (eval('typeof ' + init_table_select + '_after') !== 'undefined') {
        json = eval(init_table_select + '_after(' + $.toJSON(json) + ')');
      }

      for (i; i < json.result.length; i++) {
        html += template.render(init_table_select + '_tr', json.result[i])
      }
      $('#' + init_table_select).removeClass('loading');
      if (html !== '') {
        $('#' + init_table_select + '_table tbody').html(html);
        init_datetable();
      } else {
        $('#' + init_table_select).addClass('no_data');
      }
      if (!$('#' + init_table_select + '_dynamic_pager ul').length) {
        handle_page(Math.ceil(json.page.record_count / json.page.page_size), json.page.page);
        $('#' + init_table_select + '_page_count').text(Math.ceil(json.page.record_count / json.page.page_size));
        $('#' + init_table_select + '_page_size').text(json.page.record_count);
      }
      //显示退款总金额
      if (init_table_select == 'refund') {
        $('#totale_refund_fee').text(json.other.totale_refund_fee)
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
    },
    add_remark_back: function (json) {
      var now = new Date(),
        nowStr = now.format("yyyy-MM-dd hh:mm:ss");
      $('.renewed_mark_auth_' + json.result.customer_id).text(json.result.mark_author);
      $('.renewed_mark_time_' + json.result.customer_id).text(nowStr);
      $('.renewed_mark_content_' + json.result.customer_id).text(json.result.remark);
      PT.light_msg('添加备注', '添加成功');
    },
    get_csv_back: function (json) {
      var base_64 = json.result.csv_str,
        tabel = json.result.table,
        now = new Date(),
        nowStr = now.format("yyyy-MM-dd"),
        dom_id = tabel + nowStr,
        table_dict = {
          'renewed': '续签表',
          'navy': '水军表',
          'appraisal': '差评跟踪',
          'referrals': '转介绍',
          'refund': '退款跟踪'
        }
      dom_str = '<a class="hide" id="' + dom_id + '" href="data:text/csv;base64,' + base_64 + '"  download="' + table_dict[tabel] + '_' + nowStr + '.csv">aaaaa</a>';
      $('body').append(dom_str);
      $('#' + dom_id)[0].click();
    }
  }
}();