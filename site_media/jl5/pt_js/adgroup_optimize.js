PT.namespace('Adgroup_optimize');
PT.Adgroup_optimize = function() {

    var adgroup_id = $('#adgroup_id').val();
    var campaign_id = $('#campaign_id').val();
    var item_id = $('#item_id').val();
    var default_price = $('#default_price_hide').val();

    var get_last_day = function() {
        return $('#keyword_select_days .dropdown-value').text().match(/\d+/)[0];
    }

    var init_dom = function() {

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
                $.fancybox.close();
            } else {
                PT.alert("亲，未选中或输入任何词！");
            }
        });

        $('#keyword_select_days').on('change',function(e,v){
            PT.show_loading('正在获取数据');
            PT.instance_table.get_keyword_data();
        });

        $('.tips').tooltip();

        $('.edit_mobdiscount').on('click', function(){
            if (!$('#modal_adg_mobdiscount').length){
                $('body').append(pt_tpm["modal_adg_mobdiscount.tpm.html"]);
            }
            var adgroup_id = parseInt($('#adg_mobdiscount').attr('adgroup_id'));
            var discount = parseInt($('#adg_mobdiscount').text());
            $('#adg_mobile_discount').val(discount);
            $('#id_set_adg_mobdiscount').val(adgroup_id);
            $('#modal_adg_mobdiscount').modal();
        });

        $('body').on('click.set_adg_mobdiscount','#save_mobdiscount', function(){
            var adgroup_id = parseInt($('#id_set_adg_mobdiscount').val());
            var discount = parseInt($('#adg_mobile_discount').val());
            var org_discount = parseInt($('#adg_mobdiscount').text());
            if (org_discount == discount){
                $('#modal_adg_mobdiscount').modal('hide');
                return true;
            }else if(isNaN(discount) || discount>400 || discount <1){
                PT.alert("移动折扣要介于1%~400%之间哦亲！");
                return false;
            }else{
                PT.sendDajax({'function':'web_set_adg_mobdiscount', 'campaign_id':campaign_id, 'adgroup_id': adgroup_id, 'discount': discount, 'namespace': 'Adgroup_optimize'});
            }
        });

        $('body').on('click.use_camp_mobdiscount', "#use_camp_mobdiscount", function(){
            var adgroup_id = parseInt($('#id_set_adg_mobdiscount').val());
            var campaign_id = parseInt($('#campaign_id').val());
            PT.sendDajax({'function': 'web_delete_adg_mobdiscount', 'adgroup_id': adgroup_id, 'campaign_id': campaign_id, 'namespace': 'Adgroup_optimize'});
        });

    }



    var init_table = function() {
        //PT.show_loading('正在获取关键词数据');
        PT.instance_table = new PT.Adgroup_optimize.table_obj('common_table', 'template_common_table_tr');
    }

    return {
        //main function to initiate the module
        init: function() {
            init_dom();
            init_table();
        },
        table_callback: function(data) {
            PT.instance_table.call_back(data);
        },
        get_last_day: function() {
            return get_last_day;
        },
        adgroup_id: adgroup_id,
        item_id: item_id,
        campaign_id: campaign_id,
        default_price: default_price,
        set_adg_mobdiscount_callback: function (adgroup_id, discount){
            $('#modal_adg_mobdiscount').modal('hide');
            $('#adg_mobdiscount').text(discount);
            PT.light_msg('', "修改移动折扣成功！", 1000);
        }
    };

}();

//继承PT.Table.BaseTableObj的属性
PT.Adgroup_optimize.table_obj = function(table_id, temp_id) {
    this.get_smart_optimize_argv = function() {
        var json = {}
        json['stgy'] = $('#smart_optimize_cfg input[name="strategy"]:checked').val();
        json['rate'] = $('#id_rate').val();
        json['executor'] = $('#stgy_executor').val();
        json['cfg'] = $('#stgy_cfg').val();
        return $.toJSON(json);
    }

    //重写后台回调函数
    this.call_back = function(json) {

        var that = this;
        if (json.keyword.length) {
            this.table_obj.removeClass('hide');
            this.layout_keyword(json);
            this.sort_table(json.custom_column);
            this.layout_bulk_search(eval(json.bulk_search_list));
            this.weird_switch&&this.start_weird_class();
        } else {
            $('#loading_keyword').hide();
            $('#no_keyword').show();
        }

        $('#loading_keyword').hide();
        PT.hide_loading();
        $('#batch_optimize_count').text(0);
    }

    PT.Table.BaseTableObj.call(this, table_id, temp_id);
}

//继承PT.Table.BaseTableObj的属性方法
PT.Adgroup_optimize.table_obj.prototype = PT.Table.BaseTableObj.prototype;



