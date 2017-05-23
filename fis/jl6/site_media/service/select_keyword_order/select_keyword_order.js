define(['require','../common/common','dataTable','caret','tag_editor','jl6/site_media/widget/alert/alert','jl6/site_media/widget/confirm/confirm','shiftcheckbox','zclip','jslider',
             'jl6/site_media/widget/lightMsg/lightMsg','jl6/site_media/widget/ajax/ajax','jl6/site_media/widget/loading/loading','template','jl6/site_media/widget/templateExt/templateExt','../select_feedback/select_feedback'],
    function(require,common,dataTable,caret,tagEditor,alert,confirm,shiftcheckbox,zclip,jslider,lightMsg,ajax,loading,template,templateExt,select_feedback) {
        "use strict"
        var item_url, select_type, mode='precise', keyword_cache={}, pageSize=100, filterList = [];
        var keyword_table, core_keyword_box;

        var clear_page = function () {
            keyword_table.fnClearTable();
            $('#div_core_keyword').addClass('hidden');
            $('#alert_info, #keyword_selecter').addClass('vh');
            $('#div_item_info').addClass('vh').empty();
            $('#filter_group [data-type=all]').addClass('active').siblings().removeClass('active');
        }

        //显示宝贝信息
        var show_item_info = function (item_info) {
            var tpl, html;
            tpl = __inline('item_info.html');
            html = template.compile(tpl)(item_info);
            $('#div_item_info').removeClass('vh').html(html);
        }

        //填充关键词列表
        var show_keyword_list = function (keyword_list) {
            $('#alert_info, #keyword_selecter').removeClass('vh');
            keyword_table.fnClearTable();
            keyword_table.fnAddData(keyword_list);
            resetFilter();
            setFilterList();
            keyword_table.fnFilter('');
            $('.keyword_count').html(keyword_table.fnSettings().aiDisplay.length);
        }

        var wrap_keyword_list = function (keyword_list) {
            return $.map(keyword_list, function (keyword) {
                return [[
                        '',
                        '<input type="checkbox" name="keyword" value="'+keyword[0]+'" data-sys="'+keyword[10]+'" data-roi="'+keyword[11][0]+'" data-imp="'+keyword[11][1]+'" data-hppr="'+keyword[11][2]+'">',
                        keyword[0]+'<a href="http://subway.simba.taobao.com/#!/tools/insight/queryresult?kws='+keyword[0]+'" target="_blank"><i class="iconfont link">&#xe64a;</i></a>',
                        keyword[6],
                        (keyword[1]/100).toFixed(2),
                        keyword[2],
                        keyword[3],
                        keyword[5],
                        keyword[4].toFixed(2)+'%',
                        (keyword[8]/100).toFixed(2)+'%'
                    ]]
            });
        }

        var select_keyword_order = function (args) {
            loading.show('数据加载中，请稍候...');
            ajax.ajax('select_keyword_order', args, function (data) {
                if (data.data.item_info) {
                    show_item_info(data.data.item_info);
                    if (!$('#div_core_keyword').hasClass('hidden')) {
                        core_keyword_box.build_select_box(data.data.item_info.elemword_dict);
                    }
                }
                if (data.data.filter_field_list) {
                    layoutfilter(data.data.filter_field_list);
                }
                if (data.data.keyword_list) {
                    var keyword_list = wrap_keyword_list(data.data.keyword_list);
                    keyword_cache = {'pc':keyword_list, 'pc_filter':data.data.filter_field_list};
                    show_keyword_list(keyword_list);
                }
                loading.hide();
            }, null, {'url':'/toolkit/ajax/'});
        }

        //显示移动包数据
        var get_mobile_package = function (word_list) {
            loading.show('数据加载中，请稍候...');
            var word_list = $.map(keyword_table.fnSettings().aoData, function (obj) {
                return [[obj._aData[2].match('(.*)<a')[1], obj._aData[3], 0]];
            });
            ajax.ajax('mobile_package', {'word_list':JSON.stringify(word_list)}, function (data) {
                var keyword_list = wrap_keyword_list(data.data.keyword_list);
                keyword_cache.mobile = keyword_list;
                keyword_cache.mobile_filter = data.data.filter_field_list;
                layoutfilter(data.data.filter_field_list);
                show_keyword_list(keyword_list);
                loading.hide();
            }, null, {'url':'/toolkit/ajax/'});
        }

        //显示分页条条
        var layoutPageBar = function(recordCount, page) {
            var pageXrange = [], pageCount = Math.ceil(recordCount / pageSize);
            $('#pagination_info').html('每页显示'+pageSize+'个关键词　共'+pageCount+'页');

            for (var i = 1; i <= pageCount; i++) {
                pageXrange.push(i);
            }

            require(['widget/pageBar/pageBar'], function(pageBar) {
                var dom = pageBar.show({
                    data: {
                        record_count: recordCount,
                        page_xrange: pageXrange,
                        page_count: pageCount,
                        page: page,
	                    binfo: false
                    },
                    onChange: function(_page) {
                        keyword_table.fnPageChange(_page - 1);
                    }
                });
                $('#pagination_bar').html(dom);
            });
        }

        //初始化关键词表格
        var init_keyword_table = function (_id) {
            keyword_table = $(_id).dataTable({
                aoColumns: [{
                    bSortable: true,
                    sType: "custom",
                    sSortDataType: "custom-text",
                    sClass: "hidden"
                }, {
                    bSortable: false,
                    sClass: "hidden"
                }, {
                    bSortable: true
                }, {
                    bSortable: true
                }, {
                    bSortable: true
                }, {
                    bSortable: true
                }, {
                    bSortable: true
                }, {
                    bSortable: true
                }, {
                    bSortable: true,
                    sType: "custom-percent"
                }, {
                    bSortable: true,
                    sType: "custom-percent"
                }],
                bLengthChange: false,
                bDestroy: true,
                iDisplayLength: pageSize,
                sDom: "",
                oLanguage: {
                    sZeroRecords: "没有关键词记录",
                },
                fnDrawCallback: function(oSettings) {
                    if (oSettings.aiDisplay.length) {
                        //显示分页条
                        layoutPageBar(oSettings.aiDisplay.length, (oSettings._iDisplayStart / pageSize) + 1);

                        //有数据显示底部操作区
                        $('#keyword_selecter .bottom').css('visibility','visible');
                    }else{
                        //没有数据隐藏底部操作区
                        $('#keyword_selecter .bottom').css('visibility','hidden');
                    }
                },
                aaSorting: [
                    [0, 'desc']
                ]
            });
        }

        //datatable过滤扩展
        var customDatatableExt = function() {
            $.fn.dataTableExt.afnFiltering.push(
                function(oSettings, aData, iDataIndex) {
                    if (!filterList.length) {
                        return true;
                    }

                    //获取用slider过滤条件
                    var dataList = [Number(aData[3]), Number(aData[9].replace('%','')), Number(aData[7]), Number(aData[6]), Number(aData[4]), aData[2].match('(.*)<a')[1], Number(aData[0])],
                        i = 0;

                    for (i; i < 5; i++) {
                        if (dataList[i] < filterList[i][0] || dataList[i] > filterList[i][1]) {
                            return false;
                        }
                    }

                    //过滤关键词
                    if (filterList[5]) {
                        //包含关键词
                        if (filterList[5] && dataList[5].toUpperCase().indexOf(filterList[5].toUpperCase()) == -1) {
                            return false;
                        }
                    }

                    //过滤关键词
                    if (filterList[6]) {
                        //不包含关键词
                        if (filterList[6] && dataList[5].toUpperCase().indexOf(filterList[6].toUpperCase()) != -1) {
                            return false;
                        }
                    }

                    //过滤分类['系统推荐']
                    if (filterList[6] && filterList[6] != 'all' && filterList[6] != 'mobile') {
                        // oSettings.oInstance.fnUpdate
                        var temp = Number(aData[1].match(filterList[6] + '="(.*?)"')[1]);

                        //temp等于-1表示不是改包推荐，大于-1代表排名
                        if (temp==-1) {
                            return false;
                        }
                    }

                    //当是系统推荐和全部候选时默认使用匹配度排序
                    if (['sys', 'all'].indexOf(filterList[6]) != -1) {
                        oSettings.oInstance.fnGetNodes(iDataIndex).childNodes[0].innerText = Number(aData[3]);
                    } else {
                        oSettings.oInstance.fnGetNodes(iDataIndex).childNodes[0].innerText = temp;
                    }

                    return true;
                }
            );
        }

        //显示滑杆
        var layoutfilter = function(filterFieldList) {
            var obj = $('#filter_sliders');
            obj.empty();

            //fix slider定位问题
            $('#keyword_selecter .dropdown-menu').addClass('db vh');

            for (var i = 0; i < filterFieldList.length; i++) {
                var cfg = $.extend(true, {}, filterFieldList[i]);
                if (cfg.series_name == 'keyword_score' || cfg.series_name == 'cat_click' || cfg.series_name == 'coverage') {
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

                var html_slider = template.compile(__inline('../select_keyword/slider.html'))({
                    cfg: cfg,
                    selectType: ''
                });
                obj.append(html_slider);
                if (cfg.svl[0] != cfg.from) {
                    cfg.svl.unshift(cfg.from);
                } else if (cfg.svl.length == 1) {
                    cfg.svl.push(cfg.from + 1);
                }
                //jslider 生成滑块
                if (cfg.series_name == "cat_cpc" || cfg.series_name == "coverage") {
                    $("#_" + cfg.series_name).slider({
                        round: 2,
                        step: 0.01,
                        callback: sliderCallback,
                        from: cfg.from,
                        to: cfg.limit,
                        limits: false,
                        dimension: '',
                        skin: "plastic",
                        heterogeneity: cfg.heterogeneity || [],
                        // scale: [cfg.from, cfg.limit]
                    });
                } else {
                    $("#_" + cfg.series_name).slider({
                        step: 1,
                        callback: sliderCallback,
                        from: cfg.from,
                        to: cfg.limit,
                        limits: false,
                        dimension: '',
                        skin: "plastic",
                        heterogeneity: cfg.heterogeneity || [],
                        // scale: [cfg.from, cfg.limit]
                    });

                }
            }
            $('#keyword_selecter .dropdown-menu').removeClass('db vh');
        }

        //重置搜索条件
        var resetFilter = function(){
            //重置滑杆
            $('#filter_sliders input').each(function(){
                var data=$(this).data();
                $(this).slider("value", data.from, data.to);
            });

            //重置搜索条件
            $('#filter_include').val('');
        }

        //滑动条回调函数
        var sliderCallback = function() {
            setFilterList();
            keyword_table.fnFilter('');
            $('.keyword_count').html(keyword_table.fnSettings().aiDisplay.length);
        }

        //设置过滤器
        var setFilterList = function() {
            //filterList [匹配度,转化率,竞争度,点击指数,市场均价(元),关键词,关键词分类]
            var temp;
            filterList = [];
            for (var i=0;i<5;i++) {
                var s_obj = $('#filter_sliders input')[i];
                if (s_obj) {
                    temp = s_obj.value.split(';');
                    filterList.push([Math.min(temp[0], temp[1]), Math.max(temp[0], temp[1])]);
                } else {
                    filterList.push([0, 0]);
                }
            }
            filterList.push($.trim($('#filter_include').val()));
            filterList.push($.trim($('#filter_uninclude').val()));
            filterList.push($.trim($('#filter_group .filter.active').attr('data-type')));
        }

        //初始化核心词输入框
        var init_core_keyword = function (_id) {
            core_keyword_box = function (obj) {
		        var options = {
		            placeholder: '输入核心词',
		            onChange:function (field, editor, tags) {
		                $('#select_box ul.pt-tag>li').removeClass('select');
		                var value = '';
		                for (var i in tags) {
		                    value += tags[i];
		                    $('#select_box a[value='+tags[i]+']').parent('li').addClass('select');
		                }
		            }
		        }
		        obj.tagEditor(options);

		        return {
		            get_word_list:function () {
		                return obj.tagEditor('getTags')[0].tags;
		            },
		            clear: function () {
		                obj.text('');
		                var tags = core_keyword_box.get_word_list();
				        for (var i in tags) {
				            obj.tagEditor('removeTag', tags[i]);
				        }
				        $('#div_core_keyword>ul.tag-editor').focusout();
				        $('#select_box .pt-tag>li').removeClass('select');
		            },
		            addTag: function (word) {
		                obj.tagEditor('addTag', word);
		            },
                    removeTag: function (word) {
		                obj.tagEditor('removeTag', word);
                    },
		            build_select_box: function (data) {
		                core_keyword_box.clear();
		                var tpl, html;
		                tpl = __inline('select_box.html');
		                html = template.compile(tpl)(data);
		                $('#select_box').html(html);
		            }
		        }
            } ($(_id));
        }

        var show_select_box = function () {
            $("#select_box").height($("#select_box>div").outerHeight());
            $("#div_core_keyword>ul.tag-editor").addClass('focus');
        }

        var hide_select_box = function () {
            $("#select_box").height(0);
            $("#div_core_keyword>ul.tag-editor").removeClass('focus');
        }

        //初始化核心词选词框
        var init_select_box = function () {
            $('#div_core_keyword>ul.tag-editor').focusin(function () {
                show_select_box();
            });

            $(document).click(function (e) {
                if ($(e.target).closest('#div_core_keyword').length==0) {
                    hide_select_box();
                }
            });

            $('#select_box').on('click', '.pt-tag>li', function () {
                if($(this).hasClass('select')){
                    $(this).removeClass('select');
                    core_keyword_box.removeTag($(this).text());
                }else{
                    if (core_keyword_box.get_word_list().length<3) {
                        $(this).addClass('select');
                        core_keyword_box.addTag($(this).text());
                    } else {
                        lightMsg.show('最多只能选择3个核心词');
                    }
                }
            });
        }

        //复制关键词
        var copyData = function () {
            var oSettings = keyword_table.fnSettings();
            var word_list = $.map(oSettings.aiDisplay, function (i) {
                return oSettings.aoData[i]._aData[2].match('(.*)<a')[1];
            });
            return word_list.join('\n');
        }

        var init_dom = function () {
            //快搜一下，精准淘词
            $('#btn_quick_select, #btn_precise_tao').click(function () {
                clear_page();
                $('#top_advs div:eq(0)').addClass('inactive');
                $('#top_advs div:eq(1)').removeClass('inactive');
                item_url = $.trim($('#item_url').val());
                if (item_url) {
                    var args = {'item_url':item_url};
                    switch (this.id) {
                        case 'btn_quick_select':
                            $.extend(args, {'select_type':'quick', 'mode':'precise'});
                            $('#mode_switch').show();
                            break;
                        case 'btn_precise_tao':
                            $.extend(args, {'select_type':'precise'});
                            $('#div_core_keyword').removeClass('hidden');
                            $('#mode_switch').hide();
                            break;
                    }
	                select_keyword_order(args);
                } else {
                    alert.show('请先输入宝贝链接');
                }
            });

            //开始淘词
            $('#btn_precise_tao2').click(function () {
                var word_list = core_keyword_box.get_word_list();
                if (word_list.length==0) {
                    alert.show('请先输入核心词');
                } else {
                    hide_select_box();
                    select_keyword_order({
                        'item_url':item_url,
                        'select_type':'precise',
                        'word_filter':word_list.join(' '),
                    });
                }
            });

            //显示隐藏宝贝信息
            $('#div_item_info').on('click', 'a.arrow', function () {
                $('#div_item_info').toggleClass('up');
            });

            //精准、流量模式切换
            $('#mode_switch button').click(function () {
                if (!$(this).hasClass('active')) {
                    $(this).addClass('active btn-primary').removeClass('btn-default');
                    $(this).siblings().removeClass('active btn-primary').addClass('btn-default');
                    $('#filter_group [data-type=all]').addClass('active').siblings().removeClass('active');
                    select_keyword_order({
                        'item_url':item_url,
                        'select_type':'quick',
                        'mode':$(this).data('mode')
                    });
                }
            });

            //词包切换
            $('#filter_group .filter').click(function () {
                if (!$(this).hasClass('active')) {
                    $(this).addClass('active').siblings().removeClass('active');
                }
                if ($(this).data('type')=='mobile') {
                    if (keyword_cache.mobile) {
                        layoutfilter(keyword_cache.mobile_filter);
                        show_keyword_list(keyword_cache.mobile);
                    } else {
                        get_mobile_package();
                    }
                } else {
                    layoutfilter(keyword_cache.pc_filter);
                    show_keyword_list(keyword_cache.pc);
                    keyword_table.fnSort([
                            [0, 'desc']
                        ]);
                }
            });

            //搜索关键词
            $('.btn_search').on('click', function() {
                sliderCallback();
            });

            //复制关键词
            $('#copy_btn').zclip({
                path: __uri('../../plugins/zclip/ZeroClipboard.swf'),
                copy: function() {
                    return copyData();
                },
                afterCopy: function() {
                    lightMsg.show('已复制成功，赶紧分享给你的小伙伴吧！');
                }
            });

            //导出关键词
            $('#export_btn').click(function () {
                var oSettings = keyword_table.fnSettings();
                var row_list = $.map(oSettings.aiDisplay, function (i) {
                    var _row = oSettings.aoData[i]._aData.slice(2);
                    _row[0] = _row[0].match('(.*)<a')[1];
                    return _row.join(',');
                });
                this.href = 'data:text/csv;charset=utf-8,\ufeff'+encodeURIComponent('关键词,匹配度,市场均价,展现指数,点击指数,竞争指数,市场点击率,市场转化率\n'+row_list.join('\n'));
            });
        }

        return {
            init: function() {
                customDatatableExt();
                init_keyword_table('#table_select_keyword');
                init_core_keyword('#core_keyword');
                init_select_box();
                select_feedback.init();
                init_dom();
            }
        }
    }
);
