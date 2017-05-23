"use strict";
PT.namespace('Table');
PT.namespace('instance_table');

PT.Table.TB_LIMIT_QSCORE=5; //6分以下不预估排名
PT.Table.TB_LIMIT_FPRECAST_COUNT=20; //批量预估不超过
PT.Table.TB_LIMIT_FORECAST_ORFER='<select class="small m-wrap"><option>因淘宝限制，'+PT.Table.TB_LIMIT_QSCORE+'分以下无法预估，请谅解</option></select>';

PT.Table.BaseRowObj=function(obj,hide_clum){
	this.kw_id=obj.id;
	this.nRow=$(obj);
	this.hide_clum=hide_clum;
	this.adgroup_id=this.nRow.attr('adgroup_id');
	this.item_id=this.nRow.attr('item_id');
	this.campaign_id=this.nRow.attr('campaign_id');
	this.default_price=this.nRow.attr('default_price');

	this.word=$('#word_'+this.kw_id).text();
	this.match_span=this.nRow.find('.match');
	this.match_scope=this.match_span.attr('scope');
	this.new_price_input=this.nRow.find('.new_price');
	this.max_price=parseFloat(this.nRow.find('.max_price').text());
	this.forecast_order_btn=this.nRow.find('.forecast_order_btn');
	this.check_ranking_btn=this.nRow.find('.check_ranking');
	this.g_cpc=parseFloat(this.nRow.find('.g_cpc').text());

//	this.or_lable=this.nRow.attr('or_lable');
//	this.and_lable=this.nRow.attr('and_lable');
	this.label_code=this.nRow.attr('label_code');

	this.match_changed=0;//匹配状态
	this.kw_del=0;		//删除状态
	//this.is_del();      //屏蔽首次进入建议出价
}

PT.Table.BaseRowObj.prototype.is_del=function(){
	if(this.nRow.find('.optm_type').text()=='1'){
		this.kw_del=1;
	}
}

PT.Table.BaseRowObj.prototype.check_box=function(){
	return this.nRow.find('.kid_box');
}

PT.Table.BaseRowObj.prototype.is_checked=function(){
	return this.check_box().attr("checked")=="checked";
}

PT.Table.BaseRowObj.prototype.v_match_scope=function(){
	return this.nRow.find('span[class*="match"]').attr('scope');
}

PT.Table.BaseRowObj.prototype.v_new_price=function(){
	return parseFloat(this.new_price_input.val());
}

PT.Table.BaseRowObj.prototype.change_match_scorp=function(){
	var scorp_list={'4':1,'2':4,'1':2}
		,current_match_scope=this.v_match_scope();
	this.set_match_scorp(scorp_list[current_match_scope]);
}

PT.Table.BaseRowObj.prototype.set_match_scorp=function(match_scorp){
	if(this.kw_del){
		return false;
	}
	var scorp_list={1:'精',2:'中',4:'广'};
	this.match_span.attr('scope',match_scorp);

	this.match_span.text(scorp_list[match_scorp]);
	this.match_changed=match_scorp==this.match_scope?0:1;
	//PT.instance_table.calc_action_count();
}

PT.Table.BaseRowObj.prototype.is_plus = function() {
    return this.max_price < this.v_new_price();
}

PT.Table.BaseRowObj.prototype.is_fall = function() {
    return this.max_price > this.v_new_price();
}

PT.Table.BaseRowObj.prototype.is_limit = function() {
    return this.v_new_price() > PT.instance_table.KW_LIMIT_PRICE;
}

PT.Table.BaseRowObj.prototype.v_forecast_select = function() {
    return $('#forecast_order_'+this.kw_id);
}

PT.Table.BaseRowObj.prototype.update_style=function(){

	this.new_price_input.removeClass('safe_color m_color limit').attr('disabled',false);
	this.nRow.removeClass('kw_del');

	if(this.kw_del){
		this.nRow.addClass('kw_del');
		this.new_price_input.attr('disabled',true);
	}else{
		this.is_plus()?this.new_price_input.addClass('m_color'):'';
		this.is_fall()?this.new_price_input.addClass('safe_color'):'';
		this.is_limit()?this.new_price_input.addClass('limit'):'';
	}
	//PT.instance_table.calc_action_count();
}

PT.Table.BaseRowObj.prototype.change_new_price=function(){
	if(this.kw_del){
		return false;
	}
	var new_price=this.v_new_price();
	if(PT.instance_table.check_digit(new_price)){
		this.new_price_input.val(new_price.toFixed(2));
	}else{
		this.new_price_input.val(this.max_price);
	}
	this.forecast_order(false);
	this.update_style();
	this.calc_action_count();
}

PT.Table.BaseRowObj.prototype.delete_kw=function(statue){
	this.kw_del=statue;
//	this.update_style();
//	this.calc_action_count();
}

PT.Table.BaseRowObj.prototype.recover_kw=function(){
	this.kw_del=0;
	this.new_price_input.val(Number(this.max_price).toFixed(2));
	this.set_match_scorp(this.match_scope);
//	this.update_style();
//	this.calc_action_count();
}

PT.Table.BaseRowObj.prototype.forecast_order=function(tip){//tip 用来判断是否弹出消息框
    var _tip=(tip==undefined)?true:tip;
    if(!this.forecast_order_limit(_tip)){
//        var kw_id_list,
//            forecast_data=this.nRow.data('forecast_data');
//        if(forecast_data==undefined){
        if(this.v_forecast_select().length==0){
            this.forecast_order_btn.html("<img src='/site_media/jl5/images/forecast_orde_ajax.gif'>");
//            kw_id_list=[this.kw_id];
//            PT.sendDajax({'function':'web_get_forecast_order_list','kw_id_list':kw_id_list});
            PT.sendDajax({'function':'web_get_keywords_rankingforecast','kw_id_list':[this.kw_id]});
        }else{
            this.chose_current_rank();
        }
    }else if (PT.instance_table.bulk_forecast==1){//质量得分小于5并且在批量优化中
        this.forecast_order_btn.replaceWith(PT.Table.TB_LIMIT_FORECAST_ORFER);
        PT.instance_table.bulk_forecast_order();
    }
}

//设置预估出价
PT.Table.BaseRowObj.prototype.set_forecast_order=function(rank_data){
	// 出价排名解析函数
    var handle_rank_data = function (rank_data) {
        var result = [], page_data = [], page_data_rt = [], page_data_rb = [], page_data_b = [], page_pos = 17, position = 0, page_no, price, max_price, min_price, page_str;
        //分页处理
        for (var i=0;i<Math.ceil(rank_data.length/page_pos);i++) {
            page_no = i+1;
            page_data = rank_data.slice(i*page_pos, (i+1)*page_pos);
            page_str = page_no>1?'第'+page_no+'页':'';
            //页面区域划分
            if (page_no<3) {
                page_data_rt = page_data.slice(0, 4);
                page_data_rb = page_data.slice(4, 12);
                page_data_b = page_data.slice(12, 17);
            } else {
                page_data_rt = [];
                page_data_rb = page_data.slice(0, 12);
                page_data_b = page_data.slice(12, 17);
            }
            //右侧前四位(第3页以后为0)
            for (var j in page_data_rt) {
                price = (page_data_rt[j]/100).toFixed(2);
                result.push([page_str+'第'+(Number(j)+1)+'名：'+price+'元', price]);
            }
            //右侧后八位(第3页以后为12)
            if (page_data_rb.length>0) {
	            var rank_h = page_data_rt.length + 1, rank_l = page_data_rt.length + page_data_rb.length;
                if (page_data_rb.length==1) {
                    price = (page_data_rb[0]/100).toFixed(2);
	                result.push([page_str+'第'+rank_h+'名：'+price+'元', price]);
                } else {
                    max_price = (page_data_rb[0]/100).toFixed(2);
                    min_price = (page_data_rb[page_data_rb.length-1]/100).toFixed(2);
                    result.push([page_str+'第'+rank_h+'~'+rank_l+'名：'+max_price+'~'+min_price+'元', max_price+'-'+min_price]);
                }
            }
            //底部五位
            if (page_data_b.length>0) {
                if (page_data_b.length==1) {
                    price = (page_data_b[0]/100).toFixed(2);
                    result.push(['第'+page_no+'页底部：'+price+'元', price]);
                } else {
                    max_price = (page_data_b[0]/100).toFixed(2);
                    min_price = (page_data_b[page_data_b.length-1]/100).toFixed(2);
                    result.push(['第'+page_no+'页底部：'+max_price+'~'+min_price+'元', max_price+'-'+min_price]);
                }
            }
        }
        result.push([rank_data.length+'名以后：'+(min_price-0.01).toFixed(2)+'元', (min_price-0.01).toFixed(2)]);
        return result;
    };

	// 主逻辑
    var that=this, template_str="";
	if ($.isArray(rank_data) && rank_data.length>0) {
	    //template_str=template.compile(pt_tpm['template_forecast_select.tpm.html'])({'kw_id':this.kw_id, 'rank_data':handle_rank_data(rank_data)});
	    template_str = template.render('template_forecast_select', {'kw_id':this.kw_id, 'rank_data':handle_rank_data(rank_data)});
	    this.forecast_order_btn.replaceWith(template_str);
//	    this.nRow.data('forecast_data',rank_data);
	    this.chose_current_rank();

	    $('#forecast_order_'+this.kw_id).change(function(){
	        that.new_price_input.val(this.value.split('-')[0]);
	        that.update_style();
	        that.calc_action_count();
	    });
	} else {
	    rank_data = rank_data.length>0?rank_data:'淘宝返回预估排名数据为空';
	    //template_str=template.compile(pt_tpm['template_forecast_select_fail.tpm.html'])({'error_msg':rank_data});
	    template_str = template.render('template_forecast_select_fail', {'error_msg':rank_data});
        this.nRow.find('.forecast_order_btn').replaceWith(template_str); // 不要直接用this.forecast_order_btn，会有缓存bug
	    this.nRow.find('select.forecast_fail').change(function () {
            if (this.value=='1') {
                $(this).replaceWith('<a href="javascript:;"class="forecast_order_btn"><img src="/site_media/jl/img/forecast_orde_ajax.gif"></a>');
                that.forecast_order();
            }
        });
	}
    //判断是否是批量预测
    if (PT.instance_table.bulk_forecast){
        PT.instance_table.bulk_forecast_order();
    }
}

//设置期望排名
PT.Table.BaseRowObj.prototype.set_want_order=function(){
    var want_order= PT.instance_table.want_order;
    var v_forecast_select = this.v_forecast_select();
    if (v_forecast_select.length==0) return;
    var opt = v_forecast_select.find('option:eq('+want_order+')');
    if (opt.length==0) {
	    opt = v_forecast_select.find('option:last');
    }
    var new_price = Number(opt.val().split('-')[0]);
    var want_order_limit = Number(PT.instance_table.want_order_limit);
    new_price = want_order_limit?Math.min(new_price, want_order_limit):new_price;
    this.new_price_input.val(new_price);
    this.update_style();
    if(new_price>PT.instance_table.KW_LIMIT_PRICE){
        this.set_row_up();
    }else{
        this.set_row_down();
    }
    this.chose_current_rank();
    this.calc_action_count();

//    var forecast_data=this.nRow.data('forecast_data');
//    if(forecast_data!=undefined){
//        for (var i=0;i<forecast_data.length;i++){
//            if(forecast_data[i].page==want_order){
//                var temp_price=forecast_data[i].price;
//                if(PT.instance_table.want_order_limit!=''){
//                    var temp_price=Math.min(temp_price,PT.instance_table.want_order_limit);
//                }
//                this.new_price_input.val(temp_price);
//                this.update_style();
//
//                if(temp_price>PT.instance_table.KW_LIMIT_PRICE){
//                    this.set_row_up();
//                }else{
//                    this.set_row_down();
//                }
//                this.chose_current_rank();
//                break;
//            }
//        }
//    }
//    this.calc_action_count();
}

//根据当前出价选中预估出价
PT.Table.BaseRowObj.prototype.chose_current_rank=function(){
    var select_obj = this.v_forecast_select();
    if (select_obj.length==0) return;
    var new_price = this.v_new_price(), match_price = null;
    select_obj.find('option').each(function () {
        if (new_price>=Number(this.value.split('-').slice(-1)[0])) {
            match_price = this.value;
            return false;
        }
    });
    if (!match_price) {
        match_price = select_obj.find('option:last').val();
    }
    select_obj.val(match_price);

//    var forecast_data=this.nRow.data('forecast_data'),
//        new_price=this.v_new_price(),
//        index='';
//    if(new_price>=forecast_data[0].price){
//        index='1-5'
//    }else if(new_price<=forecast_data.slice(-1)[0].price){
//        index='101'
//    }else{
//        for (var i=1;i<forecast_data.length-1;i++){
//            var prev=Number(forecast_data[i-1].price);
//            var current=Number(forecast_data[i].price);
//            if (new_price<prev && new_price>=current){
//                index=forecast_data[i].page;
//                break;
//            }
//        }
//    }
//    this.v_forecast_select().find('[value="'+index+'"]').attr('selected','selected');
}

//查排名
PT.Table.BaseRowObj.prototype.check_ranking=function(){
    //var adgroup_info=PT.instance_table.adgroup_info();
    this.check_ranking_btn.html("<img src='/site_media/jl5/images/forecast_orde_ajax.gif'>");
    PT.sendDajax({'function':'web_get_word_order','adgroup_id':this.adgroup_id,'item_id':this.item_id,'keyword_id':this.kw_id,'ip':PT.instance_table.v_zone_ip()});
}

//设置排名
PT.Table.BaseRowObj.prototype.set_ranking=function(rank){
	this.check_ranking_btn.html(rank);
	this.check_ranking_btn.attr('switch',"0")
	//判断是否是批量预测
	if (PT.instance_table.bulk_ranking){
		PT.instance_table.bulk_ranking_order();
	}
	//判断是否需要同步强排名的表
	if (PT.instance_table.sync_rob_table){
		$('#rob_'+this.kw_id).data('rob').set_ranking(rank);
	}
}

//改变词类型
//PT.Table.BaseRowObj.prototype.change_type=function(obj){
//	PT.light_msg('改变词类型','当前选中'+obj.find("option:selected").text())
//}

//开启磨盘
PT.Table.BaseRowObj.prototype.magic_hollowware=function(){
	PT.Base.goto_ztc(5, 0, 0, this.word);

//	var template=$('#template_magic_hollowware').html();
//	$(template).modal();
}

//判断关键词是否做过改变
PT.Table.BaseRowObj.prototype.is_modified=function(){
	if(this.match_changed || this.kw_del || this.v_new_price()!=this.max_price){
		return true;
	}
	return false;
}

//删除关键词
PT.Table.BaseRowObj.prototype.delete_row=function(){
	var index=PT.instance_table.data_table.fnGetPosition(this.nRow[0]);
	PT.instance_table.data_table.fnDeleteRow(index);
}

//提交后更新关键词状态
PT.Table.BaseRowObj.prototype.update_row=function(new_price){
	var index=PT.instance_table.data_table.fnGetPosition(this.nRow[0]),
		new_price=this.v_new_price();
	//PT.instance_table.data_table.fnUpdate(new_price,index,7,false,false)
	this.nRow.find('.max_price').text(new_price);
	this.max_price=new_price;
	this.match_scope=this.v_match_scope();
	this.match_changed=0;
	this.update_style();
	this.calc_action_count();
}

PT.Table.BaseRowObj.prototype.input_check=function(checked){
	this.check_box().attr('checked',checked);
}

//将显示行显示到前面
PT.Table.BaseRowObj.prototype.set_row_up=function(checked,num){
	num!=undefined?this.check_box().prev().text(num):this.check_box().prev().text(1);
	checked!=undefined?this.input_check(checked):'';
}

//将显示行显示到后面
PT.Table.BaseRowObj.prototype.set_row_down=function(checked){
	this.check_box().prev().text(0);
	checked!=undefined?this.input_check(checked):'';
}

//获取改价基准价
PT.Table.BaseRowObj.prototype.get_base_num=function(base_type){
	switch (base_type){
		case 'max_price':
			return this.max_price;
			break;
		case 'g_cpc':
			return parseFloat(this.nRow.find('.g_cpc').text());
			break;
		case 'custom':
			return $('#custom_price').val();
			break;
		default:
			return parseFloat(base_type);
			break;
	}
}

//加价
PT.Table.BaseRowObj.prototype.bulk_plus=function(base_type,delta,mode,limit){
	if(this.kw_del){
		return false;
	}
	var base_num=this.get_base_num(base_type),current_price;
	if(base_type=='max_price' || base_type=='g_cpc'){
		if(mode=='int'){
			current_price=base_num + delta
		}else{
			current_price=base_num * (1 + delta / 100);
		}
	}else{
		current_price=base_num;
	}

    if (current_price > limit)
    {
        current_price = limit;
    }

	if(current_price<this.max_price&&base_type=='max_price'){
		this.new_price_input.val(this.max_price);
		this.update_style();
		this.calc_action_count();
		return;
	}

    if (current_price < 0.05)
    {
        current_price = 0.05;
    }

	if (current_price>99.99){
		current_price = this.max_price;
	}

	this.new_price_input.val((parseInt(Math.ceil((current_price * 100).toFixed(1))) / 100).toString());
//	this.update_style();
//	this.calc_action_count();
}

//降价
PT.Table.BaseRowObj.prototype.fall_plus=function(base_type,delta,mode,limit){
	if(this.kw_del){
		return false;
	}
	var base_num=this.get_base_num(base_type),current_price;
	if(mode=='int'){
		current_price=base_num - delta
	}else{
		current_price=base_num * (1 - delta / 100);
	}

    if (current_price < limit)
    {
        current_price = limit;
    }

	if(current_price>this.max_price&&base_type=='max_price'){
		this.new_price_input.val(this.max_price);
		this.update_style();
		this.calc_action_count();
		return;
	}

    if (current_price < 0.05)
    {
        current_price = 0.05;
    }

	if (current_price>99.99){
		current_price = this.max_price;
	}
	this.new_price_input.val((parseInt(Math.floor((current_price * 100).toFixed(1))) / 100).toString());
//	this.update_style();
//	this.calc_action_count();
}

PT.Table.BaseRowObj.prototype.calc_action_count=function(){
	PT.instance_table.calc_action_count();
}

PT.Table.BaseRowObj.prototype.forecast_order_limit=function(tip){
	if (isNaN(Number(this.hide_clum['qscore']))||Number(this.hide_clum['qscore'])<=PT.Table.TB_LIMIT_QSCORE){
		if (PT.instance_table.bulk_forecast==0&&tip){
			PT.alert('由于淘宝接口调用量限制,只能预估质量得分'+PT.Table.TB_LIMIT_QSCORE+'分以上的词');
		}
		return true;
	}
	return false;
}

//显示抢排名信息
PT.Table.BaseRowObj.prototype.show_rob_info=function(mode,new_price,rank){
	var msg,obj=$('#rob_'+this.kw_id);
	if(mode==1){
		msg='当前排名:'+rank+'，当前出价:'+new_price;
		obj.find('.rob_set').addClass('success');
		obj.find('.rob_set input').val('');
		obj.find('.max_price').text(new_price);
		obj.find('.rank').text(rank);
		//this.check_box().attr('checked',false);
	}
	if(mode==2){
		msg='未抢到排名，已恢复原出价';
		obj.find('.rob_set').addClass('fail');
	}

	obj.find('.rob_set_info').text(msg);
}

//恢复抢排名设置输入框
PT.Table.BaseRowObj.prototype.recover_rob_input=function(mode){
	var td_obj=this.nRow.find('.rob_set');
	if(td_obj.hasClass('fail')){
		td_obj.removeClass('fail');
	}
}

PT.Table.BaseRowObj.prototype.change_attention=function(is_attention){
	PT.sendDajax({'function':'web_change_attention','keyword_id':this.kw_id,'adgroup_id':this.adgroup_id,'is_attention':is_attention});
}

PT.Table.BaseRowObj.prototype.attention_call_back=function(statue){
	var obj=this.nRow.find('.icon-eye-open'),that=this;
	if(statue==0){
		obj.removeClass('s_color');
		PT.light_msg('关注成功','您可以再次点击取消关注', 2000);
	}else{
		obj.addClass('s_color');
		if(PT.hasOwnProperty('Attention')){//判断在我的关注中调用
			this.nRow.fadeTo(300,0).queue(function(next){
				$('#keyword_count').text(Number($('#keyword_count').text())-1)
				that.delete_row();
				$(this).dequeue();
			});
		}else{
			PT.light_msg('取消关注成功','您可以再次点击添加关注',2000);
		}
	}
	obj.off('click').on('click.PT.e',function(){that.change_attention(statue)});
}

PT.Table.BaseRowObj.prototype.show_chart=function(statue){
	PT.sendDajax({'function':'web_show_kw_trend','adgroup_id':this.adgroup_id,'keyword_id':this.kw_id});
}



PT.Table.BaseTableObj=function(table_id,temp_id){
	this.table_id=table_id;
	this.temp_id=temp_id;
	this.table_obj=$('#'+this.table_id);
	this.bulk_forecast=0;

	this.KW_LIMIT_PRICE=5; //设置超过该价格就提示
	this.match_count=0;
	this.plus_count=0;
	this.fall_count=0;
	this.del_count=0;

	this.want_order='';
	this.want_order_limit='';
	this.fixed_header='';

	this.init_event();
	this.get_keyword_data();
	this.check_limit_price();
	//this.init_tree();
	//this.init_label_list();

	//用来隐藏列对应的字典
	this.COLUM_DICT={'qscore':5,'create_days':6,'impressions':7,'click':8,'ctr':9,'cost':10,'ppc':11,'cpm':12,'avgpos':13,'favcount':14,'favctr':15,'favpay':16,'paycount':17,'pay':18,'conv':19,'roi':20,'g_pv':21,'g_click':22,'g_ctr':23,'g_cpc':24,'g_competition':25};
	//默认隐藏列
	this.DEFAULT_HIDE_COLUMN=['create_days','ctr','cpm','avgpos','favcount','favctr','favpay','conv','g_pv','g_click','g_ctr','g_cpc','g_competition'];
	//隐藏列的值保存到每行的data中
	this.NEED_SAVE_COLUMN=['qscore','g_click','roi'];
	//扩展回调
	this.init_ajax_event_list=[];
	this.row_cache={};
}

PT.Table.BaseTableObj.prototype.check_limit_price=function(){
	var limit=$('#user_limit_price input').val();
	if(limit!=''){
		this.KW_LIMIT_PRICE=limit;
	}
}

PT.Table.BaseTableObj.prototype.sort_table=function(custom_column){
	PT.console('begin dataTable:'+this.table_id);
	var that=this,custom_aoColumns;
	custom_aoColumns=[
			{"bSortable": true,"sSortDataType": "custom-text", "sType": "custom","sClass": "no_back_img tac"},
			{"bSortable": false},
			{"bSortable":  true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": false,"sClass": 'tac'},
			{"bSortable": true,"sClass": 'tac', "sType": "custom","sSortDataType": "custom-text"},
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
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"}
		];

	if(custom_column==''||custom_column==undefined){
		custom_column=this.DEFAULT_HIDE_COLUMN;
	}

	if(String(custom_column).indexOf('all')!=-1){ //区分于默认显示项目
		custom_column=[];
	}

	for (var i in custom_column){
		custom_aoColumns[this.COLUM_DICT[custom_column[i]]]['bVisible']=false;
	}


	this.data_table=this.table_obj.dataTable({
		"bRetrieve": true, //允许重新初始化表格
		"bPaginate": false,
		"bFilter": false,
		"bInfo": false,
		"bAutoWidth":false,//禁止自动计算宽度
		"sDom": 'Tlfrtip',
		"oTableTools": {
			"sSwfPath": "/site_media/assets/swf/copy_csv_xls.swf",
			"aButtons": [{
                    "sExtends": "xls",
					'sTitle':that.get_adgroup_title(),
                    "fnClick": function ( nButton, oConfig, flash ) {
                        this.fnSetText( flash, that.creat_scv_data() );
                    }
			}],
			"custom_btn_id":"save_as_csv"
		},
		"aoColumns":custom_aoColumns,
		"fnCreatedRow":this.fnRowCallback,
		"oLanguage": {
			"sZeroRecords": "没有关键词记录"
		}
	});
	this.init_ajax_event();
	this.set_kw_count();
	PT.hide_loading();
	PT.console('end dataTable:'+this.table_id);
}

//当datatable绘制每个tr时调用,在此生成每一行的信息并缓存到tr上
PT.Table.BaseTableObj.prototype.fnRowCallback=function(nRow, aData, iDisplayIndex, iDisplayIndexFull){
	//隐藏列的值保存到每行的data中
	var NEED_SAVE_COLUMN=PT.instance_table['NEED_SAVE_COLUMN'],hide_clum={},COLUM_DICT=PT.instance_table['COLUM_DICT'];

	for (var i in NEED_SAVE_COLUMN){
		if(aData[COLUM_DICT[NEED_SAVE_COLUMN[i]]].indexOf('custom')!=-1){
			hide_clum[NEED_SAVE_COLUMN[i]]=$(aData[COLUM_DICT[NEED_SAVE_COLUMN[i]]])[0].innerHTML;
			continue;
		}
		hide_clum[NEED_SAVE_COLUMN[i]]=aData[COLUM_DICT[NEED_SAVE_COLUMN[i]]];
	}

	var row_data=new PT.Table.BaseRowObj(nRow,hide_clum);
	//$(nRow).data('obj',row_data);
	if(nRow.id){
		PT.instance_table.row_cache[nRow.id]=row_data;
	}

}

//后台回调函数
PT.Table.BaseTableObj.prototype.call_back=function(json){
	this.layout_keyword(json.keyword);
	this.sort_table();
}

//填充表格数据
PT.Table.BaseTableObj.prototype.layout_keyword=function(json){
	PT.console('begin layout keyword');
	var tr_str='',kw_count=0,d;
	for (d in json){
		if(!isNaN(d)){
			tr_str+=template.render(this.temp_id,json[d]);
			kw_count++;
		}
	}
	this.table_obj.find('tbody tr').remove();
	this.table_obj.find('tbody').append(tr_str);
}

PT.Table.BaseTableObj.prototype.init_event=function(){
	var that=this;

	$('.select_status').click(function(){
		var mode=parseInt($(this).attr('mode'));
		switch(mode){
			case 0:
				that.row_list().each(function(){
					var obj=that.row_cache[this.id];
					if(obj.v_new_price()>obj.max_price){
						obj.set_row_up(true);
					} else {
						obj.set_row_down(false);
					}
				});
				break;
			case 1:
				that.row_list().each(function(){
					var obj=that.row_cache[this.id];
					if(obj.v_new_price()<obj.max_price){
						obj.set_row_up(true);
					} else {
						obj.set_row_down(false);
					}
				});
				break;
			case 2:
				that.row_list().each(function(){
					var obj=that.row_cache[this.id];
					if(obj.kw_del){
						obj.set_row_up(true);
					} else {
						obj.set_row_down(false);
					}
				});
				break;
			case 3:
				that.row_list().each(function(){
					var obj=that.row_cache[this.id];
					if(obj.match_changed){
						obj.set_row_up(true);
					} else {
						obj.set_row_down(false);
					}
				});
				break;
		}
		that.data_table.fnSort([ [0,'desc']]);
		that.set_checked_count();
	});

	//提交到直通车
	$('#id_curwords_submit').click(function(){
		var msg='即将提交:',row=that.row_list();
		var limit_count=0,limit_val=$('#user_limit_price input').val();

		if(limit_val==undefined||limit_val==''){
			PT.alert('请填写关键词最高限价');
			return false;
		}

		that.row_list().each(function(){
			var obj=that.row_cache[this.id];
			if (obj.is_modified()&&(!obj.kw_del)&&obj.v_new_price()>that.KW_LIMIT_PRICE){
				limit_count++;
			}
		});

		if(that.plus_count>0){
			msg+=' 加价:'+that.plus_count;
		}
		if(that.fall_count>0){
			msg+=' 降价:'+that.fall_count;
		}
		if(that.match_count>0){
			msg+=' 修改匹配方式:'+that.match_count;
		}
		if(that.del_count>0){
			msg+=' 删除:'+that.del_count;
		}

		if(msg!='即将提交:'){
			if(limit_count>0){
				msg+='。<span class="r_color">其中有'+limit_count+'个关键词改价超过了'+limit_val+'元！</span>';
			}
			msg+='<div>亲，确认提交到直通车吗？</div>';
			PT.confirm(msg,that.curwords_submit,[],that)
		}else{
			//PT.light_msg('提交操作：','没有关键词改变，请进行操作');
            $.alert({
              title:'提交操作',
              body:'没有关键词改变，请进行操作'
            });
		}

	});

	//关键词搜索
	$('.search_btn').click(function(){
		var search_word=$(this).prev().val();
		$('.search_btn').prev().val(search_word);
		if(search_word!=''){
			that.search_word_and_sort(search_word);
		}else{
			//PT.light_msg('搜索提示：','请填写要搜索的关键词');
            $.alert({
              title:'搜索提示',
              body:'请填写要搜索的关键词'
            });
		}
	});

//	//批量加价
//	$('#bulk_plus_btn').click(function(){
//		that.bulk_plus();
//	});
//
//	//批量降价
//	$('#bulk_fall_btn').click(function(){
//		that.fall_plus();
//	});

	//批量改价
	$('#bulk_btn').click(function(){
		that.bulk_price_router();
	});

	//批量删除
	$('#bulk_del_btn').click(function(){
		that.bulk_del();
	});

	//批量恢复
	$('#bulk_recover_btn').click(function(){
		that.bulk_recover();
	});

	//批量设置匹配
	$('#bulk_match_btn').click(function(){
		var match_scorp=parseInt($('#keyword_match input[name="bulk_match_radio"]:checked').val());
		that.bulk_match(match_scorp);
	});

	//批量预估排名
	$('#bulk_worder_btn').click(function(){
		that.bulk_worder();
	});

/*	$('#bulk_price>ul input[type="text"][id^="bulk_up"]').click(function(){
		$('#bulk_price>ul input[type="text"][id^="bulk_fall"]').val('');
		$('#custom_price').val('');
		$('#bulk_price>ul input[type="radio"][value="plus"]').attr('checked',true);
	});

	$('#bulk_price>ul input[type="text"][id^="bulk_fall"]').click(function(){
		$('#bulk_price>ul input[type="text"][id^="bulk_up"]').val('');
		$('#custom_price').val('');
		$('#bulk_price>ul input[type="radio"][value="fall"]').attr('checked',true);
	});*/

	$('#custom_price').click(function(){
		$('#bulk_price>ul input[type="text"][id^="bulk_"]').val('');
		$(this).parent().find('input[type="radio"]').attr('checked',true);
	});

//	$('#price_down>ul input').click(function(){
//		$('#price_down>ul input[type="text"]').not(this).val('');
//		$(this).prev().find('input').attr('checked',true);
//	});

	//批量优化按钮事件
/*	$('#batch_optimize_btn').click(function(){
		var body_ofset = document.body.scrollTop | document.documentElement.scrollTop;

		if($('#keyword_operate_area').find('ul:first').attr('class')!='two'||body_ofset>that.table_obj.offset().top){
			$('#keyword_operate_area').find('ul:first').attr('class','two');
		}else{
			$('#keyword_operate_area').hide();
			$('#keyword_operate_area').find('ul:first').removeClass('two');
			$(this).find('i').removeClass('icon-angle-up').addClass('icon-angle-down');
			return false;
		}

		if($('#keyword_operate_area:hidden').length){
			$('#keyword_operate_area').show();
		}

		$(this).find('i').removeClass('icon-angle-down').addClass('icon-angle-up');
		$('#smart_optimize_btn').find('i').removeClass('icon-angle-up').addClass('icon-angle-down');

		if(body_ofset>that.table_obj.offset().top){
			$("html,body").animate({scrollTop:$("#keyword_box").offset().top},300);
		}

		that.required_recover();
	});
*/
	//智能优化按钮事件
/*	$('#smart_optimize_btn').click(function(){
		var body_ofset = document.body.scrollTop | document.documentElement.scrollTop;

		if($('#keyword_operate_area').find('ul:first').attr('class')!='default'||body_ofset>that.table_obj.offset().top){
			$('#keyword_operate_area').find('ul:first').attr('class','default');
		}else{
			$('#keyword_operate_area').hide();
			$('#keyword_operate_area').find('ul:first').removeClass('default');
			$(this).find('i').removeClass('icon-angle-up').addClass('icon-angle-down');
			return false;
		}

		if($('#keyword_operate_area:hidden').length){
			$('#keyword_operate_area').show();
		}

		$(this).find('i').removeClass('icon-angle-down').addClass('icon-angle-up');
		$('#batch_optimize_btn').find('i').removeClass('icon-angle-up').addClass('icon-angle-down');

		if(body_ofset>that.table_obj.offset().top){
			$("html,body").animate({scrollTop:$("#keyword_box").offset().top},300);
		}

		that.required_recover();
	});

	$('#show_batch_operate_btn').click(function(){
		$('#keyword_operate_area>ul').attr('class','one')
	});*/

/*	$('.go_setup2').click(function(){
		var obj=$('#batch_optimize_box');
		obj.removeClass('setup3 setup1').addClass('setup2');
	});
	*/

	$('.go_setup2').click(function(){
		//var obj=$('#batch_optimize_box');
		$('#smart_optimize_box').removeClass('setup1').addClass('setup2');
	});

	$('.go_setup1').click(function(){
		//var obj=$('#batch_optimize_box');
		$('#smart_optimize_box').removeClass('setup2').addClass('setup1');
	});

	$('#batch_optimize_btn').click(function(e){
		e.stopPropagation();
		var temp_count=that.plus_count+that.fall_count+that.match_count+that.del_count;
		if(temp_count>0){
			$('#batch_optimize .change_count').text(temp_count);
		}
		$('#smart_optimize_box').removeClass('show');
		$('#batch_optimize_box').toggleClass('show');
	});


	$('#smart_optimize_btn').click(function(e){
		e.stopPropagation();
		$('#batch_optimize_box').removeClass('show');
		$('#smart_optimize_box').toggleClass('show');
	});


	$(document).on('click.PT.dropdown',function(e){
		e.stopPropagation()
/*		if(!$('#batch_optimize_box').find(e.target).length){
			$('#batch_optimize_box').removeClass('show');
		}*/
		if(!$('#batch_optimiz').find(e.target).length&&!$('.modal-scrollable').find(e.target).length){
			$('#batch_optimize_box').removeClass('show');
		}
		if(!$('#smart_optimize_box').find(e.target).length){
			$('#smart_optimize_box').removeClass('show');
		}
	});

	$('.dropdown-menu .closer').click(function(){
		$(this).parents('.btn-group:first').removeClass('open');
		$(this).parents('.dropdown-menu:first').removeClass('show');
	});

	$('#smart_optimize_btn').click(function(){
		var temp_count=that.plus_count+that.fall_count+that.match_count+that.del_count;
		if(temp_count>0){
			$('#change_optimize_tip').find('span').text(temp_count);
			$('#change_optimize_tip').show();
		}else{
			$('#change_optimize_tip').hide();
		}
		$('#batch_optimize_box').removeClass('show');
	});

	//改变优化策略
	$('#change_optimize_btn').click(function(){
		PT.show_loading('正在改变优化策略');
		that.get_keyword_data();
		$(this).parents('.btn-group:first').removeClass('open');
	});

	//批量抢排名按钮
	$('#rob_btn').click(function(){
		that.bulk_rob_ranking();
	});

	$('#rob_reset').click(function(){
		that.bulk_rob_reset();
	});

	//抢排名
//	$('a[href="#rob_rank"]').click(function(){
//		that.hide_custom_column([['5',true]])
//	});

	//隐藏抢排名的列
//	$('#batch_optimize_operate ul.nav a:not([href="#rob_rank"])').click(function(){
//		that.hide_custom_column([['5',false]])
//	});

	//定制列选一行
	$('#select_column li[class*="title"] input').change(function(){
		var parent=$(this).parent().parent().parent();
		parent.find('input').not('[value='+this.value+']').attr('checked',this.checked);

	});

	//定制列
	$('.select_column_btn').click(function(){
		var clumon_list=[],mode=$(this).attr('mode');
		$('#select_column li:not([class*="title"]) input').each(function(){
			if(this.checked){
				clumon_list.push([Number($(this).val()),true]);
			}else{
				clumon_list.push([Number($(this).val()),false]);
			}
		});
		$('#select_column').parent().removeClass('open');
		that.hide_custom_column(clumon_list);
		// if(mode=='save'){
		// 	that.save_custom_column();
		// }
	});

	//定制列计算
	$('#select_column_show_btn').click(function(){
		var obj=that.data_table.fnSettings().aoColumns,inputs=$('#select_column');
		for (var i in obj){
			inputs.find('input[value="'+i+'"]').attr('checked',obj[i].bVisible)
		}
	});

//	//加价按钮显示隐藏
//	$('#bulk_up_price_radio').change(function(){
//		$('#bulk_fall_price_box').addClass('hide');
//		$('#bulk_up_price_box').removeClass('hide');
//	});
//
//	//加价按钮显示隐藏
//	$('#bulk_fall_price_radio').change(function(){
//		$('#bulk_up_price_box').addClass('hide');
//		$('#bulk_fall_price_box').removeClass('hide');
//	});

	$('#bulk_price ul.tabs input[type="radio"]').change(function(){
		var index=$('#bulk_price ul.tabs input[type="radio"]').index($(this));
		$('#bulk_price ul.content li').addClass('hide');
		$('#bulk_price ul.content li').eq(index).removeClass('hide');
	});

	//新词出价超过限价提醒
	$('#user_limit_price input').change(function(){
		var limit=Number($(this).val()).toFixed(2),adg_id=$('#adgroup_id').val();
		$(this).val(that.KW_LIMIT_PRICE);
		if(isNaN(limit)||limit<0.05||limit>99.99){
			return;
		}
		if(that.KW_LIMIT_PRICE!=limit){
			that.KW_LIMIT_PRICE=limit;
			$(this).val(limit);
			that.update_all_style();
			if(adg_id){//重点关注词页面不需要提交
				PT.sendDajax({'function':'web_set_adg_limit_price','adgroup_id':adg_id,'limit_price':limit});
			}
		}
	});

	//强排名的表格
	$('#rob_box .close').click(function(){
		$('#rob_table_box').fadeTo(0,0);
		$('#rob_table').dataTable().fnClearTable();
		$('#rob_table').dataTable().fnDestroy();
		that.bulk_ranking=0; //同时停止查排名
		that.sync_rob_table=0;
	});
}

PT.Table.BaseTableObj.prototype.init_ajax_event=function(){
	var that=this;

	//批量预估排名
	$('#bulk_forecast_order').click(function(){
		if(that.has_checked_row()){
			that.start_bulk_forecast_order();
		}
	});

	//批量查当前排名
	$('#ip_zone').change(function(){
		if(that.has_checked_row()){
			if($(this).val()==''){
				return;
			}
			if(that.has_checked_row()){
				that.start_bulk_ranking_order();
			}
		}else{
			$(this).val('');
		}
	});

	//改变匹配模式
	this.table_obj.find('.match').click(function(){
		//$(this).parent().parent().parent().data('obj').change_match_scorp();
		that.row_cache[this.parentNode.parentNode.parentNode.id].change_match_scorp();
		that.row_cache[this.parentNode.parentNode.parentNode.id].calc_action_count();
	});

	//改变出价时调用
	this.table_obj.find('.new_price').change(function(){
		//$(this).parent().parent().parent().data('obj').change_new_price();
		that.row_cache[this.parentNode.parentNode.parentNode.id].change_new_price();
	});

	//删除关键词
	this.table_obj.find('.icon-remove').click(function(){
		if(that.row_cache[this.parentNode.parentNode.parentNode.parentNode.id].kw_del){
			that.row_cache[this.parentNode.parentNode.parentNode.parentNode.id].delete_kw(0);
		}else{
			that.row_cache[this.parentNode.parentNode.parentNode.parentNode.id].delete_kw(1);
		}
		that.row_cache[this.parentNode.parentNode.parentNode.parentNode.id].update_style();
		that.row_cache[this.parentNode.parentNode.parentNode.parentNode.id].calc_action_count();
	});

	//恢复关键词各个状态
	this.table_obj.find('.icon-undo').click(function(){
		//$(this).parent().parent().parent().parent().data('obj').recover_kw();
		that.row_cache[this.parentNode.parentNode.parentNode.parentNode.id].recover_kw();
		that.row_cache[this.parentNode.parentNode.parentNode.parentNode.id].update_style();
		that.row_cache[this.parentNode.parentNode.parentNode.parentNode.id].calc_action_count();
	});

	//将关键词标记为
	this.table_obj.find('.icon-eye-open').click(function(){
		var state=0;
		if($(this).hasClass('s_color')){ //如果有灰色则表示当前是未关注的状态
			state=1;
		}
		//$(this).parent().parent().parent().data('obj').change_attention(state);
		that.row_cache[this.parentNode.parentNode.parentNode.id].change_attention(state);
	});

	//单个预估排名
	this.table_obj.find('.forecast_order_btn').click(function(){
		//$(this).parent().parent().data('obj').forecast_order();
		that.row_cache[this.parentNode.parentNode.id].forecast_order();
	});

	//查看当前排名
	this.table_obj.find('.check_ranking').click(function(){
		//$(this).parent().parent().data('obj').check_ranking();
		that.row_cache[this.parentNode.parentNode.id].check_ranking();
	});

	//关键词魔方
	this.table_obj.find('.keyword').click(function(){
		//$(this).parent().parent().parent().parent().data('obj').magic_hollowware();
//		that.row_cache[this.parentNode.parentNode.parentNode.parentNode.id].magic_hollowware();
	});


	// 复选框事件
	this.table_obj.find('.father_box').click(function(e){
		var ev = e || window.event, area_id=$(this).attr('link'),there=this;
		ev.stopPropagation();
		if(area_id!=undefined){
			var kid_box=$('#'+area_id).find('.kid_box').attr('checked',there.checked);
		}
		setTimeout(function(){that.set_checked_count()},0);
	});

	//单选框触发显示个数
//	this.table_obj.find('input[class*="kid_box"]').click(function(){
//		that.set_checked_count();
//	});

	//检查抢排名的限制
	this.table_obj.find('.rob_limit').keyup(function(){
		if(parseFloat($(this).val())>that.KW_LIMIT_PRICE){
			$(this).addClass('impo_color');
		}else{
			$(this).removeClass('impo_color');
		}
	});

	//重置所有关键词出价
	$('.bulk_recover_all_btn').click(function(){
		that.bulk_recover_all();
		$('#batch_optimize .change_count').text(0);
	});

	//抢排名批量设置
	$('#show_rob_box').click(function(){
		if(that.show_rob_box()){ //返回false表示没有符合条件的关键词
			that.bulk_ranking=1; //同时进行查排名
			that.sync_rob_table=1; //查排名同步抢排名的表
			$('#ip_zone').attr('disabled',true); //禁止下拉菜单改变再次触发查询
			that.bulk_ranking_order();
		}
	});

	$('#bulk_rob_set').click(function(){
		that.bulk_rob_set();
	});

	this.table_obj.find('.show_trend_chart').click(function(){
		//$(this).parent().parent().parent().data('obj').show_chart();
		that.row_cache[this.parentNode.parentNode.parentNode.id].show_chart();
	});

	$select({name: 'idx','callBack': this.set_checked_count,'that':this}); //shift多选

	this.data_table.fnSettings()['aoDrawCallback'].push({ //当表格排序时重新初始化checkBox右键多选
		'fn':function(){selectRefresh()},
		'sName':'refresh_select'
	});

	this.init_scroll_event();
	App.initTooltips();

	for (var fn in this.init_ajax_event_list){
		this.init_ajax_event_list[fn](this);
	}
}

PT.Table.BaseTableObj.prototype.check_digit=function(num){
    if (isNaN(num) || num < 0.05 || num > 99.99) {
        PT.alert("错误：必须是0.05至99.99之间的数字",'red');
		return false;
    }
	return true;
}

PT.Table.BaseTableObj.prototype.calc_action_count=function(){
	var that=this,match_count=0,plus_count=0,fall_count=0,del_count=0;
	this.row_list().each(function(){
		var obj=that.row_cache[this.id]
		if(obj.kw_del){
			del_count++
		}else{
			match_count+=obj.match_changed;
			if(obj.v_new_price()!=obj.max_price){
				obj.v_new_price()>obj.max_price?plus_count++:fall_count++;
			}
		}
	});

	$('#match_count').text(match_count);
	$('#plus_count').text(plus_count);
	$('#fall_count').text(fall_count);
	$('#del_count').text(del_count);
	that.match_count=match_count;
	that.plus_count=plus_count;
	that.fall_count=fall_count;
	that.del_count=del_count;
}

//开始批量预估
PT.Table.BaseTableObj.prototype.start_bulk_forecast_order=function(){
    var msg = '预估排名执行时间较长，您确定要执行吗？<div class="r_color mart_6">说明：预估排名直接获取的淘宝数据，因为没有实际竞价，预估结果可能不准</div>';
    if(this.get_checked_row_count()>PT.Table.TB_LIMIT_FPRECAST_COUNT){
        msg += '<div class="r_color mart_6">同时，由于淘宝接口调用量限制，一次最多预测'+PT.Table.TB_LIMIT_FPRECAST_COUNT+'个质量得分大于'+PT.Table.TB_LIMIT_QSCORE+'的关键词</div>';
    }
    PT.confirm(msg, function(){
		this.bulk_forecast=1;
		this.forecasted=0;
		this.bulk_forecast_order();
	},[],this,this.stop_bulk_forecast_order);
}

//停止批量预估
PT.Table.BaseTableObj.prototype.stop_bulk_forecast_order=function(){
	this.bulk_forecast=0;
}

PT.Table.BaseTableObj.prototype.bulk_forecast_order=function(){
	var current_btn=$(this.table_obj.find('input[type="checkbox"]:checked').parent().parent().find('.forecast_order_btn')[0]),that=this;
	if (current_btn.length&&this.forecasted<=PT.Table.TB_LIMIT_FPRECAST_COUNT){
		this.forecasted++;
		//current_btn.parent().parent().data('obj').forecast_order();
		this.row_cache[current_btn.parent().parent().attr('id')].forecast_order();
		return;
	}
	this.bulk_forecast=0;
	//全部预测完以后判断是否需要预估出价
	if(this.want_order!=''){
		var row_obj=this.get_checked_row();
		row_obj.each(function(){
			//var obj=$(this).parent().parent().data('obj');
			var obj=that.row_cache[this.parentNode.parentNode.id];
			obj.set_want_order();
		});
		this.want_order='';
		this.data_table.fnSort([ [0,'desc']]);
	}
	PT.alert('批量预估完成');
}

//开始批量查排名
PT.Table.BaseTableObj.prototype.start_bulk_ranking_order=function(){
    PT.confirm('查询当前排名可能执行时间较长，您确定要执行吗？<div class="r_color mart_6">说明：因为直通车加入了个性化搜索算法，有时候排名结果可能不稳定</div>',function(){
		this.bulk_ranking=1;
		$('#ip_zone').attr('disabled',true); //禁止下拉菜单改变再次触发查询
		this.bulk_ranking_order();
	},[],this);
}

PT.Table.BaseTableObj.prototype.bulk_ranking_order=function(){

		var current_btn=$(this.table_obj.find('input[type="checkbox"]:checked').parent().parent().find('.check_ranking[switch="1"]')[0]);
		if(current_btn.length){
			//current_btn.parent().parent().data('obj').check_ranking();
			this.row_cache[current_btn.parent().parent().attr('id')].check_ranking();
			return;
		}
		this.bulk_ranking=0;
		$('#ip_zone').attr('disabled',false);
		$('.check_ranking').attr('switch','1');

}

PT.Table.BaseTableObj.prototype.curwords_submit=function(){
	var data=[],that=this;
	this.row_list().each(function(){
		var obj=that.row_cache[this.id];
		if (obj.is_modified()){
			data.push({
					'keyword_id':obj.kw_id,
					'adgroup_id':obj.adgroup_id,
					'campaign_id':obj.campaign_id,
					'word':obj.word,
					'is_del':obj.kw_del,
					'new_price':obj.v_new_price(),
					'max_price':obj.max_price,
					'match_scope':obj.v_match_scope()
			})
		}
	});

	data=$.toJSON(data);
	PT.show_loading('正在提交数据');
	PT.sendDajax({'function': 'web_curwords_submit','data': data});
}

//自定义csv数据格式
PT.Table.BaseTableObj.prototype.creat_scv_data=function(){
	var data_str='关键字\t质量得分\t养词天数\t展现量\t点击量\t点击率\t总花费\t平均点击花费\t千次点击花费\t昨日平均排名\t收藏量\t收藏率\t收藏成本\t成交量\t成交额\t转化率\t投资回报\t全网展现指数\t全网点击指数\t全网点击率\t全网市场均价\t全网竞争度\n';
	for (var i=0,i_end=this.data_table.fnSettings()['aiDisplay'].length;i<i_end;i++){
		var nRow=this.data_table.fnGetNodes(i);
		var keyword=$(nRow).find('.keyword_box span').text();
		var td_list=this.data_table.fnGetData(i);
		data_str+=keyword+'\t';
	  for (var j=5,j_end=td_list.length;j<j_end;j++){
		if(isNaN(Number(td_list[j]))&&td_list[j].indexOf('custom')!=-1){
			data_str+=$(td_list[j])[0].innerHTML+'\t';
			continue;
		}
		  data_str+=td_list[j]+'\t';
	  }
		data_str+='\n';
	}
	return data_str;
}

PT.Table.BaseTableObj.prototype.v_zone_ip=function(){
	return $('#ip_zone').val();
}

//提交后的回调函数
PT.Table.BaseTableObj.prototype.curwords_submit_call_back=function(json){
	var del_count=json.del_kw.length,
		update_count=json.update_kw.length,
		msg='';

	if (del_count){
		msg='删除成功:'+del_count+'个';
	}
	if (update_count){
		msg+='修改成功:'+update_count+'个';
	}
	for (var i=0;i<del_count;i++){
		//$('#'+json.del_kw[i]).data('obj').delete_row();
		this.row_cache[json.del_kw[i]].delete_row();
	}
	for (var i=0;i<update_count;i++){
		//$('#'+json.update_kw[i]).data('obj').update_row();
		this.row_cache[json.update_kw[i]].update_row();
	}

	if(json.optm_submit_time!=null&&(del_count>0||update_count>0)){ //更新上次优化提交时间
		$('#optimize_time').text(json.optm_submit_time.substr(0,json.optm_submit_time.indexOf('.')));
	}

	this.set_kw_count();
	this.set_checked_count();
	this.calc_action_count();
	PT.hide_loading();
	PT.alert(msg);
	$('a[href="#history_keyword_box"]').removeAttr('switch'); //删除词后将已删词的开关打开
	$('#history_kw_count').text(Number($('#history_kw_count').text())+del_count); //改写已删词个数
}

//设置关键词个数
PT.Table.BaseTableObj.prototype.set_kw_count=function(){
	var kw_count=this.data_table.fnSettings()['aiDisplay'].length-1; //排除定向
	$('#keyword_count').text(kw_count);
}

//搜索并排序
PT.Table.BaseTableObj.prototype.search_word_and_sort=function(search_word){
	var that=this;
	this.row_list().each(function(){
		var obj=that.row_cache[this.id];
		if(obj.word.indexOf(search_word)!=-1){
			obj.set_row_up(true);
		}else{
			obj.set_row_down(false);
		}
	});

	this.data_table.fnSort([ [0,'desc']]);
	this.set_checked_count();
}

//加价降价路由函数
PT.Table.BaseTableObj.prototype.bulk_price_router=function(){
	var that=this;
	$('#batch_optimize_box').removeClass('show');
	if(this.has_checked_row()){
		var type=$('#bulk_price input[name="bulk_radio"]:checked').val();
		if(type==undefined){
			PT.alert('请选择改价类型');
			return;
		}
		if(type=='plus'){
			var base_type=$('#bulk_up_price_base').val(),
				mode=$('#bulk_up_price_mode').val(),
				delta=$('#bulk_up_price_delta').val(),
				limit=parseFloat($('#bulk_up_price_limit').val());
			this.bulk_plus(base_type,delta,mode,limit);
		}
		if(type=='fall'){
			this.fall_plus();
		}
		if(type=='custom'){
			var mode=$('#bulk_up_price_mode').val(),
				delta=$('#custom_price').val();
			this.bulk_plus(type,delta,mode);
		}
		if(!isNaN(type)){
			this.bulk_plus(type);
		}
	}
	this.calc_action_count();
	setTimeout(function(){
		//var t1=new Date().getTime();
		that.update_all_style();
		//document.title=new Date().getTime()-t1;
	},0);
}

//批量加价
PT.Table.BaseTableObj.prototype.bulk_plus=function(base_type,delta,mode,limit){
	var row_obj=this.get_checked_row();


	if(base_type==undefined){
		PT.alert('请选择加价类型');
		return;
	}

	if(delta==""){
		PT.alert('请输入加价幅度');
		return;
	}


	if(mode=='int'&&delta!=undefined&&isNaN(delta)){
		PT.alert('请输入有效数字，必须是0.01至99.99之间的数字');
		return;
	}

	if(mode=='percent' && parseInt(delta)!=delta){
		PT.alert('加价百分比必须为整数');
		return;
	}

	delta=parseFloat(delta);

	if(mode=='int'&&(delta<0.01 || delta>99.99)){
		PT.alert('请输入有效数字，必须是0.01至99.99之间的数字');
		return;
	}

	if(base_type=='g_cpc'){
		this.hide_custom_column([[this.COLUM_DICT[base_type],true]])
	}

//	row_obj.each(function(){
//		var obj=$(this).parent().parent().data('obj');
//		obj.bulk_plus(base_type,delta,mode,limit);
//	});

	for (var i=0,i_end=row_obj.length;i<i_end;i++){
		var obj=this.row_cache[row_obj[i].parentNode.parentNode.id];
		obj.bulk_plus(base_type,delta,mode,limit);
	}

}

//批量降价fall_price
PT.Table.BaseTableObj.prototype.fall_plus=function(){
	var row_obj=this.get_checked_row(),
		base_type=$('#bulk_fall_price_base').val(),
		mode=$('#bulk_fall_price_mode').val(),
		delta=$('#bulk_fall_price_delta').val(),
		limit=parseFloat($('#bulk_fall_price_limit').val());

	if(base_type==undefined){
		PT.alert('请选择降价类型');
		return;
	}

	if(delta==""){
		PT.alert('请输入降价幅度');
		return;
	}

	if(isNaN(delta)){
		PT.alert('请输入有效数字，必须是0.01至99.99之间的数字');
		return;
	}

	if(mode=='percent' && parseInt(delta)!=delta){
		PT.alert('降价百分比必须为整数');
		return;
	}

	delta=parseFloat(delta);

	if(delta<0.01 || delta>99.99){
		PT.alert('请输入有效数字，必须是0.01至99.99之间的数字');
		return;
	}

	if(base_type=='g_cpc'){
		this.hide_custom_column([[this.COLUM_DICT[base_type],true]])
	}

//	row_obj.each(function(){
//		var obj=$(this).parent().parent().data('obj');
//		obj.fall_plus(base_type,delta,mode,limit);
//	});
	for (var i=0,i_end=row_obj.length;i<i_end;i++){
		var obj=this.row_cache[row_obj[i].parentNode.parentNode.id];
		obj.fall_plus(base_type,delta,mode,limit);
	}
}


//获取选中的行
PT.Table.BaseTableObj.prototype.get_checked_row=function(){
	return this.table_obj.find('tbody input:checked');
}

//计算选中的个数
PT.Table.BaseTableObj.prototype.get_checked_row_count=function(){
	return this.get_checked_row().length;
}

//检查是否有选中的关键词并给出提示
PT.Table.BaseTableObj.prototype.has_checked_row=function(){
	if(this.get_checked_row_count()==0){
		PT.light_msg('提示','没有选中任何关键词');
		return false;
	}
	return true;
}

//批量删除
PT.Table.BaseTableObj.prototype.bulk_del=function(){
	var that=this;
	$('#batch_optimize_box').removeClass('show');
	if(this.has_checked_row()){
		var row_obj=this.get_checked_row();

//		row_obj.each(function(){
//			var obj=$(this).parent().parent().data('obj');
//			obj.delete_kw();
//		});
		for (var i=0,i_end=row_obj.length;i<i_end;i++){
			var obj=this.row_cache[row_obj[i].parentNode.parentNode.id];
			obj.delete_kw(1);
		}
	}
	this.calc_action_count();
	setTimeout(function(){
		that.update_all_style();
	},0);

}

//批量恢复
PT.Table.BaseTableObj.prototype.bulk_recover=function(){
	var that=this;
	if(this.has_checked_row()){
		var row_obj=this.get_checked_row();

//		row_obj.each(function(){
//			var obj=$(this).parent().parent().data('obj');
//			obj.recover_kw();
//		});
		for (var i=0,i_end=row_obj.length;i<i_end;i++){
			var obj=this.row_cache[row_obj[i].parentNode.parentNode.id];
			obj.recover_kw();
		}
		this.calc_action_count();
		setTimeout(function(){
			that.update_all_style();
		},0);
	}
}

//批量设置匹配
PT.Table.BaseTableObj.prototype.bulk_match=function(match_scorp){
	var that=this;
	$('#batch_optimize_box').removeClass('show');
	if(this.has_checked_row()){
		var row_obj=this.get_checked_row();

//		row_obj.each(function(){
//			var obj=$(this).parent().parent().data('obj');
//			obj.set_match_scorp(match_scorp);
//		});
		for (var i=0,i_end=row_obj.length;i<i_end;i++){
			var obj=this.row_cache[row_obj[i].parentNode.parentNode.id];
			obj.set_match_scorp(match_scorp);
		}
		this.calc_action_count();
	}
}

//批量预估排名
PT.Table.BaseTableObj.prototype.bulk_worder=function(){
	if(this.has_checked_row()){
		var row_obj=this.get_checked_row();

		var temp_limit=$('#bulk_worder_limit').val();

		this.want_order=$('#bulk_worder_select').val();

		if(temp_limit!=''){
			this.want_order_limit=parseFloat(temp_limit);
		}

		if($('.forecast_order_btn').length>0){
			this.start_bulk_forecast_order();
		}else{
//			row_obj.each(function(){
//				var obj=$(this).parent().parent().data('obj');
//				obj.set_want_order();
//			});
			for (var i=0,i_end=row_obj.length;i<i_end;i++){
				var obj=this.row_cache[row_obj[i].parentNode.parentNode.id];
				obj.set_want_order();
			}
		}
		this.data_table.fnSort([ [0,'desc']]); //排序将大于5元的放到上面
	}
	$('#batch_optimize_box').removeClass('show');
}

//重置所有出价
PT.Table.BaseTableObj.prototype.bulk_recover_all=function(){
		var that=this;
		this.row_list().each(function(){
			var obj=that.row_cache[this.id],scorp_list={1:'精',2:'中',4:'广'};
			obj.kw_del=0;
			obj.match_changed=0;
			obj.new_price_input.val(obj.max_price);

			obj.match_span.attr('scope',obj.match_scorp);
			obj.match_span.text(scorp_list[obj.match_scope]);
			obj.update_style();
		});
		this.calc_action_count();
}

//计算超过限价的词的个数
PT.Table.BaseTableObj.prototype.calc_exceed_count=function(){
	var exceed_cound=0,that=this,that=this;
	this.row_list().each(function(){
		var obj=that.row_cache[this.id];
		if(obj.v_new_price>that.KW_LIMIT_PRICE){
			exceed_cound++;
		}
	});
	return exceed_cound;
}

//计算选中词的个数
PT.Table.BaseTableObj.prototype.set_checked_count=function(){
	var that=this;
	$('#current_check_count').text(this.get_checked_row_count());
	$('#batch_optimize_count').text(this.get_checked_row_count());
	$('#del_kw_count').text(this.get_checked_row_count());
	this.row_list().each(function(){
		var obj=that.row_cache[this.id];
		if(obj.is_checked()){
			$(this).addClass('selected');
		}else{
			$(this).removeClass('selected');
		}
	});
}

PT.Table.BaseTableObj.prototype.get_smart_optimize_argv=function(){
		var json={}
		json['stgy']=$('#smart_optimize input[name="strategy"]:checked').val();
		json['rate']=$('#id_rate').val();
		json['executor']=$('#stgy_executor').val();
		json['cfg']=$('#stgy_cfg').val();
		return $.toJSON(json);
}


//根据数据生成树
PT.Table.BaseTableObj.prototype.layout_bulk_tree=function(data){
	var that=this;
	$('#adgroup_tree').treeview({
		'showcheck': true,
		'data':data,
		'oncheckboxclick':that.tree_check,
		'cbiconpath': "/site_media/jl/plugins/wdTree/css/images/icons/",
		'theme': "bbit-tree-lines" //bbit-tree-lines ,bbit-tree-no-lines,bbit-tree-arrows
	});
}



PT.Table.BaseTableObj.prototype.init_label_event=function(){
	var that=this;

/*	$('#refine_box .dropdown_btn').click(function(){
		$('#refine_box .btn-group').removeClass('open');
		$(this).parent().addClass('open');
		var $this=$(this);

			$('#batch_optimize_box div').click(function(e){

				return function(){e.stopPropagation();
					$this.parent().removeClass('open');
				}();
			});

	});*/


	$('#refine_box').on('blur','.custom input',function(){
		var temp_val=Number($(this).val());
		if(isNaN(temp_val)||temp_val<0){
			$(this).val(0);
		}
	});

	//过滤条件点击后
	$('.refine_box_btn').click(function(){
		var index=$(this).attr('index');

		if(that.is_custom_filter(index)){
			if(that.is_valid_input(index)){
				that.set_custom_label(index);
			}else{
				return false;
			}
		}else{
			that.set_label(index);
		}
		$('#'+index).removeClass('open');
		that.filter_kw_list();
	});

	//过来条件中的自定义条件
	$('.refine_box_custom_btn').click(function(){
		$(this).parent().find('.custom_area').toggleClass('hide');
	});

	//标签点击时，清除自己并过滤
//	$('#selected_conditions .right>span').live('click.PT.e',function(){
//		var index=$(this).attr('index'),code=$(this).attr('code'),obj;
//		obj=$('#'+index);
//
//		if (index=='use_default_chckbox'){
//			obj.attr('checked',false);
//		}else{
//			obj.find('input[value="'+code+'"]').attr('checked',false);
//			obj.find('input[type="text"]').val('');	//清空自定义输入框
//		}
//
//		if(!obj.find('input:checked').length){
//			obj.find('a').removeClass('selected');
//		}
//		$(this).remove();
//		that.filter_kw_list();
//	});

	//点击checkedbox时清除自定义输入的内容
	$('#refine_box>ul>li input[type="checkbox"]').on('change.PT.e',function(){
		var change=0,obj=$(this).parents('div.dropdown-menu:first');
		obj.find('input[type="text"]').val('');
		obj.find('.custom_area').addClass('hide');
/*		obj.find('input[type="checkbox"]').each(function(){
 			if(this.checked){
				change=1;
				return;
			}
		});
		if(change){
			obj.find('input[type="text"]').addClass('input_disable');
		}else{
			obj.find('input[type="text"]').removeClass('input_disable');
		}*/
	});

	$('#refine_box>ul>li input[type="text"]').on('click.PT.e',function(){
		var obj=$(this).parents('div.dropdown-menu:first');
		obj.find('input[type="checkbox"]').attr('checked',false);
		//obj.find('input[type="text"]').removeClass('input_disable');
	})

	$('#use_default_chckbox').change(function(){
		if(this.checked){
			var data={};
			$('#refine_box .dropdown-menu input:checked').attr('checked',false);  //清除选中的checkbox
			$('#refine_box .dropdown-menu input[type="text"]').val('');		  //清除自定义的checkbox
			$('#refine_box .dropdown_btn').removeClass('selected');			  //清除选中样式
			//$('#selected_conditions .right span').remove();					  //删除已有标签
			data['title']='自定义';
			data['code']='custom';
			data['state']='默认出价';
			data['index']=this.id;
			that.creative_label(data,'C');
		}else{
			$('#selected_conditions .right li').remove();					  //删除已有标签
		}
		that.filter_kw_list();
	});

	//设置默认出价的个数
	$('#use_default_num').text(this.calc_default_price_row());
}

//根据数据生成标签列表
PT.Table.BaseTableObj.prototype.layout_bulk_search=function(data){
	var input_dom='',i;
	for (i in data){
		input_dom+=template.render('template_custom_input',data[i]);
	}
	$('#refine_box>ul li:not(li[class="default"])').remove();
	$('#refine_box>ul li').before(input_dom);
	this.init_label_event();
}

//判断是否是用户输入
PT.Table.BaseTableObj.prototype.is_custom_filter=function(id){
	var obj=$('#'+id),inputs;
	inputs=obj.find('input[type="text"]');
	for (var i=0;i<inputs.length;i++){
		if($(inputs[i]).val()!=''){
			$('#selected_conditions .right li[index='+id+']').remove();
			return true	;
		}
	}
	return false;
}

//验证输入是否有效
PT.Table.BaseTableObj.prototype.is_valid_input=function(id){
	var obj=$('#'+id),inputs;
	inputs=obj.find('input[type="text"]');
	obj.find('.error').hide();//隐藏错误提示
	for (var i=0;i<inputs.length;i++){
		if($.trim(inputs[i].value)==''||isNaN($.trim(inputs[i].value))){
			obj.find('.error').show().find('span').text('无效输入，请重新输入');
			return false;
		}
	}

	if(Number($.trim(inputs[0].value))>Number($.trim(inputs[1].value))){
		obj.find('.error').show().find('span').text('最小值大于最大值，请重新输入');
		return false;
	}
	obj.find('.error').hide();
	return true;
}

//用户自定义标签
PT.Table.BaseTableObj.prototype.set_custom_label=function(id){
	var obj=$('#'+id),text,start,end,data={};

	text=obj.find('a').addClass('selected').text();
	$('#selected_conditions .right').find('span[index="'+id+'"]').remove(); //删除系统标签

	obj.find('input[type="checkbox"]').attr('checked',false);
	start=obj.find('.min').val();
	end=obj.find('.max').val();

	data['index']=id;
	data['title']=text;
	data['state']='自定义:'+start+'~'+end;
	data['code']='custom';
	$('#selected_conditions .right li[index='+id+'] span[code=custom]').remove();
	this.creative_label(data,'C');

/*	if(this.COLUM_DICT[id.replace('refine_box_','')]!=undefined){
		this.hide_custom_column([[this.COLUM_DICT[id.replace('refine_box_','')],true]]); //当用户过滤隐藏的列时，将他显示出来
	}*/
}

//设置标签
PT.Table.BaseTableObj.prototype.set_label=function(id){
	var obj=$('#'+id),data={},dom='',selected_num=0,that=this,checkbox,title,state,text,code_str,code;
	checkbox=obj.find('input[type="checkbox"]');

	title=obj.find('.dropdown_btn').text();
	code_str=String(this.get_label_code_list());
	$('#selected_conditions .right').find('li[index="'+id+'"] span[code="custom"]').remove(); //删除自定义标签

	checkbox.each(function(){
		code=$(this).val();
		data['code']=code;
		data['index']=id;
		if (code_str.indexOf(data['code'])==-1&&this.checked){
			state=$(this).next().text();

			text=state.slice(0,state.indexOf('('));
			data['title']=title;
			data['state']=state;
			//data['text']=title+':'+state;
			that.creative_label(data,code.slice(-1));
			selected_num++;
		}
		if (code_str.indexOf(data['code'])!=-1&&!this.checked){ //删除没选中且在选择条件中的sapn
			$('#selected_conditions .right span[code="'+code+'"]').remove();
		}
	});

	if (selected_num){//判断是否有选中的 然后给按钮加上颜色
		obj.find('a').addClass('selected');
	}else{
		obj.find('a').removeClass('selected');
	}
}

//生成标签
PT.Table.BaseTableObj.prototype.creative_label=function(data,class_type){
	var class_dic,box,child,that=this;

	if(!$('#selected_conditions .right li[index='+data['index']+']').length){
		box=template.render('template_selected_condition_box',data);
		$('#selected_conditions .right ul').append(box);
	}

	child=template.render('template_selected_condition_child',data);
	$('#selected_conditions .right li[index='+data['index']+'] .title').after(child);

	$('#selected_conditions .right li[index="'+data['index']+'"] span[code='+data['code']+']').click(function(e){
		e.stopPropagation();
		var index=$(this).parent().attr('index'),code=$(this).attr('code'),obj;
		obj=$('#'+index);

		if (index=='use_default_chckbox'){
			obj.attr('checked',false);
		}else{
			obj.find('input[value="'+code+'"]').attr('checked',false);
			obj.find('input[type="text"]').val('');	//清空自定义输入框
		}

		if(!obj.find('input:checked').length){
			obj.find('a').removeClass('selected');
		}
		if($(this).parent().find('span[code]').length>1){
			$(this).remove();
		}else{
			$(this).parent().remove();
		}
		that.filter_kw_list();
	});


}

//过滤关键词列表
PT.Table.BaseTableObj.prototype.filter_kw_list=function(){
	var that=this;
	setTimeout(function(){
		PT.console('start filter');
		//判断是否是使用默认出价的标签
		//if(!$('#selected_conditions span[index="use_default_chckbox"]').length){
			//首先首选过滤树中的节点
			var tree_checked_list_str,custom_limit=[];

			//获取系统标签条件
			var label_filter_list=that.get_group_code_list(),row=that.row_list();

			var use_default=$('#selected_conditions span[index="use_default_chckbox"]').length

			tree_checked_list_str=String($('#adgroup_tree').getCheckedNodes());

			//获取用户自定义条件
			$('#selected_conditions .right span[code="custom"]').each(function(){
				var line=$(this).parent().attr('index').replace('refine_box_',''),
					min_num=$(this).text().slice($(this).text().indexOf(':')+1).split('~')[0],
					max_num=$(this).text().slice($(this).text().indexOf(':')+1).split('~')[1];

					custom_limit.push([line,min_num,max_num]);
			});

			if(tree_checked_list_str.length||label_filter_list.length||custom_limit.length){
				for (var i=0,i_end=row.length;i<i_end;i++){
					var obj=that.row_cache[row[i].id],tree_judge=1,lable_judge=1,custom_judge=1,or_lable=String($.trim(obj.label_code).split(' ')[0]),and_lable=String($.trim(obj.label_code).split(' ').slice(1)),lable_judge_list=[];

					if(tree_checked_list_str.length&&tree_checked_list_str.indexOf(or_lable)==-1){
						tree_judge=0;
					}

					for (var c=0,c_end=label_filter_list.length;c<c_end;c++){
						lable_judge_list[c]=0;
						for (var s=0,s_end=label_filter_list[c].length;s<s_end;s++){//里层循环取并集
							if(and_lable.indexOf(label_filter_list[c][s])!=-1){
								lable_judge_list[c]=1;
								break;
							}
						}
					}

					if(String(lable_judge_list).indexOf(0)!=-1){//取并集
						lable_judge=0;
					}


					for (var j=0,j_end=custom_limit.length;j<j_end;j++){
						var current_val;
						if(custom_limit[j][0]=='use_default_chckbox'){
							if(obj.default_price!=obj.max_price){
								custom_judge=0
							}
							break;
						}
						if(that.NEED_SAVE_COLUMN.indexOf(custom_limit[j][0])!=-1){
							current_val=parseFloat(obj.hide_clum[custom_limit[j][0]]);
						}else{
							current_val=parseFloat(obj.nRow.find('.'+custom_limit[j][0]).text());
						}
						if(isNaN(current_val)||current_val<custom_limit[j][1] || current_val>custom_limit[j][2]){
							custom_judge=0;
						}
					}

					if(tree_judge&lable_judge&custom_judge){
						obj.set_row_up(true);
					}else{
						obj.set_row_down(false);
					}
				};
			}else{
				that.table_obj.find('.kid_box').attr('checked',false);
			}

		that.data_table.fnSort([[0,'desc']]);
		that.set_checked_count();
		that.change_filter_tips(tree_checked_list_str,label_filter_list,custom_limit);
	},17);
}

//获得显示的过滤条件
PT.Table.BaseTableObj.prototype.get_label_code_list=function(){
	var code_lsit=[];
	$('#selected_conditions .right span[code]:not([code="custom"])').each(function(){
		code_lsit.push($(this).attr('code'));
	});
	return code_lsit;
}

//获取分组的过滤条件
PT.Table.BaseTableObj.prototype.get_group_code_list=function(){
	var code_lsit=this.get_label_code_list(),code_dict={},temp_list=[];
	for (var i=0,i_end=code_lsit.length;i<i_end;i++){
		var current=code_lsit[i],index=current.slice(0,-1);
		if(!code_dict.hasOwnProperty(index)){
			code_dict[index]=[];
		}
		code_dict[index].push(current);
	}
	for (var c in code_dict){
		temp_list.push(code_dict[c]);
	}
	return temp_list;
}

//点击树后调用过滤
PT.Table.BaseTableObj.prototype.tree_check=function(tree, item, status){
	PT.instance_table.filter_kw_list();
}

//批量抢排名
PT.Table.BaseTableObj.prototype.bulk_rob_ranking=function(){
	if(this.has_checked_row()){
		var that=this,error_count=0,unfull_count=0,total_count=0,keyword_list={},msg,min_obj,max_obj,limit_obj,rob_min,rob_max,rob_limit;

		$('#rob_table tbody tr').each(function(){
			if($(this).find('.rob_set').hasClass('fail')||$(this).find('.rob_set').hasClass('success')){
				return;
			}
			var obj=$(this).data('rob');
			min_obj=obj.o_min;
			max_obj=obj.o_max;
			limit_obj=obj.o_limit;

			rob_min=Number(min_obj.val());
			rob_max=Number(max_obj.val());
			rob_limit=Number(limit_obj.val());
			total_count++;

			if(rob_min!=''||rob_max!=''||rob_limit!=''){
				if(that.check_rob_input(min_obj,[1,100],true)&&that.check_rob_input(max_obj,[1,100],true)&&that.check_rob_input(limit_obj,[0.05,99.99],false)){
					if(rob_min>rob_max){ //确保最小值小于最大值
						min_obj.addClass('red_border');
						max_obj.addClass('red_border');
						error_count++;
					}else{
						min_obj.removeClass('red_border');
						max_obj.removeClass('red_border');
						//keyword_list.push([obj.word,obj.kw_id,obj.campaign_id,obj.item_id,Number(rob_min),Number(rob_max),Number(rob_limit)]);
						keyword_list[obj.kw_id]=[Number(rob_min),Number(rob_max),Number(rob_limit)];
					}
				}else{
					error_count++;
				}
			}else{
				min_obj.removeClass('red_border');
				max_obj.removeClass('red_border');
				limit_obj.removeClass('red_border');
				unfull_count++;
			}

		});
		if(total_count>(error_count+unfull_count)){
			msg='当前有关键词:'+total_count+'个,输入有误'+error_count+'个,未填写'+unfull_count+'个。您确定要批量抢排名吗？';
			if(confirm(msg)){//会栈溢出所以不用PT.cnfirm
				that.start_rob_ranking(keyword_list);
			}
		}else{
			alert('没有正确设置的关键词，请重新设置！');//会栈溢出所以不用PT.alert
		}
	}
	$('#batch_optimize_box').removeClass('show');
}

//验证抢抢排名输入合法性
PT.Table.BaseTableObj.prototype.check_rob_input=function(obj,limit_arr,is_int){
	var num=parseFloat(obj.val());
	if(isNaN(num)||num<limit_arr[0]||num>limit_arr[1]||(is_int&&parseInt(num)!=num)){
		obj.addClass('red_border');
		return false;
	}else{
		obj.removeClass('red_border');
		return true;
	}
}

//开始抢排名
PT.Table.BaseTableObj.prototype.start_rob_ranking=function(keyword_list){
//	PT.show_loading('正在执行抢排名');
//	$('#rob_info').slideUp(300);
//	$('.new_price').removeClass('yello_border');
//	PT.sendDajax({'function':'web_rob_ranking','adgroup_id':adgroup_id,'keyword_list':$.toJSON(keyword_list),'lock_status':1,'ip':$('#ip_zone').val()});
}

//抢排名回调函数
PT.Table.BaseTableObj.prototype.rob_ranking_call_back=function(data){
	var i,obj,kw_list=[],rob_info_change=0,rob_info_unchange=0,rob_error=0,msg='';
	for (i in data){
		kw_list.push(data[i].kw_id);
		//obj=$('#'+data[i].kw_id).data('obj');
		obj=this.row_cache[data[i].kw_id];
		if(data[i].state==0){ //抢成功并在期望排名区间
			//obj.new_price_input.addClass('yello_border');
			var new_price=(data[i].new_price/100).toFixed(2);
			obj.new_price_input.val(new_price);
			obj.nRow.find('.max_price').text(new_price);
			obj.max_price=new_price;
			obj.check_ranking_btn.text(data[i].rank);
			rob_info_change++;
			obj.set_row_up(true,3);
			obj.show_rob_info(1,new_price,data[i].rank);
		}
		if(data[i].state==1){ //表示执行成功
			obj.check_ranking_btn.text('100+');
			obj.set_row_up(true,2);
			rob_info_unchange++;
			obj.show_rob_info(2);
		}
		if(data[i].state==2){ //表示执行失败
			//obj.check_ranking_btn.text(data[i].rank);
			obj.set_row_up(true,1);
			obj.show_rob_info(2);
			rob_error++;
		}
	}

	//排序相关
	var row_obj=this.get_checked_row(),kw_list_str=String(kw_list);

//	row_obj.each(function(){
//		var obj=$(this).parent().parent().data('obj');
//		if(kw_list_str.indexOf(obj.kw_id)!=-1){
//			obj.set_row_down();
//		}
//	});
	for (var i=0,i_end=row_obj.length;i<i_end;i++){
		var obj=this.row_cache[row_obj[i].parentNode.parentNode.id];
		if(kw_list_str.indexOf(obj.kw_id)!=-1){
			obj.set_row_down();
		}
	}
	this.data_table.fnSort([ [0,'desc']]);
	this.set_checked_count();
	setTimeout(function(){
//		$('#rob_info_change').text(rob_info_change);
//		$('#rob_info_unchange').text(rob_info_unchange);
//		$('#rob_info_error').text(rob_error);
//		$('#rob_info').stop().slideDown(300);
		msg="执行结果：达到期望排名"+rob_info_change+"个 未达期望排名"+rob_info_unchange+"个 失败"+rob_error+"个";
		//PT.alert(msg);
		alert(msg);//会栈溢出所以不用PT.alert
	},16);

}

PT.Table.BaseTableObj.prototype.row_list=function(){
	return this.table_obj.find('tbody tr:not([class*="noSearch"])');
}

//显示或隐藏列 参数 [[1,true],[2,false]]
PT.Table.BaseTableObj.prototype.hide_custom_column=function(iCol){
	var custom_column=[];
	for (var i in iCol){
		var bVis = this.data_table.fnSettings().aoColumns[iCol[i][0]].bVisible;
		if(iCol[i][1]!=bVis){
			this.data_table.fnSetColumnVis(iCol[i][0], iCol[i][1]);
		}
		if(!iCol[i][1]){
			custom_column.push(iCol[i][0]);
		}
	}
	this.recount_table_width(custom_column,true);
}

//计算关键词表格宽度
PT.Table.BaseTableObj.prototype.recount_table_width=function(custom_column,manual){
	var th_list=this.table_obj.find('th'),
	style_dict={'th_width01':185,'th_width02':75,'th_width1':63,'th_width2':30,'th_width3':45,'th_width00':8,'th_width03':160,'th_width04':110},
	table_width=0,
	re=new RegExp('th_width\\d*','g'),
	th_hide=[];

	if(!manual){
		if(custom_column==''||custom_column==undefined){
			custom_column=this.DEFAULT_HIDE_COLUMN;
		}
		if(String(custom_column).indexOf('all')!=-1){ //区分于默认显示项目
			custom_column=[];
		}
		for (var t=0;t<custom_column.length;t++){
			if(typeof this.COLUM_DICT[custom_column[t]]!=undefined){
				th_hide.push(this.COLUM_DICT[custom_column[t]])
			}
		}
	}else{
		th_hide=custom_column;
	}

//	th_list.each(function(){
//		if($(this).css('display')!='none'){
//			var class_name=this.className.match(re);
//			if(class_name==undefined){
//				return false;
//			};
//			table_width+=style_dict[class_name]+17;
//		}
//	});
for (var i=0;i<th_list.length;i++){
		var hide=false;
		for (var s=0,s_end=th_hide.length;s<s_end;s++){
			if(i==th_hide[s]){
				hide=true;
			}
		}

		if(hide){
			continue;
		}

		if($(th_list[i]).css('display')!='none'){
			var class_name=th_list[i].className.match(re);
			if(class_name==undefined){
				return false;
			};
			table_width+=style_dict[class_name]+17;
		}
}
//	if (table_width>1280) {
//		$('body').css('min-width',table_width+84);
//	}
	$('body').css('min-width',table_width+84);
	this.table_obj.show();
};

//隐藏表格
PT.Table.BaseTableObj.prototype.loading_table=function(){
	this.table_obj.hide();
	$('#loading_keyword').show();
}

//获取使用默认出价的行的个数
PT.Table.BaseTableObj.prototype.calc_default_price_row=function(){
	var num=0,that=this;
	this.row_list().each(function(){
		var obj=that.row_cache[this.id];
		if(obj.default_price==obj.max_price){
			num++;
		}
	})

	return num;
}

//保存用户自定义列
PT.Table.BaseTableObj.prototype.save_custom_column=function(){
	var column_list=[],that=this;

	$('#select_column li:not([class*="title"]) input').each(function(){
		if(!this.checked){
			for (var i in that.COLUM_DICT){
				if (parseInt(this.value)==that.COLUM_DICT[i]){
					column_list.push(i);
					break;
				}
			}
		}
	});
	if(!column_list.length){
		column_list=['all'];
	}
	// PT.sendDajax({'function':'web_save_custom_column','column_str':$.toJSON(column_list)});
}

//更新所有关键词的样式
PT.Table.BaseTableObj.prototype.update_all_style=function(){
	var that=this;
	this.row_list().each(function(){
		var obj=that.row_cache[this.id];
		obj.update_style();
	})
}

PT.Table.BaseTableObj.prototype.unbind_scroll_event=function(){
	$(window).off('scroll.PT.Table');
}

PT.Table.BaseTableObj.prototype.init_scroll_event=function(){
	if($.browser.msie&&Number($.browser.version)<9){
		return;
	}
	var that=this;
	//关键词信息浮动
	$(window).on('scroll.PT.Table',function(){
		if(that.data_table==undefined){
			return;
		}
		var body_ofset = document.body.scrollTop | document.documentElement.scrollTop;
		var body_ofset_left = document.body.scrollLeft | document.documentElement.scrollLeft;
		var base_top=that.data_table.offset().top-40;
		if (body_ofset>base_top&&base_top>0){
			$('#fixed_box').addClass('active').css({'marginLeft':-body_ofset_left+43,'width':$('#fixed_box').parent().width()});
			if(this.fixed_header==undefined){
				this.fixed_header=new FixedHeader(that.data_table,{"offsetTop":40});
			}
		}else{
			$('#fixed_box').removeClass('active').css({'marginLeft':0,'width':'auto'});

				if(this.fixed_header!=undefined){
					$(this.fixed_header.fnGetSettings().aoCache[0].nWrapper).remove();
				}
				this.fixed_header=null;

		}
	});
}

PT.Table.BaseTableObj.prototype.get_adgroup_title=function(){
	return $('#adgroup_title').text();
}

PT.Table.BaseTableObj.prototype.required_recover=function(){//询问是否重置关键词状态
	var temp_count=this.plus_count+this.fall_count+this.match_count+this.del_count;
	if(temp_count>0){
		PT.confirm('您有'+temp_count+'个词改变了出价或者匹配模式，但是没有提交到直通车，您需要重置这些关键词吗？',this.bulk_recover_all,[],this,'','','',['重置','不重置']);
	}
}

//提交操作近一步确认信息
//PT.Table.BaseTableObj.prototype.next_submit_verify=function(){
//	var msg='';
//	if((this.plus_count+this.fall_count+this.match_count+this.del_count)>0){
//		msg='加价:'+this.plus_count+' 降价:'+this.fall_count+' 匹配:'+this.match_count+' 删除:'+this.del_count
//		PT.confirm(msg,this.curwords_submit,[],this)
//	}else{
//		PT.light_msg('提交操作：','没有关键词改变，请进行操作');
//	}
//}

//改变过滤信息
PT.Table.BaseTableObj.prototype.change_filter_tips=function(tree_checked_list_str,label_filter_list,custom_limit){
	var checked_num,msg='请选择过滤条件',prev_class="label label-info";
	if(tree_checked_list_str.length||label_filter_list.length||custom_limit.length){
		checked_num=this.get_checked_row_count();
		if(checked_num>0){
			msg='当前选中<span class="r_color">'+checked_num+'</span>个关键词';
			prev_class="label label-success";

		}else{
			msg='没有符合条件的关键词';
			prev_class="label label-important";
		}
	}
	$('#filter_tips').html(msg).prev().attr('class',prev_class);
}

//批量强排名设置
PT.Table.BaseTableObj.prototype.bulk_rob_set=function(){

		var rob_min,rob_max,rob_limit;
		rob_min=$('#rob_worder_select').val().split('-')[0];
		rob_max=$('#rob_worder_select').val().split('-')[1];
		rob_limit=Number($('#rob_worder_input').val());
		if(isNaN(rob_limit)||rob_limit<0.05||rob_limit>99.99){
			PT.alert('统一限价必须是0.05到99.99的数字，请重新填写');
			return;
		}
		$('#rob_table tbody tr').each(function(){
			var obj=$(this).data('rob');
			//obj.recover_rob_input();
			obj.o_min.val(rob_min);
			obj.o_max.val(rob_max);
			obj.o_limit.val(rob_limit);
		});
		//$('#batch_optimize_box').removeClass('show');

}

//显示抢排名的box
PT.Table.BaseTableObj.prototype.show_rob_box=function(){
	if(this.has_checked_row()){
		var template_str,data,i,data,that=this;
		data=that.get_rob_data();

		for(i in data){
			template_str+=template.render('template_rob_tr',data[i]);
		}

		$('#rob_table tbody').html(template_str);

		$('#rob_box').modal();

		setTimeout(function(){
		var config={
			"bRetrieve":true,
			"bPaginate": false,
			"bFilter": false,
			"bInfo": false,
			"bAutoWidth":false,//禁止自动计算宽度
			"aaSorting":[],
			"fnCreatedRow":that.fnRobRowCallback,
			"aoColumns": [
				{"bSortable": false},
				{"bSortable": true},
				{"bSortable": false},
				{"bSortable": true},
				{"bSortable": true},
				{"bSortable": true},
				{"bSortable": true},
				{"bSortable": true},
				{"bSortable": false}
			],
			"oLanguage": {
				"sEmptyTable":'没有质量得分5分以上的词,请重新选择！'
		}}

		if(Number(i)>8){
			config['sScrollY']="300px";
		}

		$('#rob_table').dataTable(config);
		$('#rob_table_box').fadeTo(300,1);
		},1000);

		if(!data.length){
			return false;
		}

		return true;
	}
	$('#batch_optimize_box').removeClass('show');
}

//获取强排名的表格的信息
PT.Table.BaseTableObj.prototype.get_rob_data=function(){
	var that=this,data=[],default_row=['qscore','impressions','ppc','avgpos','g_cpc']
		,row_obj=this.get_checked_row();
//	row_obj.each(function(){
//		var index,temp={},obj=$(this).parent().parent().data('obj');
//		index=that.table_obj.fnGetPosition($(this).parent()[0])[0];
//		temp['kw_id']=obj.kw_id;
//		temp['keyword']=obj.word;
//		temp['max_price']=obj.max_price;
//		for (var i=0,i_end=default_row.length;i<i_end;i++){
//			temp[default_row[i]]=that.data_table.fnGetData(index,that.COLUM_DICT[default_row[i]]);
//		}
//		if(temp['qscore']<=5){//过滤5分以下的词
//			obj.check_box().attr('checked',false);
//			return;
//		}
//		data.push(temp);
//	});
	for (var i=0,i_end=row_obj.length;i<i_end;i++){
		var index,temp={},obj=this.row_cache[row_obj[i].parentNode.parentNode.id];
		index=this.table_obj.fnGetPosition(row_obj[i].parentNode.parentNode);
		temp['kw_id']=obj.kw_id;
		temp['keyword']=obj.word;
		temp['max_price']=obj.max_price;
		for (var t=0,t_end=default_row.length;t<t_end;t++){
			temp[default_row[t]]=this.data_table.fnGetData(index,this.COLUM_DICT[default_row[t]]);
		}
		if(temp['qscore']<=5){//过滤5分以下的词
			obj.check_box().attr('checked',false);
			continue;
		}
		data.push(temp);
	}
	return data;
}

PT.Table.BaseTableObj.prototype.fnRobRowCallback=function(nRow, aData, iDisplayIndex, iDisplayIndexFull){
	var row_data=new PT.Table.RobTable(nRow);
	$(nRow).data('rob',row_data);
}

PT.Table.BaseTableObj.prototype.bulk_rob_reset=function(){
	$('#rob_table tbody tr').each(function(){
		var obj=$(this).data('rob');
		$(this).find('.rob_set').removeClass('fail');
		obj.o_min.val('');
		obj.o_max.val('');
		obj.o_limit.val('');
	});
}

PT.Table.BaseTableObj.prototype.show_trend=function(keyword_id, category_list, series_cfg_list){
	var cmap_title = $('#title_'+keyword_id).text();
	$('#camp_trend_title').text(cmap_title);
	PT.draw_trend_chart( 'camp_trend_chart' , category_list, series_cfg_list);
	$('#modal_camp_trend').modal();
}

//抢排名的行对象
PT.Table.RobTable=function(obj){
	this.nRow=$(obj);
	this.kw_id=obj.id.replace('rob_','');
	this.o_max_price=this.nRow.find('.max_price');
	this.o_rank=this.nRow.find('.rank');
	this.o_min=this.nRow.find('.rob_min');
	this.o_max=this.nRow.find('.rob_max');
	this.o_limit=this.nRow.find('.rob_limit');
}

PT.Table.RobTable.prototype.set_ranking=function(rank){
	this.o_rank.html(rank);
}
