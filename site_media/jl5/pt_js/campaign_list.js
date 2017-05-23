PT.namespace('Campaign_list');
PT.Campaign_list = function () {
    var checked_count = 0;
    var init_sort=function(idx){
    	if(idx == null || idx == undefined)
    		idx = 3
        PT.campaign_table=$('#campaign_table').dataTable({
            //"bRetrieve": true, 允许重新初始化表格
            "bPaginate": false,
            "bFilter": false,
            "bInfo": false,
            "sDom":"",
            "aaSorting":[[idx,'desc']],
            "oLanguage": {
                "sZeroRecords": "亲，您还没有开启推广计划"
            },
            "bAutoWidth":false,
            "aoColumns": [{
                "bSortable": false
            }, {
                "bSortable": false
            }, {
                "bSortable": false
            }, {
                "bSortable": false,
                "sSortDataType": "dom-text",
                "sType": "numeric",
                "sClass": "no_back_img"
            }, {
                "bSortable": false,
                "sSortDataType": "dom-text",
                "sType": "numeric",
                "sClass": "no_back_img"
            }, {
                "bSortable": false,
                "sSortDataType": "dom-text",
                "sType": "numeric",
                "sClass": "no_back_img"
            }, {
                "bSortable": false,
                "sSortDataType": "dom-text",
                "sType": "numeric",
                "sClass": "no_back_img"
            }, {
                "bSortable": false
            }, {
                "bSortable": false
            }]
        });
    };

    var init_dom=function () {
    
        //启用、暂停、新建计划
        $(document).on('click', '.update_camp', function() {
            var mode = parseInt($(this).attr('mode')),
                camp_id_arr = [],
                mode_str = mode? '启动推广': '暂停推广';
            if($(this).hasClass('single')){
                camp_id_arr = [parseInt($(this).parents('tr').attr('id'))];
                update_camp_status(mode, camp_id_arr);
                return;
            }
            var objs = $('#campaign_table tbody input:checked');
            objs.each(function(){
                camp_id_arr.push(parseInt($(this).val()));
            });
            if (camp_id_arr.length) {
                PT.confirm('确认'+mode_str+'所选的'+ camp_id_arr.length +'个计划吗？',update_camp_status,[mode,camp_id_arr]);
            } else {
                PT.alert('请选择要操作的计划');
            }
        });
    };

    // var init_help=function(){
    //  var help_list=([
    //      {
    //          element:'#campaign_table td:eq(1)',
    //          content:'1/2 点铅笔可编辑标题,点击图表可以查看趋势',
    //          placement:'right'
    //      },
    //      {
    //          element: "#campaign_table td:eq(2)",
    //          content: "2/2 这里点铅笔是修改计划限额",
    //          placement:'top'
    //      }
    //  ]);
    //  PT.help(help_list);
    // }

    $('#campaign_select_days').on('change',function(e,v){
    	PT.show_loading('正在获取数据');
        PT.sendDajax({'function':'web_get_campaign_list','last_day':v});
    });

    var update_camp_status = function(mode, camp_id_arr) {
        PT.sendDajax({'function':'web_update_camps_status','camp_id_list':camp_id_arr,'mode':mode,'name_space':'Campaign_list'});
    };

    //发送请求获取数据
    var get_date=function (){
        PT.show_loading('正在获取数据');
        PT.sendDajax({'function':'web_get_campaign_list','last_day':0});
    };

    var update_checked_count=function() {
        checked_count = $('input[class*="kid_box"]:checked').length;
        $('#checked_count').text(checked_count);
    };

    //给修改计划日限额的弹窗弹中的"确定"和"取消"加上关闭弹窗件
    var budget_popover_after=function (){

        budget_popover_set(this);

        $('.tips').tooltip({
          html: true
        });

        //控制日限额显示，当选中不限时隐藏下面的框
        $('#edit_budget_box').find('input[name="budget_radio"]').click(function(){
            if($(this).val()=='1'){
                $('#put_setting').show();
                $('#budget_value').attr('disabled',false);
            }else{
                $('#put_setting').hide();
                $('#budget_value').attr('disabled',true);
            }
        });
    };

    //页面显示时设置弹出层显示状态是不限制日限额还是已设置
    var budget_popover_set=function (iDom){
        var budget=parseInt($(iDom).prev().text());
        if(!isNaN(budget)){
            var smooth=parseInt($(iDom).parent().find('[id^="is_smooth"]').val());
            $('#set_budget').attr('checked',true);
            $('#budget_value').val(budget);
            $('#put_setting').find('[name="smooth_radio"]').eq(smooth).attr('checked',true);
        }else{
            $('#noset_budget').attr('checked',true);
            $('#put_setting').hide();
            $('#budget_value').attr('disabled',true);
        }
    };

    var modify_camp_budget=function (){
        var budget,
            use_smooth=true,
            camp_id=$(this).parents('tr').attr('id'),
            is_set_budget=parseInt($('input[name="budget_radio"]:checked').val());
        //判断是否设置日限额
        if(is_set_budget){
            budget=$('#budget_value').val();
            use_smooth=$('#put_setting').find('[name="smooth_radio"]').eq(1).attr('checked')=='checked';
            if(!check_budget(budget)){
                return false;
            }
        }else{
            budget=20000000;
        }
        PT.show_loading('正在修改计划日限额');
        PT.sendDajax({
            'function':'web_modify_camp_budget',
            'camp_id':camp_id,
            'budget':parseInt(budget,10),
            'use_smooth':use_smooth
        });
        return true;
    };

    var check_budget=function (budget){
        var re=/^[1-9]+[0-9]*]*$/ ;
        if(budget===''){
            PT.alert('日限额不能为空');
            return false;
        }
        if(parseInt(budget)>=100000){
            PT.alert('<div style="text-indent:2em">日限额不能超过10万元 ! </div></br><div style="text-indent:2em">因为淘宝只允许第三方软件修改日限额最大为10万，如果您确定要修改为'+budget+'元，请到直通车后台修改</div>');
            return false;
        }
        if(parseInt(budget)<30){
            PT.alert('日限额不能低于30元');
            return false;
        }
        if(!re.test(budget)){
            PT.alert('日限额只能为整数');
            return false;
        }
        return true;
    };

    //修改标题弹出层显示后调用
    var title_popover_after=function (){

        title_popover_set(this);

    };

    //设置弹出默认计划名称
    var title_popover_set=function (obj){
        $('#edit_title_input').val($(obj).prev().text());
    };

    //设置计划标题
    var modify_camp_title=function (){
        var old_title=$(this).prev().text(),
            new_title=$('#edit_title_input').val(),
            camp_id=$(this).parents('tr').attr('id');
        if(check_camp_title(old_title,new_title,this)){
            PT.show_loading('正在修改计划名称');
            PT.sendDajax({
                'function':'web_modify_camp_title',
                'camp_id':camp_id,
                'new_title':new_title
                });
            return true;
        }else{
            return false;
        }
    };

    //检测输入标题是否合法
    var check_camp_title=function (old_title,new_title,obj){
        if($.trim(new_title)==''){
            PT.alert('标题不能为空');
            return false;
        }
        if(old_title==new_title){
            $.alert({
              backdrop:false,
              body:'标题没有修改过哦！'
            });
            return false;
        }
        return true;
    };
    
    //开启时实引擎
	var open_rt_engine = function(){				
		var camp_id = $(this).attr('camp_id');
        var title = '实时优化引擎设置';
        var desc_str = '实时优化引擎会自动优化有实时数据的关键词。当全自动托管和实时优化同时开启，实时引擎会覆盖全自动优化过的关键词出价；但实时引擎优化过的关键词，全自动引擎在当日不会再改价。'
        var price_desc = '建议设在0.80~5.00元之间';        
        	            
        var body_str='<div><span>' + desc_str + '</span></div><div class="input-append mt10 mb10"><span class="add-on">关键词最高限价：</span><input class="w60" type="text" id="price"><span class="add-on">元</span></div><span class="gray ml10">(' + price_desc + ')</span>';
        $.confirm({
            backdrop:'static',
            title:title,
            okBtn:'确认开启实时优化',
            width:'middle',
            body:body_str,
            okHide:function(){
                var price = $('#price').val(), error_msg = '';
		        if(price===''||isNaN(price)){
		            error_msg = '关键词最高限价必须是数字！';
		        }else if (Number(price)<0.2||Number(price)>5.00){ // 方便客服设置更低限价
		            error_msg = '关键词最高限价必须介于0.20~5.00元之间！';
		        }else if(camp_id===''||isNaN(camp_id)){
		        	error_msg = '参数错误 ，请刷新页面后再试试吧~';
		        }else{				
		            PT.sendDajax({'function':'web_set_camp_limit_price','camp_id':camp_id,'limit_price':Number(price),'flag':1});
		        }
                if (error_msg) {
                    $.alert({ title:'填写错误', body:error_msg, width:'small' });	                       
                }	                    
            }
        });
	}

  	//关闭时实引擎
	var close_rt_engine = function(){			
		var camp_id = $(this).attr('camp_id'); 
		PT.confirm("确定要关闭时实优化吗？",function(){
			PT.show_loading('正在停止...');					
        	PT.sendDajax({'function':'web_set_camp_limit_price','camp_id':camp_id,'limit_price':0,'flag':0});
		});		
	}

    //用于ajax调用之后初始化dom元素,避免使用live方法
    var ajax_init_dom=function (){

        var title_popover_temp='<input id="edit_title_input" type="text" class="m-wrap" maxlength="20" style="width:260px; height:15px;"/>';

        $('.edit_budget').click(function(){
          var that=this;
          $.confirm({
            backdrop: 'static',
            bgColor: '#000',
            title:'修改计划日限额',
            body:pt_tpm['home_camp_budget.tpm.html'],
            show:$.proxy(budget_popover_after,that),
            okHide:$.proxy(modify_camp_budget,that)
          });
        });

        $('.edit_title').click(function(){
          var that=this;
          $.confirm({
            backdrop: 'static',
            width:'small',
            bgColor: '#000',
            title:'修改计划标题（不超过20个汉字）',
            body:title_popover_temp,
            show:$.proxy(title_popover_after,that),
            shown:function(){
                $(this).html();
            },
            okHide:$.proxy(modify_camp_title,that)
          });
        });
      
        $('.edit_rt_price').on('click', open_rt_engine);

        $('.js_show_trend').click(function(){
            var camp_id=$(this).parents('tr').attr('id');
            PT.sendDajax({'function':'web_show_camp_trend','camp_id':camp_id});
        });

        // 复选框事件
        $('.father_box').click(function(){
            var area_id=$(this).attr('link'),
                kid_box=$('#'+area_id).find('input[class*="kid_box"]'),
                now_check=this.checked;
            kid_box.each(function(){
                if (this.checked!=now_check) {
                    this.checked=now_check;
                    $(this).parent().toggleClass('bg_silver');
                }
            });
            // update_checked_count();
        });

        $('input[class*="kid_box"]').click(function(){
            // update_checked_count();
            $(this).parent().toggleClass('bg_silver');
            var all_num = $('input[class*="kid_box"]').length;
            var checked_num = $('input[class*="kid_box"]:checked').length;
            if(all_num == checked_num)
            	$('.father_box').attr("checked", true);
            else
            	$('.father_box').attr("checked", false);  
        });

        $('.tips').tooltip({
          html: true
        });

        $('.change_camp_mnt').on('click', function(){
            var jq_tr = $(this).parents('tr'),
                camp_id = jq_tr.attr('id'),
                mnt_type = parseInt(jq_tr.attr('mnt_type')),
                set_flag = parseInt($(this).attr('type'));
            if (set_flag) {
                choose_mnt_campaign(camp_id);
            }else{
                var body_str="1、系统会停止托管您的宝贝，但不会改变当前计划的推广状态<br/>2、您可以重新开启，但需要重新选择计划和宝贝等等";
                $.confirm({
                    backdrop:'static',
                    title:'确认【取消托管】该计划吗？',
                    body:body_str,
                    okBtn:'取消托管',
                    cancelBtn:'不取消托管',
                    okHide:function(){
                        PT.sendDajax({'function':'mnt_mnt_campaign_setter','campaign_id':camp_id,'set_flag':0,'mnt_type':mnt_type, 'namespace':'Campaign_list'});
                    }
                });
            }
        });

        $('.choose_mnt_campaign').on('click', function(){
            choose_mnt_campaign(0);
        });
    };

    var choose_mnt_campaign = function(camp_id) {
        var blank_mnt_index = $('a[blank_mnt_index]:eq(0)').attr('blank_mnt_index'),
            init_url = '/mnt/choose_mnt_campaign/'+blank_mnt_index,
            jump_url = camp_id? init_url+'?campaign_id='+camp_id: init_url;
        if(blank_mnt_index === undefined) {
            var jq_a = $('a[name=upgrade]');
            if (jq_a.length > 0) {
//                $('a[name=upgrade]').eq(0).click();
                window.open('/web/upgrade_suggest/?referer=upgrade&item_code=ts-25811-1');
            } else {
                PT.alert('最多只能开启4个托管引擎');
            }
            return;
        }
        window.location.href = jump_url;
    };

    return {

        //main function to initiate the module
        init: function (){
            get_date();
            init_dom();
        },
        append_table_data:function(data, last_day, is_rt_camp){
            var tr_str='',table=$('#campaign_table'),total_camp_count;
            for (var d in data){
                if(!isNaN(d)){
                    tr_str+=template.compile(pt_tpm[table.data().target])(data[d]);
                }
            }
            total_camp_count=data.length;
            PT.hide_loading();
            if(PT.hasOwnProperty('campaign_table')){
                PT.campaign_table.fnDestroy(); //删除datetable
            }
            table.find('tbody tr').remove();
            table.find('tbody').append(tr_str);
            //table.show();
           
            $('#total_camp_count').text(total_camp_count);
            ajax_init_dom();
            //App.initTooltips();
            //init_help();
            
            var sort_idx;
            if(is_rt_camp == 0){
            	$('.li_rt_camp').addClass('hide');
        		$('.rt_colum').addClass('hide');
				$('.n_colum').removeClass('hide');
				sort_idx = 3;
				if(last_day > 0)
					$('.rt_camp_title').html('过去' + last_day + '天');
				else
					$('.rt_camp_title').html('过去1天');
        	}else{
            	if(last_day > 0){
					$('.rt_colum').addClass('hide');
					$('.n_colum').removeClass('hide');
					sort_idx = 3;
				}else{
					$('.li_rt_camp').removeClass('hide');
					$('.rt_camp_title').html('今日实时');
					$('.rt_colum').removeClass('hide');
					$('.n_colum').addClass('hide');
					sort_idx = 5;
				}
			}            
            init_sort(sort_idx);
			$('.open_rt').on('click', open_rt_engine);
			$('.close_rt').on('click', close_rt_engine);
        },
        set_camp_limit_price_call_back:function(result){
            PT.hide_loading();
            if(result.status){
            	if(result.flag == 1){
	            	$('.open_rt[camp_id=' + result.camp_id + ']').addClass('hide');
	        		$('.close_rt[camp_id=' + result.camp_id + ']').removeClass('hide');
	        		$('.lbl_rt_start[camp_id=' + result.camp_id + ']').show();
	        		$('.lbl_rt_stop[camp_id=' + result.camp_id + ']').hide();
	        		var html = '<div class="div_rt_price" camp_id=' + result.camp_id + ' >实时限价￥' + result.limit_price 
	        		html += '<i class="iconfont ml5 hover-show edit_rt_price" camp_id=' + result.camp_id + ' >&#xe60e;</i></div>'	
	        		$('.div_rt_price[camp_id=' + result.camp_id + ']').html('');
	        		$('.div_rt[camp_id=' + result.camp_id + ']').append(html);
	        		$('.edit_rt_price[camp_id=' + result.camp_id + ']').on('click', open_rt_engine);	        		
	                PT.light_msg('精灵提示','实时优化开启成功！');
                }else if(result.flag == 0){
                	$('.open_rt[camp_id=' + result.camp_id + ']').removeClass('hide');
	        		$('.close_rt[camp_id=' + result.camp_id + ']').addClass('hide');
	        		$('.lbl_rt_start[camp_id=' + result.camp_id + ']').hide();
	        		$('.lbl_rt_stop[camp_id=' + result.camp_id + ']').show();	  
	        		$('.div_rt_price[camp_id=' + result.camp_id + ']').remove();
	                PT.light_msg('精灵提示','实时优化己经停止！');
                }
            }else{
                PT.alert(result.err);
            }
        },
        modify_title_call_back:function(result){
            PT.hide_loading();
            if(result.status){
                PT.light_msg('修改计划名称','修改计划名称成功！');
                $('#title_'+result.camp_id).text(result.new_title);
            }else{
                PT.alert(result.err);
            }
        },
        modify_budget_call_back:function(result){
            PT.hide_loading();
            if(result.status){
                var budget_hide=$('#budget_value_hide_'+result.camp_id);
                var budget_show=$('#budget_value_show_'+result.camp_id);
                if(result.budget<20000000){
                    budget_hide.text(result.budget);
                    budget_show.text(result.budget+'元');
                }else{
                    budget_hide.text(result.budget);
                    budget_show.text('不限');
                }

                $("#is_smooth_"+result.camp_id).val(result.use_smooth=='true'?1:0);

                PT.campaign_table.fnDestroy();//日限额改变后重新加载datatable
                init_sort();
                PT.light_msg('修改日限额','修改日限额成功！');
            }else{
                PT.alert(result.err);
            }
        },
        update_status_back:function(mode, success_id_list){
            PT.hide_loading();
            if (success_id_list.length === 0) {
                PT.alert('修改失败：淘宝接口不稳定，请稍后再试');
                return;
            }
            if (mode) {
                for(var i=0; i<success_id_list.length; i++) {
                    var camp_id = success_id_list[i],
                        jq_tr=$('#'+camp_id),
                        jq_oper = jq_tr.find('.update_camp');
                    jq_tr.removeClass('silver');
                    jq_oper.prev().removeClass('red').text('推广中');
                    jq_oper.attr('mode', 0).text('暂停');
                }
            } else {
                for(var i=0; i<success_id_list.length; i++) {
                    var camp_id = success_id_list[i],
                        jq_tr=$('#'+camp_id),
                        jq_oper = jq_tr.find('.update_camp');
                    jq_tr.addClass('silver');
                    jq_oper.prev().addClass('red').text('已暂停');
                    jq_oper.attr('mode', 1).text('开启');
                }
            }

        },
        show_camp_trend:function(camp_id, category_list, series_cfg_list) {
            var cmap_title = $('#title_'+camp_id).text(),timer;
            // $.alert({
            //   title:cmap_title,
            //   body:'<div id="camp_trend_chart"></div>',
            //   width:'large',
            //   height:'400px',
            //   okBtn: '关闭',
            //   shown:function(){PT.draw_trend_chart( 'camp_trend_chart' , category_list, series_cfg_list);}
            // });
            if (!$('#modal_camp_trend').length){
                $('body').append(pt_tpm["modal_camp_trend.tpm.html"]);
            }
            $('#camp_trend_title').text(cmap_title);
            PT.draw_trend_chart( 'camp_trend_chart' , category_list, series_cfg_list);
            $('#modal_camp_trend').modal();
        },
        close_redicet:function(camp_id) {
            var jq_tr = $('#'+camp_id),
                new_url = '/web/adgroup_list/'+camp_id,
                mnt_index = jq_tr.attr('mnt_index');
            $('#main_nav li.mnt_index:eq('+(Number(mnt_index)-1)+') a').attr('blank_mnt_index', mnt_index).html(mnt_index+'号引擎[未启动]');
            jq_tr.attr({'mnt_type':0, 'mnt_index':0});
            jq_tr.find('.is_mnt').hide();
            jq_tr.find('.no_mnt').fadeIn();
            $('#title_'+camp_id).attr('href', new_url);
            PT.light_msg('托管状态修改','取消托管成功');
        }
    };
}();
