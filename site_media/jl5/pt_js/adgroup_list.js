PT.namespace('Adgroup_list');
PT.Adgroup_list = function () {
    var search_type='all', //快速查找的类型
        PAGE_NO=1,
        PAGE_SIZE=100,//表格每页显示的记录数
        CONSULT_WW = $('#CONSULT_WW').val(),
        page_type = parseInt($('#page_type').val()),
        adgroup_table=null,
        camp_id=$('#campaign_id').val(),
        search_val=$('#search_val').val(),
        max_num= parseInt($('#mnt_max_num').val()),
        camp_mnt_type=parseInt($('#mnt_type').val()),
        sort = '';

    var get_last_day=function (){
        return $('.adgroup_select_days .dropdown-value').text().match(/\d+/)[0];
    };

    var init_table= function (){
        adgroup_table=$('#adgroup_table').dataTable({
            "bRetrieve": true, //允许重新初始化表格
            "bPaginate": false,
            "bFilter": true,
            "bInfo": false,
//            "aaSorting": [[3,'desc'],[4,'desc']],
            "bAutoWidth":false,//禁止自动计算宽度
            "sDom":'',
            "aoColumns": [
                {"bSortable": false},
                {"bSortable": false},
                {"bSortable": false},
                {"bSortable": false,"sSortDataType": "dom-text", "sType": "numeric","sClass": "no_back_img"},
                {"bSortable": false,"sSortDataType": "dom-text", "sType": "numeric","sClass": "no_back_img"},
                {"bSortable": true,"sSortDataType": "dom-text", "sType": "numeric"},
                {"bSortable": true,"sSortDataType": "dom-text", "sType": "numeric"},
                {"bSortable": false}
            ],
            "oLanguage": {
                "sZeroRecords": "没有符合要求的宝贝",
                "sInfoEmpty": "显示0条记录"
            }
        });
    };

    // 创建创意工厂订单
    var add_imgorder2 = function (item_id) {
        PT.sendDajax({'function':'cf_add_imgorder2',
                                'item_id':item_id,
                                'phone':$.trim($('#modal_contact_us .phone').val()),
                                'qq':$.trim($('#modal_contact_us .qq').val()),
                                'namespace':'Adgroup_list'
        });
    };

    var init_dom=function (){

        $('.page_size').text(PAGE_SIZE);

        //当计划切换时,重新获取数据
        $('#id_campaign_id').change(function (e,v){
            // PT.show_loading('正在切换计划');
            camp_id = v;
            window.location.href = '/web/adgroup_list/' + v;
            // get_adgs(1);
        });

        $('#search_btn').click(function (){
            search_adg();
        });

        $('#search_val').keyup(function(e){
            if (e.keyCode==13) {
                search_adg();
            }
        });

        //快速查找事件
        $('#id_quick_search').change(function(){
            search_type=$(this).attr('value');
            get_adgs(1);
        });

        // setTimeout(function(){
        //     PT.aks.start();
        // },PT.aks.delay);

        $('#select_campaign').click(function(){
            $.confirm({
                backdrop: 'static',
                width:'small',
                title:'请先选择推广计划',
                body:$('#select_campaign_div').html(),
                okHide:function(){
                    var camp_id = $('#campaign_2add_item').val();
                    window.location.href = '/web/adgroup_list/' + camp_id + '?add_item_flag=1';
                },
            });
        });

        $('.show_count').click(function(){
            // if($(this).data('is_lock')==1) {
            //     return;
            // }

            var type = $(this).val(),
                jq_table = $('#adgroup_table');
            var adg_id_arr = $.map(jq_table.find('tbody tr'), function(obj) {
                return Number(obj.id);
            });
            jq_table.find('.'+type+'_count_str').show();
            PT.sendDajax({
                'function':'web_get_adg_status',
                'type':type,
                'adg_id_list':$.toJSON(adg_id_arr),
                'namespace':'Adgroup_list'
            });
        });

        $('.adgroup_select_days').on('change',function(e,v){
            get_adgs(0);
        });

        $('#submit_mnt_oper').unbind('click');
        $('#submit_mnt_oper').click(function () {
            if ($('#modal_limit_price .loading_tag:visible').length) {
                PT.alert('正在加载数据，请等待加载完后再操作');
                return;
            }
            var limit_price = $.trim($('#adg_limit_price').val()),
                check_error = check_limit_price(limit_price);
            if (check_error=='') {
                $('#adg_limit_price').closest('div').removeClass('input_error');
                $('#modal_limit_price').modal('hide');
                var adg_id=parseInt($('#modal_limit_price').attr('adg_id'));
                $('#'+adg_id).find('.limit_price').text(Number(limit_price).toFixed(2)).parent().show();
                if ($('#modal_limit_price').attr('mnt_type')=='0') {
                    confirm_mnt_oper($('#modal_limit_price').attr('mnt_opt_type'), adg_id);
                } else {
                    PT.sendDajax({'function':'web_set_adg_limit_price', 'adgroup_id':adg_id, 'limit_price':Number(limit_price).toFixed(2), 'mnt_type':camp_mnt_type});
                }
            } else {
                $('#adg_limit_price').closest('div').addClass('input_error');
                $('#adg_limit_price').next().find('.iconfont').attr('data-original-title', check_error);
            }
        });

        // 创建创意工厂订单
        $('#modal_add_imgorder2 .submit_imgorder').click(function () {
            PT.show_loading('正在创建订单');
            add_imgorder2($(this).attr('item_id'));
//            PT.sendDajax({'function':'cf_add_imgorder2',
//                                    'item_id':$(this).attr('item_id'),
//                                    'phone':$.trim($('#modal_contact_us .phone').val()),
//                                    'qq':$.trim($('#modal_contact_us .qq').val()),
//                                    'namespace':'Adgroup_list'
//            });
        });

        // 修改联系方式
        $('#modal_contact_us .update_contact_info').click(function () {
            var phone = $.trim($('#modal_contact_us .phone').val()),
                org_phone = $('#modal_contact_us .phone').attr('org_value'),
                qq = $.trim($('#modal_contact_us .qq').val()),
                org_qq = $('#modal_contact_us .qq').attr('org_value');
            if (phone!=org_phone || qq!=org_qq) {
                PT.sendDajax({'function':'cf_update_contact_info',
                                        'contact_id':$(this).attr('contact_id'),
                                        'phone':phone,
                                        'qq':qq
                });
            } else {
                $('#modal_contact_us').modal('hide');
            }
        });

        $('button.update_adg').click(function(){
            var adg_id_arr=[], mode=$(this).attr('name'),
                mode_str = (mode=='start' ? '启动推广' : (mode=='stop' ? '暂停推广' : '删除【将在直通车后台消失且无法恢复，不要误删哦】'));
            if($(this).hasClass('single')){
                var adg_id_arr=[parseInt($(this).parents('tr').find('.kid_box').val())];
                if (mode=='del') {
                    PT.confirm('确认'+mode_str+'该宝贝？',update_adg_status,[mode,adg_id_arr]);
                } else {
                    update_adg_status(mode,adg_id_arr);
                }
                return;
            }else{
                var obj=$('#adgroup_table tbody .kid_box:checked');
            }
            obj.each(function(){
                adg_id_arr.push(parseInt($(this).val()));
            });
            if (adg_id_arr.length){
                if(mode=='del' && $(".father_box").is(':checked')){
                    PT.confirm('即将删除本页所有推广宝贝，删除后将在直通车后台消失且无法恢复，确认要删除吗？',confirm_update_adgs,[mode_str,mode,adg_id_arr]);
                } else {
                    confirm_update_adgs(mode_str,mode,adg_id_arr);
                }
            }else{
                PT.alert('请选择要操作的推广宝贝');
            }
        });


        $('#adgroup_table').on('click', '.edit_mobdiscount', function(){
            if (!$('#modal_adg_mobdiscount').length){
                $('body').append(pt_tpm["modal_adg_mobdiscount.tpm.html"]);
            }
            var adgroup_id = parseInt($(this).parent().parent().parent().parent().attr('id'));
            var discount = parseInt($('#adg_mobdiscount_'+adgroup_id).text());
            $('#adg_mobile_discount').val(discount);
            $('#id_set_adg_mobdiscount').val(adgroup_id);
            $('#modal_adg_mobdiscount').modal();
        });

        $('body').on('click.set_adg_mobdiscount','#save_mobdiscount', function(){
            var adgroup_id = parseInt($('#id_set_adg_mobdiscount').val());
         	var campaign_id = parseInt($('#adg_mobdiscount_'+adgroup_id).attr('campaign_id'));
            var discount = parseInt($('#adg_mobile_discount').val());
            var org_discount = parseInt($('#adg_mobdiscount_'+adgroup_id).text());
            if (org_discount == discount){
                $('#modal_adg_mobdiscount').modal('hide');
                return true;
            }else if(isNaN(discount) || discount>400 || discount <1){
                PT.alert("移动折扣要介于1%~400%之间哦亲！");
                return false;
            }else{
                PT.sendDajax({'function':'web_set_adg_mobdiscount', 'campaign_id':campaign_id, 'adgroup_id': adgroup_id, 'discount': discount, 'namespace': 'Adgroup_list'});
            }
        });

        $('body').on('click.use_camp_mobdiscount', "#use_camp_mobdiscount", function(){
            var adgroup_id = parseInt($('#id_set_adg_mobdiscount').val());
            var campaign_id = parseInt($('#adg_mobdiscount_'+adgroup_id).attr('campaign_id'));
            PT.sendDajax({'function': 'web_delete_adg_mobdiscount', 'adgroup_id': adgroup_id, 'campaign_id': campaign_id, 'namespace': 'Adgroup_list'});
        });

    };



    var search_adg=function() {
        search_val=$('#search_val').val();
        get_adgs();
    };

    var ajax_init_dom=function (){

        $('#adgroup_table .update_adg').click(function(){
            var adg_id_arr=[], mode=$(this).attr('name'),
                mode_str = (mode=='start' ? '启动推广' : (mode=='stop' ? '暂停推广' : '删除【将在直通车后台消失且无法恢复，不要误删哦】'));
            if($(this).hasClass('single')){
                var adg_id_arr=[parseInt($(this).parents('tr').find('.kid_box').val())];
                if (mode=='del') {
                    PT.confirm('确认'+mode_str+'该宝贝？',update_adg_status,[mode,adg_id_arr]);
                } else {
                    update_adg_status(mode,adg_id_arr);
                }
                return;
            }else{
                var obj=$('#adgroup_table tbody .kid_box:checked');
            }
            obj.each(function(){
                adg_id_arr.push(parseInt($(this).val()));
            });
            if (adg_id_arr.length){
                if(mode=='del' && $(".father_box").is(':checked')){
                    PT.confirm('即将删除本页所有推广宝贝，删除后将在直通车后台消失且无法恢复，确认要删除吗？',confirm_update_adgs,[mode_str,mode,adg_id_arr]);
                } else {
                    confirm_update_adgs(mode_str,mode,adg_id_arr);
                }
            }else{
                PT.alert('请选择要操作的推广宝贝');
            }
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
            get_checked_num();
        });

        $('input[class*="kid_box"]').click(function(){
            get_checked_num();
            $(this).parent().toggleClass('bg_silver');
            var all_num = $('input[class*="kid_box"]').length;
            var checked_num = $('input[class*="kid_box"]:checked').length;
            if(all_num == checked_num)
            	$('.father_box').attr("checked", true);
            else
            	$('.father_box').attr("checked", false);
        });

        $select({name: 'adg_checkbox','callBack': update_checked_status});
        adgroup_table.fnSettings()['aoDrawCallback'].push({ //当表格排序时重新初始化checkBox右键多选
            'fn':function(){selectRefresh()},
            'sName':'refresh_select'
        });

        $('#adgroup_table .dropdown>a').dropdown();
        $('.tips').tooltip({html: true});

        $('#adgroup_table').on('click', '.show_price_popover', function () {
            set_limit_price(this);
        });

        // $('#adgroup_table').on('click', '.mnt_oper.single', function(){
        //     var mnt_oper=Number($(this).attr('mnt_type')),
        //         new_num = parseInt($('.new_num').html()),
        //         adg_id=parseInt($(this).parents('tr').attr('id'));
        //     if (mnt_oper==0) {
        //         confirm_mnt_oper(mnt_oper,adg_id);
        //         return;
        //     }
        //     if(new_num<=0){
        //         var mnt_num= parseInt($('.mnt_num').html());
        //         PT.alert('已托管'+mnt_num+'个宝贝，达到了托管最大数，若要继续托管，请先删除一些已托管宝贝！');
        //     }else if(camp_mnt_type==2){
        //         set_limit_price(this);
        //     }else{
        //         confirm_mnt_oper(mnt_oper,adg_id);
        //     }
        // });

        $('#adgroup_table .change_mnt_type').on('shown',function(e){
            var mnt_opt_type=$(this).attr('mnt_opt_type'),
                mnt_type = $(this).attr('mnt_type');
            $('#adgroup_table .change_mnt_type').not(this).popover('hide');
            $('#adgroup_table').data('current_adgroup_id',$(this).parent().attr('id').replace('mnt_type_',''));

            target_value = mnt_type == 0? 0 : mnt_opt_type;
            $(this).next().find('input[name=mnt_type][value='+target_value+']').attr('checked',true);
            // $(this).next().find('label:eq(1)').hide();
            // 开放 只优化价格 功能给 长尾托管
            // if($(this).attr('page_type')==2){
            //     $(this).next().find('label:eq(1)').show();
            // }else{
            //     $(this).next().find('label:eq(1)').hide();
            // }

        });

        $('#adgroup_table').on('click','button[data-ok="popover"]',function(){
            var adg_id=$('#adgroup_table').data('current_adgroup_id'),
                mnt_oper=Number($(this).parent().prev().find('input:checked').val()),
                new_num = parseInt($('.new_num').html()),
                jq_i = $(this).parents('.popover').prev(),
                old_mnt_type = parseInt(jq_i.attr('mnt_type'));

            jq_i.popover('hide');

            if (mnt_oper===0) {
                confirm_mnt_oper(mnt_oper,adg_id);
                return;
            }
            if(new_num<=0 && old_mnt_type == 0 ){
                var mnt_num= parseInt($('.mnt_num').html());
                PT.alert('已托管'+mnt_num+'个宝贝，达到了托管最大数，若要继续托管，请先删除一些已托管宝贝！');
            }else if(camp_mnt_type==2 && old_mnt_type === 0){
                set_limit_price(this, mnt_oper);
            }else{
                confirm_mnt_oper(mnt_oper,adg_id);
            }


        });

        $('#adgroup_table').on('click','button[data-dismiss="popover"]',function(){
            $(this).parents('.popover').prev().popover('hide');
        });

        $('#adgroup_table .change_mnt_type').popover({
            'trigger':'click',
            'html':true,
            'placement':'right',
            'content':$('#mnt_type_box').html(),
            'multi':true   //同屏只显示一个
        });

        $('#adgroup_table .optm_crt_img').click(function () {
            var tr_obj = $(this).closest('tr');
            var item_id = $(this).attr('item_id'),
                item_title = tr_obj.find('.item_title:eq(0)').html(),
                item_price = tr_obj.find('.item_price:eq(0)').html(),
                item_pic_url = tr_obj.find('.item_pic_url:eq(0)').attr('src').replace('_100x100.jpg', '_160x160.jpg'),
                ppc = Number(tr_obj.find('.ppc:eq(0)').html()) || 0.3;
            $('#modal_add_imgorder2 .submit_imgorder').attr('item_id', item_id);
            $('#modal_add_imgorder2 .item_title').attr('href', 'http://item.taobao.com/item.htm?id='+item_id).html(item_title);
            $('#modal_add_imgorder2 .item_price').html(item_price);
            $('#modal_add_imgorder2 .item_pic_url').attr('src', item_pic_url);
            $('#modal_add_imgorder2 .saved_money:eq(0)').html(((ppc*1000)/6).toFixed());
            $('#modal_add_imgorder2 .saved_money:eq(1)').html(((ppc*1000)/3).toFixed());
            $('#modal_add_imgorder2 .saved_money:eq(2)').html(((ppc*1000)/2).toFixed());
            $('#modal_add_imgorder2').modal('show');
        });

        // 表格下拉全局排序
        $('#adgroup_table').off('change', '.table_g_sort_dropdown');
        $('#adgroup_table').on('change', '.table_g_sort_dropdown', function (e, v) {
            var dropdown_toggle = $(this).find('.dropdown-toggle:eq(0)');
            var prev_val = dropdown_toggle.attr('data-prev-value');
            var asc_desc = dropdown_toggle.attr('asc_desc') || -1;
            dropdown_toggle.attr('data-prev-value', v);
            if (v === prev_val) { // 默认点击一次为降序，点击两次则升降序交替
                asc_desc *= -1;
            } else {
                asc_desc = -1;
            }
            dropdown_toggle.attr('asc_desc', asc_desc);
            sort = v+'_'+String(asc_desc);
            get_adgs(0);
        });




    };

    //发送请求获取数据
    var get_adgs=function (is_reset){
        PT.show_loading('正在获取数据');
        if(is_reset){
            PAGE_NO=1;
            $('#dynamic_pager').html('').off('page');
        }
        PT.sendDajax({
            'function':'web_get_adgroup_list',
            'campaign_id':camp_id,
            'page_size':PAGE_SIZE,
            'page_no':PAGE_NO,
            'last_day':get_last_day(),
            'sSearch':search_val,
            'search_type':search_type,
            'auto_hide':0,
            'page_type':page_type,
            'offline_type':$('#offline_type').val(),
            'sort':sort
        });
    };

    var update_checked_status=function(){
        var kid_box=$('input[class*="kid_box"]');
        kid_box.each(function(){
            if ($(this).attr("checked")=="checked") {
                $(this).parent().addClass('bg_silver');
            } else {
                $(this).parent().removeClass('bg_silver');
            }
        });
        get_checked_num();
    };

    var get_checked_num=function() {
        var checked_num = $('input[class*="kid_box"]:checked').length;
        $('.current_count').text(checked_num);
        return checked_num;
    };

    var confirm_update_adgs=function (mode_str,mode,adg_id_arr){
        var opt_num=adg_id_arr.length;
        PT.confirm('确认'+mode_str+'所选的'+opt_num+'个宝贝吗？',update_adg_status,[mode,adg_id_arr]);
    };

    //改变宝贝的推广状态
    var update_adg_status=function (mode,adg_id_arr){
        PT.show_loading("正在提交数据到后台");
        PT.sendDajax({'function':'web_update_adg_status','adg_id_list':adg_id_arr,'mode':mode,'campaign_id':camp_id,'mnt_type':$('#mnt_type').val(),'namespace':'Adgroup_list'});
    };

    var change_tr_color=function(){
        var obj=$('#adgroup_table tbody input[type="checkbox"]');
        obj.each(function(){
            if($(this).attr('online_status')=='offline'){
                $(this).parents('tr').addClass('silver');
            }
        });
    };

    var handle_page=function(page_count,page_no){
        if(!page_count){
            page_no = 1;
            page_count = 1;
        }
        $('#dynamic_pager').bootpag({
                total: page_count,
                page: page_no,
                leaps: false,
                prev:'上一页',
                next:'下一页',
                maxVisible: 10
        }).on('page', function(event, num){
                PAGE_NO=num;
                get_adgs(0);
                $('.show_count').data('is_lock',0)
        });
    };

    var set_limit_price = function (obj, mnt_opt_type) {
        if (!mnt_opt_type) {
            mnt_opt_type = 1;
        }
        var adg_id = parseInt($(obj).closest('tr').attr('id'));
        var mnt_type = $(obj).closest('tr').attr('mnt_type');
        var limit_price=Number($(obj).closest('tr').find('.limit_price').text()).toFixed(2);
        limit_price=(limit_price==0?'':limit_price);
        $('#modal_limit_price').modal('show').attr({'adg_id':adg_id, 'mnt_type':mnt_type, 'mnt_opt_type':mnt_opt_type}).find('input').val(limit_price);
        $('#modal_limit_price .input_error').removeClass('input_error');
        $('#modal_limit_price [name="cat_path"]').empty();
        $('#modal_limit_price .cat_path').removeClass('danger_cat');
        $('#modal_limit_price [name="cat_avg_cpc"]').empty();
        $('#modal_limit_price .loading_tag').show();
        PT.sendDajax({'function':'mnt_get_cat_avg_cpc', 'adg_id':adg_id, 'namespace':'AddItemBox3'});
    };

    var confirm_mnt_oper=function(mnt_oper,adg_id) {
        PT.show_loading("正在提交数据到后台");
        PT.sendDajax({'function':'mnt_update_single_adg_mnt',
            'adg_id':adg_id,
            'flag':mnt_oper,
            'mnt_type':camp_mnt_type,
            'camp_id':camp_id,
            'limit_price':Number($.trim($('#adg_limit_price').val())) || 0
            });
    };

    var update_mnt_num=function(add_num){
        var mnt_num=parseInt($('.mnt_num').html()),
            new_num=parseInt($('.new_num').html());
        if (mnt_num+add_num>=0) {
            $('.mnt_num').html(mnt_num+add_num);
            $('.new_num').html(new_num-add_num);
        }
    };

    // 校验关键词限价
    var check_limit_price = function (limit_price){
        var error='';
        var limit_price_min = Number($('#modal_limit_price .limit_price_min').html()) || 1;
        var limit_price_max = Number($('#modal_limit_price .limit_price_max').html()) || 20;
        limit_price_min = Math.min(limit_price_min * 0.4, 0.50);
        if (PT.MntCampaign.mnt_opter > 1){ // 方便客服设置更低限价
            limit_price_min = 0.05;
        }
        if($.trim(limit_price)===''){
            error='值不能为空！';
        }else if(isNaN(limit_price)){
            error='值必须是数字！';
        }else if (Number(limit_price)<limit_price_min || Number(limit_price)>limit_price_max){
            error='值必须介于'+limit_price_min.toFixed(2)+'~'+limit_price_max.toFixed(2)+'元之间！';
        }
        return error;
    };

    return {
        //main function to initiate the module
        init: function () {
            init_dom();
            get_adgs(1);
        },
        append_table_data:function (page_info, data, mnt_info, sort_field){
            //后台回调函数
            if (!Number($('#add_item_flag').val())) {
                PT.hide_loading();
            } else {
                $('#add_item_flag').val('0');
                $('#add_item').click();
            }
            var table=$('#adgroup_table'),temp_str='';
            if(adgroup_table){
                adgroup_table.fnDestroy();
                table.find('tbody tr').remove();
            }
            for (var i=0;i<data.length;i++){
                data[i].page_type = page_type;
                data[i].CONSULT_WW = CONSULT_WW;
                temp_str += template.compile(pt_tpm['adgroup_list.tpm.html'])(data[i]);
            }
            table.find('tbody').html(temp_str);
            init_table();

            // 初始化分页器及页数信息
            $('.current_count').text(0);
            $('.page_count').text(page_info.page_count);
            $('.adgroup_count').text(page_info.total_count);
            handle_page(page_info['page_count'],page_info['page_no']);

            // 判断排序机制，宝贝只有1页时为当前页前端排序，否则为全局后台排序
            $('#adgroup_table').off('change', '.dropdown');
            if (page_info['page_count']<=1) {
                $('#adgroup_table .dropdown').removeClass('table_g_sort_dropdown').addClass('table_sort_dropdown');
            } else {
                $('#adgroup_table .dropdown').removeClass('table_sort_dropdown').addClass('table_g_sort_dropdown');
            }
            if (sort_field) {
                var span_sort = $('#adgroup_table tbody .'+sort_field);
                span_sort.closest('td').find('span.b.baseColor:eq(0)').removeClass('b baseColor');
                span_sort.addClass('b baseColor');
            }

            ajax_init_dom();

            $('#mnt_type').val(mnt_info.mnt_type);
            $('.mnt_num').html(mnt_info.mnt_num);
            if (max_num) {
                $('.new_num').html(max_num-mnt_info.mnt_num);
            }
            change_tr_color();
            if ($('#mnt_index').length === 0) {
                new FixedHeader(adgroup_table);
            }
        },
        // select_call_back:function(value){
        //  //改变天数的回调函数
        //  get_adgs(0);
        // },
        get_adgroup_fail:function(){
            //获取数据失败
            PT.hide_loading();
            PT.alert('获取数据失败,请稍后重试','red');
        },
        update_adg_back:function(mode,result){
            PT.hide_loading();
            switch(mode){
                case 'start':
                    for(var i=0; i<result.success_id_list.length; i++) {
                        var adg_id = result.success_id_list[i],
                            jq_status=$('#status_'+adg_id),
                            jq_tr=$('input[value='+adg_id+']').parents('tr');
                        jq_tr.removeClass('silver');
                        jq_status.text('推广中').removeClass('red');
                        jq_status.next().attr('name','stop').text('暂停');
                    }
                    break;
                case 'stop':
                    for(var i=0; i<result.success_id_list.length; i++) {
                        var adg_id = result.success_id_list[i],
                            jq_status=$('#status_'+adg_id),
                            jq_tr=$('input[value='+adg_id+']').parents('tr');
                        jq_tr.addClass('silver');
                        jq_status.text('已暂停').addClass('red');
                        jq_status.next().attr('name','start').text('开启');
                    }
                    break;
                case 'del':
                    for(var i=0; i<result.success_id_list.length; i++) {
                        var jq_tr=$('#status_'+result.success_id_list[i]).parents('tr');
                        adgroup_table.fnDeleteRow(jq_tr[0]);
                    }
                    var msg = '';
                    if(result.error_msg){
                        msg=result.error_msg;
                    }else{
                        if(result.ztc_del_count>0){
                            msg += "您已经在直通车后台删除了"+result.ztc_del_count+"个推广宝贝";
                        }
                        msg += result.cant_del_list.length? ("有"+result.cant_del_list.length+"个推广宝贝无法删除"):'';
                    }
                    if(msg){
                        PT.alert(msg);
                    }else if(msg==''&&result.success_id_list.length==PAGE_SIZE){
                        window.location.reload();
                    }
                    var num=$('.adgroup_count').text()-result.success_id_list.length;
                    $('#mnt_adg_count').text(result.mnt_num);
                    $('.adgroup_count').text(num);
                    get_checked_num();
                    PT.AddItemBox3.init_tables();
                    PT.AddItemBox3.get_item_list();
                    break;
            }
        },
        'get_keyword_count_callback':function (type, data_dict) {
            var desc = type=='keyword'? '关键词数': '创意数';
            $('#adgroup_table tbody tr').each(function () {
                var adg_id = Number(this.id),
                    count = Number(data_dict[adg_id]),
                    obj = $(this).find('.'+type+'_count_str');
                if (isNaN(count)) {
                    count = 0;
                }
                $(obj).siblings('.'+type+'_count').html(count);
                $(obj).hide();
                $(obj).html(desc+'：'+count+'个').fadeIn();
            });

            $('.show_count[value="'+type+'"]').data('is_lock', 1).html('刷新'+desc);
        },
        update_mnt_back: function(adg_id, status){
            var obj=$('#mnt_type_'+adg_id),
                link_obj=obj.parent().next().find('a.btn');

            if (Number(status)>0) {
                opt_status = status == 1? '自动优化中': '只优化价格';
                obj.find('>span').removeClass('red').addClass('baseColor').text(opt_status);
                obj.find('>i').attr({'mnt_type': camp_mnt_type, 'mnt_opt_type': status});
                link_obj.attr('href',link_obj.attr('href').replace('web/smart_optimize','mnt/adgroup_data'));
                var set_key_word = "<a href='javascript:;' class='open_manage_elemword' id='manage_elemword_"+link_obj.attr("item_id")+"'>关键词设置</a>";
                $("#set_key_work_"+link_obj.attr("item_id")).html(set_key_word);
            } else {
                obj.find('>span').removeClass('baseColor').addClass('red').text('不自动优化');
                obj.find('>i').attr({'mnt_type': 0, 'mnt_opt_type': 1});
                link_obj.attr('href',link_obj.attr('href').replace('mnt/adgroup_data','web/smart_optimize'));
                $("#set_key_work_"+link_obj.attr("item_id")).html("");
            }
            if (camp_mnt_type == 2) {
                if (Number(status>0)) {
                    obj.next('div').fadeIn();
                } else{
                    obj.next('div').fadeOut();
                }
            }

            update_mnt_num(parseInt(status)?1:-1);
        },
        get_adgs: get_adgs,
        add_imgorder2: add_imgorder2,
        add_imgorder2_callback: function (order_id, contact_id, phone, qq) {
            $('#modal_add_imgorder2').modal('hide');
            if (order_id) {
                $('#modal_contact_us .phone').val(phone).attr('org_value', phone);
                $('#modal_contact_us .qq').val(qq).attr('org_value', qq);
                $('#modal_contact_us .update_contact_info').attr('contact_id', contact_id);
                $('#modal_contact_us').modal('show');
            } else {
                PT.alert('下单失败，请联系顾问');
            }
        },
        set_adg_mobdiscount_callback: function (adgroup_id, discount){
            $('#modal_adg_mobdiscount').modal('hide');
            $('#adg_mobdiscount_'+ adgroup_id).text(discount);
            PT.light_msg('', "修改移动折扣成功！", 1000);
        }
    };

}();
