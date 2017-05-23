/**
 * Created by Administrator on 2015/11/17.
 */
define(['../common/common','dataTable','widget/pageBar/pageBar','template', 'json'],function(common,dataTable,pageBar,template,_){

    var page_size = 20;
    var page_no = 1;
    var page_count = 1;
    var data_table,data_table_header;
    var detail_table,detail_table_header;
    var sort = 'desc';
    var cur_index=-1;
    var DUPLICATE_CHECK_LEAVE_LOCK=3; //锁定删词级别小于设定的数值的词
    var show_header = true;
    var del_condition = "level"

    /**
     * 重复词删除条件
     * @type {{del_level: number, del_day: number, del_statistics_type: string, del_offline: number}}
     */
    var dupl_condition = {
        del_level:3,
        del_day:7,
        del_statistics_type:'impressions',
        del_offline:0,
        del_longtail:0
    };

    /**
     * 低分词删除条件
     * @type {{del_level: number, del_day: number, del_statistics_type: string, del_offline: number}}
     */
    var qscore_condition = {
        del_qscore:3,
        del_day:7,
        del_statistics_type:'impressions',
        del_offline:0,
        del_longtail:0
    };

    /**
     * 页面初始化
     */
    var init = function(){
        getPageData();

        /**
         * 显示详细重复词详细信息
         */
        $('#duplicate_table>tbody').on('click','.click_show',function(){
            var tr_obj = $(this).closest('tr');
            var keyword = tr_obj.find('.keyword').html();
            $('.cur_kw_title').html(keyword);

            var index = tr_obj.attr('index');
            //如通过当前显示的详情为该关键词的详情，则无须做任何处理
            if(cur_index==index){
                return false;
            }
            cur_index = index;
            $('#duplicate_table>tbody>tr').removeClass('cur_dupl_detail');
            tr_obj.addClass('cur_dupl_detail');

            //如果当前关键词的详细信息已显示过么，则无需再请求后台，直接从data中取
            if (tr_obj.data('has_load')) {
                var html = tr_obj.data('detail');
                initDetailTable(html);
            }else{
                common.loading.show('数据加载中，请稍候...');
                common.sendAjax.ajax('dupl_kw_detail', {'keyword':keyword}, function(data){
                    var tpl, html;
                    tpl = __inline('duplicate_detail_list.html');
                    html = template.compile(tpl)({datas:data.result});
                    tr_obj.data('detail',html);
                    tr_obj.data('has_load',1);//当加载完之后解锁.
                    initDetailTable(html);
                    common.loading.hide();
                });
            }
        });
        /*$('#duplicate_table>tbody').on('click','.click_show',function() {
            var tr_obj = $(this).closest('tr');

            //防止快速多次点击
            if(tr_obj.data('is_lock')){
                return false;
            }
            tr_obj.find('.single_submit_btn').toggleClass('hide')
            var index = tr_obj.attr('index');
            //如果已经显示，则需关闭,同时销毁dataTable
            if (tr_obj.data('is_show')) {
                tr_obj.data('is_show',0);
                $('#'+index+'_detail').dataTable().fnDestroy();
                $('.'+index+'_kw_detail').remove();
            }else{
                tr_obj.data('is_lock',1);//加载时上锁，防止重复点击
                tr_obj.data('is_show', 1);
                //如果已获取数据并绑定到data中，则直接从data中取
                if(tr_obj.data('kw_detail')){
                    tr_obj.after(tr_obj.data('kw_detail'));
                    initDetailTable($('#'+index+'_detail'));
                    tr_obj.data('is_lock',0);//当加载完之后解锁
                }else{
                    var tpl, html;
                    tpl = __inline('duplicate_detail.html');
                    html = template.compile(tpl)({index:index});
                    tr_obj.after(html);
                    var keyword = tr_obj.find('.keyword').html();
                    common.sendAjax.ajax('dupl_kw_detail', {'keyword':keyword}, function(data){
                        tpl = __inline('duplicate_detail_list.html');
                        html = template.compile(tpl)({datas:data.result});
                        $('#'+index+'_detail tbody').html(html);
                        initDetailTable($('#'+index+'_detail'));
                        tr_obj.data('kw_detail',$('.'+index+'_kw_detail'));
                        tr_obj.data('is_lock',0);//当加载完之后解锁
                    });
                }
            }
        });*/

        /**
         * 排序(多页后端排序)
         */
        /*$('#duplicate_table thead .sort_field').unbind('click').click(function(){
            if (page_count>1){
                if($(this).attr('class').indexOf('desc')>-1){
                    sort = 'asc'
                }else{
                    sort = 'desc'
                }
                getPageData();
            }
        });*/

        /**
         * 关键词checkbox选中事件
         */
        $(document).on('change','table .choose_column :checkbox',function(){
            var status = $(this).prop('checked');
            var selectCount = 0;
            if($(this).hasClass('select-all')){
                if(status){
                    $('#duplicate_table .choose_column :checkbox').prop('checked',true);
                }else{
                    $('#duplicate_table .choose_column :checkbox').prop('checked',false);
                }
                selectCount = $('#duplicate_table .child-select:checked').length
            }else{
                selectCount = $('#duplicate_table .child-select:checked').length;
                if($('#duplicate_table .child-select').length==selectCount){
                    $('.choose_column .select-all').prop('checked',true);
                }else{
                    $('.choose_column .select-all').prop('checked',false);
                }
            }

            $('.hand_del_count').html(selectCount);
        });

        /**
         * 重复词详情checkbox选中事件
         */
        $(document).on('change','table .choose_sub_column :checkbox',function(){
            var childTable = $('#dupl_detail_table');
            var status = $(this).prop('checked');
            if($(this).hasClass('select-all-sub')){
                if(status){
                    childTable.find('.choose_sub_column :checkbox').not(':disabled').prop('checked',true);
                }else{
                    childTable.find('.choose_sub_column :checkbox').prop('checked',false);
                }
            }else{
                var selectCount = childTable.find('.child-select-sub:checked').length;
                if( childTable.find('.child-select-sub').not(':disabled').length==selectCount){
                    $('.select-all-sub').prop('checked',true);
                }else{
                    $('.select-all-sub').prop('checked',false);
                }
            }
        });

        /**
         * 锁定/解锁事件
         */
        $('#dupl_detail_table').on('click','.lock_kw',function(){
            var check_sub = $(this).closest('tr').find('.child-select-sub');
            if(check_sub.prop('disabled')){
                $(this).html('&#xe660;');
                check_sub.prop('disabled',false);
                check_sub.prop('checked',true);
            }else{
                $(this).html('&#xe620;');
                check_sub.prop('disabled',true);
                check_sub.prop('checked',false);
            }
            check_sub.trigger('change');
        });

        /**
         * 一键删除垃圾词
         */
        $('#del_garbage').click(function(){
            if($('.garbage_count').html()=='0'){
                common.alert.show('您的店铺暂无垃圾词，无需删除！');
                return false;
            }
            common.confirm.show({body:'您确定要删除店铺中的垃圾词吗？',okHidden:function(){
                del_condition = 'smart';
                common.loading.show('正在删除垃圾词，请稍候...');
                common.sendAjax.ajax('delete_dupl_word',{'del_type':'smart'},delCallBack);
            }});
        });

        /**
         * 按条件批量删除低分词
         */
        $('#del_by_score').click(function(){
            if($('.lowscore_count').html()=='0'){
                common.alert.show('您的店铺暂无低分词，无需删除！');
                return false;
            }
            common.confirm.show({body:'您确定按条件批量删除店铺中的低分词吗？',okHidden:function(){
                del_condition = 'score';
                common.loading.show('正在删除低分词，请稍候...');
                common.sendAjax.ajax('delete_dupl_word',{'condition':$.toJSON(qscore_condition),'del_type': 'advanced','word_list':[]},delCallBack);
            }});
        });

        /**
         * 按条件批量删除重复词
         */
        $('#del_by_condition').click(function(){
            if($('.duplicate_count').html()=='0'){
                common.alert.show('您的店铺暂无重复词，无需删除！');
                return false;
            }
            common.confirm.show({body:'您确定按条件批量删除店铺中的重复词吗？',okHidden:function(){
                del_condition = 'level';
                common.loading.show('正在删除重复词，请稍候...');
                common.sendAjax.ajax('delete_dupl_word',{'condition':$.toJSON(dupl_condition),'del_type': 'advanced','word_list':[]},delCallBack);
            }});
        });

        /**
         * 手动删除选中的关键词
         */
        $('#del_by_hand').click(function(){
            var kw_arr=getKwArr();
            var check_total = parseInt($('.hand_del_count').html());
            if(check_total>0){
                common.confirm.show({body:'<strong>说明：</strong>针对选中的关键词，删除重复次数大于3，过去7天展现量为0，且添加时间超过7天的重复词。您确定要删除吗？',okHidden:function(){
                    del_condition = 'level';
                    common.loading.show('正在删除重复词，请稍候...');
                    var condition = {
                        del_level:3,
                        del_day:7,
                        del_offline:1,
                        del_longtail:1,
                        del_statistics_type:'impressions'
                    };
                    common.sendAjax.ajax('delete_dupl_word',{'condition':$.toJSON(condition),'del_type': 'advanced','word_list':kw_arr},delCallBack);
                }});
            }else{
                common.alert.show('请选中下方要删除的关键词！');
            }
        });

        /**
         * 删除操作的回调函数
         */
        var delCallBack = function(data){
            common.loading.hide();
            if(data.del_count===0){
				if (data.failed_count>0) {
                    common.alert.show('亲，淘宝接口错误，删词失败，请稍后重试');
				} else{
                    if(del_condition=='score'){
                        common.alert.show('亲，您的店铺中不存在符合条件的低分词');
                    }else if(del_condition =='level'){
                        common.alert.show('亲，您的店铺中不存在符合条件的重复词');
                    }else{
                        common.alert.show('亲，您的店铺中不存在符合条件的垃圾词');
                    }
				}
			} else if(data.del_count>=0) {
				var msg = '删除成功'+data.del_count+'个';
				if (data.failed_count>0) {
					msg += '，删除失败'+data.failed_count+'个';
				}
				common.alert.show({
                    body:msg,
                    hidden:function(){
                        page_no = 1;
                        getPageData();
                    }
                });
			}
        };

        /**
         * 切换轮播
         */
        var is_to_carousel = false;
        $('.to_carousel').click(function(){
            //如果正在切换中，则禁止点击
            if(is_to_carousel){
                return false;
            }

            $('.to_carousel').removeClass('btn-primary');
            $(this).addClass('btn-primary');
            var item_index = parseInt($(this).attr('item'));
            switch (item_index){
                case 3:
                    show_header = true;
                    break;
                default :
                    show_header = false;
                    $('.fixedHeader').hide();
                    break;
            }
            $("#dupl_del_carousel").carousel(item_index);
        });
        $('#dupl_del_carousel').on('slide.bs.carousel', function () {
            is_to_carousel = true;
        });
        $('#dupl_del_carousel').on('slid.bs.carousel', function () {
            is_to_carousel = false;//切换完成之后，将切换状态变为false
            if(show_header){
                if(!data_table_header){
                    data_table_header = new FixedHeader(data_table);
                }else{
                    data_table_header.fnUpdate();
                }
                if(!detail_table_header){
                    detail_table_header = new FixedHeader(detail_table);
                }else{
                    detail_table_header.fnUpdate();
                }
                $('.fixedHeader').show();
            }
        })

        $('#condition_detail').on('change','.select_warp',function(e,value){
            dupl_condition[$(this).attr('name')] = value;
            $('#del_dupl_day').html(dupl_condition.del_day);
        });

        $('#condition_detail').on('change','#del_offline',function(){
            $(this).prop('checked')?dupl_condition.del_offline=0:dupl_condition.del_offline=1;
        });

        $('#condition_detail').on('change','#del_longtail',function(){
            $(this).prop('checked')?dupl_condition.del_longtail=0:dupl_condition.del_longtail=1;
        });

        $('#condition_score').on('change','.select_warp',function(e,value){
            qscore_condition[$(this).attr('name')] = value;
            $('#del_low_day').html(qscore_condition.del_day);
        });

        $('#condition_score').on('change','#del_offline_score',function(){
            $(this).prop('checked')?qscore_condition.del_offline=0:qscore_condition.del_offline=1;
        });

        $('#condition_score').on('change','#del_longtail_score',function(){
            $(this).prop('checked')?qscore_condition.del_longtail=0:qscore_condition.del_longtail=1;
        });

        /**
         * 重新检查按钮事件
         */
		$('#id_recheck').click(function(){
            common.confirm.show({
                body:'排查重复词可能较慢，确认现在就重新排查吗？',
                okHidden:function(){
                    page_no = 1;
                    getPageData();
                }
            });
		});

        /**
         * 手动删除详细表中的词
         */
		$(document).on('click','#single_submit_btn',function(){
            var cur_dupl = $('#duplicate_table').find('tr[index='+cur_index+']');
            var old_times = cur_dupl.find('.dupl_times:first').html();//记录原始重复次数
			var kw_id_arr=[];
            $('#dupl_detail_table tbody').find('input:checked').each(function(){
                kw_id_arr.push(parseInt($(this).val()));
            });
			if (kw_id_arr.length){
                common.confirm.show({
                    body:'确定要删除选中的重复词吗?',
                    okHidden:function(){
                        del_condition = 'level';
                        common.loading.show('正在删除重复词，请稍候...');
                        common.loading.hide();
                        common.sendAjax.ajax('delete_dupl_word',{'kw_id_list':kw_id_arr,'del_type':'manual'},function(data){
                            common.loading.hide();
                            cur_index = -1;
                            cur_dupl.data('has_load',false);
                            cur_dupl.find('.click_show').click();
                            cur_dupl.find('.dupl_times').html(parseInt(old_times) - data.del_count);
                        });
                    }
                });
			}else{
                common.alert.show('请选择下方未锁定的关键词！');
			}
		});

        /**
         * 点击区域，选中checkbox 和 radio
         */
        $('.del_box').on('click', '.select_div :radio,:checkbox', function (e) {
            //停止事件冒泡,当点击的是checkbox时,就不执行父div的click
            e.stopPropagation();
        });
        $('.del_box').on('click','.select_div',function(){
            $(this).find(':radio,:checkbox').click();
        });

        $('[data-toggle="tooltip"]').tooltip({html:true});
    };

    /**
     * 初始化重复词列表
     * @param datas
     */
    var initTable = function(datas){
        cur_index=-1;
        if(data_table){
            data_table.fnClearTable();
            data_table.fnDestroy();
        }

        var tpl, html;
        tpl = __inline('duplicate_list.html');
        html = template.compile(tpl)({datas:datas});

        $('#duplicate_table tbody').html(html);

        data_table = $('#duplicate_table').dataTable({
            "bRetrieve": true, //允许重新初始化表格
            "bPaginate": false,
            "bFilter": false,
            "bInfo": false,
            "bAutoWidth":false,//禁止自动计算宽度
            "language": {"emptyTable": "没有数据"},
            "aoColumns": [
                {"bSortable": false},
                {"bSortable": false}],
            "initComplete": function () {
                /**
                 * 结合th的点击事件，单页时前端排序，多叶时，后端排序
                 */
                $.fn.dataTableExt.afnSortData['custom-text'] = function(oSettings, iColumn) {
                    return $.map(oSettings.oApi._fnGetTrNodes(oSettings), function(tr, i) {
                        var td = oSettings.oApi._fnGetTdNodes(oSettings, i)[iColumn],
                        val=Number($(td).find('span:first').text());
                        if (page_count>1) {
                            return 0;
                        } else {
                            return val;
                        }
                    });
                };
            }
        });

        if(!data_table_header){
            data_table_header = new FixedHeader(data_table);
        }else{
            data_table_header.fnUpdate();
        }
        $('.select-all').prop('checked',false);
        $('.click_show:first').click();
    };

    /**
     * 初始化重复词详情列表
     * @param obj
     */
    var initDetailTable = function(html){
        if(detail_table){
            detail_table.fnClearTable();
            detail_table.fnDestroy();
        }
        $('#dupl_detail_table tbody').html(html);
        detail_table = $('#dupl_detail_table').dataTable({
            "bRetrieve": true, //允许重新初始化表格
            "bPaginate": false,
            "bFilter": false,
            "bInfo": false,
            "bSort": true,
            "bAutoWidth":false,//禁止自动计算宽度
            "language": {"emptyTable": "没有数据"},
            "aoColumns": [
                {"bSortable": false},
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
                {"bSortable": true}],
            "fnRowCallback": function( nRow, aData, iDisplayIndex, iDisplayIndexFull ) {
				//设置删词级别小于设定值时，锁定关键词
				var leave=$(nRow).find('td:eq(1) span:first').text();
                if (parseInt(leave)<=DUPLICATE_CHECK_LEAVE_LOCK){
                    $(nRow).find('.lock_kw').html('&#xe620;');
                    $(nRow).find('.child-select-sub').prop('disabled',true);
                }
			}
        });

        if(detail_table_header){
            $(detail_table_header.fnGetSettings().aoCache[0].nWrapper).remove();
        }
        detail_table_header = new FixedHeader(detail_table);
        $('.select-all-sub').prop('checked',false);
    };

    /**
     * 分页事件
     * @param page
     */
    var pageChange = function(page){
        page_no = parseInt(page);
        getPageData();
    };

    /**
     * 获取分页数据
     */
    var getPageData = function(){
        common.loading.show('数据加载中，请稍候...');
        common.sendAjax.ajax('dupl_kw_list', {'page_size':page_size,'page_no':page_no,'sort':sort}, function(data){
            page_count = Math.ceil(data.data_count / page_size);
            var recordCount = data.data_count;
            var draw_config = {
                inObj:$('.pagination_bar'),
                recordCount:recordCount,
                page_size:page_size,
                page_no:page_no,
                onChange:pageChange
            };

            $('.garbage_count').html(data.garbage_words_len);
            $('.duplicate_count').html(recordCount);
            $('.lowscore_count').html(data.lowscore_words_len);
            $('.hand_del_count').html('0');

            //更新分页条
            pageBar.draw(draw_config);
            initTable(data.duplicate_data_list);
            common.loading.hide();
        });
    };

    /**
     * 获取选中的关键词
     */
    var getKwArr=function (){
		var kw_arr=[];
		$('#duplicate_table tbody input:checked').each(function(){
			kw_arr.push($(this).parent().next().find('.keyword').text());
		});
		return kw_arr;
	};

    return{
        init:init
    }
});
