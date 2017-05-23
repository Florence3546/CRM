PT.namespace('CategoryTree');
PT.CategoryTree = function() {
    var cond_fields = {},
        psuser_id = $('#psuser_id').val(),
        tree_psuser_id = $('#tree_psuser_id').val(),
        is_myself = psuser_id==tree_psuser_id,
        default_tree_id = localStorage['default_tree_'+tree_psuser_id],
        default_cat_id_list = $.evalJSON(localStorage['default_cat_'+tree_psuser_id] || '[]'),
        mark_color_list = ['gold', 'red', 'silver', 'gray', 'green', 'cyan'];

    var get_tree_data = function (tree_id) {
        PT.show_loading('数据加载中');
        PT.sendDajax({
            'function': 'ncrm_get_category_tree',
            'tree_id': tree_id,
            'psuser_id': tree_psuser_id,
            'cat_id_list': $.toJSON(default_cat_id_list),
            'all_cat_flag': $('#modal_shop_category_statistics :checkbox.checkall').prop('checked')?1:0,
            'callback': 'PT.CategoryTree.get_category_tree_callback'
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

    var build_tree = function (tree_data, parent_node, depth) {
        var mark = Number(tree_data.mark);
        mark = isNaN(mark)?'2':mark;
        var node = $('<li><div path="'+tree_data.path+'" mark="'+mark+'">'+tree_data.name+'<div class="f24 mt2">'+tree_data.shop_count+'</div></div></li>');
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
        $('#div_category_tree_'+tree_id+' div.node').each(function () {
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

    var init_dom = function() {
        // 切换查看分类树
        $(':radio[name=my_trees]').click(function () {
            var tree_id = $(this).val();
            localStorage['default_tree_'+tree_psuser_id] = tree_id;
            if (is_myself) {
                $(this).parent().append($('#div_operate'));
                $('#edit_category_tree').attr('href', '/ncrm/edit_category_tree/?tree_id='+tree_id);
                $('#copy_category_tree').attr('href', '/ncrm/edit_category_tree/?tree_id='+tree_id+'&copy_flag=1');
            }
            var div_tree = $('#div_category_tree_'+tree_id);
            if (div_tree.attr('loaded')=='0') {
                get_tree_data(tree_id);
            } else {
                $('div.category_tree').hide();
                div_tree.show();
            }
        });

        // 设置类目
        $('#set_default_cat_list').click(function () {
            default_cat_id_list = $.map($('#modal_shop_category_statistics [name=cat_id]:checked'), function(n) {return n.value;});
            localStorage['default_cat_'+tree_psuser_id] = $.toJSON(default_cat_id_list);
            PT.show_loading('正在加载');
            window.location.reload();
        });
        $('#modal_shop_category_statistics :checkbox.checkall').click(function () {
            $('#modal_shop_category_statistics :checkbox[name=cat_id]').attr('checked', this.checked);
            $('#checked_category_count').html($('#modal_shop_category_statistics [name=cat_id]:checked').length);
        });
        $('#modal_shop_category_statistics :checkbox[name=cat_id]').click(function () {
            if ($('#modal_shop_category_statistics [name=cat_id]:not(:checked)').length) {
                $('#modal_shop_category_statistics :checkbox.checkall').attr('checked', false);
            } else {
                $('#modal_shop_category_statistics :checkbox.checkall').attr('checked', true);
            }
            $('#checked_category_count').html($('#modal_shop_category_statistics [name=cat_id]:checked').length);
        });

        // 初始化数据
        if (default_cat_id_list.length) {
            var temp_list = $.map(default_cat_id_list, function (cat_id) {
                var cat_obj = $('#modal_shop_category_statistics [name=cat_id][value='+cat_id+']');
                cat_obj.attr('checked', true);
                return cat_obj.attr('cat_name');
            });
            $('#checked_category_count').html(default_cat_id_list.length);
            if (default_cat_id_list.length == Number($('#all_category_count').html())) {
                $('#cat_list_name').html('所有');
                $('#modal_shop_category_statistics :checkbox.checkall').attr('checked', true);
            } else {
                $('#cat_list_name').html(temp_list.join(' + '));
            }
        } else {
            $('#cat_list_name').html('所有');
        }

        if (default_tree_id) {
            var default_tree = $(':radio[name=my_trees][value='+default_tree_id+']');
            if (default_tree.length>0) {
                default_tree.click();
            } else {
                $(':radio[name=my_trees]:eq(0)').click();
            }
        } else {
	        get_tree_data($(':radio[name=my_trees]:checked').val());
        }

        // 删除分类树
        $('#del_category_tree').click(function () {
            var tree_checked = $(':radio[name=my_trees]:checked');
            PT.confirm('确定要删除分类树：'+tree_checked.attr('tree_name')+'吗？', function () {
                PT.show_loading('正在删除');
                PT.sendDajax({
                    'function': 'ncrm_del_category_tree',
                    'tree_id': tree_checked.val()
                });
            });
        });

        // 初始化右键菜单
        if (is_myself || $('#has_extra_perms').val()=='1') {
            $(document).bind('contextmenu', function (e) {
                var node = $(e.target).closest('div.node');
                if (node.length>0) {
                    if (window.event) {
                        e = window.event;
                        e.returnValue = false;
                    } else {
                        e.preventDefault();
                    }
                    $('#work_bench_view').attr('href', '/ncrm/myworkbench/?node_path='+node.find('div[path]').attr('path')+'&tree_psuser_id='+tree_psuser_id);
                    if (is_myself) {
                        $('#bulk_opt_view').attr('href', '/ncrm/bulk_optimize/?node_path='+node.find('div[path]').attr('path'));
                    } else {
                        $('#bulk_opt_view').parent('li').remove();
                    }
                    $('#node_right_menu').show().css({'top':e.pageY, 'left':e.pageX});
                } else {
                   $('#node_right_menu').hide();
                }
            });
            $(document).click(function (e) {
                if (e.button!=2) {
                    $('#node_right_menu').hide();
                }
            });
        }

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
        get_category_tree_callback: function (tree_id, tree_data) {
            var ul_tree = $('#ul_category_tree_'+tree_id),
                  div_tree = $('#div_category_tree_'+tree_id);
            ul_tree.empty();
            div_tree.empty();
            $('div.category_tree').hide();
            div_tree.show();
            build_tree(tree_data, ul_tree, 0);
            ul_tree.jOrgChart({
                chartElement: '#div_category_tree_'+tree_id
            });
            $('#div_category_tree_'+tree_id+' div[path][mark]').each(function () {
                if ($(this).attr('mark')) {
                    $(this).parent('div.node').addClass(mark_color_list[Number($(this).attr('mark'))]);
                }
            });
            div_tree.attr('loaded', '1');
            init_tooltip(tree_id, tree_data);
        }
    }
}();
