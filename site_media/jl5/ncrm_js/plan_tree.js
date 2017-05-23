PT.namespace('PlanTree');
PT.PlanTree = function() {
    var cond_fields = {},
        psuser_id = $('#psuser_id').val(),
        tree_psuser_id = $('#tree_psuser_id').val(),
        is_myself = psuser_id==tree_psuser_id,
        default_tree_id = localStorage['plan_tree_'+tree_psuser_id],
        mark_color_list = ['gold', 'red', 'silver', 'gray', 'green', 'cyan'];

    var get_tree_data = function (tree_id) {
        PT.show_loading('数据加载中');
        PT.sendDajax({
            'function': 'ncrm_get_plan_tree',
            'tree_id': tree_id,
            'callback': 'PT.PlanTree.get_plan_tree_callback'
        });
    }

    var parse_node_path = function (node_path, node_data) {
        var path_list = node_path.split('_').slice(1);
        editor_node_path_name = node_data.name;
        if (path_list.length>0) {
            for (var i in path_list) {
                node_data = node_data.child_list[path_list[i]];
                editor_node_path_name += ' ▶ ' + node_data.name;
            }
        }
        return node_data;
    };

    var fire_node_path = function (tree_id, fire_path, rec_type) {
        var path_list = fire_path.split('_'),
            sub_path = '',
            div_node_objs = $(),
            rec_type_objs = $(),
            div_node;
        for (var i in path_list) {
            if (i==0) {
                sub_path = path_list[0];
            } else {
                sub_path += '_'+path_list[i];
            }
            div_node = $('#div_plan_tree_'+tree_id+' div[path='+sub_path+']').parent('div.node');
            div_node_objs = div_node_objs.add(div_node);
            rec_type_objs = rec_type_objs.add(div_node.find('span[name='+rec_type+']').parent('div'));
        }
        $('#div_plan_tree_'+tree_id+'div.node.fire div.bbw').removeClass('bbw');
        $('#div_plan_tree_'+tree_id+'div.node.fire').removeClass('fire');
        div_node_objs.addClass('fire');
        rec_type_objs.addClass('bbw');
    }

    var build_tree = function (tree_data, parent_node, depth) {
        var node = $(template.render('template_node', {'tree_data':tree_data}));
        parent_node.append(node);
        if (tree_data.child_list.length>0) {
//            if (depth>=2) {
//                node.addClass('collapsed');
//            }
            node.append('<ul></ul>');
            for (var i in tree_data.child_list) {
                build_tree(tree_data.child_list[i], node.children('ul'), depth+1);
            }
        }
    }

    var render_node_cond = function (cond_obj) {
        var cond_list = [];
        for (var cond_name in cond_obj) {
            var args = cond_obj[cond_name],
                  args_str = cond_fields[cond_name].name_cn;
            switch (cond_fields[cond_name].type) {
                case 'cmpfield':
                case 'listcmpfield':
                    if (args[0]!=null && args[1]!=null) {
                        if (args[0]==args[1]) {
                            args_str += '='+args[0];
                        } else {
                            args_str = args[0]+'<='+args_str+'<='+args[1];
                        }
                    } else {
	                    if (args[0]!=null) {
	                        args_str += '>='+args[0];
	                    } else if (args[1]!=null) {
	                        args_str += '<='+args[1];
	                    }
                    }
                    break;
                case 'enumeratefield':
                    args_list = $.map(args, function (n) {
                        return cond_fields[cond_name].enum_fields_dict[n];
                    });
                    args_str += ' '+args_list.join(' , ');
                    break;
                case 'boolfield':
                    args_str += args[0] ? ' 是' : ' 不是';
                    break;
            }
            cond_list.push(args_str);
        }
        return cond_list.join('<br/>且 ');
    }

    var render_editor_node_cond = function (node_cond_list) {
        var cond_str = '';
        $.each(node_cond_list, function (i, cond_obj) {
            if (i>0) {
                cond_str += '<div class="mt5 mb5">或</div>';
            }
            cond_str += render_node_cond(cond_obj);
        });
        return cond_str;
    }
    
    var get_node_cond_str = function (node_path, node_data) {
        var cond_list = [];
        var path_list = node_path.split('_').slice(1);
        if (path_list.length>0) {
            for (var i in path_list) {
                node_data = node_data.child_list[path_list[i]];
                cond_list.push(render_editor_node_cond(node_data.cond_list));
            }
        }
        return '<div class="w200">'+cond_list.join('<div class="mt5 mb5">且 --------------------</div>')+'</div>';
    }

    // 初始化节点信息悬浮窗
    var init_tooltip = function (tree_id, tree_data) {
        $('#div_plan_tree_'+tree_id+' div.node').each(function () {
//            var node_path = $(this).children('div[path]').attr('path');
//            var node_data = parse_node_path(node_path, tree_data);
//            var cond_str = render_editor_node_cond(node_data.cond_list);
            var cond_str = get_node_cond_str($(this).children('div[path]').attr('path'), tree_data);
            $(this).tooltip({
                placement: 'top',
                title: cond_str,
                html: true
            });
        });
    }

    var init_rec_type_count = function () {
        $('#modal_plan_tree_record_table :checkbox.rec_type').each(function () {
            var tr_objs = $('#modal_plan_tree_record_table tr[rec_type='+this.value+']');
            var shop_list = $.map($('#modal_plan_tree_record_table tr[rec_type='+this.value+']'), function (obj) {
                return 'nick='+$(obj).attr('shop_id');
            });
            $(this).parent().children('span.red').html(shop_list.length);
            if (shop_list.length>0) {
                $(this).parent().children('a').attr('href', '/ncrm/myworkbench/?'+shop_list.join('&')).show();
            } else {
                $(this).parent().children('a').attr('href', '').hide();
            }
        });
    }

    var init_dom = function() {
        // 切换查看计划树
        $(':radio[name=my_trees]').click(function () {
            var tree_id = $(this).val(),
                tree_status = $(this).attr('status'),
                start_time = $(this).attr('start_time'),
                today = new Date().format('yyyy-MM-dd');
            localStorage['plan_tree_'+tree_psuser_id] = tree_id;
            if (is_myself) {
                if (tree_status=='1') {
                    $('#release_plan_tree').hide();
                    if (today>=start_time) {
                        $('#edit_plan_tree, #del_plan_tree').hide();
                        $('#stop_plan_tree').show();
                    } else {
                        $('#edit_plan_tree, #del_plan_tree').show();
                        $('#stop_plan_tree').hide();
                    }
                } else {
                    $('#edit_plan_tree, #del_plan_tree, #release_plan_tree').show();
                    $('#stop_plan_tree').hide();
                }
                $(this).parent().append($('#div_operate'));
                $('#edit_plan_tree').attr('href', '/ncrm/edit_plan_tree/?tree_id='+tree_id);
                //$('#copy_plan_tree').attr('href', '/ncrm/copy_plan_tree/?tree_id='+tree_id+'&copy_flag=1');
            }
            var div_tree = $('#div_plan_tree_'+tree_id);
            if (div_tree.attr('loaded')=='0') {
                get_tree_data(tree_id);
            } else {
                $('div.plan_tree').hide();
                div_tree.show();
            }
        });

        // 初始化数据
        if (default_tree_id) {
            var default_tree = $(':radio[name=my_trees][value='+default_tree_id+']');
            if (default_tree.length>0) {
                default_tree.click();
            } else {
                $(':radio[name=my_trees]:eq(0)').click();
            }
        } else {
            $(':radio[name=my_trees]:eq(0)').click();
        }

        // 删除计划树
        $('#del_plan_tree').click(function () {
            var tree_checked = $(':radio[name=my_trees]:checked');
            PT.confirm('确定要删除计划树：'+$.trim(tree_checked.next().text())+'吗？', function () {
                PT.show_loading('正在删除');
                PT.sendDajax({
                    'function': 'ncrm_del_plan_tree',
                    'tree_id': tree_checked.val(),
                    'callback': 'window.location.reload();'
                });
            });
        });

        // 发布计划树
        $('#release_plan_tree').click(function () {
            var tree_checked = $(':radio[name=my_trees]:checked');
            PT.confirm('确定要发布计划树：'+$.trim(tree_checked.next().text())+'吗？', function () {
                PT.show_loading('正在保存');
                PT.sendDajax({
                    'function': 'ncrm_operate_plan_tree',
                    'tree_id': tree_checked.val(),
                    'tree_data': $.toJSON({"status":1}),
                    'callback': 'window.location.reload();'
                });
            });
        });

        // 终止计划树
        $('#stop_plan_tree').click(function () {
            var tree_checked = $(':radio[name=my_trees]:checked');
            PT.confirm('确定要终止计划树：'+$.trim(tree_checked.next().text())+'吗？', function () {
                PT.show_loading('正在保存');
                PT.sendDajax({
                    'function': 'ncrm_operate_plan_tree',
                    'tree_id': tree_checked.val(),
                    'stop_tree_flag': 1,
                    'callback': 'window.location.reload();'
                });
            });
        });

        // 初始化右键菜单
        if (is_myself || $('#has_extra_perms').val()=='1') {
            $(document).bind('contextmenu', function (e) {
                var node = $(e.target).closest('div.node');
                if (node.length > 0) {
                    if (window.event) {
                        e = window.event;
                        e.returnValue = false;
                    } else {
                        e.preventDefault();
                    }
                    $('#work_bench_view').attr('href', '/ncrm/myworkbench/?node_path=' + node.find('div[path]').attr('path'));
                    if (is_myself) {
                        $('#bulk_opt_view').attr('href', '/ncrm/bulk_optimize/?node_path=' + node.find('div[path]').attr('path'));
                    } else {
                        $('#bulk_opt_view').parent('li').remove();
                    }
                    $('#plan_tree_record_view').attr('node_path', node.find('div[path]').attr('path'));
                    $('#node_right_menu').show().css({'top': e.pageY, 'left': e.pageX});
                } else {
                    $('#node_right_menu').hide();
                }
            });
            $(document).click(function (e) {
                if (e.button != 2) {
                    $('#node_right_menu').hide();
                }
            });
        }

        // 查看目标记录
        $('#plan_tree_record_view').click(function () {
            PT.show_loading('正在加载');
            PT.sendDajax({
                'function': 'ncrm_get_tree_record_list',
                'node_path': $(this).attr('node_path'),
                'callback': 'PT.PlanTree.get_tree_record_list_callback'
            });
        });

        // 删除目标记录
        $('#modal_plan_tree_record_table').on('click', 'a.del_plan_tree_record', function () {
            PT.show_loading('正在提交');
            PT.sendDajax({
                'function': 'ncrm_del_plan_tree_record',
                'record_id': $(this).attr('record_id'),
                'callback': 'PT.PlanTree.del_plan_tree_record_callback'
            });
        });

        // 添加目标记录
        $('#add_plan_tree_record').click(function () {
            var tree_checked = $(':radio[name=my_trees]:checked');
            if (tree_checked.attr('status')=='1') {
                if (tree_checked.attr('start_time')<=new Date().format('yyyy-MM-dd')) {
                    $('#ptr_nick, #ptr_rec_value').val('').attr('disabled', false);
                    $(':radio[name=ptr_rec_type]').attr('checked', false);
                    $('#modal_plan_tree_record').modal();
                } else {
                    PT.alert('计划树的开始日期小于等于今天后才可以添加目标记录');
                }
            } else {
                PT.alert('选中的计划树必须发布后，才可以添加目标记录');
            }
        });
        $('#modal_plan_tree_record [name=ptr_rec_type]').change(function () {
            switch (this.value) {
                case 'renew_order_pay':
                    $('#ptr_rec_value').val('').attr('disabled', false);
                    break;
                case 'good_comment_count':
                case 'unknown_order_count':
                    $('#ptr_rec_value').val(1).attr('disabled', false);
                    break;
                case 'is_potential':
                    $('#ptr_rec_value').val(1).attr('disabled', true);
                    break;
            }
        });

        $('#submit_plan_tree_record').click(function () {
            var tree_id = $.trim($(':radio[name=my_trees]:checked').val()),
                nick = $.trim($('#ptr_nick').val()),
                rec_type = $(':radio[name=ptr_rec_type]:checked').val(),
                rec_value = Number($.trim($('#ptr_rec_value').val()));
            if (!tree_id) {
                PT.alert('必须先选中一个计划树');
                return;
            }
            if (!nick) {
                PT.alert('必须填写店铺名/ID');
                return;
            }
            if (!rec_type) {
                PT.alert('必须选择记录类型');
                return;
            }
            if (!rec_value) {
                PT.alert('必须填写记录值，且必须是不为0的数字');
                return;
            }
            if (rec_type=='renew_order_pay') {
                rec_value = parseInt(rec_value*100);
            } else if (rec_value==parseInt(rec_value)) {
                rec_value = parseInt(rec_value);
            } else {
                PT.alert('该类型的数值必须是整数');
                return;
            }
            PT.show_loading('正在保存');
            PT.sendDajax({
                'function': 'ncrm_save_plan_tree_record',
                'tree_id': tree_id,
                'nick': nick,
                'rec_type': rec_type,
                'rec_value': rec_value,
                'callback': 'PT.PlanTree.save_plan_tree_record_callback'
            });
        });

        $('#modal_plan_tree_record_table :checkbox.rec_type').change(function () {
            if (this.checked) {
                $('#modal_plan_tree_record_table tr[rec_type='+this.value+']').show();
                if ($('#modal_plan_tree_record_table .rec_type:not(:checked)').length==0) {
                    $('#modal_plan_tree_record_table .checkall').attr('checked', true);
                }
            } else {
                $('#modal_plan_tree_record_table tr[rec_type='+this.value+']').hide();
                $('#modal_plan_tree_record_table .checkall').attr('checked', false);
            }
        });

        $('#modal_plan_tree_record_table .checkall').click(function () {
            $('#modal_plan_tree_record_table :checkbox.rec_type').attr('checked', this.checked);
            if (this.checked) {
                $('#modal_plan_tree_record_table tr[rec_type]').show();
            } else {
                $('#modal_plan_tree_record_table tr[rec_type]').hide();
            }
        });

    }

    return {
        init: function (all_cond_fields) {
            init_dom();
            $.each(all_cond_fields, function (i, cond_obj) {
                cond_fields[cond_obj.name] = cond_obj;
                if (cond_obj.type=='enumeratefield') {
                    cond_obj.enum_fields_dict = {};
                    $.each(cond_obj.enum_fields, function (i, n) {
                        cond_obj.enum_fields_dict[n[0]] = n[1];
                    });
                }
            });
        },
        get_plan_tree_callback: function (tree_id, tree_data) {
            var ul_tree = $('#ul_plan_tree_'+tree_id),
                div_tree = $('#div_plan_tree_'+tree_id);
            ul_tree.empty();
            div_tree.empty();
            $('div.plan_tree').hide();
            div_tree.show();
            build_tree(tree_data, ul_tree, 0);
            ul_tree.jOrgChart({
                chartElement: '#div_plan_tree_'+tree_id
            });
            $('#div_plan_tree_'+tree_id+' div[path][mark]').each(function () {
                if ($(this).attr('mark')) {
                    $(this).parent('div.node').addClass(mark_color_list[Number($(this).attr('mark'))]);
                }
            });
            div_tree.attr('loaded', '1');
            init_tooltip(tree_id, tree_data);
        },
        save_plan_tree_record_callback: function (tree_id, tree_data, fire_path, rec_type) {
            PT.PlanTree.get_plan_tree_callback(tree_id, tree_data);
            fire_node_path(tree_id, fire_path, rec_type);
            $('#modal_plan_tree_record').modal('hide');
        },
        get_tree_record_list_callback: function (error, record_list) {
            if (error) {
                PT.alert('发生异常，联系研发');
            } else {
                $('#modal_plan_tree_record_table').modal('show');
                $('#plan_tree_record_count').html(record_list.length);
                if (record_list.length > 0) {
                    $('#modal_plan_tree_record_table div.modal_body').html(template.render('template_plan_tree_record_table', {'record_list':record_list}));
                } else {
                    $('#modal_plan_tree_record_table div.modal_body').html('没有记录');
                }
                init_rec_type_count();
                $('#modal_plan_tree_record_table :checkbox').attr('checked', true);
            }
        },
        del_plan_tree_record_callback: function (error, record_id) {
            if (error) {
                PT.alert('发生异常，联系研发');
            } else {
                $('#modal_plan_tree_record_table a[record_id='+record_id+']').closest('tr').remove();
                $('#plan_tree_record_count').html($('#modal_plan_tree_record_table .modal_body tr').length);
                init_rec_type_count();
            }
        }
    }
}();
