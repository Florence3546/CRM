define(['require', "template", 'widget/alert/alert', 'widget/ajax/ajax', 'widget/loading/loading', 'widget/lightMsg/lightMsg', 'widget/tagEditor/tagEditor', '../select_feedback/select_feedback', 'json', 'dataTable', 'jslider', 'widget/templateExt/templateExt', 'shiftcheckbox', 'zclip'], function(require, template, alert, ajax, loading, lightMsg, tagEditor, select_feedback) {
    "use strict";

    var wordFilter,

        prdtwordList = [],

        dcrtwordList = [],

        prmtwordList = [],

        manwordList = [],

        prdtwordMaxNum = 5,

        dcrtwordMaxNum = 15,

        prmtwordMaxNum = 5,

        adgroupId = $("#adgroup_id").val(),

        catId = $("#cat_id").val(),

        //首次进入的选词类型
        initSelectType = $('#init_select_type').val(),

        keywordCount = Number($("#keyword_count_hidden").val()) || 0,

        maxAddNum = 200 - keywordCount,

        bottomLimit,

        bodyHeight = document.body.offsetHeight,

        pageSize = 50,

        maxPriceLimit = Number($('#max_price_limit').val()),

        filterList = [],

        cache = {},

        fixedHeader,

        initDom = function() {

            $('.btn_search').on('click', function() {
                sliderCallback();
            });

            $('button.filter').on('click', function() {
                var type = $(this).attr('data-type'),
                    selectType = currentSelectType();
                $(this).parent().find('.filter').removeClass('active');
                $(this).addClass('active');

                resetFilter();
                // setFilterList();
                fixDom();

                setTimeout(function() {
                    if (type != 'mobile') {
                        if (typeof cache[selectType] != "undefined") {
                            getDataCallback(cache[selectType]);
                        }
                        // currentDataTable().fnFilter('');
                        currentDataTable().fnSort([
                            [0, 'desc']
                        ]);
                        refreshBottomLimit();
                    } else {
                        if (typeof cache[selectType + 'Mobile'] == "undefined") {
                            getMobileData();
                        } else {
                            getMobileDataCallback(cache[selectType + 'Mobile'])
                        }
                    }
                    currentDataTable().fnSort([
                        [0, 'desc']
                    ]);
                }, 0);
            });

            //选词车全选事件
            $('#keyword_cart .choose_all_column input').on('change', function() {
                if (this.checked) {
                    $('#scroll_box table>tbody>tr td.check_column input').each(function() {
                        this.checked = true;
                    });
                } else {
                    $('#scroll_box table>tbody>tr td.check_column input').each(function() {
                        this.checked = false;
                    });
                }
                calcCheckedNum();
            });

            //选词车修改确定
            $('#modify_box .btn-primary').on('click', function() {
                var mode,
                    matchType,
                    rows;

                mode = $('#modify_box input[name=price]:checked').val();
                matchType = $('#modify_box input[name=match]:checked').val();

                if (mode || matchType) {
                    rows = cartCheckRow();

                    if (rows.length) {
                        //修改出价
                        editCartPrice(mode, rows);

                        //修改匹配模式
                        if (matchType) {
                            editCartMatchType(matchType, rows);
                        }
                    } else {
                        lightMsg.show('没有选中的关键词');
                    }

                    $('#modify_box').parent().removeClass('open');
                } else {
                    lightMsg.show('没有选择操作类型');
                }
            });

            //选词车修改取消
            $('#modify_box .btn-default').on('click', function() {
                $('#modify_box').parent().removeClass('open');
            });

            //修改最高限价
            // $('#max_price_limit').on('change', function() {
            //     maxPriceLimit = Number($(this).val());
            // });

            //选词车删除
            $('#remove_cart').on('click', function() {
                var rows = cartCheckRow();
                if (rows.length) {
                    for (var i in rows) {
                        rows[i].find('.del').trigger('click');
                    }
                    calcCheckedNum();
                    $('#keyword_cart .choose_all_column input')[0].checked = false;
                } else {
                    lightMsg.show('没有选中的关键词');
                }
            });

            //复制关键词
            $('.copy_btn').zclip({
                path: __uri('../../plugins/zclip/ZeroClipboard.swf'),
                copy: function() {
                    return copyData();
                },
                afterCopy: function() {
                    // var hasChecked;
                    // $(currentTableSettings().aoData).each(function() {
                    //     if (this.nTr.childNodes[1].childNodes[0].checked) {
                    //         hasChecked=true;
                    //         return;
                    //     }
                    // });
                    // if(hasChecked){
                    lightMsg.show('已复制成功，赶紧分享给你的小伙伴吧！');
                    // }else{
                    //     alert.show('请勾选候选词中要复制的关键词');
                    // }
                }
            });

            //导出关键词
            $('.export_btn').click(function() {
                var oSettings = currentDataTable().fnSettings();
                var row_list = $.map(oSettings.aiDisplay, function(i) {
                    var _row = oSettings.aoData[i]._aData.slice(1);
                    _row[0] = _row[0].match('(.*)</div')[1];
                    _row[0] = _row[0].substr(18, _row[0].length)
                    return _row.join(',');
                });
                this.href = 'data:text/csv;charset=utf-8,\ufeff' + encodeURIComponent('关键词,匹配度,市场均价,展现指数,点击指数,竞争指数,市场点击率,市场转化率\n' + row_list.join(''));
            });

            //选中当前页到选词车
            $('.add_page').on('click', function() {
                currentDataTable().find('tbody tr').each(function() {
                    var input = this.childNodes[1].childNodes[1];
                    input.checked = true;
                    chooseKeyword.call($(input));
                });
            });

            //提交选中的词到后台
            $('#submit_keyword').on('click', function() {
                var rows = cartCheckRow(),
                    kwArgList = [];
                if (rows.length) {
                    for (var i in rows) {
                        kwArgList.push([
                            rows[i].find('.word').text(),
                            Number(rows[i].find('.price').val()) * 100,
                            rows[i].find('.match').data().match,
                            null,
                            null
                        ]);
                    }

                    loading.show('正在提交关键词');

                    ajax.ajax('batch_add_keywords', {
                        adgroup_id: adgroupId,
                        keyword_count: keywordCount,
                        kw_arg_list: $.toJSON(kwArgList),
                        init_limit_price: maxPriceLimit
                    }, function(data) {
                        loading.hide();
                        alert.show(data.data.result_mesg);


                        $('#count_keyword_count').text(Number($('#count_keyword_count').text()) + data.data.added_keyword_count);
                        //删除已选
                        for (var i in rows) {
                            rows[i].find('.del').trigger('click', true);
                        }
                    });

                } else {
                    lightMsg.show('没有选中的关键词');
                }
            });

            //切换选词方式
            $('#select_keyword_nav>li>a').on('shown.bs.tab', function() {
                var selectType = currentSelectType(),
                    pageName;

                if (selectType === 'quick' && !$(this).hasClass('inited')) {
                    getData(selectType);
                    $(this).addClass('inited');
                } else {
                    filterList = [];
                }

                if (selectType === 'combine') {
                    calcCombineUnput();
                }

                initFixedHeader();
                fixDom();

                pageName = "/web/select_keyword/" + selectType + "?adgroup_id=" + adgroupId;
                //改变浏览器URL,以便于刷新操作
                history.pushState && history.pushState(pageName, "", pageName);
            });

            //选词车删除
            $('#scroll_box').on('click', '.del', function(e, type) {
                var inputId;

                inputId = $(this).parent().parent().attr('id').replace('cart_tr_', '');

                $(this).parent().parent().remove();
                $('#' + inputId).length && ($('#' + inputId)[0].checked = false);
                calcTotalNum();
                calcCheckedNum();

                //type为true时表示关联的元素也删除
                if (type == true && $('#' + inputId).length) {
                    var instance = currentDataTable();
                    instance.fnDeleteRow(instance.fnGetPosition($('#' + inputId).parent().parent()[0]));
                }
            });

            //猜你想淘
            $('.guess_elemword li').on('click', function() {
                var tag = $(this).text();

                if (!$(this).hasClass('select')) {
                    if (preciseTag.getTags().length < 3) {
                        preciseTag.addTag(tag);
                    } else {
                        lightMsg.show('最多只能选择3个核心词！');
                    }
                } else {
                    preciseTag.removeTag(tag);
                }
                // if($(this).hasClass('select')){
                //     if(preciseTag.getTags().length<3){
                //         preciseTag.addTag(tag);
                //     }else{
                //         $(this).removeClass('select');
                //         lightMsg.show('最多只能选择3个核心词！');
                //     }
                // }else{
                //     preciseTag.removeTag(tag);
                // }
            });

            //显示更多修饰词
            // $('#select_box').on('click', '.btn_more',function(){
            //     $(this).siblings('li').removeClass('hide');
            //     $(this).html('&#xe604;');
            //     $(this).removeClass('btn_more');
            //     $(this).addClass('btn_collapse');
            // });

            // $('#select_box').on('click', '.btn_collapse',function(){
            //     $(this).siblings('li:gt(13)').addClass('hide');
            //     $(this).html('&#xe605;');
            //     $(this).removeClass('btn_collapse');
            //     $(this).addClass('btn_more');
            // });

            //精准淘词选词框
            var preciseTag = tagEditor.tagEditor($('#word_filter'), {
                placeholder: '点击输入框选择或输入核心词',
                onChange: function() {
                    var inputTags = preciseTag.getTags();
                    $('.guess_elemword>li').each(function() {
                        var sysTags = $(this).text(),
                            exist = false;
                        for (var i in inputTags) {
                            if (inputTags[i] == sysTags) {
                                exist = true;
                            }
                        }

                        if (exist) {
                            $(this).addClass('select');
                        } else {
                            $(this).removeClass('select');
                        }
                    });
                }
            });

            preciseTag.focus(function() {
                $('#select_box').removeClass('hide');
            });

            $(document).on('click.select_box', function() {
                $('#select_box').addClass('hide');
            });

            $('#btn_tao_keyword').on('click', function() {
                var inputTags = preciseTag.getTags();

                if (inputTags.length) {
                    wordFilter = inputTags.join(' ');
                    getData();
                } else {
                    alert.show('亲，请先输入要包含的核心词。')
                }
            });

            //手工组词计算产品词
            $('#textarea_prdtword').on('keyup', function() {
                var _prdtwordList = $.trim($(this).val()).split('\n');
                _prdtwordList = $.map(_prdtwordList, function(word) {
                    if (word) {
                        return word;
                    }
                });
                $('#prdtword_count').html(_prdtwordList.length);
                prdtwordList = _prdtwordList;
            });

            //修饰词计算产品词
            $('#textarea_dcrtword').on('keyup', function() {
                var _dcrtwordList = $.trim($(this).val()).split('\n');
                _dcrtwordList = $.map(_dcrtwordList, function(word) {
                    if (word) {
                        return word;
                    }
                });
                $('#dcrtword_count').html(_dcrtwordList.length);
                dcrtwordList = _dcrtwordList;
            });

            //促销词计算产品词
            $('#textarea_prmtword').on('keyup', function() {
                var _prmtwordList = $.trim($(this).val()).split('\n');
                _prmtwordList = $.map(_prmtwordList, function(word) {
                    if (word) {
                        return word;
                    }
                });
                $('#prmtword_count').html(_prmtwordList.length);
                prmtwordList = _prmtwordList;
            });

            //手工组词选词按钮事件
            $('#btn_auto_combine_words').on('click', function() {

                $('#textarea_prdtword').trigger('keyup');
                $('#textarea_dcrtword').trigger('keyup');
                $('#textarea_prmtword').trigger('keyup');

                if (prdtwordList.length === 0) {
                    alert.show('亲，产品词至少要有一个！');
                    return false;
                } else if (prdtwordList.length > prdtwordMaxNum) {
                    alert.show('亲，产品词请不要超过' + prdtwordMaxNum + '个！');
                    return false;
                } else if (dcrtwordList.length > dcrtwordMaxNum) {
                    alert.show('亲，属性词/修饰词请不要超过' + dcrtwordMaxNum + '个！');
                    return false;
                } else if (prmtwordList.length > prmtwordMaxNum) {
                    alert.show('亲，促销词请不要超过' + prmtwordMaxNum + '个！');
                    return false;
                }
                getData();
            });

            //手工加词计算词数
            $('#textarea_manual').on('keyup', function() {
                manwordList = $.trim($(this).val()).split('\n');
                manwordList = $.map(manwordList, function(word) {
                    if (word) {
                        return word;
                    }
                });
                $('#manual_count').html(manwordList.length);
            });

            //手工加词选词按钮事件
            $('#btn_manual_add_words').on('click', function() {
                $('#textarea_manual').trigger('keyup');
                if (manwordList.length == 0) {
                    alert.show('亲，请先输入关键词！');
                    return false;
                }
                getData();
            });


            $('#scroll_box').on('change', 'input[type=text]', function() {
                var currentPrice = Number(this.value);
                if (isValidInput(currentPrice)) {
                    if (currentPrice > maxPriceLimit) {
                        $(this).val(Number(maxPriceLimit).toFixed(2));
                    } else {
                        $(this).val(currentPrice.toFixed(2));
                    }
                } else {
                    $(this).val($(this).data().cpc);
                }
            });

            $('#max_price_limit').on('change', function() {
                var rows = cartCheckRow();

                maxPriceLimit = Number($(this).val()).toFixed(2);

                if (isValidInput(maxPriceLimit)) {
                    for (var i in rows) {
                        var obj = rows[i].find('.price');

                        if (Number(obj.val()) > maxPriceLimit) {
                            obj.val(maxPriceLimit);
                        }

                    }
                    $('#max_price_limit').val(maxPriceLimit);
                } else {
                    $(this).val($(this).data().old);
                    lightMsg.show('最高限价无效');
                }
            });


            //关闭alert时，修改表头
            $('.alert').bind('closed.bs.alert', function() {
                fixedHeader.fnUpdate();
            });

            $('#custome_price,#custome_price_multiple').on('focus', function() {
                console.log($(this));
                $(this).prev()[0].checked = true;
            });

            $('#slider_input').slider({
                from:50,
                to:250,
                step:1,
                range:'min',
                skin:"platform",
                limits:false,
                scale: ['0.5', '1.0', '1.5', '2.0', '2.5'],
                onstatechange: function(value){
                    var parent_div = $('.slider_input[name=slider_input]').closest('div');
                    parent_div.find('.jslider-bg .v').css('width',parseFloat((value-50)*100)/200+"%");
                    $('#custome_price_multiple').val((Number(value)/100).toFixed(2));
                }
            });

            $('#slider_input').on('click',function(){
                $('#custome_price_multiple').trigger('focus');
            });

            $('#custome_price_multiple').on('blur', function() {
                if(isNaN(this.value) || this.value < 0.5 || this.value > 2.5){
                    this.value=(Number($('#slider_input').slider('value'))/100).toFixed(2);
                    return false;
                }
                $('#slider_input').slider('value',this.value*100);

            });

        },

        isValidInput = function(str) {
            if (isNaN(str) || str < 0.05 || str > 99.99) {
                return false;
            }
            return true;
        },

        //当前选词方式
        currentSelectType = function() {
            return $('#select_keyword_nav li.active a').attr('href').replace('#', '');
        },

        //计算系统推荐的词数
        calcCombineUnput = function() {
            $('#textarea_prdtword').trigger('keyup');
            $('#textarea_dcrtword').trigger('keyup');
            $('#textarea_prmtword').trigger('keyup');
        },

        //刷新浮动框界限
        refreshBottomLimit = function() {
            $('#keyword_cart').removeClass('fixed').css({
                'marginTop': 0
            });
            bottomLimit = $('#keyword_selecter').outerHeight() + $('#keyword_selecter').offset().top - bodyHeight;
            $(document).trigger('scroll');
        },

        fixDom = function() {
            var keywordCartHeight;

            keywordCartHeight = $('#keyword_cart_box').offset().top;

            refreshBottomLimit();

            $(document).off('scroll').on('scroll', function() {
                var bodyOffset = document.body.scrollTop | document.documentElement.scrollTop;

                if (bodyOffset > keywordCartHeight) {
                    if (bodyOffset > bottomLimit) {
                        if (bottomLimit > 0 && bottomLimit > keywordCartHeight) {
                            $('#keyword_cart').removeClass('fixed').css({
                                'marginTop': bottomLimit - keywordCartHeight
                            });
                        }
                        $('#keyword_cart .bottom_operation').css('position', 'absolute');
                        $('#keyword_selecter .bottom_operation').css('position', 'absolute');
                    } else {
                        if (bottomLimit > 0) {
                            $('#keyword_cart').addClass('fixed').css({
                                'marginTop': 0
                            });
                        }
                        $('#keyword_cart .bottom_operation').css('position', 'fixed');
                        $('#keyword_selecter .bottom_operation').css('position', 'fixed');
                    }
                } else {
                    $('#keyword_cart').removeClass('fixed');
                }
            });

            $('#scroll_box').css('maxHeight', bodyHeight - 140);
            $('#keyword_cart_box').css('height', bodyHeight);
            $('#keyword_cart .bottom_operation').css('visibility', 'visible');
            $(document).trigger('scroll');
        },

        //获取关键词数据
        getData = function() {
            var selectType = currentSelectType(),
                sendData = {
                    'adgroup_id': adgroupId,
                    'cat_id': catId,
                    'select_type': selectType,
                    'max_add_num': maxAddNum,
                    'auto_hide': 0
                };

            switch (selectType) {
                case 'precise':
                    sendData['word_filter'] = wordFilter;
                    break;
                case 'combine':
                    sendData['prdtword_list'] = $.toJSON(prdtwordList);
                    sendData['dcrtword_list'] = $.toJSON(dcrtwordList);
                    sendData['prmtword_list'] = $.toJSON(prmtwordList);
                    break;
                case 'manual':
                    sendData['manword_list'] = $.toJSON(manwordList);
                    break;
            }

            loading.show('正在获取数据,请稍候...');
            ajax.ajax('select_keyword', sendData, function(data) {
                data.timestamp = new Date().getTime();
                getDataCallback(data);
            });

        },

        getDataCallback = function(data) {
            var selectType = currentSelectType();

            loading.hide();
            $('#' + selectType + '_box').removeClass('hidden');

            layoutfilter(data.data.filter_field_list);
            layoutTable(data.data.keyword_list, data.timestamp);

            cache[selectType] = data;

            initFixedHeader();
            refreshBottomLimit();
        },

        //获取移动数据
        getMobileData = function() {
            var selectType = currentSelectType(),
                dataRows = currentDataTable().fnGetData(),
                wordList = [];

            for (var i in dataRows) {
                wordList.push([
                    dataRows[i][1].match(/mobile="0">(.*?)<\/span/)[1],
                    Number(dataRows[i][2]), (dataRows[i][1].indexOf('del') == -1) ? 0 : 1
                ])
            }

            loading.show('正在获取数据,请稍候...');
            ajax.ajax('mobile_package', {
                word_list: $.toJSON(wordList)
            }, function(data) {
                data.timestamp = new Date().getTime();
                getMobileDataCallback(data);
            });

        },

        getMobileDataCallback = function(data) {
            var selectType = currentSelectType();
            loading.hide();

            layoutfilter(data.data.filter_field_list);
            layoutTable(data.data.keyword_list, data.timestamp);

            cache[selectType + 'Mobile'] = data;
        },

        //填充表格数据
        layoutTable = function(keywordList, timestamp) {
            var dom = [],
                i = 0,
                tpl = __inline('table.html'),
                selectType = currentSelectType(),
                iEnd = keywordList.length;

            setFilterList();

            for (i; i < iEnd; i++) {
                dom.push(template.compile(tpl)({
                    r: keywordList[i],
                    i: String(i) + String(timestamp),
                    s: selectType
                }).split('^,^'));
            }
            currentDataTable().fnClearTable();
            currentDataTable().fnAddData(dom);
            // fixDom();
        },

        //显示分页条条
        layoutPageBar = function(recordCount, page) {
            var selectType = currentSelectType(),
                pageXrange = [],
                pageCount = Math.ceil(recordCount / pageSize);

            for (var i = 1; i <= pageCount; i++) {
                pageXrange.push(i);
            }

            require(['widget/pageBar/pageBar'], function(pageBar) {
                var dom = pageBar.show({
                    data: {
                        record_count: recordCount,
                        page_xrange: pageXrange,
                        page_count: pageCount,
                        page: page
                    },
                    onChange: function(_page) {
                        currentDataTable().fnPageChange(_page - 1);
                        refreshBottomLimit();
                    }
                });

                $('#' + selectType + '_pagination').html(dom);
            });

        },

        //显示滑杆
        layoutfilter = function(filterFieldList) {
            var selectType = currentSelectType(),
                obj = $('#' + selectType + '_div_sliders');

            obj.empty();

            fixSliderPositionStart();
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

                var html_slider = template.compile(__inline('slider.html'))({
                    cfg: cfg,
                    selectType: selectType
                });
                obj.append(html_slider);
                if (cfg.svl[0] != cfg.from) {
                    cfg.svl.unshift(cfg.from);
                } else if (cfg.svl.length == 1) {
                    cfg.svl.push(cfg.from + 1);
                }
                //jslider 生成滑块
                if (cfg.series_name == "cat_cpc" || cfg.series_name == "coverage") {
                    $("#" + selectType + '_' + cfg.series_name).slider({
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
                    $("#" + selectType + '_' + cfg.series_name).slider({
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
            fixSliderPositionEnd();
        },

        //重置搜索条件
        resetFilter = function() {
            var selectType = currentSelectType();

            //重置滑杆
            $('#' + selectType + '_div_sliders input').each(function() {
                var data = $(this).data();
                $(this).slider("value", data.from, data.to);
            });

            //重置搜索条件
            $('#' + selectType + '_include').val('');
        },

        //fix slider定位问题
        fixSliderPositionEnd = function() {
            var selectType = currentSelectType();
            $('#' + selectType + ' .dropdown-menu').removeClass('db vh');
        },

        fixSliderPositionStart = function() {
            var selectType = currentSelectType();
            $('#' + selectType + ' .dropdown-menu').addClass('db vh');
        },

        //滑动条回调函数
        sliderCallback = function() {
            setFilterList();
            currentDataTable().fnFilter('');
            refreshBottomLimit();
        },

        //设置过滤器
        setFilterList = function() {
            //filterList [匹配度,竞争度,点击指数,市场均价(元),关键词,关键词分类]
            var selectType = currentSelectType(),
                temp;
            filterList = []
            for (var i = 0; i < 5; i++) {
                var s_obj = $('#' + selectType + '_div_sliders input')[i];
                if (s_obj) {
                    temp = s_obj.value.split(';');
                    filterList.push([Math.min(temp[0], temp[1]), Math.max(temp[0], temp[1])]);
                } else {
                    filterList.push([0, 0]);
                }
            }
            filterList.push($.trim($('#' + selectType + '_include').val()));
            filterList.push($.trim($('#' + selectType + '_uninclude').val()));
            filterList.push($.trim($('#' + selectType).find('.filter.active').attr('data-type')));
        },

        //滑杆筛选关键词核心函数
        // slideCheck = function() {
        //     var r = 0,
        //         rows = getRows(),
        //         r_end = rows.length;

        //     for (r; r < r_end; r++) {
        //         var i = 0,
        //             judge=1,
        //             data_list = [Number(rows[r]._aData[2]), Number(rows[r]._aData[6]), Number(rows[r]._aData[5]), Number(rows[r]._aData[3])];

        //         for (i; i < 4; i++) {
        //             if (data_list[i] < filterList[i][0] || data_list[i] > filterList[i][1]) {
        //                 judge=0;
        //                 break;
        //             }
        //         }

        //         if (judge){
        //             rows[r].nTr.children[0].children[0].checked = true;
        //         }else{
        //             rows[r].nTr.children[0].children[0].checked = false;
        //         }
        //     }
        // },

        //初始化datatable
        initTable = function() {
            var taht = this;
            $('table[id*=_common_table]').each(function() {
                var select_type = this.id.replace('_common_table', '');
                $(this).dataTable({
                    aoColumns: [{
                        bSortable: true,
                        sType: "custom",
                        sSortDataType: "custom-text",
                        sClass: "hide"
                    }, {
                        bSortable: false
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
                    autoWidth: false,
                    bDestroy: true,
                    fnRowCallback: function(nRow, aData, iDisplayIndex, iDisplayIndexFull) {
                        //已经选中
                        var inputId = aData[1].match(/id="(.*?)"/)[1],
                            dom;

                        dom = document.getElementById('cart_tr_' + inputId);
                        if (dom) {
                            $('#' + inputId, nRow)[0].checked = true;
                        } else {
                            $('#' + inputId, nRow)[0].checked = false;
                        }
                        $(nRow).addClass('check_column');
                    },
                    aaSorting: [
                        [0, 'desc']
                    ],
                    iDisplayLength: pageSize,
                    sDom: "",
                    oLanguage: {
                        "sZeroRecords": "没有关键词记录"
                    },
                    fnDrawCallback: function(oSettings) {
                        var selectType = currentSelectType();
                        if (oSettings.aiDisplay.length) {
                            //显示分页条
                            layoutPageBar(oSettings.aiDisplay.length, (oSettings._iDisplayStart / pageSize) + 1);

                            //绑定shift多选
                            oSettings.oInstance.find('.check_column').off('.shiftcheckbox').shiftcheckbox({
                                checkboxSelector: 'input',
                                ignoreClick: 'a',
                                onChange: function(checked) {
                                    if (checked) {
                                        chooseKeyword.call(this);
                                    } else {
                                        unchooseKeyword.call(this);
                                    }
                                }
                            });

                            oSettings.oInstance.find('.check_column input').off('change').on('change', function() {
                                if (this.checked) {
                                    chooseKeyword.call($(this));
                                } else {
                                    unchooseKeyword.call($(this));
                                }
                            });

                            //有数据显示底部操作区
                            $('#' + selectType).find('.bottom_operation').css('visibility', 'visible');
                        } else {
                            //没有数据隐藏底部操作区
                            $('#' + selectType).find('.bottom_operation').css('visibility', 'hidden');
                        }
                    }
                });
            });
        },

        //datatable过滤扩展
        customDatatableExt = function() {
            $.fn.dataTableExt.afnFiltering.push(
                function(oSettings, aData, iDataIndex) {
                    if (!filterList.length) {
                        return true;
                    }

                    //获取用slider过滤条件
                    var dataList = [Number(aData[2]), Number(aData[8].replace('%', '')), Number(aData[6]), Number(aData[5]), Number(aData[3]), aData[1].match(/<span.*>(.+?)<\/span>/i)[1], Number(aData[0])],
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
                    if (filterList[7] && filterList[7] != 'all' && filterList[7] != 'mobile') {
                        // oSettings.oInstance.fnUpdate
                        var temp = Number(aData[1].match(filterList[7] + '="(.*?)"')[1]);

                        //temp等于-1表示不是改包推荐，大于-1代表排名
                        if (temp == -1) {
                            return false;
                        }
                    }

                    //当是系统推荐和全部候选时默认使用匹配度排序
                    if (['sys', 'all'].indexOf(filterList[7]) != -1) {
                        oSettings.oInstance.fnGetNodes(iDataIndex).childNodes[0].childNodes[0].innerText = Number(aData[2]);
                    } else {
                        oSettings.oInstance.fnGetNodes(iDataIndex).childNodes[0].childNodes[0].innerText = temp;
                    }

                    return true;
                }
            );
        },

        //获取当前所有行
        getRows = function() {
            var oSettings = currentTableSettings(),
                nTrs,
                rows;

            rows = $.map(oSettings.aiDisplay, function(i) {
                return oSettings.aoData[i];
            });
            return rows;
        },

        currentTableSettings = function() {
            return currentDataTable().fnSettings();
        },

        //获取当前dataTable对象
        currentDataTable = function() {
            var selectType = currentSelectType();
            return $('#' + selectType + '_common_table').dataTable();
        },

        //选择关键词
        chooseKeyword = function() {
            var tpl = __inline('select_word.html'),
                obj,
                html,
                $that = this,
                inputId = this.attr('id');

            if ($('#cart_tr_' + inputId).length) {
                return false;
            }

            html = template.compile(tpl)({
                title: this.next().text(),
                price: this.next().data().price >= maxPriceLimit ? maxPriceLimit : this.next().data().price < 0.05 ? 0.05 : this.next().data().price,
                inputId: inputId,
                cpc: this.next().data().cpc
            });

            obj = $(html);

            // $(obj).find('.del').on('click', function(e, type) {
            //     $that[0].checked = false;
            //     $(this).parent().parent().remove();
            //     calcTotalNum();
            //     calcCheckedNum();

            //     //type为true时表示关联的元素也删除
            //     if (type == true) {
            //         setTimeout(function() {
            //             var instance = $that.parent().parent().parent().parent().dataTable();
            //             instance.fnDeleteRow(instance.fnGetPosition($that.parent().parent()[0]));
            //         }, 17);

            //         return false;
            //     }
            // });

            $('#scroll_box table tbody').append(obj);

            calcTotalNum();
            calcCheckedNum();
            bindChooseEvent();
        },

        //取消选中关键词
        unchooseKeyword = function() {
            var inputId;

            inputId = this.attr('id');

            $('#cart_tr_' + inputId).remove();

            calcTotalNum();
            calcCheckedNum();
        },

        //计算候选关键词个数
        calcTotalNum = function() {
            $('.total_num').text($('#scroll_box table>tbody>tr').length);
        },

        //计算选中关键词个数
        calcCheckedNum = function() {
            $('.checked_num').text($('#scroll_box table>tbody>tr td.check_column input:checked').length);

            if ($('#scroll_box table>tbody>tr td.check_column input:checked').length && ($('#scroll_box table>tbody>tr td.check_column input:checked').length == $('#scroll_box table>tbody>tr td.check_column input').length)) {
                $('#keyword_cart .choose_all_column input')[0].checked = true;
            } else {
                $('#keyword_cart .choose_all_column input')[0].checked = false;
            }
        },

        //绑定input事件
        bindChooseEvent = function() {

            $('#scroll_box table>tbody>tr td.check_column input').off('shiftcheckbox').shiftcheckbox();

            $('#scroll_box table>tbody>tr td.check_column input').off('change').on('change', function() {
                calcCheckedNum();
            });
        },

        //获取选词车中选中的row
        cartCheckRow = function() {
            var rowList = [];
            $('#keyword_cart table tbody>tr td.check_column input:checked').each(function() {
                rowList.push($(this).parents('tr'));
            });
            return rowList;
        },

        //修改选词车的出价
        editCartPrice = function(mode, rows) {

            var custome_price = Number($('#custome_price').val()),
                custome_price_multiple = Number($('#custome_price_multiple').val());

            for (var i in rows) {

                var input = rows[i].find('.price'),
                    newPrice;

                if (mode == 'sys') {
                    newPrice = Number(input.data().price).toFixed(2);
                } else if (mode == 'custom' && isValidInput(custome_price)) {
                    newPrice = custome_price.toFixed(2);
                } else if(mode == 'custom_multiple') {
                    newPrice = Number((input.data().cpc * custome_price_multiple).toFixed(2));
                }

                if (newPrice < 0.05) {
                    newPrice = 0.05;
                }

                if (newPrice > maxPriceLimit) {
                    newPrice = maxPriceLimit.toFixed(2);
                }

                newPrice&&input.val(newPrice);
            }
        },

        //修改选词车的匹配方式
        editCartMatchType = function(matchType, rows) {
            var matchDict = {
                1: '&#xe622;',
                2: '&#xe624;',
                4: '&#xe623;'
            };

            for (var i in rows) {
                var icon = rows[i].find('.match');

                icon.html(matchDict[matchType]).data('match', matchType);
            }

        },

        //复制关键词
        copyData = function() {
            var copyStr = ""

            $(currentTableSettings().aoData).each(function() {
                // if (this.nTr.childNodes[1].childNodes[0].checked) {
                copyStr += this.nTr.childNodes[1].childNodes[0].innerText + '\n'
                    // }
            });
            return copyStr
        },

        //adasd
        initFixedHeader = function() {
            $('.FixedHeader_Cloned').remove();
            if (currentTableSettings().aoData.length) {
                fixedHeader = new FixedHeader(currentDataTable());
            }
        },

        //显示选中的关键词
        layoutSelectWord = function(data) {
            var tpl = __inline('select_word.html'),
                html;

            html = template.compile(tpl)({
                data: data
            });

            $('#keyword_cart table tbody').html(html);
        };



    return {
        init: function() {
            fixDom();

            initDom();

            customDatatableExt();

            initTable();

            if (initSelectType === 'quick') {
                // getData();
                $('#select_keyword_nav>li>a[href=#quick]').trigger('shown.bs.tab');
            }

            if (initSelectType === 'combine') {
                calcCombineUnput();
            }
            select_feedback.init();
        }
    }
});
