define(['require','template','moment','../common/common','dataTable',
        'jl6/site_media/widget/ajax/ajax','jl6/site_media/widget/loading/loading',
        'jl6/site_media/widget/confirm/confirm','jl6/site_media/widget/lightMsg/lightMsg',
        'jl6/site_media/widget/alert/alert','../report_detail/report_detail'],
    function(require,template,moment,common,dataTable,ajax,loading,confirm,lightMsg,alert,report_detail) {
    "use strict"

    var CampaignIdList=[];

    var campaign_table;

    var start_date = moment().subtract(7, 'days').format('YYYY-MM-DD'),
        end_date = moment().subtract(1, 'days').format('YYYY-MM-DD');
    var init_dom=function(){
        getCampaignList(start_date,end_date);

        //显示全部细分
        $('#show_subdivide_all').on('click',function(){
            if ($(this).data('is_lock')) {
                return; // 防止连续多次重复点击
            };
            $(this).data('is_lock', 1);
            var is_showing = $(this).data('is_showing');
            $.map($('#campaign_table .show_subdivide'),function(obj){
                if($(obj).data('is_showing') == is_showing){
                    $(obj).click();
                }
            });
            if (is_showing){
                delete($(this).data().is_showing);
            }else{
                $(this).data('is_showing', 1);
            }
            delete($(this).data().is_lock);
        });
    }

    //设置当前操作的计划id列表
    var setCampaignIdList=function(){
        CampaignIdList=[];
        $('#campaign_table .check_column input').each(function(){
            if(this.checked){
                CampaignIdList.push(this.value);
                $(this).parent('td').addClass('tr-checked');
            }else{
                $(this).parent('td').removeClass('tr-checked');
            }
        });
    }

    //绑定计划列表事件
    var bind_event=function(){
        //shift input操作
        $('#campaign_table .check_column').shiftcheckbox({
            checkboxSelector : 'input',
            selectAll: $('#campaign_table .all'),
            onChange:function(){
                setCampaignIdList();
            }
        }).on('click','input',function(){
            setCampaignIdList();
        });

        //修改标题
        $('#campaign_table .edit_title').on('click', function() {
            var title_warp, camp_title;
            title_warp = $(this).closest('td');
            camp_title = $.trim(title_warp.find('.title>a').text());
            title_warp.find('input[name=input_title]').val(camp_title);
            title_warp.find('.j_text_len').text(common.true_length(camp_title));
            title_warp.addClass('editor');
        });
        $('#campaign_table .editor_title>input[name=input_title]').on('keyup', function() {
            var limit_length = 40,
                text = this.value,
                true_length = common.true_length(text);
            if (true_length>limit_length) {
                this.value = text.slice(0, text.length-1);
                true_length = limit_length;
            }
            $(this).parent('.editor_title').find('.j_text_len').text(true_length);
        });
        $('#campaign_table .save_title').on('click', function() {
            var title_warp, origin_title, new_title;
            title_warp = $(this).closest('td');
            origin_title = $.trim(title_warp.find('.title').text());
            new_title = $.trim(title_warp.find('input[name=input_title]').val());
            if (new_title == '') {
                lightMsg.show({body:'计划名称不能为空'});
                return;
            }
            if (origin_title==new_title) {
	            title_warp.removeClass('editor');
            } else {
                ajax.ajax('modify_camp_title',{'camp_id':$(this).closest('tr').attr('id'),'new_title':new_title},function(data){
                    if (data.errMsg) {
	                    lightMsg.show({
	                        body:data.errMsg
	                    });
                    } else {
	                    title_warp.find('.title>a').text(new_title);
	                    lightMsg.show({
	                        body:'修改计划名称成功！'
	                    });
			            title_warp.removeClass('editor');
			            $('#li_camp_'+data.json_result_data.camp_id+' .camp_title').html(new_title);
                    }
                });
            }
        });
        $('#campaign_table .cancel_modify_title').on('click', function() {
            $(this).closest('td').removeClass('editor');
        });

        //显示报表
        $('#campaign_table .show_chart').on('click', function() {
            var camp_title, campaign_id;
            camp_title=$(this).closest('tr').find('.title').text();
            campaign_id=$(this).closest('tr').data('id');
            report_detail.show('计划明细：'+camp_title, 'campaign', $('#shop_id').val(), campaign_id);
        });

        //显示细分
        $('#campaign_table .show_subdivide').on('click', function() {
            if ($(this).data('is_lock')) {
                return; // 防止连续多次重复点击
            };
            $(this).data('is_lock', 1);
            var html,
                obj,
                campaign_id,
                tr_obj,
                tpl=__inline("subdivide.html");
            var that = this;
            tr_obj=$(this).closest('tr');
            campaign_id=tr_obj.data('id');
            if ($(this).data('is_showing')) {
                tr_obj.data('subdivide').remove();
                delete($(this).data().is_showing); // 一定要删除
                delete($(this).data().is_lock);
            }else if(tr_obj.data('subdivide')) {
                var obj = tr_obj.data('subdivide');
                tr_obj.after(obj);
                $(this).data('is_showing', 1);
                delete($(this).data().is_lock);
            }else{
                ajax.ajax('get_aggregate_rpt',{camp_id:campaign_id,'start_date':start_date,'end_date':end_date},function(data){
                    var result = data.result;
                    var tpl_data = {id:campaign_id}
                    for(var i=0;i<result.length;i++){
                        var temp_result = result[i];
                        switch (temp_result.source_id){
                            case 1:
                                tpl_data['pcin'] = temp_result;
                                break;
                            case 2:
                                tpl_data['pcout'] = temp_result;
                                break;
                            case 4:
                                tpl_data['ydin'] = temp_result;
                                break;
                            case 5:
                                tpl_data['ydout'] = temp_result;
                                break;
                            default:
                                break;
                        }
                    }
                    html = template.compile(tpl)(tpl_data);
                    obj=$(html);
                    tr_obj.after(obj);
                    $(tr_obj).data('subdivide',obj);
                    $(that).data('is_showing', 1);
                    delete($(that).data().is_lock);
                });
            }

        });

        //修改日限额
        $('#campaign_table .edit_budget').on('click',function(){
            var old_budget,
                campaign_id,
                old_is_smooth;
            var edit_budget = $(this);
            var show_budget = $(this).prev();
            campaign_id=$(this).closest('tr').data('id');
            old_budget=$(this).data('budget');
            old_is_smooth=$(this).data('smooth');
            var mnt_type = $(this).closest('tr').attr('mnt_type');

            require(["../edit_camp_budget/edit_camp_budget"],function(modal){
                modal.show({
                    campaign_id:campaign_id,
                    budget:old_budget,
                    is_smooth:old_is_smooth,
                    mnt_type:mnt_type,
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
                        ajax.ajax('modify_camp_budget',{'camp_id':campaign_id,'use_smooth':use_smooth,'budget':budget},function(data){
                            //title_warp.text(newTitle);
                            if(data.errMsg){
                                alert.show(data.errMsg);
                                return;
                            }

                            if(budget<20000000){
                                show_budget.text(budget+'元');
                            }else{
                                show_budget.text('不限');
                            }
                            edit_budget.data('budget',budget);
                            edit_budget.data('smooth',is_smooth);
                            lightMsg.show({
                                body:'修改日限额成功！'
                            });
                        });
                    }
                });
            });
        });

        //设置投放平台
        $('#campaign_table .edit_platform').on('click',function(){
            var camp_id=$(this).closest('tr').data('id');

            loading.show('正在获取计划投放平台');
            ajax.ajax('get_camp_platform',{'camp_id':camp_id},function(data){
                loading.hide();
                var platform = data.platform,
                    can_set_nonsearch = data.can_set_nonsearch;

                if (platform) {

                    require(['../edit_camp_platform/edit_camp_platform'],function(modal){
                        modal.show({
                            pc_insite_search: platform.pc_insite_search,
                            pc_outsite_nonsearch: platform.pc_outsite_nonsearch,
                            pc_insite_nonsearch: platform.pc_insite_nonsearch,
                            outside_discount: platform.outside_discount,
                            yd_outsite: platform.yd_outsite,
                            pc_outsite_search: platform.pc_outsite_search,
                            mobile_discount: platform.mobile_discount,
                            yd_insite: platform.yd_insite,
                            can_set_nonsearch: can_set_nonsearch,
                            onChange:function(newdata){
                                loading.show('正在设置计划投放平台');
                                ajax.ajax('update_camp_platform',{ 'camp_id':camp_id,'platform_dict':JSON.stringify(newdata)},function(result){
                                    loading.hide();
                                    if (result.is_success) {
                                        lightMsg.show({'body':'修改计划投放平台成功！'})
                                    } else {
                                        alert.show('修改计划投放平台失败');
                                    }
                                });
                            }
                        });
                    });
                } else {
                    alert.show('淘宝接口不稳定，请稍候再试');
                }
            });

        });

        //设置分时折扣
        $('#campaign_table .edit_schedule').on('click',function(){
            loading.show('正在获取分时折扣');
            var camp_id=$(this).closest('tr').data('id');
            ajax.ajax('get_camp_schedule',{'camp_id':camp_id},function(data){
                loading.hide();
                if (data.schedule_str) {
                    require(['../edit_camp_schedule/edit_camp_schedule'],function(modal) {
                        modal.show({
                            schedules: data.schedule_str,
                            onChange: function (schedule_str) {
                                ajax.ajax('update_camp_schedule',{'camp_id':camp_id, 'schedule_str': schedule_str},function(result){
                                    if(result.errMsg){
                                        alert.show(result.errMsg);
                                    }else{
                                        lightMsg.show({body:'修改计划分时折扣成功'});
                                    }
                                })
                            }
                        });
                    });
                } else {
                    alert.show('淘宝接口不稳定，请稍候再试');
                }

            });

        });

        //启用、暂停新建计划
        $(document).on('click', '.update_camp', function() {
            var mode = parseInt($(this).attr('mode')),
                camp_id_arr = [],
                mode_str = mode? '启动推广': '暂停推广';
            if($(this).hasClass('single')){
                camp_id_arr = [parseInt($(this).parents('tr').attr('data-id'))];
                confirm.show({
                    body:'确定'+mode_str+'这个计划吗？',
                    okHide:function(){
                        update_camp_status(mode, camp_id_arr);
                    }
                });
                return;
            }
            var objs = $('#campaign_table tbody input:checked');
            objs.each(function(){
                camp_id_arr.push(parseInt($(this).val()));
            });
            if (camp_id_arr.length) {
                confirm.show({
                    body:'确定'+mode_str+'所选的'+ camp_id_arr.length +'个计划吗？',
                    okHide:function(){
                        update_camp_status(mode, camp_id_arr);
                    }
                });
            } else {
                lightMsg.show({body:'请选择要操作的计划'});
            }
        });

        //开启、取消自动托管
        $(document).on('click','.change_camp_mnt', function(){
            var jq_tr = $(this).parents('tr'),
                camp_id = jq_tr.attr('id'),
                mnt_type = parseInt(jq_tr.attr('mnt_type')),
                set_flag = parseInt($(this).attr('type'));
            if (set_flag) {
                choose_mnt_campaign(camp_id);
            }else{
                var title = '确定“取消托管”该计划吗？';
                var mnt_days = Number($(this).attr('mnt_days'));
                if(mnt_days>=-10&&mnt_days<0){
                    title = "该计划只托管了"+Math.abs(mnt_days)+'天，'+title;
                }else if(mnt_days==0){
                    title = "该计划托管不满1天，"+title;
                }
                var body_str="<div class='lh25'>1、效果需要一定周期培养，建议不要短期托管或频繁更换策略</div><div class='lh25'>2、系统会停止优化您的宝贝，但不会改变计划和宝贝的推广状态</div><div class='lh25'>3、取消后可以重新开启托管，但需要重新设置计划、宝贝、策略</div>";
                confirm.show({
                    title:title,
                    body:body_str,
                    cancleStr: "不取消托管",
                    okStr: "取消托管",
                    okHidden:function(){
                        ajax.ajax('mnt_campaign_setter',{'campaign_id':camp_id,'set_flag':0,'mnt_type':mnt_type},function(data){
                            var jq_tr = $('#'+camp_id),
                            new_url = '/web/adgroup_list/'+camp_id,
                            mnt_index = jq_tr.attr('mnt_index');
                            $('#main_nav li.mnt_index:eq('+(Number(mnt_index)-1)+') a').attr('blank_mnt_index', mnt_index).html(mnt_index+'号引擎[未启动]');
                            jq_tr.attr({'mnt_type':0, 'mnt_index':0});
                            jq_tr.find('.change_camp_mnt').text('开启托管').attr('type',1);
                            jq_tr.find('.mnt_desc').text('手动');
                            jq_tr.find('.mnt_desc').removeClass("label-primary").addClass("label-default");
                            $('#title_'+camp_id).attr('href', new_url);
                            $('#li_camp_'+camp_id).remove();
                            lightMsg.show({
                                title: '托管状态修改',
                                style: 'default',
                                body:'取消托管成功',
                                timeout: 5000
                            });
                        },null,{url:'/mnt/ajax/'});
                    }
                });
            }
        });
    }

    //获取计划列表数据
    var getCampaignList=function(start,end){
        var html,
            tpl=__inline("campaign_list.html");

        ajax.ajax('get_campaign_list',{start:start,end:end},function(data){
            html = template.compile(tpl)({list:data.json_campaign_list});

            if(campaign_table){
                campaign_table.fnClearTable();
                campaign_table.fnDestroy();
            }

            $('#campaign_table tbody').html(html);

            bind_event();
            campaign_table = $('#campaign_table').dataTable({
                "bRetrieve": true, //允许重新初始化表格
                "bPaginate": false,
                "bDestroy":true,
                "bFilter": true,
                "bInfo": false,
                "bAutoWidth":false,//禁止自动计算宽度
                "sDom":'',
                // "aaSorting": [[0,'asc'], ],
                "aoColumns": [
                    {"bSortable": false},
                    {"bSortable": false},
                    {"bSortable": false},
                    {"bSortable": false},
                    {"bSortable": false},
                    {"bSortable": true,
                     "sType":'custom',
                     "sSortDataType":"custom-text"
                    },
                    {"bSortable": true,
                     "sType":'custom',
                     "sSortDataType":"custom-text"
                    },
                    {"bSortable": true,
                     "sType":'custom',
                     "sSortDataType":"custom-text"
                    },
                    {"bSortable": true,
                     "sType":'custom',
                     "sSortDataType":"custom-text"
                    },
                    {"bSortable": true,
                     "sType":'custom',
                     "sSortDataType":"custom-text"
                    },
                    {"bSortable": true,
                     "sType":'custom',
                     "sSortDataType":"custom-text"
                    },
                    {"bSortable": true,
                     "sType":'custom',
                     "sSortDataType":"custom-text"
                    },
                    {"bSortable": true,
                     "sType":'custom',
                     "sSortDataType":"custom-text"
                    },
                    {"bSortable": true,
                     "sType":'custom',
                     "sSortDataType":"custom-text"
                    },
                    {"bSortable": true,
                     "sType":'custom',
                     "sSortDataType":"custom-text"
                    },
                    {"bSortable": true,
                     "sType":'custom',
                     "sSortDataType":"custom-text"
                    },
                    {"bSortable": false},
                    {"bSortable": false}
                ],
                "fnDrawCallback": function(oSettings) {
                    delete($('#show_subdivide_all').data().is_showing);
                    delete($('#show_subdivide_all').data().is_lock);
                    $.map($('#campaign_table .show_subdivide'),function(obj){
                            delete($(obj).data().is_showing);
                            delete($(obj).data().is_lock);
                    });
                }
            });
        });
    };

    //暂停、启动推广
    var update_camp_status = function(mode,camp_id_arr){
        ajax.ajax('update_camps_status',{'camp_id_list':camp_id_arr,'mode':mode},function(data){
            if (data.success_camp_ids.length === 0) {
                alert.show('修改失败：淘宝接口不稳定，请稍候再试');
                return;
            }
            if (mode) {
                for(var i=0; i<data.success_camp_ids.length; i++) {
                    var camp_id = data.success_camp_ids[i],
                        jq_tr=$('#'+camp_id),
                        jq_oper = jq_tr.find('.update_camp');
                    //jq_oper.prev().addClass('item_base').removeClass('item_dark').text('推广中');
                    jq_tr.removeClass('gray_light');
                    jq_oper.prev().text('推广中');
                    jq_oper.attr('mode', 0).text('暂停');
                }
            } else {
                for(var i=0; i<data.success_camp_ids.length; i++) {
                    var camp_id = data.success_camp_ids[i],
                        jq_tr=$('#'+camp_id),
                        jq_oper = jq_tr.find('.update_camp');
                    //jq_oper.prev().addClass('item_dark').removeClass('item_base').text('已暂停');
                    jq_tr.addClass('gray_light');
                    jq_oper.prev().text('已暂停');
                    jq_oper.attr('mode', 1).text('开启');
                }
            }
        });
    };

    //开启、取消自动托管
    var choose_mnt_campaign = function(camp_id){
        var jump_url =  '/mnt/choose_mnt_campaign/'+camp_id;

        window.open(jump_url, "_blank");
    };

    //设置开始时间和结束时间
    var setQueryDate = function(start,end){
        start_date = start;
        end_date = end;
    }

    return {
        init:function(){
            //顶部通栏事件
            init_dom();
        },
        setQueryDate:setQueryDate,
        getCampaignList:getCampaignList
    }
});
