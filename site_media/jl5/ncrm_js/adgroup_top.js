PT.namespace('AdgroupTop');
PT.AdgroupTop = function() {
    var adg_top_table = null;

    var init_table=function (){
        adg_top_table = $('#adg_top_table').dataTable({
            "bRetrieve": true, //允许重新初始化表格
            "bPaginate": false,
            "bFilter": false,
            "bInfo": true,
            "bSort": true,
            "aaSorting": [[9,'desc']],
            "iDisplayLength": 100,
            "bAutoWidth": true,
            'sDom': "<t<'mt10'<i><'pr10 tr'p>>",
            "aoColumns": [{"bSortable": false},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": false},
                          ],
            "oLanguage": {"sEmptyTable":"没有数据",
                          "sProcessing" : "正在获取数据，请稍候...",
                          "sInfo":"显示第_START_条到第_END_条记录, 共_TOTAL_条记录",
                          "sZeroRecords" : "没有您要搜索的内容",
                          "sInfoEmpty": "显示0条记录",
                          "sInfoFiltered" : "(全部记录数 _MAX_ 条)",
                          "oPaginate": {"sFirst" : "第一页",
                                        "sPrevious": "上一页",
                                        "sNext": "下一页",
                                        "sLast" : "最后一页"
                                        }
                         }
        });
        new FixedHeader(adg_top_table);

    };

    var init_dom = function() {

        //当鼠标经过该元素时，加上hover这个class名称，修复ie中css的hover动作
        $(document).on('mouseover.PT.e','*[fix-ie="hover"]',function(){
            $(this).addClass('hover');
            $(this).mouseout(function(){
                $(this).removeClass('hover');
            });
        });

        $(document).on('blur', '.cat_name_input', function() {
            var link_id = $(this).attr('link');
            if ($(link_id).val() === '') {
                $(this).val("");
            }
        });

        $(document).on('keydown', '.cat_name_input', function(e) {
            var e = window.event || e,
                link_id = $(this).attr('link');
            if (e.keyCode == 8 || e.keyCode == 46) {
                $(this).val('');
                $(link_id).val('');
            }
        });

        $('#submit_form').click(function(){
            if ($('.cat_name_input').val() === '') {
                PT.light_msg('', '请先输入类目');
                return false;
            }
            $('#adg_top_form').submit();
            PT.show_loading('正在查询');
        });

        $('.check_num').change(function(){
            current_count = Number($(this).val());
            if (isNaN(current_count) || current_count<0) {
                $(this).val('');
                PT.light_msg('', '请输入正数');
            }
        });

        $('.tooltips').tooltip({'html': true});

        $('#item_cat_path').click(function () {
            var item_cat_path_id = $('#adg_top_form input[name=item_cat_path_id]').val(),
                item_cat_path_name = $('#adg_top_form input[name=item_cat_path_name]').val();
            if (item_cat_path_id && item_cat_path_name) {
                $('#cat_path_id').val(item_cat_path_id);
                $('#adg_top_form input[name=cat_path_name]').val(item_cat_path_name);
            }
        });

        $('#item_prdtword_list').on('click', 'a.item_prdtword', function () {
            $('#adg_top_form input[name=product_word]').val($(this).text());
        });

        $('#a_search_item').click(function () {
            PT.show_loading('正在搜索');
            PT.sendDajax({
                'function': 'ncrm_search_item_byurl',
                'item_url': $('#item_url').val(),
                'callback': 'PT.AdgroupTop.search_item_byurl_callback'
            });
        });

    };

    var init_cat_name_select = function(cat_obj_list){
        var i = 0,
            show_items = [],
            i_end = cat_obj_list.length;
        for (i; i < i_end; i++) {
            show_items.push(cat_obj_list[i].cat_path_name);
        }

        $('.cat_name_input').typeahead({
            source: show_items,
            items: 20,
            // matcher: function(item) {
            //     return true;
            // },
            updater: function(item) {
                var link_id, name_cn;
                for (var j = 0; j < i_end; j++) {
                    if (cat_obj_list[j].cat_path_name == item) {
                        current_value = cat_obj_list[j].cat_id;
                    }
                }
                link_id = this.$element.attr('link');
                $(link_id).val(current_value);
                return item;
            }
        });

        $('.cat_name_input').attr('placeholder', '');
    };

    var get_cat_name_list = function(){
        $('.cat_name_input').attr('placeholder', '正在获取类目数据。。。');
        var cat_name_list = window.localStorage.getItem('level3_cat_list');
        // PT.sendDajax({
        //     'function': 'ncrm_get_cat_name_list',
        //     'namespace': 'AdgroupTop.cat_name_select_callBack'
        // });
        if (! cat_name_list){
            PT.sendDajax({
                'function': 'ncrm_get_cat_name_list',
                'namespace': 'AdgroupTop.cat_name_select_callBack'
            });
        }else{
            init_cat_name_select(JSON.parse(cat_name_list));
        }
    };

    return {
        init: function() {
            init_table();
            get_cat_name_list();
            init_dom();
        },
        cat_name_select_callBack: function(cat_obj_list) {
            init_cat_name_select(cat_obj_list);
            window.localStorage.setItem('level3_cat_list', JSON.stringify(cat_obj_list));
        },
        search_item_byurl_callback: function (error, item_data) {
            if (error) {
                PT.alert(error);
            } else {
                $('#adg_top_form input[name=item_cat_path_id]').val(item_data.cat_id);
                $('#adg_top_form input[name=item_cat_path_name]').val(item_data.cat_path);
                $('#item_cat_path').html(item_data.cat_path).click();
                $('#adg_top_form input[name=item_prdtwords]').val(item_data.prdtword_list.join(','));
                $('#adg_top_form a.item_prdtword').remove();
                $.each(item_data.prdtword_list, function (i, prdtword) {
                    $('#item_prdtword_list').append('<a href="javascript:;" class="item_prdtword mr10">'+prdtword+'</a>');
                });
                $('#item_prdtword_list a.item_prdtword:eq(0)').click();
            }
        }
    };
}();
