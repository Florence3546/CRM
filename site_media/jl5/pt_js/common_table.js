PT.namespace('Table');
PT.namespace('instance_table');

PT.Table.TB_HIDE_COLUMN = ['qscore', 'rank', 'rt_forecast'];
PT.Table.TB_LIMIT_QSCORE=5; //6分以下不预估排名
PT.Table.TB_LIMIT_FPRECAST_COUNT=201; //批量预估不超过
PT.Table.TB_LIMIT_FORECAST_ORFER='<div class="rel"><select class="f12 p0 h22 abs t50 mt-10 w80 l0 ml5 l0"><option>因淘宝限制，'+PT.Table.TB_LIMIT_QSCORE+'分以下无法预估，请谅解</option></select></div>';
PT.Table.LOADING_HTML = "<img src='/site_media/jl5/images/forecast_orde_ajax.gif'>"


PT.Table.BaseRowObj=function(obj,hide_clum){
    this.kw_id=obj.id;
    this.nRow=$(obj);
    this.hide_clum=hide_clum;
    //this.cat_id = this.nRow.attr('cat_id');
    this.adgroup_id=this.adgroup_id||$('#adgroup_id').val()||this.nRow.attr('adgroup_id');
    this.item_id=this.item_id||$('#item_id').val()||this.nRow.attr('item_id');
    this.campaign_id=this.campaign_id||$('#campaign_id').val()||this.nRow.attr('campaign_id');
    this.default_price=this.default_price||$('#default_price_hide').val();

    this.word=$('#word_'+this.kw_id).text();
    this.match_span=this.nRow.find('.match');
    this.match_scope=this.match_span.attr('scope');
    this.new_price_input=this.nRow.find('.new_price');
    this.order_new_price=this.nRow.find('.order_new_price');
    this.max_price=parseFloat(this.nRow.find('.max_price').text());
    this.forecast_order_btn=this.nRow.find('.forecast_order_btn');
    this.rt_forecast_order_btn=this.nRow.find('.rt_forecast_order_btn');
    this.check_ranking_btn=this.nRow.find('.check_ranking');
    this.rt_check_ranking_btn=this.nRow.find('.rt_check_ranking');
    this.g_cpc=parseFloat(this.nRow.find('.g_cpc').text());

//  this.or_lable=this.nRow.attr('or_lable');
//  this.and_lable=this.nRow.attr('and_lable');
    this.label_code=this.nRow.attr('label_code');

    this.rt_rank_data = {};
    this.match_changed=0;//匹配状态
    this.kw_del=0;      //删除状态
    //this.is_del();      //屏蔽首次进入建议出价
}

PT.Table.BaseRowObj.prototype.is_del=function(){
    if(this.nRow.find('.optm_type').text()=='1'){
        this.kw_del=1;
    }
}

PT.Table.BaseRowObj.prototype.check_box=function(){
    return this.nRow.find('[type=checkbox]');
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

    this.new_price_input.removeClass('green orange red').attr('disabled',false);
    this.nRow.removeClass('kw_del');

    if(this.kw_del){
        this.nRow.addClass('kw_del');
        this.new_price_input.attr('disabled',true);
    }else{
        this.is_plus()?this.new_price_input.addClass('orange'):'';
        this.is_fall()?this.new_price_input.addClass('green'):'';
        this.is_limit()?this.new_price_input.addClass('red'):'';
    }
    this.order_new_price.text(this.new_price_input.val());
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
    this.rt_forecast_order();
    this.update_style();
    this.calc_action_count();
}

PT.Table.BaseRowObj.prototype.delete_kw=function(statue){
    this.kw_del=statue;
//  this.update_style();
//  this.calc_action_count();
}

PT.Table.BaseRowObj.prototype.recover_kw=function(){
    this.kw_del=0;
    this.new_price_input.val(Number(this.max_price).toFixed(2));
    this.set_match_scorp(this.match_scope);
//  this.update_style();
//  this.calc_action_count();
}

PT.Table.BaseRowObj.prototype.forecast_order=function(tip){//tip 用来判断是否弹出消息框
    if (PT.Table.TB_HIDE_COLUMN.indexOf('forecast') >= 0) {
        return;
    }
    var _tip=(tip==undefined)?true:tip;
    // if(!this.forecast_order_limit(_tip)){
//        var kw_id_list,
//            forecast_data=this.nRow.data('forecast_data');
//        if(forecast_data==undefined){
        if(this.v_forecast_select().length==0){
            this.forecast_order_btn.html(PT.Table.LOADING_HTML);
//            kw_id_list=[this.kw_id];
//            PT.sendDajax({'function':'web_get_forecast_order_list','kw_id_list':kw_id_list});
            PT.sendDajax({'function':'web_get_keywords_rankingforecast','kw_id_list':[this.kw_id]});
        }else{
            this.chose_current_rank();
        }
    // }else if (PT.instance_table.bulk_forecast==1){//质量得分小于5并且在批量优化中
    //     this.forecast_order_btn.replaceWith(PT.Table.TB_LIMIT_FORECAST_ORFER);
    //     PT.instance_table.bulk_forecast_order();
    // }
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
        template_str = template.compile(pt_tpm['template_forecast_select.tpm.html'])({'kw_id':this.kw_id, 'rank_data':handle_rank_data(rank_data)});
        this.forecast_order_btn.replaceWith(template_str);
//      this.nRow.data('forecast_data',rank_data);
        this.chose_current_rank();

        $('#forecast_order_'+this.kw_id).change(function(){
            that.new_price_input.val(this.value.split('-')[0]);
            that.update_style();
            that.calc_action_count();
        });
    } else {
        rank_data = rank_data.length>0?rank_data:'淘宝返回预估排名数据为空';
        template_str=template.compile(pt_tpm['template_forecast_select_fail.tpm.html'])({'error_msg':rank_data});
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

PT.Table.BaseRowObj.prototype.rt_forecast_order=function(){//tip 用来判断是否弹出消息框
    if (PT.Table.TB_HIDE_COLUMN.indexOf('rt_forecast') >= 0) {
        return;
    }
    this.nRow.find('.forecast_rank_info').hide();
    this.rt_forecast_order_btn.html(PT.Table.LOADING_HTML)
    this.nRow.find('.forecast_rank_before').show();
    this.check_rt_rank_data(0, this.v_new_price());
}

//设置预估出价
PT.Table.BaseRowObj.prototype.check_rt_rank_data=function(is_check_rank, price){
    if (this.rt_rank_data.hasOwnProperty(price)){
        this.set_rt_rank_data(is_check_rank, price)
    } else {
        PT.sendDajax({'function':'web_get_kws_rtrank_forecast', 'adg_id': this.adgroup_id,
              'kw_id': this.kw_id, 'price': price, 'is_check_rank': is_check_rank});
    }
}

//设置预估出价
PT.Table.BaseRowObj.prototype.get_rt_rank_data_back=function(is_check_rank, price, rank_data){
    if (rank_data.hasOwnProperty('pc_rank')) {
        this.rt_rank_data[price] = rank_data;
    }
    this.set_rt_rank_data(is_check_rank, price)
}

//设置预估出价
PT.Table.BaseRowObj.prototype.set_rt_rank_data=function(is_check_rank, price){
    var that=this, template_str="",
        rank_data = this.rt_rank_data[price],
        flag = is_check_rank? 'check': 'forecast';
    if (rank_data) {
        var rank_info = this.nRow.find('.'+ flag +'_rank_info');
        rank_info.find('.pc').html(rank_data.pc_rank);
        rank_info.find('.yd').html(rank_data.mobile_rank);
        this.nRow.find('.'+ flag +'_rank_before').hide();
        rank_info.fadeIn(200);
    } else {
        var class_str = is_check_rank? 'rt_check_ranking': 'rt_forecast_order_btn';
        this.nRow.find('.'+ class_str).html("稍后重试"); // 不要直接用this.rt_forecast_order_btn，会有缓存bug
    }

    if ((!is_check_rank) && PT.instance_table.bulk_rt_forecast) {
        this.nRow.find('.rt_forecast_order_btn').attr('switch','0');
        PT.instance_table.bulk_rt_forecast_order();
    }
    if (is_check_rank && PT.instance_table.bulk_rt_check) {
        this.nRow.find('.rt_check_ranking').attr('switch','0');
        PT.instance_table.bulk_rt_check_order();
    }
}

// //设置预估出价
// PT.Table.BaseRowObj.prototype.set_rt_forecast_order=function(rank_data, is_check_rank){
//     var that=this, template_str="";
//     if (rank_data) {
//         this.nRow.find('.rt_rank_before').hide();
//         var rob_rank_info = this.nRow.find('.rt_rank_info');
//         rob_rank_info.find('.pc').html(rank_data.pc_rank);
//         rob_rank_info.find('.yd').html(rank_data.mobile_rank);
//         rob_rank_info.fadeIn();
//     } else {
//         var template_str="淘宝返回预估排名数据为空";
//         this.nRow.find('.rt_forecast_order_btn').replaceWith(template_str); // 不要直接用this.rt_forecast_order_btn，会有缓存bug
//     }
// }


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
    var temp_price;
    select_obj.find('option').each(function (i) {
        temp_price = Number(this.value.split('-').slice(-1)[0]);
        if (i==0 && !temp_price) {
	        return true;
        } else if (new_price>=temp_price) {
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
    this.check_ranking_btn.html(PT.Table.LOADING_HTML);
    PT.sendDajax({'function':'web_get_word_order','adgroup_id':this.adgroup_id,'item_id':this.item_id,'keyword_id':this.kw_id,'ip':PT.instance_table.v_zone_ip()});
}


//查排名
PT.Table.BaseRowObj.prototype.rt_check_ranking=function(){
    this.rt_rank_data = {};
    this.nRow.find('.check_rank_info').hide();
    this.rt_check_ranking_btn.html(PT.Table.LOADING_HTML);
    this.nRow.find('.check_rank_before').show();
    this.check_rt_rank_data(1, this.max_price);
}

//设置排名
PT.Table.BaseRowObj.prototype.set_ranking=function(rank){
    this.check_ranking_btn.html(rank);
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
//  PT.light_msg('改变词类型','当前选中'+obj.find("option:selected").text())
//}

//开启磨盘
PT.Table.BaseRowObj.prototype.magic_hollowware=function(){
    PT.Base.goto_ztc(5, 0, 0, this.word);

//  var template=$('#template_magic_hollowware').html();
//  $(template).modal();
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
//  this.update_style();
//  this.calc_action_count();
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
//  this.update_style();
//  this.calc_action_count();
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

PT.Table.BaseRowObj.prototype.parse_keyword=function(){
    //PT.show_loading('正在解析屏蔽词');
    PT.sendDajax({'function':'web_parse_keyword', 'word':this.word, 'keyword_id':this.kw_id});
};

PT.Table.BaseRowObj.prototype.attention_call_back=function(statue){
    var obj=this.nRow.find('.attention'),that=this;
    if(statue==0){
        obj.removeClass('silver');
        PT.light_msg('关注成功','您可以再次点击取消关注', 2000);
    }else{
        obj.addClass('silver');
//        if(PT.hasOwnProperty('Attention')){//判断在我的关注中调用
//            this.nRow.fadeTo(300,0).queue(function(next){
//                $('#keyword_count').text(Number($('#keyword_count').text())-1)
//                that.delete_row();
//                $(this).dequeue();
//            });
//        }else{
//            PT.light_msg('取消关注成功','您可以再次点击添加关注',2000);
//        }
        PT.light_msg('取消关注成功','您可以再次点击添加关注',2000);
    }
    obj.off('click').on('click.PT.e',function(){
        that.change_attention(statue);
    });
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
    this.fixed_header=null;

    this.init_event();
    this.get_keyword_data();
    this.check_limit_price();

    //用来隐藏列对应的字典
//    this.COLUM_DICT={'keyword':1,'new_price':2,'forecast':3,'max_price':4,'rank':5,'qscore':6,'create_days':7,'impressions':8,'click':9,'ctr':10,'cost':11,'ppc':12,'cpm':13,'avgpos':14,'favcount':15,'favctr':16,'favpay':17,'paycount':18,'pay':19,'conv':20,'roi':21,'g_pv':22,'g_click':23,'g_ctr':24,'g_cpc':25,'g_competition':26};
    //默认隐藏列
    this.DEFAULT_HIDE_COLUMN=['cpm','avgpos','favctr','favpay','g_pv','g_ctr','g_cpc','g_competition','create_days']
    //隐藏列的值保存到每行的data中
    this.NEED_SAVE_COLUMN=['qscore', 'g_click', 'roi'];
    //扩展回调
    this.init_ajax_event_list=[];
    this.row_cache={};
}

PT.Table.BaseTableObj.prototype.weird_switch = function () {
    var habit=PT.get_habit();
    if(habit&&habit['weird_switch']===0){
        $('#keyword_seitch').removeClass('on').addClass('off');
        return 0;
    }else{
        $('#keyword_seitch').removeClass('off').addClass('on');
        return 1;
    }
} ();

PT.Table.BaseTableObj.prototype.check_limit_price=function(){
    var limit=$('#user_limit_price input').val();
    if(limit!=''){
        this.KW_LIMIT_PRICE=limit;
    }
}

//用来隐藏列对应的字典
PT.Table.BaseTableObj.prototype.COLUM_DICT={'keyword': 1, 'new_price': 2, 'rt_forecast': 3, 'forecast': 4, 'max_price': 5,
                                            'rt_rank': 6, 'rank': 7, 'new_qscore':8, 'qscore':9, 'create_days': 10, 'impressions': 11,
                                            'click': 12, 'ctr': 13, 'cost': 14, 'ppc': 15, 'cpm': 16,
                                            'avgpos': 17, 'favcount': 18, 'favctr': 19, 'favpay': 20, 'paycount': 21,
                                            'pay': 22, 'conv': 23, 'roi': 24, 'g_pv': 25, 'g_click': 26,
                                            'g_ctr': 27, 'g_cpc': 28, 'g_competition': 29
                                            };

//dataTable默认列参数
PT.Table.BaseTableObj.prototype.custom_aoColumns=[
    {"bSortable": true,"sSortDataType": "custom-text", "sType": "custom","sClass": "no_back_img tc"},
    {"bSortable": false},
    {"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
    {"bSortable": false, "sClass": 'tc', "sType": "custom", "sSortDataType": "custom-text"},
    {"bSortable": false, "sClass": 'tc'},
    {"bSortable": true, "sClass": 'tc', "sType": "custom", "sSortDataType": "custom-text"},
    {"bSortable": false, "sClass": 'tc', "sType": "custom", "sSortDataType": "custom-text"},
    {"bSortable": true},
    {"bSortable": false, "sType": "custom","sSortDataType": "custom-text"},
    {"bSortable": true, "sType": "custom", "sSortDataType": "custom-text"},
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

PT.Table.BaseTableObj.prototype.sort_table=function(custom_column){
    var that=this, custom_aoColumns=this.custom_aoColumns;

    if(custom_column==''||custom_column==undefined){
        custom_column=this.DEFAULT_HIDE_COLUMN;
    }

    if(String(custom_column).indexOf('all')!=-1){ //区分于默认显示项目
        custom_column=[];
    }

    for (var i in PT.Table.TB_HIDE_COLUMN) {
        custom_column.push(PT.Table.TB_HIDE_COLUMN[i]);
    };

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
}

//当datatable绘制每个tr时调用,在此生成每一行的信息并缓存到tr上
PT.Table.BaseTableObj.prototype.fnRowCallback=function(nRow, aData, iDisplayIndex, iDisplayIndexFull){
    //隐藏列的值保存到每行的data中
    var NEED_SAVE_COLUMN=PT.instance_table['NEED_SAVE_COLUMN'],hide_clum={},COLUM_DICT=PT.instance_table['COLUM_DICT'];

    for (var i in NEED_SAVE_COLUMN){
        if(aData[COLUM_DICT[NEED_SAVE_COLUMN[i]]].indexOf('custom')!=-1){
//            hide_clum[NEED_SAVE_COLUMN[i]]=$(aData[COLUM_DICT[NEED_SAVE_COLUMN[i]]])[0].innerHTML;
            hide_clum[NEED_SAVE_COLUMN[i]]=$(aData[COLUM_DICT[NEED_SAVE_COLUMN[i]]]).eq(0).text();
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

PT.Table.BaseTableObj.prototype.init_event=function(){
    var that=this;

    $('.select_status').click(function(){
        if(that.weird_switch){
            return;
        }
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
        var optm_type = $(this).attr('optm_type');
        optm_type = optm_type?optm_type:'';
        var mnt_type = Number($('#mnt_type').val()) || 0;

        if(mnt_type==0 && (limit_val==undefined||limit_val=='')){
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
                msg+='。<br><span class="red">其中有'+limit_count+'个关键词改价超过了'+limit_val+'元！</span>';
            }
            msg+='<div>亲，确认提交到直通车吗？</div>';
            PT.confirm(msg, that.curwords_submit, [optm_type], that)
        }else{
            PT.alert('没有关键词改变，请进行操作');
        }

    });


    //批量降价
    $('#bulk_fall_btn').click(function(){
        that.bulk_price_router('fall');
        $(this).parents('.dropdown').removeClass('open');
    });

    //批量改价
    $('#bulk_up_btn').click(function(){
        that.bulk_price_router('plus');
        $(this).parents('.dropdown').removeClass('open');
    });

    //自定义出价
    $('#bulk_custom_btn').click(function(){
        that.bulk_price_router('custom');
        $(this).parents('.dropdown').removeClass('open');
    });

    // //批量删除
    $('#bulk_del_btn').click(function(){
        that.bulk_del();
    });

    //批量恢复
    // $('#bulk_recover_btn').click(function(){
    //  that.bulk_recover();
    // });

    //批量设置匹配
    $('#bulk_match_btn').click(function(){
        var match_scorp=parseInt($('#keyword_match input[name="bulk_match_radio"]:checked').val());
        that.bulk_match(match_scorp);
        $(this).parents('.dropdown').removeClass('open');
    });

    //批量预估排名
    $('#bulk_worder_btn').click(function(){
        if($("input:checkbox[name=idx]:checked").length>0){
            that.bulk_worder();
            $(this).parents('.dropdown').removeClass('open');
        }else{
            PT.alert("请先选择关键词！");
        }

    });

    $('#keyword_seitch').on('change',function(e,statue){
        if (statue == undefined) {
            that.weird_switch = ($(this).hasClass('on'))? 1:0;
        }else{
            that.weird_switch=(statue)?1:0;
        }
        var jq_d = $('.common_table_sort_dropdown'),
            jq_i = $('.common_table_sort_dropdown .iconfont');
        if(that.weird_switch){
            jq_i.hide();
            $('.common_table_sort_dropdown').off('change');
            $('.common_table_sort_dropdown .dropdown-menu').css({'display': 'none'});
            that.start_weird_class();
            $('span:first','.select_status').removeClass('tdl');
            $('#filter_tag').html('');
            $('#refine_box input:checked').attr('checked',false)
            that.set_checked_count();
        }else{
            that.start_sort();
            jq_i.show();
            $('.common_table_sort_dropdown').on('change');
            $('.common_table_sort_dropdown .dropdown-menu').css({'display': ''});
            that.table_obj.find('tbody tr.weird').remove();
            that.table_obj.find('tbody tr').removeClass('hide');
            $('span:first','.select_status').addClass('tdl');
            that.data_table.fnSort([[0,'desc']]);
        }
        PT.set_habit({'weird_switch':that.weird_switch});
    });

    $("#select_column").find(".ul_line").each(function(){
        var lis = $(this).find("input");
        for(i=1;i<lis.length;i++){
            $(lis[i]).on('change',function(){
                var all_checked = true;
                for(n=1;n<lis.length;n++){
                    if(!$(lis[n]).attr("checked")){
                        all_checked = false;
                        break;
                    }
                }
                if(all_checked){
                    $(lis[0]).attr("checked","checked");
                }else{
                    $(lis[0]).attr("checked",false);
                }
            });

            $(lis[0]).on('change',function(){
                for(n=1;n<lis.length;n++){
                    if($(lis[0]).attr("checked")){
                        $(lis[n]).attr("checked","checked");
                    }else{
                        $(lis[n]).attr("checked",false);
                    }
                }
            });
        }

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
        if(mode=='save'){
            that.save_custom_column();
            $('#batch_optimize_count').text($('input[class="input-small new_price orange"]').length+$('input[class="input-small new_price green"]').length);
            $('.green').parent().parent().find("input[type=checkbox]").attr("checked","checked");
            $('.orange').parent().parent().find("input[type=checkbox]").attr("checked","checked");
            $(".father_box").attr("checked",false);
            $("#common_table tr").removeClass("bg_striped");
        }
    });

    //定制列计算
    $('#select_column_show_btn').click(function(){
        var obj=that.data_table.fnSettings().aoColumns,inputs=$('#select_column');
        for (var i in obj){
            inputs.find('input[value="'+i+'"]').attr('checked',obj[i].bVisible)
        }

        $("#select_column").find(".ul_line").each(function(){
            var lis = $(this).find("input");
            var all_checked = true;
            for(i=1;i<lis.length;i++){
                if(!$(lis[i]).attr("checked")){
                    all_checked = false;
                    break;
                }
            }
            if(all_checked){
                $(lis[0]).attr("checked","checked")
            }
        });
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

    $(document).on('change', '.common_table_sort_dropdown', function (e, v) {
        if (that.weird_switch) {
            return;
        }

        var old_index = that.COLUM_DICT[$(this).parent().attr('th_name')],
            new_index=$(this).parents('table').find('th').index($(this).parent()),
            prev_val=$(this).find('.dropdown-toggle').attr('data-prev-value');

        if (!old_index) {
            return;
        }

        $(this).find('.dropdown-toggle').attr('data-prev-value',v);

        var dataTable=that.data_table;

        $(dataTable.fnSettings().aoData).each(function(){
            var currentTd=this.nTr.children[new_index],
                currentObj=$(currentTd).find('.'+v),
                value = currentObj.text();
            if (!value) {
                value = 102;
            } else if (value == '>100') {
                value = 101;
            }
            $(currentTd).find('>span:first').text(value);
        });

        if (v === prev_val){ //默认点击一次为降序，点击两次则升降序交替
            if (dataTable.fnSettings().aaSorting[0][1]==="asc"){
                dataTable.fnSort([[old_index,'desc']]);
            }else{
                dataTable.fnSort([[old_index,'asc']]);
            }
        }else{
            dataTable.fnSort([[old_index,'desc']]);
        }
    })
}

PT.Table.BaseTableObj.prototype.display_word_parts=function(data){
    var dom=template.compile(pt_tpm['template_ban_word.tpm.html'])($.evalJSON(data));
    $(dom).modal();
};

PT.Table.BaseTableObj.prototype.init_ajax_event=function(){
    var that=this;

    //关键词搜索
    $('.search_btn').click(function(){
        var search_word=$(this).prev().val();
        $('.search_btn').prev().val(search_word);
        if(search_word!=''){
            that.search_word_and_sort(search_word);
        }else{
            PT.alert('请填写要搜索的关键词');
        }
    });
    $('.search_val').keyup(function (e) {
        if (e.keyCode==13) {
            $(this).siblings('.search_btn').click();
            $(this).focus();
        }
    });

    //批量预估排名
    $('#bulk_forecast_order').click(function(){
        if(that.has_checked_row()){
            that.start_bulk_forecast_order();
        }
    });


    //批量预估排名
    $('#bulk_rt_forecast_order').click(function(){
        if(that.has_checked_row()){
            that.start_bulk_rt_forecast_order();
        }
    });

    //批量预估排名
    $('#bulk_rt_check_order').click(function(){
        if(that.has_checked_row()){
            that.start_bulk_rt_check_order();
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
        var keyword_id=this.parentNode.parentNode.parentNode.id;
        that.row_cache[keyword_id].change_match_scorp();
        that.row_cache[keyword_id].calc_action_count();
    });

    //改变出价时调用
    this.table_obj.find('.new_price').change(function(){
        that.row_cache[this.parentNode.parentNode.id].change_new_price();
    });

    //删除关键词
    this.table_obj.find('.remove').click(function(){
        var keyword_id=this.parentNode.parentNode.parentNode.id;
        if(that.row_cache[keyword_id].kw_del){
            that.row_cache[keyword_id].delete_kw(0);
        }else{
            that.row_cache[keyword_id].delete_kw(1);
        }
        that.row_cache[keyword_id].update_style();
        that.row_cache[keyword_id].calc_action_count();
    });

    //恢复关键词各个状态
    this.table_obj.find('.recovery').click(function(){
        //$(this).parent().parent().parent().parent().data('obj').recover_kw();
        that.row_cache[this.parentNode.parentNode.id].recover_kw();
        that.row_cache[this.parentNode.parentNode.id].update_style();
        that.row_cache[this.parentNode.parentNode.id].calc_action_count();
        that.row_cache[this.parentNode.parentNode.id].chose_current_rank();
    });

    //将关键词标记为
    this.table_obj.find('.attention').click(function(){
        var state=0;
        if($(this).hasClass('silver')){ //如果有灰色则表示当前是未关注的状态
            state=1;
        }
        //$(this).parent().parent().parent().data('obj').change_attention(state);
        that.row_cache[this.parentNode.parentNode.parentNode.id].change_attention(state);
    });

    //解析关键词
    this.table_obj.find('.icon-ban-circle').click(function(){
       that.row_cache[this.parentNode.parentNode.id].parse_keyword();
    });

    //单个预估排名
    this.table_obj.find('.forecast_order_btn').click(function(){
        //$(this).parent().parent().data('obj').forecast_order();
        that.row_cache[this.parentNode.parentNode.id].forecast_order();
    });

    //单个预估排名
    this.table_obj.find('.rt_forecast_order_btn').click(function(){
        that.row_cache[this.parentNode.parentNode.parentNode.id].rt_forecast_order();
    });

    //查看当前排名
    this.table_obj.find('.check_ranking').click(function(){
        //$(this).parent().parent().data('obj').check_ranking();
        that.row_cache[this.parentNode.parentNode.id].check_ranking();
    });

    //查看当前排名
    this.table_obj.find('.rt_check_ranking').click(function(){
        that.row_cache[this.parentNode.parentNode.parentNode.id].rt_check_ranking();
    });

    this.table_obj.find('.js_rt_check').click(function(){
        that.row_cache[this.parentNode.parentNode.parentNode.parentNode.id].rt_check_ranking();
    });

    //关键词魔方
    this.table_obj.find('.word').click(function(){
        //$(this).parent().parent().parent().parent().data('obj').magic_hollowware();
        that.row_cache[this.parentNode.parentNode.parentNode.id].magic_hollowware();
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
        $('.select_status span:odd').text(0);
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
        that.row_cache[this.parentNode.parentNode.parentNode.id].show_chart();
    });

    $select({name: 'idx','callBack': this.set_checked_count,'that':this}); //shift多选

    this.data_table.fnSettings()['aoDrawCallback'].push({ //当表格排序时重新初始化checkBox右键多选
        'fn':function(){selectRefresh()},
        'sName':'refresh_select'
    });

    this.init_scroll_event();
    $('.tips').tooltip();

    // 展示质量得分详情
    this.table_obj.find('.qscore').children().popover({
        'trigger':'hover',
        'content':function () {
                return template.compile(pt_tpm['keyword_qscore_details.tpm.html'])({
                    'qscore':$(this).attr('qscore'),
                    'cust_score':$(this).attr('cust_score'),
                    'creative_score':$(this).attr('creative_score'),
                    'rele_score':$(this).attr('rele_score'),
                    'cvr_score':$(this).attr('cvr_score'),
                });
            },
        'html':true,
        'placement':'right'
    });

    // 展示质量得分详情
    this.table_obj.find('.new_qscore').popover({
        'trigger':'hover',
        'content':function () {
                return template.compile(pt_tpm['keyword_qscore_details_new.tpm.html'])({
                    'qscore':$(this).attr('qscore'),
                    'cust_score':$(this).attr('cust_score'),
                    'creative_score':$(this).attr('creative_score'),
                    'rele_score':$(this).attr('rele_score'),
                    'cvr_score':$(this).attr('cvr_score'),
                    'score_type':$(this).attr('score_type'),
                    'plflag':$(this).attr('plflag'),
                    'wireless_matchflag':$(this).attr('wireless_matchflag')
                });
            },
        'html':true,
        'placement':'right'
    });

    for (var fn in this.init_ajax_event_list){
        this.init_ajax_event_list[fn](this);
    }

    $('#keyword_seitch').change();
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
    var msg = '预估排名执行时间较长，您确定要执行吗？<div class="red mt5">说明：预估排名直接获取的淘宝数据，因为没有实际竞价，预估结果可能不准</div>';
    if(this.get_checked_row_count()>PT.Table.TB_LIMIT_FPRECAST_COUNT){
        msg += '<div class="red mt5">同时，由于淘宝接口调用量限制，一次最多预测'+PT.Table.TB_LIMIT_FPRECAST_COUNT+'个质量得分大于'+PT.Table.TB_LIMIT_QSCORE+'的关键词</div>';
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
    PT.light_msg('批量预估','执行完成');
}

//开始批量预估
PT.Table.BaseTableObj.prototype.start_bulk_rt_forecast_order=function(){
    this.bulk_rt_forecast=1;
    this.rt_forecasted=0;
    this.bulk_rt_forecast_order();
}

//停止批量预估
PT.Table.BaseTableObj.prototype.stop_bulk_rt_forecast_order=function(){
    this.rt_bulk_forecast=0;
}

PT.Table.BaseTableObj.prototype.bulk_rt_forecast_order=function(){
    var current_btn=$(this.table_obj.find('input[type="checkbox"]:checked').parent().parent().find('.rt_forecast_order_btn[switch="1"]')[0]);
    if (this.rt_forecasted<=PT.Table.TB_LIMIT_FPRECAST_COUNT && current_btn.length){
        this.rt_forecasted++;
        this.row_cache[current_btn.parent().parent().parent().attr('id')].rt_forecast_order();
    } else {
        this.bulk_rt_forecast = 0;
        this.rt_forecasted = 0;
        $('.rt_forecast_order_btn').attr('switch','1');
    }
}

PT.Table.BaseTableObj.prototype.start_bulk_rt_check_order=function(){
    this.bulk_rt_check=1;
    this.rt_checked=0;
    this.bulk_rt_check_order();
}

PT.Table.BaseTableObj.prototype.bulk_rt_check_order=function(){
    var current_btn=$(this.table_obj.find('input[type="checkbox"]:checked').parent().parent().find('.rt_check_ranking[switch="1"]')[0]);

    if (current_btn.length){
        this.rt_forecasted++;
        this.row_cache[current_btn.parent().parent().parent().attr('id')].rt_check_ranking();
    } else {
        this.bulk_rt_check = 0;
        this.rt_checked = 0;
        $('.rt_check_order_btn').attr('switch','1');
    }

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

PT.Table.BaseTableObj.prototype.curwords_submit=function(optm_type){
    var data=[],that=this;
    this.row_list().each(function(){
        var obj=that.row_cache[this.id];
        if (obj.is_modified()){
            data.push({
                    'keyword_id':parseInt(obj.kw_id),
                    'adgroup_id':parseInt(obj.adgroup_id),
                    'campaign_id':parseInt(obj.campaign_id),
                    'word':obj.word,
                    'is_del':obj.kw_del,
                    'new_price':obj.v_new_price(),
                    'max_price':obj.max_price,
                    'match_scope':obj.v_match_scope()
            })
        }
    });

    PT.show_loading('正在提交数据');
    PT.sendDajax({'function': 'web_curwords_submit',
                             'data': $.toJSON(data),
                             'optm_type':optm_type,
                             'mnt_type':$('#mnt_type').val() || 0,
                             'campaign_id':$('#campaign_id').val() || 0
                             });
}

//自定义csv数据格式
PT.Table.BaseTableObj.prototype.creat_scv_data=function(){
    var data_str1 = '关键词\t当前出价\t',
        data_str2 = '养词天数\t展现量\t点击量\t点击率\t总花费\t平均点击花费\t千次点击花费\t昨日平均排名\t收藏量\t收藏率\t收藏成本\t成交量\t成交额\t转化率\t投资回报\t全网展现指数\t全网点击指数\t全网点击率\t全网市场均价\t全网竞争度\n';
        data_str = '';
    var start_j = 9;
    if (PT.Table.TB_HIDE_COLUMN.indexOf('qscore') >= 0) {
        data_str = data_str1 + 'PC质量得分\t移动质量得分\t' + data_str2;
        start_j = 8;
    }else {
        data_str = data_str1 + '质量得分\t' + data_str2;
    }
    for (var i=0,i_end=this.data_table.fnSettings()['aiDisplay'].length;i<i_end;i++){
        var nRow=this.data_table.fnGetNodes(i);
        var keyword=$(nRow).find('.word').text();
        var td_list=this.data_table.fnGetData(i);

        data_str+=keyword+'\t';
        if (i==0) {
            data_str+='-\t';
        } else {
            data_str+=$(td_list[5]).text()+'元\t';
        }
        for (var j=start_j,j_end=td_list.length;j<j_end;j++){
            if (j==8 && i>0) {
                var qscore_list = $(td_list[j]).map(function(){return $(this).hasClass('new_qscore')? $.trim($(this).text()):null;});
                data_str += qscore_list[0]+'\t'+qscore_list[1]+'\t';
                j++;
                continue;
            } else if(isNaN(Number(td_list[j]))&&td_list[j].indexOf('custom')!=-1){
                if (j==24) {
                    data_str += $.trim($(td_list[j]).eq(4).text()) + '\t';
                } else {
                    data_str+=$.trim($(td_list[j]).eq(0).text())+'\t';
                }
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
        failed_count = json.failed_kw.length,
        top_del_count = json.top_del_kw.length;

    var msg='修改成功:'+update_count+'个，删除成功:'+del_count+'个';
    if (top_del_count){
        msg+='，其中'+top_del_count+'个关键词已在淘宝被删除！';
    }
    if(failed_count){
        msg+='操作失败:'+failed_count+'个';
    }
    for (var i=0;i<del_count;i++){
        this.row_cache[json.del_kw[i]].delete_row();
    }
    for (var i=0;i<top_del_count;i++){
        this.row_cache[json.top_del_kw[i]].delete_row();
    }
    for (var i=0;i<update_count;i++){
        this.row_cache[json.update_kw[i]].update_row();
    }
    /*
    if(json.optm_submit_time!=null&&(del_count>0||update_count>0)){ //更新上次优化提交时间
        $('#optimize_time').text(json.optm_submit_time.substr(0,json.optm_submit_time.indexOf('.')));
    }*/

    this.set_kw_count();
    this.set_checked_count();
    this.calc_action_count();
    PT.hide_loading();
    PT.alert(msg);
    $('a[href="#history_keyword_box"]').removeAttr('switch'); //删除词后将已删词的开关打开
    $('#history_kw_count').text(Number($('#history_kw_count').text())+del_count+top_del_count); //改写已删词个数

    if(this.weird_switch){
        this.start_weird_class();
        $('span:first','.select_status').removeClass('tdl');
        $('#filter_tag').html('');
        $('#refine_box input:checked').attr('checked',false)
        this.set_checked_count();
    }
}

PT.Table.BaseTableObj.prototype.set_bwords_callback=function(data){
    var del_kw_list = $.evalJSON(data);
    for (var i=0;i<del_kw_list.length;i++){
        this.row_cache[del_kw_list[i]].delete_row();
    }
    this.set_kw_count();
    PT.alert("设置成功！");
};

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
    $('span:first','.select_status').addClass('tdl');
    $('#keyword_seitch').removeClass('on').addClass('off');
    this.weird_switch = 0;
}

//加价降价路由函数
PT.Table.BaseTableObj.prototype.bulk_price_router=function(type){
    var that=this;
    if(this.has_checked_row()){
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
            var delta=$('#custom_price').val();
            this.bulk_plus(type,delta,'int');
        }
        if(!isNaN(type)){
            this.bulk_plus(type);
        }
    }
    this.calc_action_count();
    setTimeout(function(){
        that.update_all_style();
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
        if(base_type=="custom"){
            PT.alert('请输入自定义价格');
        }else{
            PT.alert('请输入加价幅度');
        }
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

//  row_obj.each(function(){
//      var obj=$(this).parent().parent().data('obj');
//      obj.bulk_plus(base_type,delta,mode,limit);
//  });

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

//  row_obj.each(function(){
//      var obj=$(this).parent().parent().data('obj');
//      obj.fall_plus(base_type,delta,mode,limit);
//  });
    for (var i=0,i_end=row_obj.length;i<i_end;i++){
        var obj=this.row_cache[row_obj[i].parentNode.parentNode.id];
        obj.fall_plus(base_type,delta,mode,limit);
    }
}


//获取选中的行
PT.Table.BaseTableObj.prototype.get_checked_row=function(){
    return this.table_obj.find('tbody tr[id] input:checked');
}

//计算选中的个数
PT.Table.BaseTableObj.prototype.get_checked_row_count=function(){
    return this.get_checked_row().length;
}

//检查是否有选中的关键词并给出提示
PT.Table.BaseTableObj.prototype.has_checked_row=function(){
    // var mnt_type = Number($('#mnt_type').val()) || 0;
    // if(mnt_type==0 && this.get_checked_row_count()==0){
    if(this.get_checked_row_count()==0){
        PT.light_msg('', '没有选中任何关键词');
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

//      row_obj.each(function(){
//          var obj=$(this).parent().parent().data('obj');
//          obj.delete_kw();
//      });
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

//      row_obj.each(function(){
//          var obj=$(this).parent().parent().data('obj');
//          obj.recover_kw();
//      });
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

//      row_obj.each(function(){
//          var obj=$(this).parent().parent().data('obj');
//          obj.set_match_scorp(match_scorp);
//      });
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
//          row_obj.each(function(){
//              var obj=$(this).parent().parent().data('obj');
//              obj.set_want_order();
//          });
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
    var mnt_type = Number($('#mnt_type').val()) || 0;
    $('#current_check_count').text(this.get_checked_row_count());
    $('#batch_optimize_count').text(this.get_checked_row_count());
    $('#del_kw_count').text(this.get_checked_row_count());
    this.row_list().each(function(){
        var obj=that.row_cache[this.id];
        if(obj.is_checked()){
            $(this).addClass('selected');
        }else{
            $(this).removeClass('selected');
//            if (mnt_type==1 || mnt_type==2) {
//                obj.recover_kw();
//                obj.update_style();
//                obj.calc_action_count();
//            }
        }
    });
    // if (mnt_type==1 || mnt_type==2) {
    //     that.bulk_del();
    // }
}

// PT.Table.BaseTableObj.prototype.get_smart_optimize_argv=function(){
//      var json={}
//      json['stgy']=$('#smart_optimize input[name="strategy"]:checked').val();
//      json['rate']=$('#id_rate').val();
//      json['executor']=$('#stgy_executor').val();
//      json['cfg']=$('#stgy_cfg').val();
//      return $.toJSON(json);
// }

PT.Table.BaseTableObj.prototype.init_label_event=function(){
    var that=this;

    $('#refine_box').on('change','input[type=checkbox]',function(){
        that.filter_kw_list();
    })

    $('#filter_tag').on('click','.select',function(){
        var i=0,filter_list=$(this).find('i').data().value.split(',');
        for (var i,i_end=filter_list.length;i<i_end;i++){
            if($('#refine_'+filter_list[i]).length){
                $('#refine_'+filter_list[i]).find('input[type=text]').val('');
            }else{
                $('#refine_box input[type=checkbox][value='+filter_list[i]+']').attr('checked',false);
            }
        }
        that.filter_kw_list();
    });

    $('#refine_box button.custom').on('click',function(){
        $(this).parents('.dropdown').removeClass('open');
        that.filter_kw_list();
    })
}

//根据数据生成标签列表
PT.Table.BaseTableObj.prototype.layout_bulk_search=function(data){
    var input_dom='',i;
    for (i in data){
        if(data[i].cond.length){
            input_dom=template.compile(pt_tpm['keyword_custom_select.tpm.html'])(data[i]);
            $('#refine_'+data[i].id).html(input_dom).prev().removeAttr('disabled');
        }
    }

    this.init_label_event();
}

//判断是否是用户输入
PT.Table.BaseTableObj.prototype.is_custom_filter=function(id){
    var obj=$('#'+id),inputs;
    inputs=obj.find('input[type="text"]');
    for (var i=0;i<inputs.length;i++){
        if($(inputs[i]).val()!=''){
            $('#selected_conditions .right li[index='+id+']').remove();
            return true ;
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

//过滤关键词列表
PT.Table.BaseTableObj.prototype.filter_kw_list=function(){
    var that=this;
    setTimeout(function(){
        var custom_limit=[],filter_list=that.get_label_code_list();
        $('#refine_box .dropdown-menu').each(function(){
            var min,max,obj=$(this);
            min=Number(obj.find('input[type=text]:eq(0)').val());
            max=Number(obj.find('input[type=text]:eq(1)').val());
            if (min||max){
                custom_limit.push([obj.attr('id').replace('refine_',''),min,max]);
            }
        });
        if (filter_list.length||custom_limit.length){
            var row=that.row_list();
            for (var i=0,i_end=row.length;i<i_end;i++){
                var lable_judge=0,obj=that.row_cache[row[i].id],lable=String($.trim(obj.label_code).split(' ').slice(1));
                for (var c = 0, c_end = filter_list.length; c < c_end; c++) {
                    var lable_temp_judge = 0;
                    for (var f = 0, f_end = filter_list[c].length; f < f_end; f++) {
                        if (lable.indexOf(filter_list[c][f]) != -1) {
                            lable_temp_judge = 1;
                            break;
                        }
                    }

                    if (lable_temp_judge) {
                        continue;
                    } else {
                        break;
                    }
                }

                for (var j=0,j_end=custom_limit.length;j<j_end;j++){
                    var current_val,custom_judge=0;
                    if(that.NEED_SAVE_COLUMN.indexOf(custom_limit[j][0])!=-1){
                        current_val=parseFloat(obj.hide_clum[custom_limit[j][0]]);
                    }else{
                        current_val=parseFloat(obj.nRow.find('.'+custom_limit[j][0]).text());
                    }
                    if(!isNaN(current_val)){
                        if(custom_limit[j][1]&&custom_limit[j][2]&&(current_val<custom_limit[j][1]||current_val>custom_limit[j][2])){
                        //存在最小值和最大值
                            custom_judge=0;
                        }else if((custom_limit[j][1]&&(current_val<custom_limit[j][1])) || (custom_limit[j][2]&&(current_val>custom_limit[j][2]))){
                        //存在一个值
                            custom_judge=0;
                        }else{
                            custom_judge=1;
                        }
                    }else{
                        custom_judge=0;
                    }
                }

                lable_temp_judge===undefined?lable_judge=custom_judge:custom_judge===undefined?lable_judge=lable_temp_judge:lable_judge=custom_judge&&lable_temp_judge;

                if(lable_judge){
                    obj.set_row_up(true);
                }else{
                    obj.set_row_down(false);
                }
            }

        }else{

            that.table_obj.find('[type=checkbox]').attr('checked',false);
        }

        if(!that.weird_switch){
            that.data_table.fnSort([[0,'desc']]);
        }

        that.set_checked_count();
        //生成label
        var filter_str='',custom_dict={'max_price':'当前出价','ctr':'点击率','click':'点击量','cpc':'花费','roi':'ROI','qscore':'质量得分'}
        for (var c=0,c_end=filter_list.length;c<c_end;c++){
            var title=$('#refine_box input[type=checkbox][value='+filter_list[c][0]+']').data().title,status='';
            for (var t = 0, t_end = filter_list[c].length; t < t_end; t++) {
                status+=$('#refine_box input[type=checkbox][value='+filter_list[c][t]+']').data().status+'，';
            }
            filter_str+='<li class="select"><a href="javascript:;">'+title+'：'+status.slice(0,-1)+'<i data-value="'+filter_list[c]+'"></i></a></li>';
        }
        for (var j=0,j_end=custom_limit.length;j<j_end;j++){
            if(custom_limit[j][1]&&custom_limit[j][2]){
                filter_str+='<li class="select"><a href="javascript:;">'+custom_dict[custom_limit[j][0]]+':'+custom_limit[j][1]+'~'+custom_limit[j][2]+'<i data-value="'+custom_limit[j][0]+'"></i></a></li>';
            }else{
                if(custom_limit[j][1]){
                    filter_str+='<li class="select"><a href="javascript:;">'+custom_dict[custom_limit[j][0]]+':大于'+custom_limit[j][1]+'<i data-value="'+custom_limit[j][0]+'"></i></a></li>';
                }else{
                    filter_str+='<li class="select"><a href="javascript:;">'+custom_dict[custom_limit[j][0]]+':小于'+custom_limit[j][2]+'<i data-value="'+custom_limit[j][0]+'"></i></a></li>';
                }
            }
        }
        $('#filter_tag').html(filter_str);
        return;
    },17);
}

//获得显示的过滤条件
PT.Table.BaseTableObj.prototype.get_label_code_list = function() {
    var code_lsit = [],
        temp;
    $('#refine_box .dropdown-menu').each(function(i) {
        temp = [];
        if ($('input:checked', this).length) {
            $('input:checked', this).each(function() {
                temp.push(this.value);
            });
            code_lsit.push(temp);
        }
    });
    return code_lsit;
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
    PT.show_loading('正在执行抢排名');
    $('#rob_info').slideUp(300);
    $('.new_price').removeClass('yello_border');
    PT.sendDajax({'function':'web_rob_ranking','adgroup_id':this.adgroup_id,'keyword_list':$.toJSON(keyword_list),'lock_status':1,'ip':$('#ip_zone').val()});
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

//  row_obj.each(function(){
//      var obj=$(this).parent().parent().data('obj');
//      if(kw_list_str.indexOf(obj.kw_id)!=-1){
//          obj.set_row_down();
//      }
//  });
    for (var i=0,i_end=row_obj.length;i<i_end;i++){
        var obj=this.row_cache[row_obj[i].parentNode.parentNode.id];
        if(kw_list_str.indexOf(obj.kw_id)!=-1){
            obj.set_row_down();
        }
    }
    this.data_table.fnSort([ [0,'desc']]);
    this.set_checked_count();
    setTimeout(function(){
//      $('#rob_info_change').text(rob_info_change);
//      $('#rob_info_unchange').text(rob_info_unchange);
//      $('#rob_info_error').text(rob_error);
//      $('#rob_info').stop().slideDown(300);
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
    if(this.weird_switch){
        this.start_weird_class()
    }
    $('#common_table th').removeClass('hide');
}

//关键词分类 what a fuck?
PT.Table.BaseTableObj.prototype.start_weird_class=function(){
    var class_dict={'o011':[600,'有转化'],'o012':[500,'有收藏，无转化'],'o013':[400,'有点击，无收藏，无转化'],'o02':[300,'有展现，无点击'],'o03':[200,'无展现'],'o04':[100,'今日新加词']},row=this.row_list(),row_num;

    for (var i=0,i_end=row.length;i<i_end;i++){
        var obj=this.row_cache[row[i].id],lable=String($.trim(obj.label_code).split(' ')[0]);
        obj.set_row_up(false,(class_dict[lable][0])+Number(obj.max_price));
    }
    this.data_table.fnSort([[0,'desc']]);

    for (var c in class_dict){
        var tr_obj=$('#common_table tr[label_code*= '+c+']');
        tr_obj.first().before('<tr class="noSearch weird"> <th class="w12 nbl tc"> <input class="kid_box" type="checkbox" rule="'+c+'"> </th> <th colspan="'+(obj.nRow.find('td').length-1)+'" class="tl poi" rule="'+c+'">'+class_dict[c][1]+'<span>'+tr_obj.length+'个</span> <i class="icon-chevron-down"></i></th> </tr>');
     }

     this.shield_sort();
     this.bing_weird_checked();
     this.toggle_weird();
}

//分类的复选框事件绑定
PT.Table.BaseTableObj.prototype.bing_weird_checked=function(){
    var that=this;
    this.table_obj.find('tr.weird input').on('click',function(e){
        var ev = e || window.event, label_code=$(this).attr('rule'),there=this;
        ev.stopPropagation();
        if(label_code!=undefined){
            var kid_box=that.table_obj.find('tr[label_code*="'+label_code+'"] .kid_box').attr('checked',there.checked);
            setTimeout(function(){that.set_checked_count()},0);
        }
    });
}

//显示隐藏分类
PT.Table.BaseTableObj.prototype.toggle_weird=function(){
    var that=this;
    this.table_obj.find('tr.weird th.poi').on('click',function(){
        var label_code=$(this).attr('rule'),
            objs=that.table_obj.find('tr[label_code*="'+label_code+'"]').toggleClass('hide');
            if (objs.first().hasClass('hide')){
                $(this).find('i').removeClass('icon-chevron-down').addClass('icon-chevron-up');
            }else{
                $(this).find('i').removeClass('icon-chevron-up').addClass('icon-chevron-down');
            }
    });

}

//屏蔽排序
PT.Table.BaseTableObj.prototype.shield_sort=function(){
    var aoColumns=this.data_table.fnSettings().aoColumns,i=0;
    for (i;i<aoColumns.length;i++){
        if(aoColumns[i].bSortable){
            aoColumns[i].nTh.className+=' no_back_img';
            aoColumns[i].bSortable=false;
        }
    }
}

//开启排序
PT.Table.BaseTableObj.prototype.start_sort=function(){
    var aoColumns=this.data_table.fnSettings().aoColumns,i=0;
    for (i;i<aoColumns.length;i++){
        if (aoColumns[i].nTh.className.indexOf('no_back_img')!=-1){
            if(i!==0){
                aoColumns[i].nTh.className=aoColumns[i].nTh.className.replace('no_back_img','');
            }
            aoColumns[i].bSortable=true;
        }
    }
}


//隐藏表格
// PT.Table.BaseTableObj.prototype.loading_table=function(){
//  //PT.show_loading('正在获取关键词');
//  $('#loading_keyword').show();
// }

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
    PT.sendDajax({'function':'web_save_custom_column','column_str':$.toJSON(column_list)});
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
    var that=this,box_obj=$('#fixed_box'),box_h=box_obj.height(),box_exists=$('#fixed_box').length,box_scroll=true;

    if(PT.get_habit()!==undefined&&PT.get_habit()['bulk_float_switch']===false){
        box_h=0;
        box_scroll=false;
    }
    //关键词信息浮动
    $(window).on('scroll.PT.Table',function(){
        if(that.data_table==undefined){
            return;
        }
        var body_ofset = document.body.scrollTop | document.documentElement.scrollTop;
        var body_ofset_left = document.body.scrollLeft | document.documentElement.scrollLeft;
        var base_top=box_exists&&box_obj.parent().offset().top||that.table_obj.offset().top;
        var box_p_w=box_obj.parent().width();
        if (body_ofset>base_top&&base_top>0){
            if(box_exists&&box_scroll){
                box_obj.addClass('fixed').css({'marginLeft':-body_ofset_left,'width':box_p_w});
                //that.table_obj.css('marginTop',box_h);
            }

            if(this.fixed_header==null){
                this.fixed_header=new FixedHeader(that.data_table,{"offsetTop":box_h});
            }
        }else{
            if(box_exists){
                box_obj.removeClass('fixed').css({'marginLeft':0,'width':'100%'});
                that.table_obj.css('marginTop',0);
            }
            if(this.fixed_header!=null){
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

PT.Table.BaseTableObj.prototype.show_trend=function(keyword_id, category_list, series_cfg_list){
    var cmap_title = $('#word_'+keyword_id).text();
    if (!$('#modal_camp_trend').length){
        $('body').append(pt_tpm["modal_camp_trend.tpm.html"]);
    }
    $('#camp_trend_title').text(cmap_title);
    PT.draw_trend_chart( 'camp_trend_chart' , category_list, series_cfg_list);
    $('#modal_camp_trend').modal();
}

//填充表格数据
PT.Table.BaseTableObj.prototype.layout_keyword = function(json) {
    var tr_str = '',
        kw_count = json.keyword.length,
        d;

    tr_str = template.compile(pt_tpm['keyword_nosearch_tabler.tpm.html'])(json.nosearch);

    for (var i = 0; i < kw_count; i++) {
        tr_str += template.compile(pt_tpm['keyword_common_table_tr.tpm.html'])(json.keyword[i]);
    }

    if (this.data_table){
        this.data_table.fnDestroy();
    }
    $('tbody', this.table_obj).html(tr_str);
}

//获取关键词列表
PT.Table.BaseTableObj.prototype.get_keyword_data = function() {
    PT.sendDajax({
        'function': 'web_adgroup_optimize',
        'adgroup_id': PT.Adgroup_optimize.adgroup_id,
        'last_day': PT.Adgroup_optimize.get_last_day(),
        'stgy_list': this.get_smart_optimize_argv(),
        'auto_hide': 0
    });
}

PT.Table.BaseTableObj.prototype.change_price_status_4data = function(data) {
    var result = data.keyword;
    for (var i in result) {
        var kw_id = result[i]['keyword_id'],
            obj = this.row_cache[kw_id];
        obj.new_price_input.val(result[i]['new_price']);
        obj.nRow.attr('label_code', result[i]['label_code'])
        obj.nRow.find('.optm_type').text(result[i]['optm_type']);
        if (result[i]['optm_type'] == '1') {
            obj.kw_del = 1;
        }
        if (result[i]['optm_reason']) {
            obj.nRow.find('i.info').attr('data-original-title', result[i]['optm_reason']).removeClass('hide');
        } else {
            obj.nRow.find('i.info').addClass('hide');
        }
    }
    this.table_obj.find('.tips').tooltip();
}
