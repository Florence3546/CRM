define(['require','template','moment', 'dataTable', '../../widget/ajax/ajax', '../../widget/loading/loading'],
    function(require,template,moment, dataTable, ajax, loading) {
    "use strict"

    var campaign_table;

    var init_dom=function(start_date, end_date){
        getCampaignList(start_date, end_date);
        bindEvent();
    }

    //设置当前操作的计划id列表
    var getCampaignIdList=function(){
        var campaignIdList=[];
        $('#campaign_table .check_column input').each(function(){
            if($(this).prop('checked')){
                campaignIdList.push($(this).val());
            }
        });
        return campaignIdList;
    };

    //获取计划列表数据
    var getCampaignList=function(start,end) {
        /**
         * 在这里从后台取数据
         */
        loading.show('数据加载中,请稍候...');
        ajax.ajax('campaign_list',{'start_date':start, 'end_date':end},function(data){
            drawDataTable(data);
            loading.hide();
        });
    };

    /**
     * 事件绑定
     */
    var bindEvent = function(){
        /**
         * 修改日限额
         */
        $('#campaign_table tbody').on('click','.edit_budget', function(){
            var old_budget,
                campaign_id,
                old_is_smooth;
            campaign_id=$(this).closest('tr').data('id');
            old_budget=$(this).data('budget');
            old_is_smooth=$(this).data('smooth');
            var mnt_type = $(this).closest('tr').attr('mnt_type');
            require(["edit_camp_budget"],function(modal){
                modal.show({
                    campaign_id:campaign_id,
                    budget:old_budget,
                    is_smooth:old_is_smooth,
                    mnt_type: parseInt(mnt_type),
                    onChange:function(budget,is_smooth){
                        if(budget == old_budget && is_smooth == old_is_smooth) {
                            return;
                        }
                        var use_smooth;
                        if(is_smooth=='0'){
                            use_smooth='false';
                        }else{
                            use_smooth='true';
                        }
                        ajax.ajax('set_budget',{'camp_id':campaign_id,'use_smooth':use_smooth,'budget':budget},function(data){
                            //title_warp.text(newTitle);
                            var edit_budget = $('#'+data.json_result_data.camp_id).find('.edit_budget');
                            var show_budget = edit_budget.prev();
                            if(budget<20000000){
                                show_budget.text(budget+'元');
                            }else{
                                show_budget.text('不限');
                            }
                            edit_budget.data('budget',budget);
                            edit_budget.data('smooth',is_smooth);
                            $.alert({title:'提示', body: '修改成功！', okBtn:"确定", height:"30px"});
                        });
                    }
                });
            });
        });

        /**
         * 全选
         */
        $('.choose_column').change(function(){
            $('.check_column [type=checkbox]').prop('checked', $(this).prop('checked'));
        });

        $('#campaign_table').change('.check_column [type=checkbox]', function(){
            if($('.check_column [type=checkbox]:checked').length==$('#campaign_table tbody tr').length){
                $('.choose_column').prop('checked', true)
            }else{
                $('.choose_column').prop('checked', false)
            }
        });

        $("#campaign_table").on("click", ".set_online_status", function(){
            var trObj = $(this).closest("tr");
            var status = $(this).attr("opt");
            var camp_id_arr = trObj.data('id');
            updateCampStatus(status, [camp_id_arr]);
        });
    };

    //暂停、启动推广
    var updateCampStatus = function(mode,camp_id_list){
        var camp_ids = new Array();
        for(var i in camp_id_list){
            var trObj = $("#campaign_table").find('#'+camp_id_list[i]);
            if(trObj.find('.set_online_status').attr("opt")==mode){
                camp_ids.push(camp_id_list[i]);
            }
        }

        ajax.ajax("set_online_status", {mode:mode, camp_id_list:camp_ids},function(data){
            updateCampStatusCallBack(data);
        });
    };

    var updateCampStatusCallBack = function(data){
        var campIds = data.success_camp_ids;

        for(var i in campIds){

            var trObj = $("#campaign_table").find('#'+campIds[i]);
            if(data.mode==1){
                trObj.removeClass("gray_light");
                trObj.find('.set_online_status').attr("opt","0");
                trObj.find('.set_online_status').prev("span").text("推广中");
                trObj.find('.set_online_status').text("暂停");
            }else{
                trObj.addClass("gray_light");
                trObj.find('.set_online_status').attr("opt","1");
                trObj.find('.set_online_status').prev("span").text("已暂停");
                trObj.find('.set_online_status').text("开启");
            }
        }
        $.alert({title:'提示', body: '操作成功！', okBtn:"确定", height:"30px"});
    };

    var drawDataTable = function(data){
        if (campaign_table) {
            campaign_table.fnClearTable();
            campaign_table.fnDestroy();
        }
        var html,
            tpl = __inline("campaign_list.html");
            html = template.compile(tpl)({list: data.json_campaign_list});
        $('#campaign_table tbody').html(html);
        campaign_table = $('#campaign_table').dataTable({
            "bRetrieve": true, //允许重新初始化表格
            "bPaginate": false,
            "bDestroy": true,
            "bFilter": true,
            "bInfo": false,
            "bAutoWidth": false,//禁止自动计算宽度
            "sDom": '',
            "language": {"emptyTable": "<div style='text-align:center'>暂无数据</div>"},
            "aoColumns": [
                {"bSortable": false},
                {"bSortable": false},
                {"bSortable": true,
                    "sType": 'custom',
                    "sSortDataType": "custom-text"
                },
                {"bSortable": true,
                    "sType": 'custom',
                    "sSortDataType": "custom-text"
                },
                {"bSortable": true,
                    "sType": 'custom',
                    "sSortDataType": "custom-text"
                },
                {"bSortable": true,
                    "sType": 'custom',
                    "sSortDataType": "custom-text"
                },
                {"bSortable": true,
                    "sType": 'custom',
                    "sSortDataType": "custom-text"
                },
                {"bSortable": true,
                    "sType": 'custom',
                    "sSortDataType": "custom-text"
                },
                {"bSortable": true,
                    "sType": 'custom',
                    "sSortDataType": "custom-text"
                },
                {"bSortable": true,
                    "sType": 'custom',
                    "sSortDataType": "custom-text"
                },
                {"bSortable": true,
                    "sType": 'custom',
                    "sSortDataType": "custom-text"
                },
                {"bSortable": true,
                    "sType": 'custom',
                    "sSortDataType": "custom-text"
                },
                {"bSortable": true,
                    "sType": 'custom',
                    "sSortDataType": "custom-text"
                },
                {"bSortable": false}
            ]
        });
    };


    return {
        init:init_dom,
        getCampaignList:getCampaignList,
        getCampaignIdList:getCampaignIdList,
        updateCampStatus:updateCampStatus
    }
});
