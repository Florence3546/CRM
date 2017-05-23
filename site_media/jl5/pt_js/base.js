PT.namespace('Base');
PT.Base = function () {
    var url='';

    var init_dom=function() {

        // $('#contact').hover(function(){
        //  $('#contact_telephone').stop().animate({'marginLeft':0},300);
        // },function(){
        //  $('#contact_telephone').stop().animate({'marginLeft':-181},100);
        // });

        $('a[name=upgrade]').click(function(){
            //这里只好将url固定了
            return
            PT.confirm("您当前的版本需要升级后才可以开通该引擎，要升级吗？", function(){window.open("/web/upgrade_suggest/?referer=upgrade&item_code=ts-25811-1", '_blank');},[],this,null,[],this, ['升级'])
        });

        $('#duplicate_check_id').click(function() {
            PT.sendDajax({'function': 'web_to_duplicate_check'});
        });

        $('#attention_check_id').click(function() {
            PT.sendDajax({'function': 'web_to_attention_list'});
        });

        $('#id_sync_data').click(function(){
            PT.show_loading("正在同步数据，可能耗时较长");
            PT.sendDajax({'function':'web_sync_data'});
        });

        $('.open_feedback_dialog').click(function(){
            var title_str = '<i class="iconfont f24 b">&#xe610;</i><span class="b f20">意见反馈</span><span class="silver ml5">感谢您的参与和鞭策，精灵会做的更好</span>',
                body_str = '<div class="tc"><textarea id="id_content" name="content" class="pct90 h80" placeholder="您的意见，是我们进步的最大动力。"></textarea></div>';
            $.confirm({
                backdrop: 'static',
                title:title_str,
                body:body_str,
                okBtn:'提交反馈',
                okHide:function () {
                        var content=$('#id_content').val();
                        if(content===''){
                            PT.alert('麻烦您不吝赐教，输入您的建议');
                            return false;
                        }
                        PT.show_loading('感谢您的反馈');
                        PT.sendDajax({'function':'web_submit_feedback','score_str':'[]','content':content});
                    }
            });
        });

        //完善用户信息
        $('.open_info_dialog').click(function(){
            PT.sendDajax({'function':'web_open_info_dialog'});
        });

//        $(document).on('click','#open_msg',function(e) {
        $('#open_msg').click(function(e) {
            var modal_str = $('#id_msg_template').html();
            if(modal_str){
                $('#msg_modal_dialog').modal();
            }else{
                PT.show_loading('正在获取我的消息');
                PT.sendDajax({'function':'web_open_msg_dialog'});
            }
        });

        $(document).on('click','#msg_modal_dialog .close_msg',function() {
            eval("var data="+$(this).attr("data"));
            var is_common=data.is_common,
                msg_id=data.msg_id,
                type=is_common==1? 'common' : 'user',
                jq_count=$('#'+type+'_prompt_count'),
                prompt_count=parseInt(jq_count.text());
            if ( prompt_count > 1) {
                jq_count.text(prompt_count-1);
            }else{
                jq_count.text(0).parent().remove();
            }
            $('#dot_'+msg_id).removeClass('red').addClass('silver');
            $(this).removeClass('close_msg');
            PT.Base.change_msg_count();
            PT.sendDajax({'function':'web_close_msg','msg_id':msg_id,"is_common":is_common});
        });

        // $(document).on('click','#msg_modal_dialog .close',function() {
        //  var user_prompt_count=$('#user_prompt_count').text().slice(1,-1),
        //      common_prompt_count=$('#common_prompt_count').text().slice(1,-1),
        //      total_prompt_count=Number(user_prompt_count)+Number(common_prompt_count);
        //  if (total_prompt_count>0) {
        //      $('#prompt_msg_count').text(total_prompt_count);
        //  }else{
        //      $('#prompt_msg_count').parent().remove();
        //  }
        //  $('#msg_modal_dialog').modal('hide');
        // });

        // $(document).on('click','#submit_btn',function(){
        //  var content=$('#id_content').val();
        //  if(content=='您的意见，是我们进步的最大动力。'){
        //      content='';
        //  }
        //  if(content===''){
        //      PT.alert('麻烦您不吝赐教，输入您的建议');
        //      return false;
        //  }
        //  PT.show_loading('感谢您的反馈');
        //  var scores = $('input[id^=id_raty_]'),
        //      score_list=[];
        //  for(var i =0;i<scores.length;i++){
        //      var temp_id = $(scores[i]).attr('id'),
        //          id = temp_id.slice(0,temp_id.indexOf('-score')).replace('_raty','');
        //      score_list.push([ id.slice(3), Number($(scores[i]).val()) ]);
        //  }
        //  PT.sendDajax({'function':'web_submit_feedback','score_str':$.toJSON(score_list),'content':content});
        // });

        $(document).on('click','.open_comment',function(){
            PT.sendDajax({'function':'web_get_sigle_comment','obj_id':$(this).attr('obj_id'),'obj_type':$(this).attr('obj_type'),'name_space':'Base'});
            return false;
        });

        $('#modal_single_comment,#msg_record').on('click','.mark_comment_read',function(){
            $(this).parents('.alert-info').removeClass('alert-info').addClass('alert-success');
            PT.sendDajax({'function':'web_mark_comment_read','msg_id':String($(this).attr('msg_id'))});
            $(this).remove();
            PT.Base.change_msg_count();
            if (document.body.id=='pt_mnt_campaign'){
                var unread_count=Number($('#comment_count').text());
                if(unread_count>1){
                    $('#comment_count').text(unread_count-1);
                }else{
                    $('#comment_count').parent().remove();
                }
            }
            return false;
        });

        $('#modal_single_comment').on('click','.close',function(){
            var jq_modal=$('#modal_single_comment'),
                unread_count=jq_modal.find('.mark_comment_read').length;
            if (unread_count===0) {
                $('.open_comment[obj_id='+ jq_modal.attr('obj_id') +']').remove();
            }
            jq_modal.modal('hide');
        });

        $(document).on('click', '#id_current_nick', function(){
           $('#id_ww').val($('#id_nick').val());
        });

        $(document).on('click', '#id_submit_info', function(){
            if($(this).hasClass('disabled')){
                return false;
            }

            var old_phone = $.trim($('#id_phone').attr("old_value"));
            var old_qq = $.trim($('#id_qq').attr("old_value"));
            var ww = $('#id_ww').val();
            var qq = $.trim($('#id_qq').val());
            var phone = $.trim($('#id_phone').val());

            if(qq==old_qq&&phone==old_phone){
                $('#perfect_phone').modal('hide');
                return false;
            }
            //var code = $('#id_phone_code').val();

            if(isNaN(phone) || !(/^1[3|4|5|7|8]\d{9}$/.test(phone))){
                PT.alert("手机号码填写不正确！");
                return false;
            }

            /*
            if(!/^[1-9]\d{4}$/.test(code)){
                PT.alert("请输入正确的手机验证码！");
            }*/
            PT.sendDajax({'function':'web_submit_userinfo', 'phone':phone, 'ww':ww, 'qq':qq});

            $('#id_phone').attr("old_value",phone);
            $('#id_qq').attr("old_value",qq);
        });

        //当鼠标经过该元素时，加上hover这个class名称，修复ie中css的hover动作
        $(document).on('mouseover.PT.e','*[fix-ie="hover"]',function(){
            $(this).addClass('hover');
            $(this).mouseout(function(){
                $(this).removeClass('hover');
            });
        });

        //关联td和里面的checkbox事件
        $(document).on('click','.link_inner_checkbox',function(e){
            e.stopPropagation();
            if(this==e.target){
                $(this).find('input[type="checkbox"]').click();
            }
        });

        //新建计划
        $('.js_create_camp').click(function(){
            PT.Base.goto_ztc(1,'','','');
        });

        // 表格下拉排序
        $(document).on('change','.table_sort_dropdown',function(e,v){
            //找到table
            var table=$(this).parents('table'),tIndex=table.find('th').index($(this).parent());
            var prev_val=$(this).find('.dropdown-toggle').attr('data-prev-value');

            $(this).find('.dropdown-toggle').attr('data-prev-value',v);

            if(table.attr('source')){
                table=$('#'+table.attr('source'))
            }
            if(!table.find('tbody tr').length){
                PT.light_msg('提醒','没有可排序的数据')
                return false;
            }

            var dataTable=table.dataTable();

            $(dataTable.fnSettings().aoData).each(function(){
                var currentTd=this.nTr.children[tIndex],currentObj=$(currentTd).find('.'+v);
                $(currentTd).find('>span:first').text(currentObj.text().replace('%','').replace('￥',''));
                $(currentTd).find('span.baseColor').removeClass('b baseColor')
                currentObj.addClass('baseColor b')
            });

            if (v === prev_val){ //默认点击一次为降序，点击两次则升降序交替
                if (dataTable.fnSettings().aaSorting[0][1]==="asc"){
                    dataTable.fnSort([[tIndex,'desc']]);
                }else{
                    dataTable.fnSort([[tIndex,'asc']]);
                }
            }else{
                dataTable.fnSort([[tIndex,'desc']]);
            }
        });

        //冻结积分
        $(document).on('click','.freeze_point',function(){
            PT.sendDajax({'function':'web_freeze_point'});
        });
    };

    var duplicate_check=function () {
        PT.show_loading("正在下载关键词报表");
        window.location.href = "/web/duplicate_check";
    };

    var sync_all=function(data_type,rpt_days) {
        var tips='';
        if (data_type==1) {
            tips = '正在下载' + rpt_days + '天报表数据，可能耗时较长';
        } else if (data_type==2) {
            tips = '正在重新下载所有结构数据，耗时较长';
        }
        PT.sendDajax({'function':'web_sync_all_data','data_type':data_type,'rpt_days':rpt_days});
        return tips;
    };

    var attention_check=function(){
        PT.show_loading("正在下载关键词报表");
        window.location.href = "/web/attention_list";
    };

    return {
        init: function (){
            init_dom();
        },

        change_msg_count:function() {
            var jq_count=$('.msg_count'),
	            msg_count=Number(jq_count.text()),
	            jq_count2=$('.msg_vip_count'),
	            msg_vip_count=Number(jq_count2.text());
            if(msg_count>1){
                jq_count.text(msg_count-1);
            }else{
                jq_count.remove();
            }
            if(msg_vip_count>1){
                jq_count2.text(msg_vip_count-1);
            }else{
                jq_count2.remove();
            }
        },

        get_sigle_comment_back:function(result){
            var dom=template.render('template_single_comment',{'msg_list':result.msg_list}),
                jq_modal=$('#modal_single_comment');
            jq_modal.find('.obj_title').text(result.obj_type+'："'+result.obj_title+'"');
            jq_modal.find('.modal-body').html(dom);
            jq_modal.attr('obj_id',result.obj_id);
            jq_modal.modal('show');
        },

        submit_feedback_back: function(result_flag) {
            PT.hide_loading();
            if (result_flag===0) {
                PT.alert('亲，提交失败，非常抱歉，麻烦将意见发给您的顾问');
            } else {
                $('#feedback_modal_dialog').modal('hide');
                PT.light_msg('提交成功','感谢您的参与！我们会及时处理您的意见' );
            }
        },
        duplicate_check_confirm:function () {
            PT.confirm('关键词报表尚未下载完，会影响系统推荐的删词级别，现在就下载报表并排重吗？',duplicate_check,[],this);
        },
        //跳转到直通车后台的函数
        goto_ztc:function (type, campaign_id, adgroup_id, word) {
            var baseUrl = "http://new.subway.simba.taobao.com/#!/";
            var url = '';
            switch (type) {
                case 1: //添加计划
                    url = baseUrl + 'campaigns/standards/add';
                    break;
                case 2: //添加广告组
                    url = baseUrl + 'campaigns/standards/adgroups/items/add?campaignId=' + campaign_id;
                    break;
                case 3: //添加推广创意
                    url = baseUrl + 'campaigns/standards/adgroups/items/creative/add?adGroupId=' + adgroup_id + '&campaignId=' + campaign_id;
                    break;
                case 4: //管理推广创意
                    url = baseUrl + 'campaigns/standards/adgroups/items/detail?tab=creative&campaignId='+ campaign_id + '&adGroupId=' + adgroup_id;
                    break;
                case 5: //关键词流量解析
                    url = baseUrl + 'tools/insight/queryresult?kws=' + encodeURIComponent(word);
                    break;
                case 6://直通车充值
                    url = baseUrl + 'account/recharge';
                    break;
            }

            if (url !== ''){
                if (type != 5 && type != 2){
                    PT.alert('亲，如果在后台作了修改，请记得同步到精灵哟!');
                }
                window.open(url, '_blank');
            }
        },
        sync_result:function(msg){
            PT.hide_loading();
            msg+='即将刷新页面';
            PT.confirm(msg,function(){window.location.reload();});
        },
        attention_check_confirm:function () {
            PT.confirm('关键词报表尚未下载完，是否现在下载数据？',attention_check,[],this);
        },
        attention_check_redirect:function(){
            window.location.href="/web/attention_list";
        },
        open_msg_back:function(data) {
            template.isEscape = false;
            var modal_str = template.compile(pt_tpm['msg_dialog.tpm.html'])(data);
            $('#id_msg_template').html(modal_str);
            $('#msg_modal_dialog').modal();
        }
    };
}();

