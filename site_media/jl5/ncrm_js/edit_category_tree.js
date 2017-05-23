PT.namespace('EditCategoryTree');
PT.EditCategoryTree = function() {
    var tree_id, org_tree_data, editor_node_path_name, copy_node_path;
    var cond_fields = {},
        mark_color_list = ['gold', 'red', 'silver', 'gray', 'green', 'cyan'];

    $('#modal_category_condition span.cond').each(function () {
        cond_fields[$(this).attr('name')] = {'name_cn':this.innerHTML, 'type':$(this).attr('type')};
    });
    
    // 对象深拷贝
    var deepCopy = function (source) {
        if (!source) {
            return source;
        }
        var result;
        switch (source.constructor) {
            case Object:
                result = {};
                break;
            case Array:
                result = [];
                break;
            default:
                return source;
        }
        for (var key in source) {
            result[key] = typeof source[key]==='object'?deepCopy(source[key]):source[key];
        }
        return result;
    }
    
    var get_tree_data_byajax = function () {
        PT.show_loading('数据加载中');
        PT.sendDajax({
            'function': 'ncrm_get_category_tree',
            'tree_id': $('#tree_id').val(),
            'copy_flag': $('#copy_flag').val(),
            'is_stat': 0, // 编辑树时不需要统计数据
            'callback': 'PT.EditCategoryTree.get_category_tree_callback'
        });
    };
    
    var parse_node_path = function (node_path) {
        var path_list = node_path.split('_').slice(1),
              node_data = org_tree_data;
        editor_node_path_name = node_data.name;
        if (path_list.length>0) {
            for (var i in path_list) {
                node_data = node_data.child_list[path_list[i]];
                editor_node_path_name += ' ▶ ' + node_data.name;
            }
        }
        return node_data;
    };
    
    var build_tree = function (node_path, tree_data, parent_node, depth) {
        var node = $(template.render('template_node', {'path': node_path, 'name': tree_data.name, 'mark':tree_data.mark, 'cond_str': render_node_cond_list_str(tree_data.cond_list)}));
        parent_node.append(node);
        if (tree_data.child_list.length>0) {
//            if (depth>=2) {
//                node.addClass('collapsed');
//            }
            node.append('<ul></ul>');
            for (var i in tree_data.child_list) {
                build_tree(node_path+'_'+i, tree_data.child_list[i], node.children('ul'), depth+1);
            }
        }
    }
    
    var render_tree = function (tree_id, tree_data) {
        $('#ul_category_tree, #div_category_tree').empty();
        $(':radio[name=editor_tree_type][value='+tree_data.tree_type+']').attr('checked', true);
        $('#editor_tree_desc').val(tree_data.desc);
        build_tree(tree_id, tree_data, $('#ul_category_tree'), 0);
        $("#ul_category_tree").jOrgChart({
            chartElement: '#div_category_tree'
        });
        $('#div_category_tree div[path][mark]').each(function () {
            if ($(this).attr('mark')) {
                $(this).parent('div.node').addClass(mark_color_list[Number($(this).attr('mark'))]);
            }
        });
    }
    
    var init_modal_category_condition = function (node_path, cond_no) {
        $('#modal_category_condition').attr('path', node_path);
        $('#modal_category_condition span.cond_no').html(cond_no);
        $('#modal_category_condition span.node_name').html($('#editor_node_name').val());
        $('#modal_category_condition :text').val('');
        $('#modal_category_condition :checkbox').attr('checked', false);
        $('#modal_category_condition').modal('show');
    }

    var render_node_cond_list = function (cond_obj) {
        var cond_list = [];
        for (var cond_name in cond_obj) {
            var args = cond_obj[cond_name],
                  args_str = cond_fields[cond_name].name_cn;
            switch (cond_fields[cond_name].type) {
                case 'cmp':
                case 'listcmp':
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
                case 'enumerate':
                    args_list = $.map(args, function (n) {
                        return $('#modal_category_condition :checkbox[name='+cond_name+'_list][value='+n+']').attr('value_cn');
                    });
                    args_str += ' '+args_list.join(' , ');
                    break;
                case 'bool':
                    args_str += args[0] ? ' 是' : ' 不是';
                    break;
            }
            cond_list.push(args_str);
        }
        return cond_list;
    }
    
    var render_node_table = function (cond_no, cond_obj) {
        return template.render('template_node_cond', {
            'cond_no': cond_no,
            'cond_str': '<div class="mb5">'+render_node_cond_list(cond_obj).join('</div><div class="mb5">且 ')+'</div>'
            });
    }
    var render_editor_node_cond = function (node_cond_list) {
        $('#editor_node_cond').empty();
        $.each(node_cond_list, function (i, cond_obj) {
            $('#editor_node_cond').append(render_node_table(i+1, cond_obj));
        });
    }
    
    var render_editor_node = function (node_path) {
        $('#editor_node').attr('path', node_path);
        var node_data = parse_node_path(node_path);
        $('#editor_node_name').val(node_data.name).attr('org_value', node_data.name).focus();
        render_editor_node_cond(node_data.cond_list);
    }
    
    var render_node_cond_list_str = function (node_cond_list) {
        var cond_str = '';
        $.each(node_cond_list, function (i, cond_obj) {
            if (i>0) {
                cond_str += '<div class="mt5 mb5">或</div>';
            }
            cond_str += '<div>' +
                                 render_node_cond_list(cond_obj).join('</div><div>且 ') +
                                 '</div>';
        });
        return cond_str;
    }

    var init_dom = function() {
        // 初始化数据
        get_tree_data_byajax();

        // 初始化右键菜单
        $(document).bind('contextmenu', function (e) {
            var div_node = $(e.target).closest('div.node');
	        if (div_node.length>0) {
	            if (window.event) {
	                e = window.event;
	                e.returnValue = false;
	            } else {
	                e.preventDefault();
	            }
	            $('#node_right_menu').show().css({'top':e.pageY, 'left':e.pageX}).attr('path', div_node.children('div[path]').attr('path'));
	        } else {
	           $('#node_right_menu').hide();
	        }
        });
        $(document).click(function (e) {
            if (e.button!=2 && $(e.target).closest('#node_right_menu .disabled').length==0) {
                $('#node_right_menu').hide();
            }
        });
        
        // 选中节点
        $('#div_category_tree').on('click', 'div.node', function () {
            $('#div_category_tree div.node.selected').removeClass('selected');
            $(this).addClass('selected');
        });
        
        // 编辑节点
        $('#edit_node').click(function () {
            var node_path = $('#node_right_menu').attr('path');
            $('#div_category_tree div[path='+node_path+']').parent('div.node').click();
            $('#editor_node').modal();
            render_editor_node(node_path);
        });
        
        // 添加子节点
        $('#add_node').click(function () {
            var path_list = $('#node_right_menu').attr('path').split('_'),
                  tree_id = path_list.shift(),
                  node_data = org_tree_data,
                  new_node = {'name': '新建分类', 'child_list':[], 'cond_list':[]};
            if (path_list.length>0) {
                for (var i in path_list) {
                    node_data = node_data.child_list[path_list[i]];
                }
            }
            node_data.child_list.push(new_node);
            render_tree(tree_id, org_tree_data);
            path_list.unshift(tree_id);
            path_list.push(node_data.child_list.length-1);
            $('#div_category_tree div[path='+path_list.join('_')+']').click();
            $('#submit_tree').addClass('btn-danger');
        });
        
        // 删除此节点
        $('#del_node').click(function () {
            var path_list = $('#node_right_menu').attr('path').split('_'),
                  tree_id = path_list.shift(),
                  node_data = org_tree_data;
            if (path_list.length>0) {
                var del_index = path_list.pop();
                for (var i in path_list) {
                    node_data = node_data.child_list[path_list[i]];
                }
                node_data.child_list.splice(del_index, 1);
                render_tree(tree_id, org_tree_data);
                path_list.unshift(tree_id);
                $('#div_category_tree div[path='+path_list.join('_')+']').click();
                $('#submit_tree').addClass('btn-danger');
            } else {
                PT.alert('根节点无法删除');
            }
        });
        
        // 复制节点
        $('#copy_node').click(function () {
            var node_path = $('#node_right_menu').attr('path'),
                  path_list = node_path.split('_');
            if (path_list.length>1) {
                copy_node_path = node_path;
                $('#paste_node').removeClass('disabled');
                $('#div_category_tree div[path='+node_path+']').click();
            } else {
                PT.alert('根节点无法复制');
            }
        });
        
        // 粘贴子节点
        $('#paste_node').click(function () {
            if (copy_node_path) {
                var path_list0 = copy_node_path.split('_'),
	                  tree_id = path_list0.shift(),
	                  copy_node = org_tree_data;
	            if (path_list0.length>0) {
	                for (var i in path_list0) {
	                    copy_node = copy_node.child_list[path_list0[i]];
	                }
	                copy_node = deepCopy(copy_node);
	            } else {
	                PT.alert('根节点无法被粘贴');
	                return;
	            }
	            var path_list = $('#node_right_menu').attr('path').split('_'),
	                  tree_id = path_list.shift(),
	                  node_data = org_tree_data;
	            for (var i in path_list) {
	                node_data = node_data.child_list[path_list[i]];
	            }
	            node_data.child_list.push(copy_node);
	            render_tree(tree_id, org_tree_data);
	            $('#div_category_tree div[path='+copy_node_path+']').click();
	            $('#submit_tree').addClass('btn-danger');
            }
        });
        
        // 标记节点
        $('#node_right_menu .mark_node').click(function () {
            var node_path = $('#node_right_menu').attr('path'),
                node_data = parse_node_path(node_path);
            node_data.mark = Number($(this).attr('mark'));
            var node_obj = $('#div_category_tree div[path='+node_path+']').attr('mark', node_data.mark).parent('div.node');
            node_obj.removeClass(mark_color_list.join(' '));
            node_obj.addClass(mark_color_list[node_data.mark]);
            $('#submit_tree').addClass('btn-danger');
        });
        
        // 提交分类树
        $('#submit_tree').click(function () {
            if ($(this).hasClass('btn-danger')) {
                PT.show_loading('正在提交修改');
                PT.sendDajax({
                    'function': 'ncrm_operate_category_tree',
                    'tree_id': $('#copy_flag').val()=='1'?0:$('#tree_id').val(),
                    'tree_data':$.toJSON(org_tree_data),
                    'callback': 'PT.EditCategoryTree.get_category_tree_callback'
                });
            }
        });
        
        // 修改树类型
        $(':radio[name=editor_tree_type]').click(function () {
            if (this.value!=org_tree_data.tree_type) {
	            org_tree_data.tree_type = this.value;
	            $('#submit_tree').addClass('btn-danger');
            }
        });
        
        // 修改树备注
        $('#editor_tree_desc').blur(function () {
            if (this.value!=org_tree_data.desc) {
                org_tree_data.desc = this.value;
                $('#submit_tree').addClass('btn-danger');
            }
        });
        
        // 修改节点名称
        $('#editor_node_name').blur(function () {
            if (this.value!=$(this).attr('org_value')) {
	            var node_path = $('#editor_node').attr('path'),
	                  node_data = parse_node_path(node_path);
	            node_data.name = this.value;
	            parse_node_path(node_path); // 刷新 editor_node_path_name
	            $('#div_category_tree div.node>div[path='+node_path+']>div[name=node_name]').html(this.value);
//	            $('#editor_node_path').html(editor_node_path_name);
	            $('#submit_tree').addClass('btn-danger');
            }
        });
        
        // 左移/右移节点位置
        $('#node_right_menu a.move_node').click(function () {
            var path_list = $('#node_right_menu').attr('path').split('_'),
                  tree_id = path_list.shift(),
                  node_data = org_tree_data;
            if (path_list.length>0) {
                var this_index = parseInt(path_list.pop()), new_index = this_index;
                for (var i in path_list) {
                    node_data = node_data.child_list[path_list[i]];
                }
                if (node_data.child_list.length>1) {
                    switch ($(this).attr('direction')) {
                        case 'left':
                            if (this_index>0) {
                                new_index = this_index-1;
                            }
                            break;
                        case 'right':
                            if (this_index<node_data.child_list.length-1) {
                                new_index = this_index+1;
                            }
                            break;
                    }
                    if (new_index!=this_index) {
                        var temp_obj = node_data.child_list[new_index];
                        node_data.child_list[new_index] = node_data.child_list[this_index];
                        node_data.child_list[this_index] = temp_obj;
                        render_tree(tree_id, org_tree_data);
                        path_list.unshift(tree_id);
                        path_list.push(new_index);
                        var node_path = path_list.join('_');
//                        $('#editor_node_path').attr('path', node_path);
                        $('#editor_node').attr('path', node_path);
                        $('#div_category_tree div[path='+node_path+']').parent('div.node').addClass('selected');
                        $('#submit_tree').addClass('btn-danger');
                    }
                }
            }
        });
        
        // 添加规则
        $('#add_node_cond').click(function (e) {
            var node_path = $('#editor_node').attr('path'),
                  cond_no = $('#editor_node_cond>table[cond_no]').length+1;
            if (!node_path) {
                PT.alert('必须先选中节点，才能添加规则');
            } else if (node_path==tree_id) {
                PT.alert('根节点无法添加规则');
            } else {
	            init_modal_category_condition(node_path, cond_no);
            }
        });
        
        // 编辑规则
        $('#editor_node_cond').on('click', 'a.edit', function () {
            var node_path = $('#editor_node').attr('path'),
                  cond_no = parseInt($(this).closest('table[cond_no]').attr('cond_no')),
                  node_data = parse_node_path(node_path),
                  cond_data = node_data.cond_list[cond_no-1];
            init_modal_category_condition(node_path, cond_no);
            for (var cond_name in cond_data) {
                var args = cond_data[cond_name];
                switch (cond_fields[cond_name].type) {
                    case 'cmp':
                    case 'listcmp':
                        if (args[0]!=null) {
                            $('#modal_category_condition :text[name='+cond_name+'_min]').val(args[0]);
                        }
                        if (args[1]!=null) {
                            $('#modal_category_condition :text[name='+cond_name+'_max]').val(args[1]);
                        }
                        break;
                    case 'enumerate':
                        $.each(args, function (i, n) {
	                        $('#modal_category_condition :checkbox[name='+cond_name+'_list][value='+n+']').attr('checked', true);
                        });
                        break;
                    case 'bool':
                        $('#modal_category_condition :radio[name='+cond_name+'_booleans][value='+args[0]+']').attr('checked', true);
                        break;
                }
            }
        });
        
        // 保存规则
        $('#confirm_condition').click(function () {
            var node_path = $('#modal_category_condition').attr('path'),
                cond_no = parseInt($('#modal_category_condition span.cond_no').html()),
                node_data = parse_node_path(node_path),
                cond_obj = {},
                cond_obj_keys = 0;
            $('#modal_category_condition span.cond').each(function () {
                var cond_name = $(this).attr('name');
                switch ($(this).attr('type')) {
                    case 'cmp':
                    case 'listcmp':
                        var min_value = $.trim($(':text[name='+cond_name+'_min]').val()),
                              max_value = $.trim($(':text[name='+cond_name+'_max]').val());
                        min_value = min_value==''?NaN:Number(min_value);
                        max_value = max_value==''?NaN:Number(max_value);
                        if (!isNaN(min_value) || !isNaN(max_value)) {
                            cond_obj[cond_name] = [isNaN(min_value)?null:min_value, isNaN(max_value)?null:max_value];
                            cond_obj_keys++;
                        }
                        break;
                    case 'enumerate':
                        var value_list = $.map($('#modal_category_condition :checked[name='+cond_name+'_list]'), function (n) {
                            return n.value;
                        });
                        if (value_list.length>0) {
                            cond_obj[cond_name] = value_list
                            cond_obj_keys++;
                        }
                        break;
                    case 'bool':
                        var value_list = $.map($('#modal_category_condition :checked[name='+cond_name+'_booleans]'), function (n) {
                            return n.value;
                        });
                        if (value_list.length>0 && value_list[0] != "") {
                            cond_obj[cond_name] = value_list == 'true' ? [true]:[false];
                            cond_obj_keys++;
                        }
                        break;
                }
            });
            if (cond_obj_keys>0) {
	            node_data.cond_list[cond_no-1] = cond_obj;
	            var cond_table = $('#editor_node_cond table[cond_no='+cond_no+']'),
	                  new_cond_table = render_node_table(cond_no, cond_obj);
	            if (cond_table.length>0) {
		            cond_table.replaceWith(new_cond_table);
	            } else {
	                $('#editor_node_cond').append(new_cond_table);
	            }
	            $('#modal_category_condition').modal('hide');
	            $('#submit_tree').addClass('btn-danger');
	            render_tree(tree_id, org_tree_data);
            } else {
                PT.alert('必须选择或输入至少一个条件，才能保存规则');
            }
        });
        
        // 删除规则
        $('#editor_node_cond').on('click', 'a.del', function () {
            var node_path = $('#editor_node').attr('path'),
                  cond_no = parseInt($(this).closest('table[cond_no]').attr('cond_no')),
                  node_data = parse_node_path(node_path);
            node_data.cond_list.splice(cond_no-1, 1);
            render_editor_node_cond(node_data.cond_list);
            $('#submit_tree').addClass('btn-danger');
        });
    }

    return {
        init: function () {
            init_dom();
        },
        get_category_tree_callback: function (_tree_id, tree_data, flag) {
            if (flag) {
                if (_tree_id) {
                    window.location.href = '/ncrm/edit_category_tree/?tree_id='+_tree_id;
                } else {
	                PT.alert('出现异常，联系研发');
                }
            } else {
                tree_id = _tree_id;
                org_tree_data = tree_data;
                render_tree(tree_id, org_tree_data);
                if (tree_data.tree_type=='GENERAL') {
                    $('#editor_tree.limited').remove();
                }
            }
        }
    }
}();
