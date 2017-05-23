PT.namespace("SelectKeyword");
PT.SelectKeyword = function () {

    var init = function(adgroup_dict) {
		$('ul.main.nav>li').eq(2).addClass('active');
        var adgroup_id = $("#adgroup_id").val();
        var cat_id = $("#cat_id").val();
        var select_type = $("#select_type").val();
        var keyword_count = Number($("#keyword_count_hidden").val()) || 0;
        var max_add_num = 200 - keyword_count;
        init_zeroclipboard();
        
        // 精准淘词功能
        var init_dom_4precise = function () {
            $("#btn_tao_keyword").click(function(){
                var word_filter = $('#word_filter').val();
                if(word_filter==$('#word_filter').attr('placeholder')) word_filter = '';
                if(!word_filter) {
                    PT.alert('亲，请先输入要包含的核心词。');
                    return;
                }
                PT.show_loading('亲，正在淘词');
                PT.sendDajax({'function':'web_select_keyword',
                                         'adgroup_id':adgroup_id,
                                         'cat_id':cat_id,
                                         'select_type':select_type,
                                         'max_add_num':max_add_num,
                                         'word_filter':word_filter
                                         });
            })
            
            //精准淘词【更多】/【收起】按钮点击事件
            $('#div_guess_elemword ul').each(function(){
                var elemword_list = $(this).find('li');
                if(elemword_list.length>10){
                    $(this).append('<button type="button" class="btn mini yellow marr_12 btn_more">更多</button>');
                    $(this).find('li:gt(7)').hide();
                    $(this).on('click', '.btn_more', function(){
                        $(this).siblings().animate({opacity:'show'}, 'slow');
                        $(this).html('收起');
                        $(this).removeClass('btn_more');
                        $(this).addClass('btn_collapse');
                    });
                    $(this).on('click', '.btn_collapse', function(){
                        $(this).siblings('li:gt(7)').animate({opacity:'hide'}, 'slow');
                        $(this).html('更多');
                        $(this).removeClass('btn_collapse');
                        $(this).addClass('btn_more');
                    });
                }
            });
            
            //精准淘词词根点击事件        
            $("#div_guess_elemword li").click(function(){
                var word_filter = $("#word_filter").val();
                word_filter = word_filter.replace(new RegExp($("#word_filter").attr('placeholder')),'');
                var word_list = $.map(word_filter.split(','), function(word){
                    var result = word.split('，');
                    if(result.length>0) return result;
                })
                var elemword = $(this).text();
                if($(this).hasClass("active")){
                    $(this).removeClass("active");
                    word_list = $.map(word_list, function(word){
                        word = $.trim(word).replace(/\s{2, }/, ' ');
                        var temp_list = word.split(' ');
                        var index = $.inArray(elemword, temp_list);
                        if(index>-1) temp_list.splice(index, 1);
                        if(temp_list.length>0) return temp_list.join(' ');
                    })
                    word_filter = word_list.join('，');
                    $("#word_filter").val(word_filter);
                }else{
                    $(this).addClass("active");
                    for(var i=0, j=word_list.length;i<j;i++){
                        var elemword_list = $.trim(word_list[i]).split(" ");
                        if(elemword_list.length>=3){
                            PT.alert("建议您产品词和修饰词加起来不超过三个词！");
                            break;
                        }
                    }
                    $("#word_filter").val(word_filter + " " + elemword);
                }
            })
            
            $("#word_filter").keyup(function(){
                var word_filter = $(this).val();
                var word_list = $.map(word_filter.split(','), function(word){
                    var result = word.split('，');
                    if(result.length>0) return result;
                })
                word_list = $.map(word_list, function(word){
                    word = $.trim(word).replace(/\s{2, }/, ' ');
                    return word.split(' ');
                });
                var elemword_list = $("#div_guess_elemword li")
                for(var i=0, j=elemword_list.length;i<j;i++){
                    var index = $.inArray(elemword_list.eq(i).text(), word_list);
                    if(index>=0){
                        elemword_list.eq(i).addClass("active");
                    }else{
                        elemword_list.eq(i).removeClass("active");                
                    }
                }
            })
        }
        
        // 手工组词
        var init_dom_4combine = function () {
            var prdtword_max_num = 5,
                dcrtword_max_num = 50,
                prmtword_max_num = 50,
                prdtword_list = [],
                dcrtword_list = [],
                prmtword_list = [];
            $('#textarea_prdtword').keyup(function () {
                prdtword_list = $.trim($(this).val()).split('\n');
                prdtword_list = $.map(prdtword_list, function (word) {
                    if (word) {
                        return word;
                    }
                });
                $('#prdtword_count').html(prdtword_list.length);
            });
            $('#textarea_dcrtword').keyup(function () {
                dcrtword_list = $.trim($(this).val()).split('\n');
                dcrtword_list = $.map(dcrtword_list, function (word) {
                    if (word) {
                        return word;
                    }
                });
                $('#dcrtword_count').html(dcrtword_list.length);
            });
            $('#textarea_prmtword').keyup(function () {
                prmtword_list = $.trim($(this).val()).split('\n');
                prmtword_list = $.map(prmtword_list, function (word) {
                    if (word) {
                        return word;
                    }
                });
                $('#prmtword_count').html(prmtword_list.length);
            });
            $('#div_auto_combine_words textarea').trigger('keyup');
	        var check_combine_words = function () {
		        if (prdtword_list.length==0) {
			        PT.alert('亲，产品词至少要有一个！');
			        return false;
		        } else if (prdtword_list.length>prdtword_max_num) {
	                PT.alert('亲，产品词请不要超过'+prdtword_max_num+'个！');
	                return false;
		        } else if (dcrtword_list.length>dcrtword_max_num) {
                    PT.alert('亲，属性词/修饰词请不要超过'+dcrtword_max_num+'个！');
                    return false;
                } else if (prmtword_list.length>prmtword_max_num) {
                    PT.alert('亲，促销词请不要超过'+prmtword_max_num+'个！');
                    return false;
                }
                return true;
	        }
	        $('#btn_auto_combine_words').click(function () {
                if (check_combine_words()) {
	                PT.show_loading('亲，正在组词');
	                PT.sendDajax({'function':'web_select_keyword',
                                             'adgroup_id':adgroup_id,
                                             'cat_id':cat_id,
	                                         'select_type':select_type,
                                             'max_add_num':max_add_num,
							                 'prdtword_list':$.toJSON(prdtword_list),
							                 'dcrtword_list':$.toJSON(dcrtword_list),
							                 'prmtword_list':$.toJSON(prmtword_list)
							                 });
                }
	        });
        }
		
		// 手工加词
		var init_dom_4manual = function () {
			var manword_list = [];
		    $('#textarea_manual').keyup(function () {
			    manword_list = $.trim($(this).val()).split('\n');
			    manword_list = $.map(manword_list, function (word) {
				    if (word) {
					    return word;
				    }
			    });
			    $('#manual_count').html(manword_list.length);
		    });
		    var check_manual_words = function () {
			    if (manword_list.length==0) {
				    PT.alert('亲，请先输入关键词！');
				    return false;
			    }
				return true;
		    }
		    $('#btn_manual_add_words').click(function () {
			    if(check_manual_words()) {
	                PT.show_loading('亲，正在查询');
	                PT.sendDajax({'function':'web_select_keyword',
	                                         'adgroup_id':adgroup_id,
	                                         'cat_id':cat_id,
	                                         'select_type':select_type,
	                                         'max_add_num':max_add_num,
	                                         'manword_list':$.toJSON(manword_list)
	                                         });
			    }
		    });
		}
		
		!function(){
			$('#keyword_count').text(keyword_count);
			$('#can_add_count').text(max_add_num);
			switch (select_type) {
			    case 'quick':
			        PT.show_loading('亲，正在选词');
			        PT.sendDajax({'function':'web_select_keyword',
			                                 'adgroup_id':adgroup_id,
	                                         'cat_id':cat_id,
	                                         'select_type':select_type,
			                                 'max_add_num':max_add_num
			                                 });
			        break;
			    case 'precise':
			        init_dom_4precise();
			        break;
                case 'combine':
                    init_dom_4combine();
                    break;
                case 'manual':
                    init_dom_4manual();
                    break;
			}
		}();
          
        //窗口下拉滚动条时的设置面板定位效果
        $(window).scroll(function(){
            var scrollTop = $(window).scrollTop();
            var fixedBoxTop = $('#fixed_box').offset().top;
            var tableOffsetTop = $('#table_select_keyword thead').offset().top;
            if(scrollTop>fixedBoxTop){
                $('#fixed_box_inner').addClass('active');
                $('#div_bulk_ms_selector').css({position:'fixed', top:116});
                $('.fixedHeader .tooltips').hide();
            }else{
                $('#fixed_box_inner').removeClass('active');
                $('#div_bulk_ms_selector').css({position:'absolute', top:tableOffsetTop+3});
                $('.fixedHeader .tooltips').show();
            }
        })
        
        //选词器【包含】/【不包含】关键词搜索功能
        $("#btn_search").click(function(){
	        var include = $('#include_word').val();
	        var include_list = [];
	        for(var i=0, temp_list1=include.split(',');i<temp_list1.length;i++){
	            for(var j=0, temp_list2 = temp_list1[i].split('，');j<temp_list2.length;j++){
	                if(temp_list2[j]) include_list.push(temp_list2[j]);
	            }            
	        }
	        $('#include_words').val($.toJSON(include_list));
	        var exclude = $('#exclude_word').val();
	        var exclude_list = [];
	        for(var i=0, temp_list1=exclude.split(',');i<temp_list1.length;i++){
	            for(var j=0, temp_list2 = temp_list1[i].split('，');j<temp_list2.length;j++){
	                if(temp_list2[j]) exclude_list.push(temp_list2[j]);
	            }            
	        }
            $('#exclude_words').val($.toJSON(exclude_list));
            update_table_8selector();
        })
        
        //匹配模式切换
        $("#bulk_ms_selector").change(function() {
            var oTable = $('#table_select_keyword').dataTable();
            var match_scope = $(this).val();
            oTable.fnUpdateAllTr(toggle_match_scope, match_scope);
        })
        
        var toggle_match_scope = function (nTr, match_scope) {
            var match_scope_list = [['4', '2', '1'], ['广', '中', '精']];
            var index = match_scope_list[0].indexOf(match_scope);
            if(index==-1) index = 0;
            $(nTr).find('.match_scope').attr('match_scope', match_scope_list[0][index]);
            $(nTr).find('.match_scope').html(match_scope_list[1][index]);
        }
        
        $("html").on('click', '.match_scope', function(){
            var match_scope_list = [['4', '2', '1'], ['广', '中', '精']];
            var match_scope = $(this).attr('match_scope');
            var index = match_scope_list[0].indexOf(match_scope);
            index++;
            if(index>=match_scope_list[0].length) index = 0;
            $(this).attr('match_scope', match_scope_list[0][index]);
            $(this).html(match_scope_list[1][index]);
        });      
    }
    
    var init_help=function(){
		var help_list=[
			{
				element:'#fixed_box_inner .btn-group',
				content:'1/4 拉动滑杆筛选期望的关键词',
				placement:'top',
				onShow:function(){
					setTimeout(function(){$('#fixed_box_inner .btn-group').addClass('open');},0)
					
				},
				onHide:function(){
					$('#fixed_box_inner .btn-group').parent().removeClass('open');
				}	
			},
			{
				element:'#fixed_box_inner>.portlet-body',
				content:'2/4 设置好最高限价后，根据情况调整出价',
				placement:'bottom'	
			},
			{
				element:'#div_bulk_ms_selector',
				content:'3/4 根据情况选择关键词匹配模式',
				placement:'right',
				onShow:function(){
					setTimeout(function(){$('#div_bulk_ms_selector').css('zIndex',9999);},0)
					
				},
				onHide:function(){
					$('#div_bulk_ms_selector').css('zIndex',120);
				}					
			},
			{
				element: "#btn_submit",
				content: "4/4 最后将选择好的关键词提交到直通车",
				placement:'bottom'
			},
			
		];	
		
		PT.help(help_list);		
	}
    
    //初始化选词器面板中的拉杆控件
    var init_sliders = function(filter_field_list){        
        //slider插件只对可见元素正常渲染，对于隐藏元素，jslider需要调用$("#input_XX").slider().update()
        $("#div_sliders").empty();
        
        for(var i=0;i<filter_field_list.length;i++){
            var cfg = filter_field_list[i];
			if(cfg.series_name=='keyword_score'||cfg.series_name=='cat_click'){
				var temp=cfg.current_to,temp2=cfg.limit;
				//cfg.current_to=Number((cfg.current_to-cfg.from)/2)+cfg.from;
				cfg.current_to=cfg.current_from;
				cfg.current_from=cfg.limit;
				cfg.limit=cfg.from;
				cfg.from=temp2;
				if (cfg.heterogeneity) {
					for (var j=0;j<cfg.heterogeneity.length;j++) {
					    var percent_list = cfg.heterogeneity[j].split('/');
					    if (percent_list.length) {
					        percent_list[0]  = 100 - Number(percent_list[0]);
					        cfg.heterogeneity[j] = percent_list.join('/');
					    }
					}
					cfg.heterogeneity = cfg.heterogeneity.reverse();
				}
			}else{
				cfg.current_from=cfg.from;
			}
            var html_slider = template.render('html_slider',{cfg:cfg});
            $("#div_sliders").append(html_slider);
            if(cfg.svl[0]!=cfg.from){
                cfg.svl.unshift(cfg.from);
            }else if(cfg.svl.length==1){
                cfg.svl.push(cfg.from+1);
            }
            //jslider 生成滑块
            if (cfg.series_name=="cat_cpc") {
                $("#"+cfg.series_name).slider({round:2, step:0.01, callback:update_table_8selector, from: cfg.from, to: cfg.limit, limits:false, dimension: '', skin: "plastic", heterogeneity:cfg.heterogeneity||[], scale:[cfg.from,cfg.limit]});
            } else {
                $("#"+cfg.series_name).slider({step:1, callback:update_table_8selector, from: cfg.from, to: cfg.limit, limits:false, dimension: '', skin: "plastic", heterogeneity:cfg.heterogeneity||[], scale:[cfg.from,cfg.limit]});
            }
        }        
    }
    
    //根据选词器中设置的拉杆和过滤字，更新选词表
    var update_table_8selector = function(){
		$('#valid_count').hide().siblings('img').show();
        var oTable = $('#table_select_keyword').dataTable();
        if (!$('#div_selector').attr('active')) {
			$('#div_selector').attr('active', 1);
			$('#valid_count').parent().show().prev().hide();
//	        oTable.fnSort([[0,'asc']]); // dataTable的这个接口有问题，用下面一句替代！
	        $('#table_select_keyword th:eq(0)').click();
	        $('#btn_selector').click();
        } else if ($('#table_select_keyword th:eq(0)').hasClass('sorting_desc')) {
	        $('#table_select_keyword th:eq(0)').click();
	        $('#btn_selector').click();
        }
		oTable.fnDraw();
    }

    //动态生成【快速选词】/【精准淘词】数据表格
    var generate_table = function(all_keyword_list, okay_count, filter_field_list){
        $('#fixed_box').show();
        $('#div_select_keyword').show();
        $('#price_multi').val('1');
        init_sliders(filter_field_list);
        var html_table = template.render('html_keywords_table', {all_keyword_list:all_keyword_list});
        $('#sum_checked').html(okay_count);
        $("#sum_all_keywords").html(all_keyword_list.length);
        var Table = $('#table_select_keyword');
        Table.dataTable().fnDestroy();
        Table.find('tbody').html(html_table);
        var str_header = '.FixedHeader_Cloned:has([aria-describedby="table_select_keyword_info"])';
        $(str_header).remove();
        var oTable = Table.dataTable({'aoColumns':[{'sSortDataType':'dom-checkbox'},
                                                                                  null,
                                                                                  {'sSortDataType':'dom-input', 'sType':'numeric'},
                                                                                  null,
                                                                                  null,
                                                                                  null,
                                                                                  null,
                                                                                  null],
                                                           'aaSorting':[[0, 'desc']],
                                                           'bDestroy':true,
                                                           'iDisplayLength':200,
														   'fnDrawCallback':function (oSettings) {
																						    if ($('#div_selector').attr('active')) {
																							    update_statistic_data();
																						    }
							                                                                if (typeof selectRefresh!='undefined') {
							                                                                    selectRefresh();
							                                                                }
							                                                                $select({name: 'keyword',callBack:update_statistic_data});
							                                                            },
                                                           'oLanguage':{'sInfo':'总共_TOTAL_条记录',
                                                                                  'sInfoEmpty':'',
                                                                                  'sEmptyTable':'亲，没有找到匹配的关键词',
                                                                                  'sZeroRecords':'亲，没有找到匹配的关键词',
                                                                                  'sInfoFiltered': '(从 _MAX_ 条记录中过滤)',
                                                                                  'oPaginate':{'sNext':'下一页', 'sPrevious':'上一页'}
                                                                                  }
                                                           });
        var oSettings = oTable.fnSettings();
        new FixedHeader(oTable,{"offsetTop":112});
        
        //【匹配模式】样式调整
        var temp_top = Table.offset().top+3;
        var temp_left = Table.offset().left + Table.find('th:eq(0)').outerWidth() + 7;
        $('#div_bulk_ms_selector').css({position:'absolute', 'z-index':'120', top:temp_top, left:temp_left});
        init_zeroclipboard();
        PT.hide_loading();
        
        // checkall功能，整表全选
        Table.add(str_header).find('#checkall').unbind('click');
        Table.add(str_header).find('#checkall').click(function(e){
	        e.stopPropagation();
            var checked = this.checked; // 必须赋值给局部变量，否则 $.map 无法取到
	        $.map(oSettings.aiDisplay, function (i) {
		        $(oSettings.aoData[i].nTr).find('[name="keyword"]').attr('checked', checked);
	        });
	        update_statistic_data();
        })
        
        //【新词出价】&【新词限价】的【确定】按钮点击事件
        $('#btn_adjust_price').unbind('click');
        $('#btn_adjust_price').click(function(){
            var price_multi = Number($('#price_multi').val());
            var init_limit_price = Number($('#init_limit_price').val());
            $('#init_limit_price').attr('value_bak', init_limit_price);
            oTable.fnUpdatePrice(price_multi, init_limit_price);
            PT.sendDajax({'function':'web_update_limit_price',
                                     'adgroup_id':$('#adgroup_id').val(),
                                     'init_limit_price':init_limit_price
                                     });
        });
        var mnt_type = $('#mnt_type').val();
        if (mnt_type=='2') {
	        $('#init_limit_price').val($('#limit_price').val());
        }
        $('#btn_adjust_price').click();
        
        //【新词限价】blur事件 输入校验
        $('#init_limit_price').unbind('blur');
        $('#init_limit_price').blur(function(){
            var value = Number($(this).val());
	        var limit_price_max = Number($('#limit_price_max').val());
            if (isNaN(value) || value==0) {
                $(this).val(Number($(this).attr('value_bak')).toFixed(2));
            } else if (value<0.05) {
                $(this).val(0.05);
            } else if (value>limit_price_max) {
                $(this).val(limit_price_max.toFixed(2));
            } else {
                $(this).val(value.toFixed(2));
            }
        })
        
        //修改关键词出价后，约束出价不超过【新词限价】
        Table.off('blur', '[name="keyword_price"]');
        Table.on('blur', '[name="keyword_price"]', function(){
            var init_limit_price = Number($('#init_limit_price').val());
            if (isNaN(this.value)) {
                this.value = Math.min(Number($(this).parent().next().html()), init_limit_price).toFixed(2);
            } else {
                this.value = Math.max(Math.min(Number(this.value), init_limit_price), 0.05).toFixed(2);
            }
        })
        
        //【一键提交】
        $('#btn_submit').unbind('click');
        $('#btn_submit').click(function(){
		    var init_limit_price = Number($('#init_limit_price').val()),
				keyword_count = Number($('#keyword_count').html()) || 0,
				sum_checked = Number($('#sum_checked').html());
            if (keyword_count>=200) {
                PT.alert('宝贝已在该计划中推广了200个关键词，无法继续添加');
            } else if (sum_checked==0) {
                PT.alert('您还未选中任何关键词');
            } else {
	            PT.confirm('即将添加' + sum_checked + '个关键词，确定要提交吗？', function () {
	                PT.show_loading('亲，正在提交关键词');
	                var keywords = $.map(oSettings.aiDisplay, function(i){
	                    var nTr = oSettings.aoData[i].nTr;
	                    var checked = $(nTr).find(':checkbox')[0].checked;
	                    if(checked){
	                        //返回关键词，出价，匹配模式
	                        return [[$(nTr).find('td:eq(1) a').text(), Number((Number($(nTr).find('td:eq(2) :text').val())*100).toFixed(0)), Number($(nTr).find('td:eq(1) .match_scope').attr('match_scope')), null, null]];
	                    }
	                })
		            PT.sendDajax({'function':'web_batch_add_keywords', 
		                                     'adgroup_id':$('#adgroup_id').val(), 
		                                     'keyword_count':keyword_count, 
		                                     'kw_arg_list':$.toJSON(keywords), 
											 'init_limit_price':(init_limit_price>0?init_limit_price:0)
		                                     });
	            });
	        }
        })
		
		init_help();
    }
    
    //添加关键词后，从当前表格中删除这些数据
    var remove_dataTable_keywords = function(keyword_list){
        var oTable = $('#table_select_keyword').dataTable();
        var oSettings = oTable.fnSettings();
        var anTr_2remove = [];
        for (var i=0;i<oSettings.aiDisplay.length;i++) {
	        var ii = oSettings.aiDisplay[i];
            var nTr = oSettings.aoData[ii].nTr;
            if ($(nTr).is(':has(input:checked)')) {
	            anTr_2remove.push(nTr);
            }
        }
        for (var i=0;i<anTr_2remove.length;i++) {
	        oTable.fnDeleteRow(anTr_2remove[i]);
        }
        $('#sum_checked').html(0);
        $('#sum_all_keywords').html(oSettings.aoData.length);
    }
        
    //【复制关键词】
    var init_zeroclipboard = function(){
        for(var i in PT.ZeroClipboard.z.clients){
            PT.ZeroClipboard.z.clients[i].destroy();
            delete PT.ZeroClipboard.z.clients[i];
        }
        clip = new PT.ZeroClipboard.z.Client();
        clip.setHandCursor(true);
        clip.addEventListener('complete', function (client, text) {
            //debugstr("Copied text to clipboard: " + text );
            PT.alert("已经复制到剪切板，请使用Ctrl+V粘贴。");
        });
        clip.addEventListener('mouseOver', function (client) {
            // update the text on mouse over
            var oSettings = $('#table_select_keyword').dataTable().fnSettings();
            var checked_keywords = $.map(oSettings.aiDisplay, function(i){
                var nTr = oSettings.aoData[i].nTr;
                return $(nTr).find('[name="keyword"]:checked').val();
            }); 
            // update the text on mouse over
            clip.setText(checked_keywords.join('\n'));
        });
        clip.glue('btn_clip');
    }
    
    // 添加关键词后，更新可添加关键词个数
    var update_keyword_count_2add = function(added_keyword_count){
		$('#keyword_count').text(Number($('#keyword_count').text())+added_keyword_count);
		$('#can_add_count').text(Number($('#can_add_count').text())-added_keyword_count);
    }
	
	// 更新表格中的统计数据，包括选中关键词的个数和候选词总数
	var update_statistic_data = function () {
			var sum_checked = 0;
		    var oSettings = $('#table_select_keyword').dataTable().fnSettings();
		    $.map(oSettings.aiDisplay, function(i){
		    	var oChk = $(oSettings.aoData[i].nTr).find('[name="keyword"]');
		    	if(oChk[0].checked){
		    		sum_checked++;
		    		$(oSettings.aoData[i].nTr).addClass('checked_keyword');
		    	}else{
		    		$(oSettings.aoData[i].nTr).removeClass('checked_keyword');
		    	}
		    });
		    $('#sum_checked').html(sum_checked);
		    $('#valid_count').html(oSettings.aiDisplay.length - sum_checked).show().siblings('img').hide();
	}
    
    return {
        init: init,
        init_sliders: init_sliders,
        select_keyword_callback: generate_table,
        remove_dataTable_keywords: remove_dataTable_keywords,
        update_keyword_count_2add: update_keyword_count_2add
    }
}();