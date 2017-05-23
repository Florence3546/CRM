/* ===========================================================
 * @version			0.0.1
 * @since			2014.04.28
 * @author			zhongJinFeng
 * @package			jQuery.js,dajax.js,base.js
 */

PT.namespace('hotZone');
PT.hotZone = function () {
    'use strict';
    var DEBUG = function () {
            if (window.location.href.indexOf('127.0.0.1') !== -1 || window.location.href.indexOf('localhost') !== -1) {
                return true;
            }
            return false;
        }(),

        start_time = function () {
            var dt = new Date();
            return dt.getTime();
        }(),

        interval = 1000, //两次点击的时间间隔（秒控）

        vali_target_list = ['a', 'i', 'button', 'span', 'td', 'th', 'input', 'select', 'img', 'li'],

        general_conf = [[document, ''], ['#select_column_show_btn', ''], ['#dashboard-report-range', '']],

        conf = {
            'bulk_optomize': [
                {
                    selector: '#refine_box',
                    selector2: '.dropdown_btn'
                },
                {
                    selector: '#smart_optimize_btn'
                },
                {
                    selector: '#batch_optimize_btn'
                },
                {
                    selector: '#refine_box',
                    selector2: 'label'
                },
                {
                    selector: '#refine_box',
                    selector2: '.refine_box_custom_btn'
                },
                {
                    selector: '#refine_box',
                    selector2: 'button'
                }
            ],
            'quick_add_keyword': [
                {
                    selector: '#btn_selector'
                },
                {
                    selector: '#btn_search'
                },
                {
                    selector: '#dont_filter_checked'
                }
            ],
            'precise_tao_keyword': [
                {
                    selector: '#btn_selector'
                },
                {
                    selector: '#btn_search'
                },
                {
                    selector: '#dont_filter_checked'
                }
            ],
            'auto_combine_words': [
                {
                    selector: '#btn_selector'
                },
                {
                    selector: '#btn_search'
                },
                {
                    selector: '#dont_filter_checked'
                }
            ],
            'manual_add_words': [
                {
                    selector: '#btn_selector'
                },
                {
                    selector: '#btn_search'
                },
                {
                    selector: '#dont_filter_checked'
                }
            ]
        },

        get_page = function (e) {
            return document.body.id.replace('pt_', '');
        },

        //自动化数据列表
        auto_data_dict = {
            'page': get_page
        },

        is_vali_tagname = function (e) {
            return $.inArray(e.target.tagName.toLowerCase(), vali_target_list) !== -1;
        },

        deep_analyze = function (dom) {
            var index, i = 0,
                parent = dom.parentNode;
            index = $(parent).children(dom.tagName).index(dom);
            if (typeof parent.id !== 'undefined' && parent.hasAttribute('id')) {
                return parent.id + '|' + dom.tagName + "(" + index + ")";
            }
            return deep_analyze(parent) + '|' + dom.tagName + "(" + index + ")";
        },

        get_datebase_selector = function (selector_str) {
            var id, selector, selector_list;
            selector_list = selector_str.split('|');
            id = selector_list[0];
            selector = selector_list.slice(1, selector_list.length).join('');
            return [id, selector];
        },

        analyze = function (dom) {
            var selector_str;
            if (dom.hasAttribute('id')) {
                return [dom.id, ''];
            }
            selector_str = deep_analyze(dom);
            return get_datebase_selector(selector_str);
        },

        get_selector = function (e) {
            if (is_vali_tagname(e)) {
                return analyze(e.target);
            }
            return [];
        },

        print_friendly_selector = function (selector) {
            var log;
            if (typeof window.console === 'undefined') {
                return false;
            }
            if (selector[1].length) {
                log = '$("#' + selector[0] + '").find("' + selector[1].replace(new RegExp("\\(", "g"), ':eq(').replace(new RegExp("\\)", "g"), ')>').slice(0, -1) + '\")'; //)").find("
            } else {
                log = '$("#' + selector[0] + '")';
            }
            console.log("==========================hotZone_debug==================================");
            console.log(selector);
            console.log(log);
        },

        get_all_data = function (e) {
            var d, data = {},
                selector = get_selector(e);

            if (selector.length) {
                if (DEBUG) {
                    print_friendly_selector(selector);
                }
            } else {
                return false;
            }

            for (d in auto_data_dict) {
                if (auto_data_dict[d] !== undefined) {
                    data[d] = auto_data_dict[d](e);
                }
            }
            data.s1 = selector[0];
            data.s2 = selector[1];
            return $.toJSON(data);
        },

        //判断事件来源是否是用户触发
        is_uer_hand = function (e) {
            if (typeof e.originalEvent === 'undefined') {
                return false;
            } else {
                return true;
            }
        },

        sendData = function (e) {
            var data, dt = new Date(),
                now_time = dt.getTime();
            if (now_time - start_time > interval && is_uer_hand(e)) {
                data = get_all_data(e);
                if (data) {
                    setTimeout(function () {
                        PT.sendDajax({
                            'function': 'web_hot_zone',
                            'data': data,
                            'auto_hide':0
                        });
                    }, 0);
                }
                start_time = now_time;
            }
        },

        init_base = function () {
            var i = 0;
            for (i; i < general_conf.length; i = i + 1) {
                $(general_conf[i][0]).on('click.PT.hotZone', general_conf[i][1], function (e) {
	                try{
	                    sendData(e);
	                    }catch(e){

	                    }
                });
            }
        },

        init_specil = function () {
            var obj, i = 0,
                current_page_key = window.location.href.split('\/')[4];
            if (typeof conf[current_page_key] !== 'undefined') {
                for (i; i < conf[current_page_key].length; i = i + 1) {
                    obj = conf[current_page_key][i];
                    if (typeof obj.selector2 === 'undefined') {
                        obj.selector2 = '';
                    }
                    $(obj.selector).on('click.PT.hotZone', obj.selector2, function (e) {
		                try{
		                    sendData(e);
		                    }catch(e){

		                    }
                    });
                }
            }
        },

        //在需要监控的节点上加上点击事件
        init = function () {
            init_base();
            init_specil();

        };

    return {
        'init': function () {
            init();
        },
        'record': function (e) {
            sendData(e);
        }
    };

}();
PT.hotZone.init();
