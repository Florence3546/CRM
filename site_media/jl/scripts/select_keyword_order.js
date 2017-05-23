PT.namespace('SelectKeywordOrder');
PT.SelectKeywordOrder = function() {

    var word_filter,

        fixed_header = null,

        item_id = $("#item_id").val(),

        cat_id = $("#cat_id").val(),

        title = $("#title").val(),

        //提供给datatable扩展的过滤数据，避免多次读取dom元素  形如['quick',[0.1,1],[90-500],[2,5],[3,5000],'男','连衣裙']  按过滤器顺序来
        filter_list = [],

        keyword_count = Number($("#keyword_count_hidden").val()) || 0,

        max_add_num = 200 - keyword_count,

        //首次进入的选词类型
        init_select_type = $('#init_select_type').val(),

        //初始化dom
        init_dom = function() {

            init_table();

            //选词导航点击事件
            $('#select_keyword_nav li').on('shown', function(e, previous) {
                var select_type = current_select_type(),page_name;

                if (!$('#' + select_type + '_common_table').is(':hidden')) {
                    init_scroll();
                } else {
                    remove_scroll();
                }
            });

            $('#url_form').vaildata({
                call_back: function() {
                    var url=$('#url_form').find('input').val();
                    if((url.indexOf('detail.tmall')!=-1||url.indexOf('item.taobao')!=-1)&&url.indexOf('id=')!=-1){
                        $('#url_form')[0].submit();
                    }else{
                        PT.alert('请检查输入的链接是否是宝贝链接')
                    }
                }
            });

            //弹出错误
            if($('#err').val()!=''){
                PT.alert($('#err').val());
            };

            //精准淘词
            $('#btn_precise_keyword').on('click',function(){
                var select_type = current_select_type(),page_name;
                if (select_type === 'quick') {
                    get_data(select_type);
                }else{
                    filter_list=[];
                }
            });

            //精灵推荐
            $('button[id$=_recommend]').on('click', function() {
                recommend();
                change_filter_class('recommend');
                update_checked_num();
            });

            //过滤
            $('button[id$=_btn_search]').on('click', function() {
                set_filter_list();
                keyword_check();
                current_data_table().fnSettings().aaSorting = [
                    [0, 'desc']
                ];
                setTimeout(function() {
                    current_data_table().fnDraw();
                    update_checked_num();
                }, 0);
            });

            //精准淘词事件
            $("#btn_tao_keyword").click(function() {
                word_filter = $('#word_filter').val();
                (word_filter == $('#word_filter').attr('placeholder')) ? word_filter = '' : '';
                if (!word_filter) {
                    PT.alert('亲，请先输入要包含的核心词。');
                    return false;
                }
                get_data();
            });

            //猜你想淘
            $('.guess_elemword li').on('click', function() {
                var guess_list = [],
                    guess_str = '';

                $(this).toggleClass('select');

                $('.guess_elemword li').each(function() {
                    if ($(this).hasClass('select')) {
                        guess_list.push($(this).text());
                    }
                });

                if (guess_list.length > 3) {
                    PT.alert('您选择的词太多，可能淘不出词来！');
                }

                $.map(guess_list, function(s) {
                    guess_str += s + ' ';
                });

                $('#word_filter').val(guess_str);

            });

            //选中所有checkbox的事件
            $('.father_box').on('click',function(e){
                var select_type = current_select_type(),
                    oSettings = current_table_settings(select_type);
                    that=this;

                e.stopPropagation();

                $.map(oSettings.aiDisplay, function(i) {
                        var nTr = oSettings.aoData[i].nTr;
                        nTr.children[0].children[0].checked = that.checked;
                });

                update_checked_num();
            });

            //显示更多修饰词
            $('#precise').on('click', '.btn_more', function(){
                $(this).siblings('li').removeClass('hide');
                $(this).html('&#xe658');
                $(this).removeClass('btn_more');
                $(this).addClass('btn_collapse');
            });

            $('#precise').on('click', '.btn_collapse', function(){
                $(this).siblings('li:gt(13)').addClass('hide');
                $(this).html('&#xe61a');
                $(this).removeClass('btn_collapse');
                $(this).addClass('btn_more');
            });


        },

        //修复复制关键词的层的位置和大小
        fixed_copy_layer = function() {
            $('.tableToolBtn>div>*').css({
                width: 112,
                height: 30
            });
        },

        //设置过滤器
        set_filter_list = function(select_type) {
            var select_type = select_type || current_select_type(),
                temp;
            filter_list = []
            $('#' + select_type + '_div_sliders input').each(function() {
                temp = this.value.split(';');
                filter_list.push([Math.min(temp[0], temp[1]), Math.max(temp[0], temp[1])]);
            });
            filter_list.push($.trim($('#' + select_type + '_include').val()));
            filter_list.push($.trim($('#' + select_type + '_uninclude').val()));
            filter_list.push($('#' + select_type + '_filter_checked')[0].checked);
        },

        //获取过滤器
        get_filter_list = function() {
            return filter_list;
        },

        //当前选词方式
        current_select_type = function() {
            return $('#select_keyword_nav li.active a').attr('href').replace('#', '');
        },

        //当前datatable
        current_data_table = function(select_type) {
            var select_type = select_type || current_select_type();
            return $('#' + select_type + '_common_table').dataTable();
        },

        //当前datatable的配置fnSettings()
        current_table_settings = function(select_type) {
            return current_data_table(select_type).fnSettings();
        },


        //初始化浮动
        init_scroll = function(select_type) {
            var select_type = select_type || current_select_type(),
                data_table = current_data_table(),
                fixed_obj = $('#' + select_type).find('.fixed_box'),
                fixed_obj_h = fixed_obj.height(),
                box_scroll = true;

            if (PT.get_habit() !== undefined && PT.get_habit()['keyword_float_switch'] === false) {
                fixed_obj_h = 0;
                box_scroll = false;
            }

            //防止重复绑定
            remove_scroll();

            $(window).on('scroll.PT.e', function() {
                var body_offset = document.body.scrollTop | document.documentElement.scrollTop,
                    obj_offset = fixed_obj.parent().offset().top,
                    fixed_obj_w = fixed_obj.width();

                if (body_offset >= obj_offset) {
                    if (box_scroll) {
                        fixed_obj.addClass('fixed').css({
                            'width': fixed_obj_w
                        });
                    }

                    if (fixed_header === null) {
                        fixed_header = new FixedHeader(data_table, {
                            "offsetTop": fixed_obj_h
                        });
                    }
                } else {
                    fixed_obj.removeClass('fixed');
                    if (fixed_header !== null) {
                        $(fixed_header.fnGetSettings().aoCache[0].nWrapper).remove();
                    }
                    fixed_header = null;
                }
            });
        },

        //清除滚动事件
        remove_scroll = function() {
            $(window).off('scroll.PT.e');
            if (fixed_header !== null) {
                $(fixed_header.fnGetSettings().aoCache[0].nWrapper).remove();
            }
        },

        //fix slider定位问题
        fix_slider_position = function(select_type) {
            $('#' + select_type + ' .dropdown-menu').removeClass('db vh');
        },

        //获取当前选中行
        get_submit_data = function(select_type) {
            var oSettings = current_table_settings(select_type),
                datas;
            datas = $.map(oSettings.aiDisplay, function(i) {
                var nTr = oSettings.aoData[i].nTr;
                if (nTr.children[0].children[0].checked) {
                    //返回关键词，出价，匹配模式
                    return [
                        [nTr.children[0].children[0].value, Number((Number($(nTr).find('td:eq(2) input').val()) * 100).toFixed(0)), Number($(nTr).find('td:eq(1) .match').attr('scope')), null, null]
                    ];
                }
            });
            return datas;
        },

        //获取当前所有行
        get_rows = function(select_type) {
            var oSettings = current_table_settings(select_type),
                nTrs;
            rows = $.map(oSettings.aiDisplay, function(i) {
                return oSettings.aoData[i];
            });
            return rows;
        },

        //根据倍数更新当前出价
        update_max_price = function(multi, limit_price) {
            var default_price = Number($("#default_price").val()),
                rows = get_rows(),
                i = rows.length - 1,
                current_input,
                new_price;

            setTimeout(function() {
                for (i; i >= 0; i--) {
                    current_input = rows[i].nTr.children[2].children[1];

                    if (multi === 0) {
                        new_price = default_price;
                    } else {
                        new_price = (multi * Number(rows[i]._aData[3]));
                    }
                    if (new_price > limit_price) {
                        new_price = limit_price;
                    }
                    if (new_price < 0.05) {
                        new_price = 0.05;
                    }
                    current_input.value = new_price.toFixed(2);
                }
            }, 0);
        },

        //批量修改匹配
        bulk_change_scope = function(scope) {
            var rows = get_rows(),
                i = rows.length - 1,
                match_scope_list = [
                    ['4', '2', '1'],
                    ['广', '中', '精']
                ];

            setTimeout(function() {
                for (i; i >= 0; i--) {
                    rows[i].nTr.children[1].children[1].innerText = match_scope_list[1][$.inArray(scope, match_scope_list[0])];
                    rows[i].nTr.children[1].children[1].setAttribute('scope', scope);
                }
            }, 0);
        },

        //选中精灵推荐并排序
        recommend = function(select_type) {
            var oSettings = current_table_settings(select_type);
            $.map(oSettings.aiDisplay, function(i) {
                var nTr = oSettings.aoData[i].nTr;
                if (Number(nTr.children[0].children[0].getAttribute('data-j'))) {
                    nTr.children[0].children[0].checked = true;
                } else {
                    nTr.children[0].children[0].checked = false;
                }
            });
            current_data_table(select_type).fnSort([
                [0, 'desc']
            ]);
        },

        //提交数据
        keywords_submit = function() {
            var keywords_info,
                select_type = current_select_type(),
                limit_price = Number($('#' + select_type + '_limit_price').val()),
                keyword_count = Number($('#' + select_type + '_keyword_count').html()) || 0,
                sum_checked = Number($('#' + select_type + '_sum_checked').html());

            if (keyword_count >= 200) {
                PT.alert('宝贝已在该计划中推广了200个关键词，无法继续添加');
            } else if (sum_checked === 0) {
                PT.alert('您还未选中任何关键词');
            } else {
                PT.confirm('即将添加' + sum_checked + '个关键词，确定要提交吗？', function() {
                    keywords_info = get_submit_data();
                    PT.sendDajax({
                        'function': 'web_batch_add_keywords',
                        'adgroup_id': adgroup_id,
                        'keyword_count': keyword_count,
                        'kw_arg_list': $.toJSON(keywords_info),
                        'init_limit_price': (limit_price > 0 ? limit_price : 0)
                    });
                    PT.show_loading('正在提交数据');
                });
            }
        },

        //获取数据
        get_data = function(type) {
            var select_type = type || current_select_type(),
                send_data = {
                    'function': 'toolkit_select_keyword_order',
                    'item_id': item_id,
                    'cat_id': cat_id,
                    'select_type': select_type,
                    'title': title,
                    'router_path':'select_keyword_order'
                };

            switch (select_type) {
                case 'quick':
                    send_data.mode = 'quick_'+$('input[name="radio_type"]:checked').attr('id');
                    break;
                case 'precise':
                    send_data.word_filter = word_filter;
                    break;
            }

            PT.show_loading('正在获取数据');

            $('#' + select_type + '_common_box').show();

            current_data_table(select_type).fnClearTable();

            PT.sendDajax(send_data);

        },

        //调节slider的回调函数
        slider_callback = function() {
            set_filter_list();
            // current_data_table().fnSort([[0,'asc']]);

            //将过滤操作中没有选中的排在前面
            // current_data_table().fnSettings().aaSorting = [
            //     [0, 'asc']
            // ];

            slide_check();

            current_data_table().fnSettings().aaSorting = [
                [0, 'desc']
            ];

            change_filter_class('slide');

            setTimeout(function() {
                current_data_table().fnDraw();
                update_checked_num();
            }, 0);
        },

        //改变筛选关键词的状态
        change_filter_class = function(mode) {
            var select_type = current_select_type();
            if (mode == 'slide') {
                $('#' + select_type + '_recommend').removeClass('btn-info');
                $('#' + select_type + '_recommend').next().find('.dropdown-toggle').addClass('btn-info');
            }
            if (mode == 'recommend') {
                $('#' + select_type + '_recommend').addClass('btn-info');
                $('#' + select_type + '_recommend').next().find('.dropdown-toggle').removeClass('btn-info');
            }
        },

        //初始化datatable
        init_table = function() {
            var taht = this;
            $('table[id*=_common_table]').each(function() {
                var select_type = this.id.replace('_common_table', '');
                $(this).dataTable({
                    "aoColumns": [{
                            "bSortable": true,
                            "sSortDataType": "dom-checkbox",
                            "sClass": "no_back_img tc"
                        }, {
                            "bSortable": false,
                            "sClass": "rel pr20"
                        }, {
                            "bSortable": true
                        },
                        null,
                        null,
                        null,
                        null
                    ],
                    'autoWidth': false,
                    'bDestroy': true,
                    'aaSorting': [
                        [0, 'desc']
                    ],
                    'iDisplayLength': 200,
                    'sDom': "T<'row-fluid't<'row-fluid mt10'<'span12 pl10'i><'span12 pr10 tr'p>>",
                    'oLanguage': {
                        'sInfo': '总共_TOTAL_条记录',
                        'sInfoEmpty': '',
                        'sEmptyTable': '正在获取数据.......',
                        'sZeroRecords': '亲，没有找到匹配的关键词',
                        'sInfoFiltered': '(从 _MAX_ 条记录中过滤)',
                        'oPaginate': {
                            'sNext': '下一页',
                            'sPrevious': '上一页'
                        }
                    },
                    "oTableTools": {
                        "sSwfPath": "/site_media/assets/swf/copy_csv_xls.swf",
                        "aButtons": [{
                            "sExtends": "copy",
                            "fnClick": function(nButton, oConfig, flash) {
                                this.fnSetText(flash, PT.SelectKeywordOrder.creat_copy_data());
                                setTimeout(function() {
                                    if(PT.SelectKeywordOrder.creat_copy_data()){
                                        PT.light_msg('', '复制成功！');
                                    }else{
                                        PT.light_msg('', '请选中要复制的关键词');
                                    }
                                }, 100);
                            },
                            "btn_id":select_type+"_copy_button"
                        },{
                            "sExtends": "xls",
                            "fnClick": function(nButton, oConfig, flash) {
                                if(PT.SelectKeywordOrder.creat_copy_data()){
                                    this.fnSetText(flash, PT.SelectKeywordOrder.creat_csv_data());
                                }
                                setTimeout(function() {
                                    if(!PT.SelectKeywordOrder.creat_copy_data()){
                                        PT.light_msg('', '请选中要导出的关键词');
                                    }
                                }, 100);
                            },
                            "btn_id":select_type+"_csv_button"
                        }]
                    },
                    'fnDrawCallback': function() {
                        init_select();
                    }
                });
            });
        },

        //复制关键词
        creat_copy_data = function() {
            var select_type = current_select_type(),
                oSettings = current_table_settings(),
                keywords = '';

            $.map(oSettings.aiDisplay, function(i) {
                var nTr = oSettings.aoData[i].nTr;
                if (nTr.children[0].children[0].checked) {
                    keywords += nTr.children[1].children[0].innerText + '\t';
                }
            });
            return keywords;
        },

        //导出关键词
        creat_csv_data = function() {
            var select_type = current_select_type(),
                oSettings = current_table_settings(),
                data_str='关键字\t市场均价\t展现指数\t点击指数\t竞争度\t匹配度'+'\n';

            $.map(oSettings.aiDisplay, function(i) {
                var nTr = oSettings.aoData[i].nTr;
                if (nTr.children[0].children[0].checked) {
                    data_str += nTr.children[1].children[0].innerText.replace('\\n','') + '\t' + nTr.children[2].innerText + '\t' + nTr.children[3].innerText + '\t' + nTr.children[4].innerText + '\t' + nTr.children[5].innerText + '\t' + nTr.children[6].innerText+'\n';
                }
            });
            return data_str;
        },

        //滑杆筛选关键词核心函数
        slide_check = function() {
            var r = 0,
                rows = get_rows(),
                r_end = rows.length,
                user_filter = PT.SelectKeywordOrder.get_filter_list();

            for (r; r < r_end; r++) {
                var i = 0,
                    judge = 1,
                    data_list = [Number(rows[r]._aData[6]), Number(rows[r]._aData[5]), Number(rows[r]._aData[4]), Number(rows[r]._aData[2])];

                for (i; i < 4; i++) {
                    if (data_list[i] < user_filter[i][0] || data_list[i] > user_filter[i][1]) {
                        judge = 0;
                        break;
                    }
                }

                if (judge) {
                    rows[r].nTr.children[0].children[0].checked = true;
                } else {
                    rows[r].nTr.children[0].children[0].checked = false;
                }
            }
        },

        //关键词过滤核心函数
        keyword_check = function() {
            var r = 0,
                rows = get_rows(),
                r_end = rows.length,
                user_filter = PT.SelectKeywordOrder.get_filter_list();

            for (r; r < r_end; r++) {
                var i = 0,
                    judge = 1,
                    keyword_str = rows[r]._aData[1].match(/<a.*>(.+?)<\/a>/i)[1];

                //包含关键词
                if (user_filter[4] && keyword_str.toUpperCase().indexOf(user_filter[4].toUpperCase()) == -1) {
                    judge = 0;
                }
                //不包含关键词
                if (judge && user_filter[5] && keyword_str.toUpperCase().indexOf(user_filter[5].toUpperCase()) != -1) {
                    judge = 0;
                }

                if (judge) {
                    rows[r].nTr.children[0].children[0].checked = true;
                } else {
                    rows[r].nTr.children[0].children[0].checked = false;
                }
            }
        },

        //datatable过滤扩展
        custom_datatable_ext = function() {
            $.fn.dataTableExt.afnFiltering.push(
                function(oSettings, aData, iDataIndex) {
                    //获取用slider过滤条件
                    var data_list = [Number(aData[8]), Number(aData[7]), Number(aData[5]), Number(aData[3]), aData[1].match(/<a.*>(.+?)<\/a>/i)[1], Number(aData[0])],
                        user_filter = PT.SelectKeywordOrder.get_filter_list(),
                        i = 0;

                    if (!user_filter.length) {
                        return true;
                    }

                    for (i; i < 4; i++) {
                        if (data_list[i] < user_filter[i][0] || data_list[i] > user_filter[i][1]) {
                            return false;
                        }
                    }

                    //不过滤选中词
                    if (!(user_filter[6] && data_list[5])) {

                        //包含关键词
                        if (user_filter[4] && data_list[4].toUpperCase().indexOf(user_filter[4].toUpperCase()) == -1) {
                            return false;
                        }
                        //不包含关键词
                        if (user_filter[5] && data_list[4].toUpperCase().indexOf(user_filter[5].toUpperCase()) != -1) {
                            return false;
                        }
                    }

                    return true;
                }
            );
        },

        //跟新当前选中数量
        update_checked_num = function(chcek_num) {
            var uncheck_num = 0,
                select_type = current_select_type(),
                oSettings = current_table_settings();

            if (chcek_num) {
                $('#' + select_type + '_sum_checked').text(num);
                return false;
            }

            chcek_num = 0

            $.map(oSettings.aiDisplay, function(i) {
                var nTr = oSettings.aoData[i].nTr;
                if ((nTr.children[0].children[0].checked)) {
                    chcek_num++;
                } else {
                    uncheck_num++;
                }
            });

            $('#' + select_type + '_sum_checked').text(chcek_num);
            //$('#' + select_type + '_sum_unchecked').text(uncheck_num);
            //$('#' + select_type + '_sum_unchecked').parent().show();
        },

        //初始化select的事件
        init_select = function() {
            if (typeof selectRefresh != 'undefined') {
                selectRefresh();
            }
            $select({
                name: 'idx',
                callBack: update_checked_num
            });
        },

        //显示数据
        layout_data = function(all_keyword_list, okay_count, filter_field_list, select_type) {
            setTimeout(function() {
                layout_filter(filter_field_list, select_type);
                layout_table(all_keyword_list, select_type);
                layout_info(all_keyword_list, okay_count, select_type);
                fix_slider_position(select_type);
                //初始化滚动事件
                init_scroll();
                // init_price_slider();
                fixed_copy_layer();
            }, 0);
            PT.hide_loading();
        },

        //填充表格数据
        layout_table = function(all_keyword_list, select_type) {
            var dom = [],
                i = 0,
                i_end = all_keyword_list.length;
            for (i; i < i_end; i++) {
                dom.push(template.compile(pt_tpm['select_keyword_table_order.tpm.html'])(all_keyword_list[i]).split('^,^'));
            }
            current_data_table(select_type).fnAddData(dom);
        },

        //填充其他信息
        layout_info = function(all_keyword_list, okay_count, select_type) {
            $('#' + select_type + '_sum_checked').text(0);
            $('#' + select_type + '_all_keywords').text(all_keyword_list.length);

            if (all_keyword_list.length === 0) {
                $('#' + select_type + '_common_table .dataTables_empty').text('没有数据，请改变搜索条件重试！');
            }
        },

        //填充过滤器数据
        layout_filter = function(filter_field_list, select_type) {
            var obj = $('#' + select_type + '_div_sliders');
            obj.empty();

            for (var i = 0; i < filter_field_list.length; i++) {
                var cfg = filter_field_list[i];
                if (cfg.series_name == 'keyword_score' || cfg.series_name == 'cat_click') {
                    var temp = cfg.current_to,
                        temp2 = cfg.limit;
                    cfg.current_to = cfg.current_from;
                    cfg.current_from = cfg.limit;
                    cfg.limit = cfg.from;
                    cfg.from = temp2;
                    if (cfg.heterogeneity) {
                        for (var j = 0; j < cfg.heterogeneity.length; j++) {
                            var percent_list = cfg.heterogeneity[j].split('/');
                            if (percent_list.length) {
                                percent_list[0] = 100 - Number(percent_list[0]);
                                cfg.heterogeneity[j] = percent_list.join('/');
                            }
                        }
                        cfg.heterogeneity = cfg.heterogeneity.reverse();
                    }
                } else {
                    cfg.current_from = cfg.from;
                }
                var html_slider = template.compile(pt_tpm['select_keyword_slider.tpm.html'])({
                    cfg: cfg,
                    select_type: select_type
                });
                obj.append(html_slider);
                if (cfg.svl[0] != cfg.from) {
                    cfg.svl.unshift(cfg.from);
                } else if (cfg.svl.length == 1) {
                    cfg.svl.push(cfg.from + 1);
                }
                //jslider 生成滑块
                if (cfg.series_name == "cat_cpc") {
                    $("#" + select_type + '_' + cfg.series_name).slider({
                        round: 2,
                        step: 0.01,
                        callback: slider_callback,
                        from: cfg.from,
                        to: cfg.limit,
                        limits: false,
                        dimension: '',
                        skin: "plastic",
                        heterogeneity: cfg.heterogeneity || [],
                        scale: [cfg.from, cfg.limit]
                    });
                } else {
                    $("#" + select_type + '_' + cfg.series_name).slider({
                        step: 1,
                        callback: slider_callback,
                        from: cfg.from,
                        to: cfg.limit,
                        limits: false,
                        dimension: '',
                        skin: "plastic",
                        heterogeneity: cfg.heterogeneity || [],
                        scale: [cfg.from, cfg.limit]
                    });
                }
            }
        },

        // 添加关键词后，更新可添加关键词个数
        update_keyword_count_2add = function(added_keyword_count) {
            var select_type = current_select_type();

            $('#' + select_type + '_keyword_count').text(Number($('#' + select_type + '_keyword_count').text()) + added_keyword_count);
        },

        //添加关键词后，从当前表格中删除这些数据
        remove_dataTable_keywords = function(keyword_list) {
            var select_type = current_select_type(),
                oTable = current_data_table(),
                oSettings = oTable.fnSettings(),
                anTr_2remove = [],
                i = 0,
                ii,
                nTr;

            for (i; i < oSettings.aiDisplay.length; i++) {
                ii = oSettings.aiDisplay[i];
                nTr = oSettings.aoData[ii].nTr;
                if ($(nTr).is(':has(input:checked)')) {
                    anTr_2remove.push(nTr);
                }
            }
            for (var i = 0; i < anTr_2remove.length; i++) {
                oTable.fnDeleteRow(anTr_2remove[i]);
            }
            $('#' + select_type + '_sum_checked').html(0);
            $('#' + select_type + '_all_keywords').html(oSettings.aoData.length);
        };

    return {
        init: function() {
            init_dom();

            //添加datatable扩展
            //custom_datatable_ext();

            //进入的类型是快速选词则直接获取数据
            if (init_select_type === 'quick') {
                get_data('quick');
            }

            if (init_select_type === 'combine') {
                calc_combine_unput();
            }
        },
        select_keyword_callback: function(all_keyword_list, okay_count, filter_field_list, select_type) {
            layout_data(all_keyword_list, okay_count, filter_field_list, select_type);
        },
        get_filter_list: get_filter_list,
        remove_dataTable_keywords: remove_dataTable_keywords,
        update_keyword_count_2add: update_keyword_count_2add,
        creat_copy_data: creat_copy_data,
        creat_csv_data: creat_csv_data
    };
}();
