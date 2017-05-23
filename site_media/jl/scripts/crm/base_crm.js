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
        alert: function(msg, color , call_back , argv ,that) {
		//自定义Alert()信息
            var handle = $('#modal-alert');
            handle.find('.modal-body').html(msg);
            color ? handle.find('button:last').attr('class', 'btn ' + color) : 'blue';
            handle.find('button').click(function(){
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

            // 多页选择过滤器，日后可能需要重构 TODO yangrongkai 20140616
            var can_all_select_funcs = [
            	'crm_submit_msg',
            	'crm_open_command_dialog',
            	'crm_send_cmd'
            ]

            var obj = $("#all_selected");
            if (can_all_select_funcs.indexOf(jdata['function']) == -1){
            	if (obj.length > 0){
					if(obj.attr('is_all') == '1'){
						PT.alert('当前功能不支持多页全选，请将 多页全选开关 关闭再试。');
						return PT.hide_loading();
					}
            	}
            } else {
            	if(obj.length == 0){
            		PT.alert('异常，程序员请注意 #all_selected 元素不存在。');
					return PT.hide_loading();
            	}

            	var jump_obj = $("#base_is_jumped");
            	if(jump_obj.length == 0){
            		PT.alert('异常，程序员请注意 #base_is_jumped 元素不存在。');
					return PT.hide_loading();
            	}

            	jdata['use_cache'] = obj.attr('is_all');
            	jdata['page_index'] = obj.attr('page_index');
            	jdata['is_jumped'] = jump_obj.val();
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
			obj.find('span').text(msg+'，请稍候...');
			if(lock){
				$('body').addClass('modal-open'); //锁定屏幕，禁止滚屏
			}
			obj.show();
		},
		hide_loading: function(msg){
		//隐藏全屏tip消息
			$('body').removeClass('modal-open');
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
		console:function (msg){
			//浏览器控制台输出信息，便于调试和测试
			var dt=new Date();
			console.log(msg+' time:'+dt.getTime());
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
	};

	return {
        init: function (){
			init_dom();
        },
		//跳转到直通车后台的函数
		goto_ztc:function (type, campaign_id, adgroup_id, word) {
			var baseUrl = "http://new.subway.simba.taobao.com/#!/";
			var url = '';
			switch (type) {
				case 1: //添加计划
					url = baseUrl + 'campaigns/standards/add';
					break;
				// case 2: //添加广告组
				//	break;
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
 					PT.alert('亲，如果在后台作了修改，请记得同步哟!');
				}
				window.open(url, '_blank');
			}
		},
		set_nav_activ:function(selector){
			$('.nav.main>li').removeClass('active');
			$('.nav.main>li.'+ selector).addClass('active');
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
