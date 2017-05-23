PT.namespace('MntForecast');
PT.MntForecast = function() {

    var adgroup_id = $('#adgroup_id').val();
    var campaign_id = $('#campaign_id').val();
    var item_id = $('#item_id').val();
    var default_price = $('#default_price_hide').val();

    var init_dom = function() {
        $('.tips').tooltip();
    };

    var init_table = function() {
        PT.instance_table = new PT.MntForecast.table_obj('common_table', 'template_common_table_tr');
    };

    return {
        init: function() {
            init_dom();
            init_table();
        },
        table_callback: function(data) {
            PT.instance_table.call_back(data);
        },
        adgroup_id: adgroup_id,
        item_id: item_id,
        campaign_id: campaign_id,
        default_price: default_price
    };

}();

//继承PT.Table.BaseTableObj的属性
PT.MntForecast.table_obj = function(table_id, temp_id) {

    //重写后台回调函数
    this.call_back = function(json) {

        console.log(json.cfg_dict);
        console.log(json.instrcn_list);
        var that = this;
            // custom_column = ['forecast','rank','impressions', 'click', 'ctr', 'cost', 'cpc', 'favcount', 'paycount', 'pay', 'conv', 'roi', 'g_click', 'g_ctr', 'g_cpc', 'g_competition'];
        custom_column = ['forecast','rank','cpm','avgpos'];
        if (json.keyword.length) {
            this.table_obj.removeClass('hide');
            this.layout_keyword(json);
            this.sort_table(custom_column);
            this.change_price_status_4data(json);//只改变价格和删词状态
            // this.layout_bulk_search(eval(json.bulk_search_list));
            this.calc_action_count();
            this.update_all_style();
            this.weird_switch&&this.start_weird_class();
        } else {
            $('#loading_keyword').hide();
            $('#no_keyword').show();
        }

        $('#id_rate .dropdown-toggle').removeClass('red-border');
        $('#batch_optimize_count').text(0);
        PT.hide_loading();
        $('#loading_keyword').hide();
    };

    this.get_keyword_data = function() {
        PT.sendDajax({
            'function': 'mnt_get_forecast_data',
            'adgroup_id': PT.MntForecast.adgroup_id
        });
    };

    this.layout_keyword = function(json) {
        var tr_str = '',
            kw_count = json.keyword.length,
            d;

        // tr_str = template.compile(pt_tpm['keyword_nosearch_tabler.tpm.html'])(json.nosraech);

        for (var i = 0; i < kw_count; i++) {
            tr_str += template.compile(pt_tpm['forecast_table_tr.tpm.html'])(json.keyword[i]);
            // tr_str += template.compile(pt_tpm['keyword_common_table_tr.tpm.html'])(json.keyword[i]);
        }

        if (this.data_table){
            this.data_table.fnDestroy();
        }

        $('tbody', this.table_obj).html(tr_str);
    };

    this.set_kw_count=function(){
        var kw_count=this.data_table.fnSettings()['aiDisplay'].length;
        $('#keyword_count').text(kw_count);
    };

    this.start_weird_class=function(){
        return false;
    };

    PT.Table.BaseTableObj.call(this, table_id, temp_id);
};
//继承PT.Table.BaseTableObj的属性方法
PT.MntForecast.table_obj.prototype = PT.Table.BaseTableObj.prototype;
