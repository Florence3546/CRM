//PT是paithink的缩写，以此缩写开创一个命名空间
var PT = function() {
    return {
        namespace: function(ns) {
            var parts = ns.split("."),
            	object = this,
				i, len;
            for (i = 0, len = parts.length; i < len; i++) {
                if (!object[parts[i]]) {
                    object[parts[i]] = {};
                }
                object = object[parts[i]];
            }
            return object;
        },
        alert: function(msg, color , call_back , argv ,that, millsec) {
		//自定义Alert()信息
            var handle = $('#modal-alert');
            handle.find('.modal-body').html(msg);
            color ? handle.find('button:last').attr('class', 'btn ' + color) : 'blue';
            handle.find('button').unbind('click').click(function(){
				return function(){
					millsec = millsec!=undefined?millsec:600;
					setTimeout(function(){
						if(call_back != undefined && call_back instanceof Function){
							if(that == undefined){
								that=null;
							}
							call_back.apply(that,argv);
						}
					}, millsec);
				}
            }());
            handle.modal({
                backdrop: 'static'
            })
        },
        confirm: function(msg, call_back, argv, that, cancel_call_back, cancel_argv, cancel_that, btn_text_list) {
		//自定义confirm()信息
            var handle = $('#modal-confirm');
            handle.find('.modal-body').html(msg);
			if(btn_text_list&&btn_text_list[0]!=undefined){
				handle.find('button:eq(1)').text(btn_text_list[0]);
			}else{
				handle.find('button:eq(1)').text('确定');
			}

			if(btn_text_list&&btn_text_list[1]!=undefined){
				handle.find('button:eq(2)').text(btn_text_list[1]);
			}else{
				handle.find('button:eq(2)').text('取消');
			}

            handle.find('button:eq(1)').off('click').on('click', function(){
				return function(){
					setTimeout(function(){
						if(call_back != undefined && call_back instanceof Function){
							if(that == undefined){
								that=null;
							}
							call_back.apply(that,argv);
						}
					},600)
				}
			}());
            handle.find('button:eq(2)').off('click').on('click', function(){
				return function(){
					setTimeout(function(){
						if(cancel_call_back != undefined && cancel_call_back instanceof Function){
							if(cancel_that == undefined){
								cancel_that=that;
							}
							cancel_call_back.apply(cancel_that,cancel_argv);
						}
					},600)
				}
			}());
            handle.modal({
                backdrop: 'static'
            })
        },
        sendDajax: function(jdata) {
		//统一ajax请求接口,发起ajax请求jdata中至少要有一个参数且名字为function,例:sendDajax({'function':'test'})
		//如果有别的参数直接传jsaon 例子:sendDajax({'function':'test','day':1})
            if (!jdata.hasOwnProperty('function')) {
                $('#center_tip_popup').hide();
                PT.alert('sendDajax:缺少必要参数[function]','red');
                return false;
            }
            var q, data = {}, mArray = jdata['function'].split('_');
            for (q in jdata) {
                data[q] = jdata[q];
            }
            data['function'] = mArray.slice(1).join('_');
            Dajax.dajax_call(mArray[0], 'route_dajax', data);
        },
		show_loading: function(msg,lock){
        //显示全屏tip消息，并锁定屏幕，禁止滚屏
			var obj=$('#full_screen_tips');
			obj.find('.msg').text(msg+'，请稍候...');
			if(lock){
				$('body').addClass('modal-open'); //锁定屏幕，禁止滚屏
			}
			obj.show();
		},
		hide_loading: function(msg){
		//隐藏全屏tip消息
			if($('.modal-backdrop').length==1){
				$('body').removeClass('modal-open');
			}
			$('#full_screen_tips').hide();

		},
		initDashboardDaterange: function (){
		//日期插件
		$('.dashboard-date-range').daterangepicker({
				ranges: {
					'昨天': [1],
					'过去2天': [2],
					'过去3天': [3],
					'过去5天': [5],
					'过去7天': [7],
					'过去10天': [10],
					'过去14天': [14],
					'过去15天': [15]
				},
				call_back:function(value,form) {
				//这里相当于select的change事件
					//PT.show_loading('正在查询');
					if(form.attr('post_mode')=='ajax'){
						var post_fuc=form.attr('post_fuc');
						var fuc_arr=post_fuc.split(".");
						setTimeout(function(){
							window[fuc_arr[0]][fuc_arr[1]][fuc_arr[2]](value);
						},17);

					}else{
					form[0].submit();
					}
				}
			})
		},
		light_msg:function(title,text,time,direction,class_name) {
		/**
		* class_name: gritter-light 白色
		* direction: 控制方向
		*/
			!time?time=8000:'';
			!class_name?class_name='my-sticky-class':'';
			!direction?direction='top-right':'';
			$.extend($.gritter.options, {
				position: direction
			});
			var comm_gritter=$.gritter.add({
				title: title,
				text: text,
				sticky: true,
				class_name: class_name
			});
			setTimeout(function () {
				$.gritter.remove(comm_gritter, {
					fade: true,
					speed: 'slow'
				});
			}, time);
		},
		true_length:function (str){
		//获取中英混合真实长度
			var l = 0;
			for (var i = 0; i < str.length; i++) {
				if (str[i].charCodeAt(0) < 299) {
					l++;
				}
				else {
					l += 2;
				}
			}
			return l;
		},
		truncate_str_8true_length: function (str, l) {
			//根据指定的中英混合真实长度截断字符串
			if (PT.true_length(str)<=l) {
				return str;
			} else {
				var ll = 0;
				for (var i = 0; i < str.length; i++) {
	                if (str.charCodeAt(i) < 299) {
	                    ll++;
	                }
	                else {
	                    ll += 2;
	                }
	                if (ll > l - 2) {
		                return str.slice(0, i) + '...';
	                }
				}
			}
		},
		console:function (msg){
			//浏览器控制台输出信息，便于调试和测试
			//var dt=new Date();
			//console.log(msg+' time:'+dt.getTime());
		},
    	get_yaxis_4list:function (data) {
			var yaxis_list=[];
			for (var i=0; i<data.length; i++) {
				if (data[i].is_axis==0) {
					continue;
				}
				yaxis_list.push({'gridLineWidth' : 1,
								'title' : { 'text':'', 'style':{'color': data[i].color } },
								'labels' : { 'formatter': function() {var temp_unit=data[i].unit;return function(){return this.value+temp_unit};}(), 'style': {'color': data[i].color}},
								'opposite' : data[i].opposite
									});
			}
			return yaxis_list;
		},
		get_series_4list:function (data) {
			var series_list=[];
			for (var i=0; i<data.length; i++) {
				series_list.push({ 'name' : data[i].name,
											'color': data[i].color,
											'type': 'line',
											'yAxis' : data[i].yaxis,
											'data': data[i].value_list,
											'visible' : data[i].visible
										});
			}
			return series_list;
		},
		draw_trend_chart:function (id_container,category_list,series_cfg_list) {
			var chart = new Highcharts.Chart({
				chart: {renderTo: id_container,zoomType: 'xy',animation:true},
				title: {text: ''},
				subtitle: {text: ''},
				xAxis: [{categories: category_list}],
				yAxis: PT.get_yaxis_4list(series_cfg_list),
				tooltip: {
					formatter: function() {
						var obj_list = chart.series;
						var result = this.x +'日 '+"<br/>";
						for(var i = 0;i<obj_list.length;i++){
							if(obj_list[i].visible){
								result = result+(obj_list[i].name)+" "+obj_list[i].data[this.point.x].y+(series_cfg_list[i].unit)+"<br/>"
							}
						}
						return result;
					}
				},
				legend: {backgroundColor: '#FFFFFF'},
				series: PT.get_series_4list(series_cfg_list)
			});
    	},
		get_events_namespace:function(dom,type){
			var events=$(dom).data('events')[type],i,name_list=[];
			for(i in events){
				name_list.push(events[i].namespace);
			}
			return name_list;
		},
		help:function(msg_list){
			if(!$.browser.webkit&&$.browser.msie&&Number($.browser.version)<7){
				return;
			}
			if (typeof window.Tour!=undefined){
				var storage=window.localStorage;
				var key=document.body.id.replace('pt_','');
				if(storage.getItem('PT_tour') == null){
					storage.setItem('PT_tour','')
				}
				if(storage.getItem('PT_tour').indexOf(key)==-1){
					var help=new Tour({backdrop:true});
					help.addSteps(msg_list);
					help.restart(true);
					storage.setItem('PT_tour',storage.getItem('PT_tour')+'~'+key);
				}
			}
			return help;
		}
    }
}();

PT.namespace('Base');
PT.Base = function () {
	var url='';

	var init_dom=function() {

		$('#contact_consult').hover(function(){
			$('#contact_telephone').stop().animate({'marginLeft':0},300);
		},function(){
			$('#contact_telephone').stop().animate({'marginLeft':-181},100);
		});

		$('a[name=upgrade]').click(function(){
		    //这里只好将url固定了
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
        /*
		$('#sync_increase_data').click(function() {
			PT.show_loading('正在下载增量数据');
			PT.sendDajax({'function':'web_sync_increase_data'});
		});

		$('#sync_rpt_data').click(function(){
			PT.show_loading(sync_all(1,15));
		});

		$('#sync_base_data').click(function(){
			PT.show_loading(sync_all(2));
		});*/

		$('.open_feedback_dialog').click(function(){
			if($(this).attr('switch')==undefined){
				PT.sendDajax({'function':'web_open_feedback_dialog'});
				$(this).attr('switch',1);
			}else{
				$('#feedback_modal_dialog').modal();
			}
		});

		//完善用户信息
		$('.open_info_dialog').click(function(){
			PT.sendDajax({'function':'web_open_info_dialog'});
        });

		$(document).on('click','#open_msg',function() {
            if($(this).attr('switch')==undefined){
				PT.show_loading('正在获取我的消息');
				PT.sendDajax({'function':'web_open_msg_dialog'});
				$(this).attr('switch',1);
			}else{
				$('#msg_modal_dialog').modal();
			}
		});

		$(document).on('click','.dialog_close_msg',function() {
			eval("var data="+$(this).attr("data"));
			var is_common=data.is_common,msg_id=data.msg_id,type=is_common==1? 'common' : 'user',jq_count=$('#'+type+'_prompt_count'),prompt_count=jq_count.text().slice(1,-1);
			if ( prompt_count > 1) {
				jq_count.text('（'+(prompt_count-1)+'）');
			}	else {
				jq_count.addClass('hide').text('（0）');
			}
			$('#'+msg_id+'_'+is_common).parents('.accordion-group:first').remove();//删除首页相对应的公告
			$('#dot_'+msg_id).removeClass('r_color').addClass('s_color');
			$(this).removeClass('dialog_close_msg');
			PT.sendDajax({'function':'web_close_msg','msg_id':msg_id,"is_common":is_common});
		});

		$(document).on('click','#msg_modal_dialog .close',function() {
			var user_prompt_count=$('#user_prompt_count').text().slice(1,-1),
				common_prompt_count=$('#common_prompt_count').text().slice(1,-1),
				total_prompt_count=Number(user_prompt_count)+Number(common_prompt_count);
			if (total_prompt_count>0) {
				$('#prompt_msg_count').text(total_prompt_count);
			}else{
				$('#prompt_msg_count').parent().remove();
			}
			$('#msg_modal_dialog').modal('hide');
		});

		$(document).on('click','#submit_btn',function(){
			var content=$('#id_content').val();
			if(content=='您的意见，是我们进步的最大动力。'){
				content='';
			}
			if(content==''){
				PT.alert('麻烦您不吝赐教，输入您的建议');
				return false;
			}
			PT.show_loading('感谢您的反馈');
			var scores = $('input[id^=id_raty_]'),
				score_list=[];
			for(var i =0;i<scores.length;i++){
				var temp_id = $(scores[i]).attr('id'),
					id = temp_id.slice(0,temp_id.indexOf('-score')).replace('_raty','');
				score_list.push([ id.slice(3), Number($(scores[i]).val()) ]);
			}
			PT.sendDajax({'function':'web_submit_feedback','score_str':$.toJSON(score_list),'content':content});
		});

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
			if (unread_count==0) {
				$('.open_comment[obj_id='+ jq_modal.attr('obj_id') +']').remove();
			}
			jq_modal.modal('hide');
		});

		// $(document).on('click', '#id_get_code', function(){
		//     var phone = $('#id_phone').val();
		//     if(phone =='' ||phone ==undefined){
		//         PT.alert("请输入手机号！");
		//         return false;
		//     }
		//     else if(isNaN(phone) || !(/^1[3|4|5|8]\d{9}$/.test(phone))){
		//         PT.alert("手机号码的格式不对！");
		//         return false;
		//     }
		//     else{
		//         $('#sms_result').text("正在发送短信，请稍等...");
		//         $('#id_loading').removeClass('hide');
		//         PT.sendDajax({'function':'web_get_phone_code','phone':parseInt(phone)});
		//     }
		// });

		/*
		$(document).on('blur', '#id_phone_code', function(){
		    var code = $('#id_phone_code').val();
		    if(!/^[1-9]\d{4}$/.test(code)){
                PT.alert("请输入正确的手机验证码！");
                $('#id_submit_info').addClass('disabled');
                return false;
            }
            else{
                $('#id_submit_info').removeClass('disabled');
            }
		});*/

		$(document).on('click', '#id_current_nick', function(){
		   $('#id_ww').val($('#id_nick').val());
		});

		$(document).on('click', '#id_submit_info', function(){
		    if($(this).hasClass('disabled')){
		        return false;
		    }
		    var ww = $('#id_ww').val();
		    var qq = $('#id_qq').val();
		    var phone = $('#id_phone').val();
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
		});

		//当鼠标经过该元素时，加上hover这个class名称，修复ie中css的hover动作
		if(!$.browser.msie||Number($.browser.version)>8){
			$(document).on('mouseover.PT.e','*[fix-ie="hover"]',function(){
				$(this).addClass('hover');
				$(this).mouseout(function(){
					$(this).removeClass('hover');
				});
			});
		}

		//关联td和里面的checkbox事件
		$(document).on('click','.link_inner_checkbox',function(e){
			e.stopPropagation();
			if(this==e.target){
				$(this).find('input[type="checkbox"]').click();
			}
		});

		!function(){
			var obj=$('.page-sidebar-menu');
			if(!obj.length){
				return;
			}
			var ele_height=obj.height(),nav_height=$('.header.navbar').height();
			var visible_height=$(window).height();

			if((visible_height-nav_height)<ele_height){
				$(window).scroll(function(){
					var base_top= document.body.scrollTop | document.documentElement.scrollTop;
					if(base_top<=(ele_height-visible_height+150)){
						obj.css({top:-base_top+nav_height});
					}
				});
			}
		}();

	}

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
	}

	var attention_check=function(){
		PT.show_loading("正在下载关键词报表");
		window.location.href = "/web/attention_list";
	}

	return {
        init: function (){
			init_dom();
        },

		change_msg_count:function() {
			var jq_count=$('#prompt_msg_count'),msg_count=jq_count.text();
			if(msg_count>1){
				jq_count.text(msg_count-1);
			}else{
				jq_count.parent().remove();
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
				PT.alert('提交成功，感谢您的参与！我们会及时处理您的意见' );
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
					url = baseUrl + 'tools/insight-old/queryresult?kws=' + encodeURIComponent(word);
					break;
				case 6://直通车充值
					url = baseUrl + 'account/recharge';
					break;
			}

			if (url != ''){
				if (type != 5 && type != 2){
					PT.alert('亲，如果在后台作了修改，请记得同步到精灵哟!');
				}
				window.open(url, '_blank');
			}
		},
		set_nav_activ:function(index,next){
			//$('.page-sidebar-menu>li').removeClass('active');
			$('.page-sidebar-menu>li:eq('+index+')').addClass('active');
			$('.page-sidebar-menu>li:eq('+index+') .sub-menu li:eq('+next+')').addClass('active')
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
		}
	}
}();

//shift多选用法 1:带回调函数:$select(checkBoxName) 2:带回调 $select({name:checkBoxName,[callBack:fn]})
(function() {
    var arrList = {};
    var $select = window.$select = function(obj) {
        var checkboxName;
        if (typeof (obj) == 'string') {
            checkboxName = obj;
        }
        if (typeof (obj) == 'object') {
            checkboxName = obj.name;
        }

        // Meet the condition of 'checkbox' save into array
        arrList[checkboxName] = getCheckboxArray(checkboxName);

        // Add event for meet the condition of 'checkbox'
		for (var i=0,i_end=arrList[checkboxName].length;i<i_end;i++){
            // Left mouse and shift button event
			!function(){
				var current=arrList[checkboxName][i];
				current.onclick = function() {
					var afterClickStatus = current.checked ? true : false;
					mainFunc(current, arrList[current.name], afterClickStatus, obj);
				}

				// Right mouse event
				current.onmouseup = function(e) {
					var e = window.event || e;
					if (e.button == 2) {
						var afterClickStatus = current.checked ? false : true;
						pressShift = true;
						mainFunc(current, arrList[current.name], afterClickStatus, obj);
						pressShift = false;
					}
				}

				// (For IE) Right mouse event
				current.oncontextmenu = function(event) {
					if (document.all) {
						window.event.returnValue = false;
					} else {
						event.preventDefault();
					}
				}
			}();
		}

        // 当checkbox顺序变了之后调用此函数更新
        selectRefresh = function() {
            setTimeout(function() {
                for (var a in arrList)
                    arrList[a] = getCheckboxArray(a);
            }, 1);
            initSelect();
        }
        //表头变化后重置起止位置
        initSelect = function() {
            startEnd = [null, null];
        }
    }
    function getCheckboxArray(checkboxName) {
        var arr = [];
        var inputs = document.getElementsByTagName("input");
        for (var i = 0; i < inputs.length; i++) {
            if (inputs[i].name == checkboxName && inputs[i].type == "checkbox") {
                arr.push(inputs[i]);
            }
        }
        return arr;
    }

	function getIndex(arr,obj){
        for (var i = 0, index = 0; i < arr.length; i++, index++) {
            if (arr[i] == obj) {
                return index;
            }
        }
	}

    var pressShift = false;
    var startEnd = [null, null];

    function mainFunc(current, arr, afterClickStatus, obj) {
        // Get the index which click element in the 'checkbox' array
        var index = getIndex(arr,current);

        if (startEnd[0] == null)
            startEnd[0] = index;
        // 'shift button' whether is press
        if (pressShift) {
            startEnd[1] = index;
            // If select the 'checkbox' from the down top, reverse the array
            if (startEnd[0] > startEnd[1]) {
                startEnd.reverse();
            }

            // Select the 'checkbox'
            for (var j = startEnd[0]; j <= startEnd[1]; j++) {
				if(!arr[j].disabled){
                	arr[j].checked = afterClickStatus;
				}
            }
            startEnd[0] = startEnd[1];
        }
        startEnd[0] = index;
        if (obj.hasOwnProperty('callBack')) {
            obj.callBack.call(obj.that);
        }
    }
    /*<For left mouse and shift button event>*/
    document.onkeydown = function(e) {
        var e = window.event || e;
        if (e.keyCode == 16) {
            pressShift = true;
        } else {
            pressShift = false;
        }
    }
    document.onkeyup = function() {
        pressShift = false;
    }
})();

/*
//使用方法
var now = new Date();
var nowStr = now.format("yyyy-MM-dd hh:mm:ss");
//使用方法2:
var testDate = new Date();
var testStr = testDate.format("YYYY年MM月dd日hh小时mm分ss秒");
alert(testStr);
//示例：
alert(new Date().Format("yyyy年MM月dd日"));
alert(new Date().Format("MM/dd/yyyy"));
alert(new Date().Format("yyyyMMdd"));
alert(new Date().Format("yyyy-MM-dd hh:mm:ss"));
*/

Date.prototype.format = function(format){
	var o = {
		"M+" : this.getMonth()+1, //month
		"d+" : this.getDate(), //day
		"h+" : this.getHours(), //hour
		"m+" : this.getMinutes(), //minute
		"s+" : this.getSeconds(), //second
		"q+" : Math.floor((this.getMonth()+3)/3), //quarter
		"S" : this.getMilliseconds() //millisecond
	}

	if(/(y+)/.test(format)) {
		format = format.replace(RegExp.$1, (this.getFullYear()+"").substr(4 - RegExp.$1.length));
	}

	for(var k in o) {
		if(new RegExp("("+ k +")").test(format)) {
			format = format.replace(RegExp.$1, RegExp.$1.length==1 ? o[k] : ("00"+ o[k]).substr((""+ o[k]).length));
		}
	}
	return format;
}
