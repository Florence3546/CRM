/**
 * Created by Administrator on 2015/9/19.
 */
define(['template','jl6/site_media/widget/alert/alert','jl6/site_media/widget/confirm/confirm',
        'jl6/site_media/widget/lightMsg/lightMsg','jl6/site_media/widget/ajax/ajax','jl6/site_media/widget/loading/loading'],
        function(template,alert,confirm,lightMsg,ajax,loading){

    var init = function(list_type,camp_id,del_callback){
        var html,
            tpl=__inline("select_tool.html");
        html = template.compile(tpl)({list_type:list_type})

        $('#goods_table').after($(html));

        fixPosition();

        var windowHeight = $(window).height();
        var scrollTop = $(window).scrollTop();
        if($('#goods_table tbody tr:first').offset().top+50>scrollTop+windowHeight){
            $('.select-tool').addClass('hide');
        }

        //监听滚动条
        $(window).scroll(function(){
            $('.select-tool').removeClass('hide');
            var pageToolHeight = $('.page-tool').offset().top+10;
            var scrollTop = $(window).scrollTop();
            var windowHeight = $(window).height();
            //如果屏幕的高度加滚动的高度大于分页条的高度，则将浮动工具添加到分页条上面
            if(scrollTop+windowHeight>pageToolHeight){
                 $('.select-tool').removeClass('select-fixed');
            }else{
                $('.select-tool').addClass('select-fixed');
            }
            if($('#goods_table tbody tr:first').offset().top+50>scrollTop+windowHeight){
                $('.select-tool').addClass('hide');
            }
        });

        //监听窗口大小改变事件
        $(window).resize(function(){
            var pageToolHeight = $('.page-tool').offset().top+10;
            var windowHeight = $(window).height();

            //如果窗口高度大于滚动条高度，浮动工具则显示在列表下
            if(windowHeight>pageToolHeight){
                $('.select-tool').removeClass('select-fixed');
            }else{
                $('.select-tool').addClass('select-fixed');
            }
            $('.select-tool').removeClass('hide');
        });


        //批量操作
        $(".select-tool").on('click','.batch-opt',function(){
            var select_count = parseInt(getSelected());
            if(select_count<=0){
                alert.show('还未选择任何宝贝！');
                return false;
            }

            var opt_type = parseInt($(this).attr('opt_type'));
            switch (opt_type){
                case 1:
                    confirm.show({'body':'确定要启动推广所选的'+select_count+'个宝贝吗？','okHide':function(){
                        //在这里进行启动推广操作
                        update_adg_status('start');
                    }});
                    break;
                case 2:
                    confirm.show({'body':'确定要暂停推广所选的'+select_count+'个宝贝吗？','okHide':function(){
                        //在这里进行暂停推广操作
                        update_adg_status('stop');
                    }});
                    break;
                case 3:
                    confirm.show({'body':'即将删除所选的'+select_count+'个宝贝，删除后将在直通车后台消失且无法恢复，确认要删除吗？','okHide':function(){
                        //在这里进行删除宝贝操作
                        update_adg_status('del');
                    }});
                    break;
                case 4:
                    quick_oper_adg(1);
                    break;
                case 5:
                    quick_oper_adg(0);
                    break;
                case 6:
                    //在这里进行自动优化操作
                    update_adg_mnt(1);
                    break;
                case 7:
                    //在这里进行只优化价格操作
                    update_adg_mnt(2);
                    break;
                case 8:
                    //在这里进行不自动优化操作
                    update_adg_mnt(0);
                    break;
                default :
                    break;
            }
        });

        //批量设置优化状态
        var update_adg_mnt = function(opt_type){
            var opt_descs = '确定要将选中的宝贝设置为自动优化吗？';
            if(opt_type==2){
                opt_descs = '确定要将选中的宝贝设置为只改价吗？';
            }else if(opt_type==0){
                opt_descs = '确定要将选中的宝贝取消托管吗？';
            }
            var tr_objs = getSelectObjs();

            var adg_id_list = $.map(tr_objs,function(tr_obj){
                var flag = $(tr_obj).find('.mnt_opt_type').attr('mnt_opt_type');
                //当选中的adg的优化状态与设置的一样时，不做修改
                if(flag != opt_type){
                    return parseInt($(tr_obj).attr('adgroup_id'))
                }
            });
            if (!adg_id_list.length){
                return;
            }

            confirm.show({'body': opt_descs,okHidden:function(){
                ajax.ajax('update_adgs_mnt',{ 'camp_id':camp_id,
                  'adg_id_list':adg_id_list,
                  'mnt_type':list_type,
                  'flag':opt_type},function(data) {
                      var adg_ids = data.success_list;
                      for(var i=0;i<adg_ids.length;i++){
                          var tr_obj = $('#goods_table tr[adgroup_id='+adg_ids[i]+']');
                          var status = '自动优化';
                          var sort_value = 1;
                          //更新托管宝贝数
                          $('.mnt_num').text(data.mnt_count);
                          $('.new_num').text(data.max_num - data.mnt_count);
                          if(data.flag==0){
                              status = '未托管';
                              sort_value = 3;
                              tr_obj.find('.change_mnt_type').attr('mnt_type',0);
                              tr_obj.find('.mnt_type_true').removeClass('hide');
                              tr_obj.find('.mnt_type_false').addClass('hide');
                              tr_obj.find('.optm_submit_time').removeClass('hide');

                              //未托管时 有一键优化按钮
                              if(tr_obj.find('.onekey').length==0){
                                  var adgroup_id = tr_obj.attr('adgroup_id');
                                  var campaign_id = tr_obj.attr('campaign_id');
                                  var onekey = '<a href="javascript:;" class="onekey" adgroup_id="'+adgroup_id+'" campaign_id="'+campaign_id+'"><span><strong>一键优化</strong></span></a>';
                                  tr_obj.find('.opt_url').append(onekey);
                              }

                          }else{
                              tr_obj.find('.mnt_type_false').removeClass('hide');
                              tr_obj.find('.mnt_type_true').addClass('hide');
                              tr_obj.find('.optm_submit_time').addClass('hide');
                              if(data.flag==2){
                                  status = '只改价';
                                  sort_value = 2;
                              }
                              tr_obj.find('.onekey').remove();
                          }

                          tr_obj.find('.opt_status').text(status);
                          tr_obj.find('.sort_value').text(sort_value);
                          tr_obj.find('.mnt_opt_type').attr('mnt_opt_type',data.flag);
                      }
                      lightMsg.show({body: '操作成功！'});
                },null,{'url':'/mnt/ajax/'});
            }});
        };

        //批量加大或减少投入
        var quick_oper_adg = function(stgy){
            var tr_objs = getSelectObjs();

            var adg_id_list = $.map(tr_objs,function(tr_obj){
                if(!$(tr_obj).attr('is_quick_opered')||$(tr_obj).attr('is_quick_opered') == '0'){
                    return parseInt($(tr_obj).attr('adgroup_id'))
                }
            });
            if (!adg_id_list.length){
                alert.show('所选宝贝今日全部优化过，不能再优化了（每天只能优化一次）');
                return;
            }
            confirm.show({'body':'确定要优化选中的宝贝?',okHide:function(){
                ajax.ajax('quick_oper',{ 'campaign_id':camp_id,
                  'adg_id_list':adg_id_list,
                  'mnt_type':list_type,
                  'stgy':stgy},function(data) {
                    for(var i=0;i<adg_id_list.length;i++){
                        $('#goods_table tr[adgroup_id='+adg_id_list[i]+']').attr('is_quick_opered','1');
                    }
                    lightMsg.show({body: '操作成功！'});
                },null,{'url':'/mnt/ajax/'});
            }});
        };

        //宝贝开启、推广、暂停
        var update_adg_status = function(mode){
            var adgroupIds = getSelectParams('adgroup_id');
            loading.show('正在执行，请稍候...');
            ajax.ajax('update_adg_status', {
                'mode':mode,
                //'mnt_type':$('#mnt_type').val(),
    //            'campaign_id':$('#campaign_id').val(),
                'mnt_type':1,
                'campaign_id':0,
                'adg_id_list':'[' + adgroupIds.toString() + ']'
            }, update_adg_status_callback);
        }

        //宝贝开启、推广、暂停 的回调函数
        var update_adg_status_callback = function(result){
            switch(result.mode){
                case 'start':
                    for(var i=0; i<result.success_id_list.length; i++) {
                        var adgroup_id = result.success_id_list[i];
                        $('#goods_table tr[adgroup_id=' + adgroup_id + '] .lbl_online').html('推广中');
                        $('#goods_table tr[adgroup_id=' + adgroup_id + '] .switch_status').html('暂停');
                        $('#goods_table tr[adgroup_id=' + adgroup_id + '] .sort_online').text(1);
                        $('#goods_table tr[adgroup_id=' + adgroup_id + ']').removeClass('gray');
                    }
                    break;
                case 'stop':
                    for(var i=0; i<result.success_id_list.length; i++) {
                        var adgroup_id = result.success_id_list[i];
                        $('#goods_table tr[adgroup_id=' + adgroup_id + '] .lbl_online').html('已暂停');
                        $('#goods_table tr[adgroup_id=' + adgroup_id + '] .switch_status').html('开启');
                        $('#goods_table tr[adgroup_id=' + adgroup_id + '] .sort_online').text(0);
                        $('#goods_table tr[adgroup_id=' + adgroup_id + ']').addClass('gray');
                    }
                    break;
                case 'del':
                      lightMsg.show({body:'宝贝删除成功！'});
                      del_callback();
                    break;
            }

            loading.hide();
        };

        /*if($('.online_status').attr('mode')=='0'){
            $('.quick_oper').removeClass('hide');
        }else{
            $('.quick_oper').addClass('hide');
        }*/
    }


    //刷新选中的总条数
    var refreshSelected = function(){
        var total = 0;
        $('#goods_table').find('.kid_check').each(function(){
            if($(this).prop('checked')){
                total++;
            }
        });
        $(".select_rows").text(total);
    };

    //设置选中的总条数
    var setSelected = function(rows){
        $(".select_rows").text(rows);
        if(rows==0){
            $('.select-all').prop('checked',false);
        }
    };


    //获取选中的总条数
    var getSelected = function(){
        return $(".select_rows").text();
    };

    //获取选中的记录
    var getSelectParams = function(e){
        if(!e){
            e = 'adgroup_id';
        }
        var results = [];
        $('#goods_table').find('.kid_check').each(function(){
            if($(this).prop('checked')){
                results.push($(this).parents('tr').attr(e));
            }
        });
        return results;
    };

    //获取所有选中的行
    var getSelectObjs = function(){
        var results = [];
        $('#goods_table').find('.kid_check').each(function(){
            if($(this).prop('checked')){
                results.push($(this).parents('tr'));
            }
        });
        return results;
    };

    //设置工具条的位置
    var fixPosition = function(){
        var pageToolHeight = $('.page-tool').offset().top+10;
        var windowHeight = $(window).height();
        if(windowHeight>pageToolHeight){
             $('.select-tool').removeClass('select-fixed');
        }else{
            $('.select-tool').addClass('select-fixed');
        }

    };

    var show = function(){
        $('.select-tool').css('display','block');
    };

    var hide = function(){
        $('.select-tool').css('display','none');
    };

    return {
        init:init,
        refreshSelected: refreshSelected,
        setSelected:setSelected,
        getSelected:getSelected,
        getSelectParams:getSelectParams,
        fixPosition:fixPosition,
        getSelectObjs:getSelectObjs,
        show:show,
        hide:hide
    }
});