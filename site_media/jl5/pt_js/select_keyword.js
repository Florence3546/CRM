PT.namespace('SelectKeyword');
PT.SelectKeyword = function() {

    var word_filter,

        fixed_header = null,

        prdtword_max_num = 5,

        dcrtword_max_num = 15,

        prmtword_max_num = 5,

        prdtword_list = [],

        dcrtword_list = [],

        prmtword_list = [],

        manword_list = [],

        //提供给datatable扩展的过滤数据，避免多次读取dom元素  形如['quick',[0.1,1],[90-500],[2,5],[3,5000],'男','连衣裙']  按过滤器顺序来
        filter_list = [],

        adgroup_id = $("#adgroup_id").val(),

        cat_id = $("#cat_id").val(),

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
                if (select_type === 'quick' && !$(this).hasClass('inited')) {
                    get_data(select_type);
                    $(this).addClass('inited');
                }else{
                    filter_list=[];
                }

                if (select_type === 'combine'){
                    calc_combine_unput();
                }

                if (!$('#' + select_type + '_common_table').is(':hidden')) {
                    init_scroll();
                } else {
                    remove_scroll();
                }

                page_name="/web/select_keyword/"+select_type+"?adgroup_id="+adgroup_id;
                //改变浏览器URL,以便于刷新操作
                history.pushState&&history.pushState(page_name, "", page_name);
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

            //手工组词选词按钮事件
            $('#btn_auto_combine_words').on('click', function() {

                $('#textarea_prdtword').trigger('keyup');
                $('#textarea_dcrtword').trigger('keyup');
                $('#textarea_prmtword').trigger('keyup');

                if (prdtword_list.length === 0) {
                    PT.alert('亲，产品词至少要有一个！');
                    return false;
                } else if (prdtword_list.length > prdtword_max_num) {
                    PT.alert('亲，产品词请不要超过' + prdtword_max_num + '个！');
                    return false;
                } else if (dcrtword_list.length > dcrtword_max_num) {
                    PT.alert('亲，属性词/修饰词请不要超过' + dcrtword_max_num + '个！');
                    return false;
                } else if (prmtword_list.length > prmtword_max_num) {
                    PT.alert('亲，促销词请不要超过' + prmtword_max_num + '个！');
                    return false;
                }
                get_data();
            });

            //手工加词选词按钮事件
            $('#btn_manual_add_words').on('click', function() {
                $('#textarea_manual').trigger('keyup');
                if (manword_list.length == 0) {
                    PT.alert('亲，请先输入关键词！');
                    return false;
                }
                get_data();
            });

            //手工组词计算产品词
            $('#textarea_prdtword').on('keyup', function() {
                var _prdtword_list = $.trim($(this).val()).split('\n');
                _prdtword_list = $.map(_prdtword_list, function(word) {
                    if (word) {
                        return word;
                    }
                });
                $('#prdtword_count').html(_prdtword_list.length);
                prdtword_list = _prdtword_list;
            });

            //修饰词计算产品词
            $('#textarea_dcrtword').on('keyup', function() {
                var _dcrtword_list = $.trim($(this).val()).split('\n');
                _dcrtword_list = $.map(_dcrtword_list, function(word) {
                    if (word) {
                        return word;
                    }
                });
                $('#dcrtword_count').html(_dcrtword_list.length);
                dcrtword_list = _dcrtword_list;
            });

            //促销词计算产品词
            $('#textarea_prmtword').on('keyup', function() {
                var _prmtword_list = $.trim($(this).val()).split('\n');
                _prmtword_list = $.map(_prmtword_list, function(word) {
                    if (word) {
                        return word;
                    }
                });
                $('#prmtword_count').html(_prmtword_list.length);
                prmtword_list = _prmtword_list;
            });

            //手工加词计算词数
            $('#textarea_manual').on('keyup', function() {
                manword_list = $.trim($(this).val()).split('\n');
                manword_list = $.map(manword_list, function(word) {
                    if (word) {
                        return word;
                    }
                });
                $('#manual_count').html(manword_list.length);
            });

            //单个改变匹配
            $("body").on('click', '.match', function() {
                var match_scope_list = [
                    ['4', '2', '1'],
                    ['广', '中', '精']
                ];
                var match_scope = $(this).attr('scope');
                var index = $.inArray(match_scope,match_scope_list[0]);

                index++;
                if (index >= match_scope_list[0].length) index = 0;
                $(this).attr('scope', match_scope_list[0][index]);
                $(this).html(match_scope_list[1][index]);
            });

            //修改出价
            $('.dropdown[id$=_price_multi]').on('change', function(e, v) {
                var limit_price = $('#quick_limit_price').val();
                update_max_price(Number(v), Number(limit_price));
            });

            //修改限价
            $('input[id$=_limit_price]').on('blur', function(e) {
                // var select_type = current_select_type(),
                //     limit_price = $.trim(this.value),
                //     multi = $('#' + select_type + '_price_multi .dropdown-toggle').attr('data-value');

                var select_type = current_select_type(),
                    limit_price = $.trim(this.value),
                    multi = $('#'+select_type+' .init_price_slider').val();

                if (limit_price === '' || limit_price < 0.05 || limit_price > 99.99 || isNaN(limit_price)) {
                    this.value = $(this).attr('data-old');
                    limit_price = $(this).attr('data-old');
                }

                //同步所以限价
                $('input[id$=_limit_price]').val(this.value);

                update_max_price(Number(multi), Number(limit_price));

                PT.sendDajax({
                    'function': 'web_update_limit_price',
                    'adgroup_id': $('#adgroup_id').val(),
                    'init_limit_price': limit_price
                });
            });

            // 修改关键词出价
            $('table.keyword').on('blur', 'input.new_price', function () {
	            var new_price = isNaN(this.value)?Number($(this).prev().html()):Number(this.value),
		            select_type = current_select_type(),
		            limit_price = Number($('#'+select_type+'_limit_price').val());
                if (new_price > limit_price) {
                    new_price = limit_price;
                    $(this).addClass('orange');
                }
                if (new_price<0.05){
                    new_price = 0.05;
                    $(this).addClass('orange');
                }
                if (0.05<new_price && new_price<limit_price) {
                    $(this).removeClass('orange');
                }
                this.value = new_price.toFixed(2);
            });

            //批量修改匹配
            $('.dropdown[id$=_ms_selector]').on('change', function(e, v) {
                bulk_change_scope(v);
            });

            //精灵推荐
            $('button[id$=_recommend]').on('click', function() {
                recommend();
                change_filter_class('recommend');
                update_checked_num();
            });

            //提交到直通车
            $('button[id$=_submit]').on('click', function() {
                keywords_submit();
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

            //猜你想淘
            $('.guess_elemword li').on('click', function() {
//                var guess_list = [],
//                    guess_str = '';
//
//                $(this).toggleClass('select');
//
//                $('.guess_elemword li').each(function() {
//                    if ($(this).hasClass('select')) {
//                        guess_list.push($(this).text());
//                    }
//                });
//
//                if (guess_list.length > 3) {
//                    PT.alert('您选择的词太多，可能淘不出词来！');
//                }
//
//                $.map(guess_list, function(s) {
//                    guess_str += s + ' ';
//                });
//
//                $('#word_filter').val(guess_str);
                var guess_list;
                $(this).toggleClass('select');
                if ($(this).hasClass('select')) {
	                guess_list = $.map($('#word_filter').val().split(' '), function (kw) {return kw?kw:null;});

	                if ($('.guess_elemword li.select').length>3) {
	                    //PT.alert('您选择的词太多，可能淘不出词来！');
	                    PT.alert('最多只能选择3个核心词！');
	                }else{
	                   guess_list.push($(this).text());
	                }
                } else {
	                var that = this;
	                guess_list = $.map($('#word_filter').val().split(' '), function (kw) {return kw && kw!=$(that).text()?kw:null;});
                }
                $('#word_filter').val(guess_list.join(' '));
            });

            //猜你想淘联动
            $('#word_filter').on('keyup', function() {
                var words = $.trim($(this).val()),
                    words_list,
                    select_num = 0,
                    selected_num = 0;
                if (words === '') {
                    $('.guess_elemword li.select').removeClass('select');
                    return;
                }

                words_list = words.split(' ');

                $('.guess_elemword li').each(function() {
                    if (select_num >= words_list.length) {
                        return;
                    }
                    if ($.inArray($(this).text(), words_list) != -1) {
                        $(this).addClass('select');
                        select_num++;
                        return;
                    }
                });

                selected_num = $('.guess_elemword li.select').length;

                $('.guess_elemword li.select').each(function() {
                    if ($.inArray($(this).text(), words_list) == -1 || selected_num > words_list.length) {
                        $(this).removeClass('select');
                        selected_num--
                    }
                });

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

                if($(this).attr('checked')=='checked'){
                    $('input[class*="kid_box"]').parent().parent().addClass("bg_striped");
                }else{
                    $('input[class*="kid_box"]').parent().parent().removeClass("bg_striped");
                }

            });

            //ajax取到数据前无法抓到元素 ，用on的方式给table元素内的所有input绑定事件
            $('table').on('change','input[class*="kid_box"]',function(){
				var all_num = $('input[class*="kid_box"]').length;
				var checked_num = $('input[class*="kid_box"]:checked').length;
				if(all_num == checked_num){
				    $('.father_box').attr("checked", true);
				}else{
					$('.father_box').attr("checked", false);
				}

				if($(this).attr('checked')=='checked'){
				    $(this).parent().parent().addClass("bg_striped");
				}else{
				    $(this).parent().parent().removeClass("bg_striped");
				}

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



            //初始化tooltips
            $('.tooltips').tooltip({
                html: true
            });
        },

        //计算系统推荐的词数
        calc_combine_unput = function() {
            $('#textarea_prdtword').trigger('keyup');
            $('#textarea_dcrtword').trigger('keyup');
            $('#textarea_prmtword').trigger('keyup');
        },

        //初始化出价slider组件
        init_price_slider  =function(){
            var select_type=current_select_type();

            $('#'+select_type).find('.init_price_slider').slider({
                round: 2,
                step: 0.01,
                callback: function(v){
                    var limit_price = $('#quick_limit_price').val();
                    update_max_price(Number(v), Number(limit_price));
                },
                from: 0,
                to: 3,
                dimension: '',
                skin: "round",
                limits: false,
                scale: [0,'|',0.4,'|',0.8,'|',1.2,'|','|','|','2.0','|','|','|','|','3.0'],
                dimension: '倍行业均价'
            });
        }

        //修复复制关键词的层的位置和大小
        fixed_copy_layer = function() {
            var select_type=current_select_type(),
                obj=$('#'+select_type+'_save_as_csv>div ,#'+select_type+'_save_as_csv>div>*');

                obj.css({width:112,height:30});
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
                box_scroll=true;

            if(PT.get_habit()!==undefined&&PT.get_habit()['keyword_float_switch']===false){
                fixed_obj_h=0;
                box_scroll=false;
            }

            //防止重复绑定
            remove_scroll();

            $(window).on('scroll.PT.e', function() {
                var body_offset = document.body.scrollTop | document.documentElement.scrollTop,
                    obj_offset = fixed_obj.parent().offset().top,
                    fixed_obj_w = fixed_obj.width();

                if (body_offset >= obj_offset) {
                    if(box_scroll){
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
                        $(current_input).addClass('orange');
                    }
                    if (new_price<0.05) {
                        new_price = 0.05;
                        $(current_input).addClass('orange');
                    }
                    if (0.05<new_price && new_price<limit_price) {
                        $(current_input).removeClass('orange');
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
                    rows[i].nTr.children[1].children[1].innerText = match_scope_list[1][$.inArray(scope,match_scope_list[0])];
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
                }else{
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
//                if(sum_checked+keyword_count>200){
//                    PT.alert('一个宝贝最多只允许有200个关键词,当前已有'+keyword_count+'个，最多还能选'+(200-keyword_count)+'个');
//                }else{
//                    PT.confirm('即将添加' + sum_checked + '个关键词，确定要提交吗？', function() {
//                        keywords_info = get_submit_data();
//                        PT.sendDajax({
//                            'function': 'web_batch_add_keywords',
//                            'adgroup_id': adgroup_id,
//                            'keyword_count': keyword_count,
//                            'kw_arg_list': $.toJSON(keywords_info),
//                            'init_limit_price': (limit_price > 0 ? limit_price : 0)
//                        });
//                        PT.show_loading('正在提交数据');
//                    });
//                }
                PT.confirm('即将添加选中的关键词，确定要提交吗？', function() {
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
                    'function': 'web_select_keyword',
                    'adgroup_id': adgroup_id,
                    'cat_id': cat_id,
                    'select_type': select_type,
                    'max_add_num': max_add_num,
                    'auto_hide': 0
                };

            switch (select_type) {
                case 'precise':
                    send_data.word_filter = word_filter;
                    break;
                case 'combine':
                    send_data.prdtword_list = $.toJSON(prdtword_list);
                    send_data.dcrtword_list = $.toJSON(dcrtword_list);
                    send_data.prmtword_list = $.toJSON(prmtword_list);
                    break;
                case 'manual':
                    send_data.manword_list = $.toJSON(manword_list);
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
        change_filter_class = function(mode){
            var select_type = current_select_type();
            if(mode=='slide'){
                $('#'+select_type+'_recommend').removeClass('btn-info');
                $('#'+select_type+'_recommend').next().find('.dropdown-toggle').addClass('btn-info');
            }
            if(mode=='recommend'){
                $('#'+select_type+'_recommend').addClass('btn-info');
                $('#'+select_type+'_recommend').next().find('.dropdown-toggle').removeClass('btn-info');
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
                            "bSortable": true,
                            "sClass": "rel pr20"
                        }, {
                            'sSortDataType': 'dom-input',
                            'sType': 'numeric',
                            'sClass': "tc"
                        },
//                        null,
//                        null,
//                        null,
//                        null,
//                        null,
//                        null
                        {"sClass": "tr"},
                        {"sClass": "tr"},
                        {"sClass": "tr"},
                        {"sClass": "tr"},
                        {"sClass": "tr"},
                        {"sClass": "tr"}
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
//                        'sEmptyTable': '正在获取数据.......',
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

                             select_type = current_select_type(),
                             sum_checked = Number($('#' + select_type + '_sum_checked').html());
                             if(sum_checked=="0"){
                                PT.alert("还未选择任何关键词！");
                             }else{
                               this.fnSetText(flash, PT.SelectKeyword.creat_scv_data());
                                setTimeout(function(){
                                    PT.light_msg('','复制成功！')
                                }, 100);
                             }

                            }
                        }],
                        "custom_btn_id": select_type + "_save_as_csv"
                    },
                    'fnDrawCallback': function() {
                        init_select();
                    }
                });
            });

            $('#textarea_prdtword').css("max-width",352);
            $('#textarea_dcrtword').css("max-width",352);
            $('#textarea_prmtword').css("max-width",352);
        },

        //复制关键词
        creat_scv_data = function() {
            var select_type = current_select_type(),
                oSettings = current_table_settings(),
                keywords='';

            $.map(oSettings.aiDisplay, function(i) {
                var nTr = oSettings.aoData[i].nTr;
                if (nTr.children[0].children[0].checked) {
	                keywords+=nTr.children[1].children[0].innerText+'\r\n';
                }
            });
            return keywords;
        },

        //滑杆筛选关键词核心函数
        slide_check = function() {
            var r = 0,
                rows = get_rows(),
                r_end = rows.length,
                user_filter = PT.SelectKeyword.get_filter_list();

            for (r; r < r_end; r++) {
                var i = 0,
                    judge=1,
                    data_list = [Number(rows[r]._aData[8]), Number(rows[r]._aData[7]), Number(rows[r]._aData[5]), Number(rows[r]._aData[3])];

                for (i; i < 4; i++) {
                    if (data_list[i] < user_filter[i][0] || data_list[i] > user_filter[i][1]) {
                        judge=0;
                        break;
                    }
                }

                if (judge){
                    rows[r].nTr.children[0].children[0].checked = true;
                }else{
                    rows[r].nTr.children[0].children[0].checked = false;
                }
            }
        },

        //关键词过滤核心函数
        keyword_check = function() {
            var r = 0,
                rows = get_rows(),
                r_end = rows.length,
                user_filter = PT.SelectKeyword.get_filter_list();

            for (r; r < r_end; r++) {
                var i = 0,
                    judge = 1,
                    judge_0 = 1,
                    keyword_str = rows[r]._aData[1].match(/<a.*>(.+?)<\/a>/i)[1];

                //包含关键词
//                if (user_filter[4] && keyword_str.toUpperCase().indexOf(user_filter[4].toUpperCase()) == -1) {
//                    judge=0;
//                }
                if (user_filter[4]) {
	                judge = 0;
	                $.each(user_filter[4].replace(/，/g, ',').split(','), function (i, temp_str0) {
		                judge_0 = 1;
		                if (temp_str0) {
			                $.each(temp_str0.split(' '), function (ii, temp_str1) {
				                if (temp_str1) {
					                if (keyword_str.toUpperCase().indexOf(temp_str1.toUpperCase())==-1) {
						                judge_0 = 0;
						                return false;
					                }
				                }
			                });
		                }
		                if (judge_0==1) {
			                judge = 1;
			                return false;
		                }
	                });
                }
                //不包含关键词
//                if (judge && user_filter[5] && keyword_str.toUpperCase().indexOf(user_filter[5].toUpperCase()) != -1) {
//                    judge=0;
//                }
                if (judge && user_filter[5]) {
                    $.each(user_filter[5].replace(/，/g, ',').replace(/,/g, ' ').split(' '), function (i, temp_str0) {
                        if (temp_str0) {
                            if (keyword_str.toUpperCase().indexOf(temp_str0.toUpperCase())!=-1) {
                                judge = 0;
                                return false;
                            }
                        }
                    });
                }

                if (judge){
                    rows[r].nTr.children[0].children[0].checked = true;
                }else{
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
                        user_filter = PT.SelectKeyword.get_filter_list(),
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
        update_checked_num = function(check_num) {
            var uncheck_num=0,
                select_type = current_select_type(),
                oSettings = current_table_settings();

            if (check_num) {
                $('#' + select_type + '_sum_checked').text(num);
                return false;
            }

            check_num = 0

            $.map(oSettings.aiDisplay, function(i) {
                var nTr = oSettings.aoData[i].nTr;
                if ((nTr.children[0].children[0].checked)) {
                    check_num++;
                }else{
                    uncheck_num++;
                }
            });

            $('#' + select_type + '_sum_checked').text(check_num);
            var total_keys = $('#'+select_type+'_all_keywords').text();
            if(total_keys == check_num){
                $('input.father_box').attr("checked","checked");
            }else{
	     	$('input.father_box').removeAttr("checked");
	    }
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
                init_price_slider();
                fixed_copy_layer();
                update_max_price(1, Number($('#'+select_type+'_limit_price').val()));
            }, 0);
            PT.hide_loading();
        },

        //填充表格数据
        layout_table = function(all_keyword_list, select_type) {
            var dom = [],
                i = 0,
                i_end = all_keyword_list.length;
            for (i; i < i_end; i++) {
                dom.push(template.compile(pt_tpm['select_keyword_table.tpm.html'])({
                    'r': all_keyword_list[i]
                }).split('^,^'));
            }
            current_data_table(select_type).fnAddData(dom);
        },

        //填充其他信息
        layout_info = function(all_keyword_list, okay_count, select_type) {
            $('#' + select_type + '_sum_checked').text(0);
            $('#' + select_type + '_all_keywords').text(all_keyword_list.length);

            if(all_keyword_list.length===0){
                $('#'+select_type+'_common_table .dataTables_empty').text('没有数据，请改变搜索条件重试！');
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
            //手工加词提交完关键词后，清空输入框
            $('#textarea_manual').val('');

            //取消列头的全选状态
            $('input.father_box').removeAttr("checked");
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

            if(init_select_type === 'combine') {
                calc_combine_unput();
            }
        },
        select_keyword_callback: function(all_keyword_list, okay_count, filter_field_list, select_type) {
            layout_data(all_keyword_list, okay_count, filter_field_list, select_type);
        },
        get_filter_list: get_filter_list,
        remove_dataTable_keywords: remove_dataTable_keywords,
        update_keyword_count_2add: update_keyword_count_2add,
        creat_scv_data: creat_scv_data
    };
}();
