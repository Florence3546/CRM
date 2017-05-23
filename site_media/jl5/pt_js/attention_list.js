PT.namespace('Attention');
PT.Attention = function () {

    var adgroup_id = $('#adgroup_id').val();
    var campaign_id = $('#campaign_id').val();
    var item_id = $('#item_id').val();
    var default_price = $('#default_price_hide').val();

    var get_last_day = function() {
        return $('#keyword_select_days .dropdown-value').text().match(/\d+/)[0];
    }

    var show_big_pic = function (obj) {
        obj.table_obj.find('.item_picture').popover({
            'trigger':'hover',
            'content':get_picture_html,
            'html':true,
            'placement':'right'
        });
    }

    var get_picture_html = function () {
        eval("var data="+$(this).attr('data'));
        return template.render('template_item_picture',data);
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

        $('.tips').tooltip()
    }

    var init_table = function() {
        PT.instance_table = new PT.Attention.table_obj('common_table', 'template_common_table_tr');
        PT.instance_table.init_ajax_event_list.push(show_big_pic);
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
        default_price: default_price
    };

}();

//继承PT.Table.BaseTableObj的属性
PT.Attention.table_obj = function(table_id, temp_id) {
	this.weird_switch = 0;
    //重写关键词数据获取函数
    this.get_keyword_data = function () {
	    PT.sendDajax({
		    'function':'web_get_attention_list',
		    'last_day':PT.Attention.get_last_day(),
		    'auto_hide': 0
		});
    }
    //重写填充表格数据
	this.layout_keyword = function (json) {
//	    var tr_str = this.table_obj.find('tr.noSearch').prop('outerHTML'),
	    var tr_str = $('#template_noSearch_tr').html(),
	        kw_count = json.keyword.length;

	    for (var i = 0; i < kw_count; i++) {
	        tr_str += template.compile(pt_tpm['keyword_attention_table_tr.tpm.html'])(json.keyword[i]);
	    }

	    if (this.data_table){
	        this.data_table.fnDestroy();
	    }

	    $('tbody', this.table_obj).html(tr_str);
	}

	// //重写dataTable 排序参数 TODO: 按照宝贝排序
	this.COLUM_DICT = {'keyword':2,'new_price':3,'rt_forecast': 4, 'forecast': 5,
                       'max_price': 6, 'rt_rank': 7, 'rank': 8, 'new_qscore':9, 'qscore':10,
                       'create_days': 11, 'impressions': 12, 'click': 13, 'ctr': 14, 'cost': 15,
                       'ppc': 16, 'cpm': 17, 'avgpos': 18, 'favcount': 19, 'favctr': 20,
                       'favpay': 21, 'paycount': 22, 'pay': 23, 'conv': 24, 'roi': 25,
                       'g_pv': 26, 'g_click': 27, 'g_ctr': 28, 'g_cpc': 29, 'g_competition': 30
                        };
	this.custom_aoColumns = [
            {"bSortable": true,"sSortDataType": "custom-text", "sType": "custom","sClass": "no_back_img tc"},
            {"bSortable": false},
            {"bSortable": false},
            {"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
            {"bSortable": false, "sClass": 'tc', "sType": "custom", "sSortDataType": "custom-text"},
            {"bSortable": false, "sClass": 'tc'},
            {"bSortable": true, "sClass": 'tc', "sType": "custom", "sSortDataType": "custom-text"},
            {"bSortable": false, "sClass": 'tc', "sType": "custom", "sSortDataType": "custom-text"},
            {"bSortable": true},
            {"bSortable": false, "sType": "custom","sSortDataType": "custom-text"},
            {"bSortable": true, "sType": "custom", "sSortDataType": "custom-text"},
            {"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
            {"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
            {"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
            {"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
            {"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
            {"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
            {"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
            {"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
            {"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
            {"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
            {"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
            {"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
            {"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
            {"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
            {"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
            {"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
            {"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
            {"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
            {"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
            {"bSortable": true, "sType": "custom","sSortDataType": "custom-text"}
        ];

    //自定义csv数据格式
	this.creat_scv_data = function () {
        var data_str1 = '关键词\t当前出价\t',
            data_str2 = '养词天数\t展现量\t点击量\t点击率\t总花费\t平均点击花费\t千次点击花费\t昨日平均排名\t收藏量\t收藏率\t收藏成本\t成交量\t成交额\t转化率\t投资回报\t全网展现指数\t全网点击指数\t全网点击率\t全网市场均价\t全网竞争度\n';
            data_str = '';
        var start_j = 10;
        if (PT.Table.TB_HIDE_COLUMN.indexOf('qscore') >= 0) {
            data_str = data_str1 + 'PC质量得分\t移动质量得分\t' + data_str2;
            start_j = 9;
        }else {
            data_str = data_str1 + '质量得分\t' + data_str2;
        }

	    for (var i=1, i_end=this.data_table.fnSettings()['aiDisplay'].length;i<i_end;i++){
	        var nRow = this.data_table.fnGetNodes(i);
	        var keyword = $(nRow).find('.word').text();
	        var td_list = this.data_table.fnGetData(i);

	        data_str += keyword + '\t';
	        data_str += $(td_list[6]).text() + '元\t';
            for (var j=start_j,j_end=td_list.length;j<j_end;j++){
                if (j==9 && i>0) {
                    var qscore_list = $(td_list[j]).map(function(){return $(this).hasClass('new_qscore')? $.trim($(this).text()):null;});
                    data_str += qscore_list[0]+'\t'+qscore_list[1]+'\t';
                    j++;
                    continue;
                } else if(isNaN(Number(td_list[j]))&&td_list[j].indexOf('custom')!=-1){
                    if (j==25) {
                        data_str += $.trim($(td_list[j]).eq(4).text()) + '\t';
                    } else {
                        data_str+=$.trim($(td_list[j]).eq(0).text())+'\t';
                    }
                    continue;
                }
                data_str+=td_list[j]+'\t';
            }
	          data_str += '\n';
	    }
	    return data_str;
	}

    //重写后台回调函数
    this.call_back = function (json) {
        var that = this;
        if (json.keyword.length) {
            this.table_obj.removeClass('hide');
            this.layout_keyword(json);
            this.sort_table(json.custom_column);
        } else {
            $('#loading_keyword').hide();
            $('#no_keyword').show();
            $('#keyword_count').text(0);
        }

        $('#loading_keyword').hide();
        PT.hide_loading();
        $('#batch_optimize_count').text(0);
    }

    PT.Table.BaseTableObj.call(this, table_id, temp_id);
}

PT.Attention.table_obj.prototype = PT.Table.BaseTableObj.prototype;
