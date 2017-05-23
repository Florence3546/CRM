PT.namespace('Mnt_optimize');
PT.Mnt_optimize = function() {

    var adgroup_id = $('#adgroup_id').val();
    var campaign_id = $('#campaign_id').val();
    var item_id = $('#item_id').val();
    var default_price = $('#default_price_hide').val();

    var get_last_day = function() {
        return $('#dashboard-report-range').find('input[name="last_day"]').val();
    }

    var init_dom = function() {
        $('#keyword_select_days').on('change', function(e, v) {
            PT.show_loading('正在获取数据');
            PT.instance_table.get_keyword_data();
        });

        $(document).off('click.PT.submit_bword', '#id_submit_bword').on('click.PT.submit_bword', '#id_submit_bword', function() {
            var word_list = new Array();
            var manual_blackword = $.trim($('#manual_blackword').val());
            $('#id_ban_word_part input:checked').each(function() {
                word_list.push($.trim(this.value));
            });
            if (manual_blackword && $.inArray(manual_blackword, word_list) == -1) {
                word_list.push(manual_blackword);
            }
            if (word_list.length > 0) {
                PT.sendDajax({
                    'function': 'web_submit_bwords',
                    'campaign_id':campaign_id,
                    'adgroup_id':adgroup_id,
                    'item_id': $('#item_id').val(),
                    'blackwords': word_list.join(),
                    'save_or_update': 1,
                    'common_table_flag': $('#common_table').length
                });
                $(this).parents('.modal').modal('hide');
            } else {
                PT.alert("亲，未选中或输入任何词！");
            }
        });
    }

    var init_table = function() {
        PT.instance_table = new PT.Mnt_optimize.table_obj('common_table', 'template_common_table_tr');
    }

    return {
        init: function() {
            init_dom();
            init_table();
        },
        adgroup_id: adgroup_id,
        item_id: item_id,
        campaign_id: campaign_id,
        default_price: default_price
    };

}();

//继承PT.Table.BaseTableObj的属性
PT.Mnt_optimize.table_obj = function(table_id, temp_id) {

    this.get_smart_optimize_argv = function() {
        var json = {}
        json['stgy'] = 'routine';
        json['rate'] = '10';
        json['executor'] = '';
        json['cfg'] = '';
        return $.toJSON(json);
    }

    //重写填充函数
    PT.Table.BaseTableObj.prototype.layout_keyword = function(json) {
        var tr_str = '',
            kw_count = json.keyword.length,
            d;
        tr_str = template.compile(pt_tpm['mnt_keyword_nosearch_tabler.tpm.html'])(json.nosraech);

        for (var i = 0; i < kw_count; i++) {
            tr_str += template.compile(pt_tpm['mnt_keyword_tabler_tr.tpm.html'])(json.keyword[i]);
        }

        if (this.data_table){
            this.data_table.fnDestroy();
        }

        $('tbody', this.table_obj).html(tr_str);
    }

    //重写后台回调函数
    this.call_back = function(json) {

        var that = this;

        json.custom_column.push('new_price', 'forecast', 'rank')
        if (json.keyword.length) {
            this.layout_keyword(json);
            this.sort_table(json.custom_column);
            //this.change_price_status_4data(json);//只改变价格和删词状态
            //this.layout_bulk_search(eval(json.bulk_search_list));
            //this.calc_action_count();
            //this.update_all_style();
            this.start_weird_class();
        } else {
            $('#loading_keyword').hide();
            $('#no_keyword').show();
        }

        $('#batch_optimize_count').text(0);
        PT.hide_loading();
        $('#loading_keyword').hide();
    }

    PT.Table.BaseTableObj.call(this, table_id, temp_id);
}
//继承PT.Table.BaseTableObj的属性方法
PT.Mnt_optimize.table_obj.prototype = PT.Table.BaseTableObj.prototype;
