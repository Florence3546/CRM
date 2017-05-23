/**
 * Created by Administrator on 2015/9/28.
 */
var upload_item_img_callback;
define(['moment','widget/alert/alert','widget/confirm/confirm',
    'widget/loading/loading','widget/lightMsg/lightMsg',
    'widget/ajax/ajax','kinetic','Jcrop','webfontloader','creative','dataTable','template','../report_detail/report_detail'],
    function(moment,alert,confirm,loading,lightMsg,ajax,kinetic,Jcrop,WebFont,_creative,_datatable,template,report_detail){

    var Jcrop_api,box_model,modify_creative_id,modify_waiting_creative_id;

    var adgroup_id = $('#adgroup_id').val(),
        campaign_id = $('#campaign_id').val(),
        item_id = $('#item_id').val();
    var IDM,ICM;
    var init = function(){
        IDM = new _creative.ImageDrawManager({
            id: 'stage'
        });

        ICM = new _creative.ImageCutManager();

        //初始化列表
        $('#table_box').dataTable({
            "bRetrieve": true, //允许重新初始化表格
            "bPaginate": false,
            "bFilter": true,
            "bInfo": false,
            "aaSorting": [[2,'desc']],
            "bAutoWidth":false,//禁止自动计算宽度
            "sDom":'',
            "language": { "emptyTable": "没有数据" },
            "aoColumns": [
                {"bSortable": false},
                {"bSortable": false},
                {
                    bSortable: true,
                    "sType": "custom",
                    "sSortDataType": "custom-text"
                },
                {
                    bSortable: true,
                    "sType": "custom",
                    "sSortDataType": "custom-text"
                },
                {
                    bSortable: true,
                    "sType": "custom",
                    "sSortDataType": "custom-text"
                },
                {
                    bSortable: true,
                    "sType": "custom",
                    "sSortDataType": "custom-text"
                },
                {
                    bSortable: true,
                    "sType": "custom",
                    "sSortDataType": "custom-text"
                },
                {
                    bSortable: true,
                    "sType": "custom",
                    "sSortDataType": "custom-text"
                },
                {
                    bSortable: true,
                    "sType": "custom",
                    "sSortDataType": "custom-text"
                },
                {
                    bSortable: true,
                    "sType": "custom",
                    "sSortDataType": "custom-text"
                },
                {
                    bSortable: true,
                    "sType": "custom",
                    "sSortDataType": "custom-text"
                },
                {
                    bSortable: true,
                    "sType": "custom",
                    "sSortDataType": "custom-text"
                },
                {"bSortable": false}
            ]
        });

        $('#table_complete_box').dataTable({
            "bRetrieve": true, //允许重新初始化表格
            "bPaginate": false,
            "bFilter": true,
            "bInfo": false,
            "aaSorting": [[2,'desc']],
            "bAutoWidth":false,//禁止自动计算宽度
            "sDom":'',
            "language": {
                          "emptyTable": "没有数据"
                      },
            "aoColumns": [
                {"bSortable": false},
                {"bSortable": false},
                {"bSortable": true},
                {"bSortable": true},
                {"bSortable": true},
                {"bSortable": true},
                {"bSortable": true},
                {"bSortable": true},
                {"bSortable": true},
                {"bSortable": true},
                {"bSortable": true},
                {"bSortable": true},
                {"bSortable": false}
            ]
        });

        bind_event();
        $('a[data-toggle=tooltip]').tooltip();
    };

    //绑定事件
    var bind_event = function(){
        //关闭提示条
        $('.close-sign').on('click',function(){
            $('.sign-bar').fadeOut(200);
        });

        //切换显示模式
        $('.show_model').on('click','a', function() {
            if($(this).hasClass('active')){
                return false;
            }
            var type=$(this).find('i').attr('data-type');
            $(this).parent().find('a').toggleClass('active');
            $('.image_optimize').toggleClass('hide');
            $('#show_type').val(type);
            $('#add_image').toggleClass('hide');

            var t = GetUrlParam('t');
            if(t)
                window.location.href = ChangeUrlArg(window.location.href, 't', type);
            else
                window.location.href = window.location.href + '&t=' + type;
        });

        //显示修改标题框
        $(document).on('click.image_optimize.modify_title', '.modify_title', function() {
            var title,warp = $(this).closest('.item');
            title=warp.find('.title').text();
            warp.find('.input_title').val(title);
            warp.find('.j_text_len').text(true_length(title));
            warp.addClass('editor');
        });

        //隐藏修改标题框
        $(document).on('click.image_optimize.cancel_modify_title', '.cancel_modify_title', function() {
            var warp = $(this).closest('.item');
            warp.removeClass('editor');
        });

        //预览模式点击图片修改创意
        $('#list_add_box .img').on('click.image_optimize.img.modify_creative', function() {
            var title,src = $(this).find('img').attr('src');
            modify_creative_id=$(this).find('img').attr('data-id');
            title=$(this).next().text();
            IDM.draw(src, function() {
                $('#img_cut').attr('src', src);
                set_box_model(0);
                $('.item_main_pic li:eq(0)').removeClass('checked');

                $('#switch_optimize').trigger('click'); //切换弹窗选项卡

                $('#image_optimize_modal').find('.title').text(title);

                $('#image_optimize_modal').modal({keyboard:false,backdrop:'static'});

                updateStyleBox(src);
            });
        });

        //列表模式点击修改创意
        $('#table_box').on('click','.edit_image', function() {
            var title,src = $(this).parents('tr').find('img').attr('data-url');
            modify_creative_id=$(this).parents('tr').find('img').attr('data-id');
            title=$(this).parents('tr').find('.adg_title').text();
            IDM.draw(src, function() {
                $('#img_cut').attr('src', src);
                set_box_model(0);
                $('.item_main_pic li:eq(0)').removeClass('checked');

                $('#switch_optimize').trigger('click'); //切换弹窗选项卡

                $('#image_optimize_modal').find('.title').text(title);

                $('#image_optimize_modal').modal({keyboard:false,backdrop:'static'});

                updateStyleBox(src);
            });
        });

        //预览模式点击图片修改测试创意
        $('#list_add_test_box .img').on('click.image_optimize.img.modify_creative', function() {
            var title,src = $(this).find('img').attr('src');
            modify_waiting_creative_id=$(this).find('img').attr('data-id');
            title=$(this).next().text();
            IDM.draw(src, function() {
                $('#img_cut').attr('src', src);
                set_box_model(3);
                $('.item_main_pic li:eq(0)').removeClass('checked');

                $('#switch_optimize').trigger('click'); //切换弹窗选项卡

                $('#image_optimize_modal').find('.title').text(title);

                $('#image_optimize_modal').modal({keyboard:false,backdrop:'static'});

                updateStyleBox(src);
            });
        });

        //列表模式点击修改测试创意
        $('#table_test_box').on('click','.edit_image', function() {

            var title,src = $(this).parents('tr').find('img').attr('data-url');
            modify_waiting_creative_id=$(this).parents('tr').find('img').attr('data-id');
            title=$(this).parents('tr').find('.title').text();
            IDM.draw(src, function() {
                $('#img_cut').attr('src', src);
                set_box_model(3);
                $('.item_main_pic li:eq(0)').removeClass('checked');

                $('#switch_optimize').trigger('click'); //切换弹窗选项卡

                $('#image_optimize_modal').find('.title').text(title);

                $('#image_optimize_modal').modal({keyboard:false,backdrop:'static'});

                updateStyleBox(src);
            });
        });

        //添加创意
        $(document).on('click', '#list_add_box .add_creative,#add_new_img', function() {
            var title=$('#list_add_box .item:first .title').text();

            $('#image_optimize_modal').find('.title').text(title); //设置弹出曾标题为默认的创意标题

            $('.item_main_pic li:eq(0)').trigger('click'); //选中第一个图片
            set_box_model(1);
            $('#rechoose_img').trigger('click');
            $('#image_optimize_modal').modal({keyboard:false,backdrop:'static'});
        });

        //添加测试的创意
        $(document).on('click', '#list_add_test_box .add_creative,#add_test_img', function() {
            var title=$('#list_add_box .item:first .title').text();

            $('#image_optimize_modal').find('.title').text(title); //设置弹出曾标题为默认的创意标题

            $('.item_main_pic li:eq(0)').trigger('click'); //选中第一个图片
            set_box_model(2);
            $('#rechoose_img').trigger('click');
            $('#image_optimize_modal').modal({keyboard:false,backdrop:'static'});
        });

        //删除创意
        $('#list_add_box .delete_creative,#table_box .delete_image').on('click.image_optimize.delete_creative',function(){
            var creative_id;
            creative_id = $(this).attr('data-id');

            confirm.show({'body':'你确定要删除吗？','okHidden':function(){
                loading.show('正在删除，请稍候...');
                //在这里进行删除操作
                ajax.ajax('del_creative',{'adgroup_id':adgroup_id,'creative_id':creative_id},delete_creative_callback)
            }});
        });

        //删除测试创意
        $('#list_add_test_box .delete_creative,#table_test_box .delete_image').on('click.image_optimize.delete_creative',function(){
            var creative_id = $(this).attr('data-id');
            confirm.show({'body':'你确定要删除吗？','okHidden':function(){
                loading.show('正在删除，请稍候...');
                //在这里进行删除操作
                ajax.ajax('delete_waiting_creative',{'adgroup_id':adgroup_id,'creative_id':creative_id,'auto_hide':0},delete_creative_callback)
            }});
        });

        //删除已完成的创意
        $('#complete_creatives_box .delete_creative,#table_complete_box .delete_image').on('click.image_optimize.delete_creative',function(){
            var creative_id = $(this).attr('data-id');
            //在这里进行删除操作
            confirm.show({'body':'你确定要删除吗？','okHidden':function(){
                loading.show('正在删除，请稍候...');
                //在这里进行删除操作
                ajax.ajax('delete_waiting_creative',{'adgroup_id':adgroup_id,'creative_id':creative_id,'auto_hide':0},delete_creative_callback)
            }});
        });

        //预览模式将已完成的创意设置为投放的创意
        $('#complete_creatives_box .reset_creative').on('click.image_optimize.reset_creative',function(){
            var title,src,warp = $(this).closest('.item2'),creative_count=Number($('#creative_count').val());
            if(creative_count==4){
                alert.show('请先删除一个投放中创意');
                return false;
            }
            title=warp.find('.title').text();
            src = warp.find('img').attr('src');

            IDM.draw(src, function() {
                $('#img_cut').attr('src', src);
                set_box_model(1);
                $('.item_main_pic li:eq(0)').removeClass('checked');

                $('#rechoose_img').trigger('click'); //切换弹窗选项卡

                $('#image_optimize_modal').find('.title').text(title);

                $('#image_optimize_modal').modal({keyboard:false,backdrop:'static'});

                updateStyleBox(src);
            });
        });

        //列表模式将已完成的创意设置为投放的创意
        $('#table_complete_box .reset_creative').on('click.image_optimize.reset_creative',function(){
            var title,src,warp = $(this).parents('tr'),creative_count=Number($('#creative_count').val());
            if(creative_count==4){
                alert.show('请先删除一个投放中创意');
                return false;
            }
            title=warp.find('.adg_title').text();
            src = warp.find('img').attr('src');

            IDM.draw(src, function() {
                $('#img_cut').attr('src', src);
                set_box_model(1);
                $('.item_main_pic li:eq(0)').removeClass('checked');

                $('#rechoose_img').trigger('click'); //切换弹窗选项卡

                $('#image_optimize_modal').find('.title').text(title);

                $('#image_optimize_modal').modal({keyboard:false,backdrop:'static'});

                updateStyleBox(src);
            });
        });

        //预览模式重新测试
        $('#complete_creatives_box .reset_waiting_creative').on('click.image_optimize.reset_waiting_creative',function(){
            var title,src,warp = $(this).closest('.item2'),waiting_creatives_count=Number($('#waiting_creatives_count').val());
            if(waiting_creatives_count==4){
                alert.show('请先删除一个排队中创意');
                return false;
            }
            title=warp.find('.title').text();
            src = warp.find('img').attr('src');

            IDM.draw(src, function() {
                $('#img_cut').attr('src', src);
                set_box_model(2);
                $('.item_main_pic li:eq(0)').removeClass('checked');

                $('#rechoose_img').trigger('click'); //切换弹窗选项卡

                $('#image_optimize_modal').find('.title').text(title);

                $('#image_optimize_modal').modal({keyboard:false,backdrop:'static'});

                updateStyleBox(src);
            });
        });

        //列表模式重新测试
        $('#table_complete_box .reset_waiting_creative').on('click',function(){
            var title,src,warp = $(this).parents('tr'),waiting_creatives_count=Number($('#waiting_creatives_count').val());
            if(waiting_creatives_count==4){
                alert.show('请先删除一个排队中创意');
                return false;
            }
            title=warp.find('.adg_title').text();
            src = warp.find('img').attr('src');

            IDM.draw(src, function() {
                $('#img_cut').attr('src', src);
                set_box_model(2);
                $('.item_main_pic li:eq(0)').removeClass('checked');

                $('#rechoose_img').trigger('click'); //切换弹窗选项卡

                $('#image_optimize_modal').find('.title').text(title);

                $('#image_optimize_modal').modal({keyboard:false,backdrop:'static'});

                updateStyleBox(src);
            });
        });

        //统计输入文字个数
        $('.editor_title .input_title').on('keyup.image_optimize',function(){
            var text_len=true_length(this.value);
            $(this).next().find('.j_text_len').text(text_len);
        });

        //修改标题
        $('#list_add_box,#table_box').on('click','.save_title',function(){
            var creative_id=$(this).attr('data-id'),warp = $(this).closest('.item'),title,img_url;
            title=warp.find('.input_title').val();
            var old_title=warp.find('.title').text();
            img_url=warp.find('.img img').attr('data-url');
            if(true_length(title)>40){
                alert.show('创意标题限制为40个字符之内，请修改后再次保存');
                return false;
            }

            if(true_length(title)==0){
                alert.show('创意标题不能为空，请修改后再次保存');
                return false;
            }

            warp.removeClass('editor');

            if (title==old_title){
                return false;
            }

            loading.show('正在修改，请稍候...');
            ajax.ajax( 'super_update_creative',
                       {'item_id': item_id,
                       'adgroup_id': adgroup_id,
                       'campaign_id': campaign_id,
                       'creative_id': creative_id,
                       'title': title,
                       'img_str': img_url},
                       update_creative_callback);
        });

        //修改等待标题
        $('#list_add_test_box,#table_test_box').on('click','.save_title',function(){
            var id=$(this).attr('data-id'),warp = $(this).closest('.item'),title;
            title=warp.find('.input_title').val();
            var old_title=warp.find('.title').text();
            if(true_length(title)>40){
                alert.show('创意标题限制为40个字符之内，请修改后再次保存');
                return false;
            }

            if(true_length(title)==0){
                alert.show('创意标题不能为空，请修改后再次保存');
                return false;
            }

            warp.removeClass('editor');

            if (title==old_title){
                return false;
            }

            loading.show('正在修改，请稍候...');
            ajax.ajax( 'update_waiting_creative',
                       {'id': id,'title': title},
                       update_test_title_callback);
        });

        //显示创意趋势图
        report_detail.init(1,1);
        $('.show_chart').on('click',function(){
            var creative_id=$(this).attr('data-id');
            var creative_title = $('#item_'+creative_id+' .title').text();
            report_detail.show('创意明细：'+creative_title, 'creative', $('#shop_id').val(), null, null, creative_id);
        });

        //切换到图片优化选项卡
        $(document).on('click.image_optimize.switch_optimize', '#switch_optimize', function() {
            $('#switch_optimize').hide();
            $('#rechoose_img').show();
            $('.operation_box').addClass('optimize');
        });

        //同步弹窗的里修改的标题
        $('#image_optimize_modal .sync_title').on('click.image_optimize.sync_title',function(){
            var warp = $(this).closest('.item'),title;
            title=warp.find('textarea').val();
            if(true_length(title)>40){
                alert.show('创意标题限制为40个字符之内，请修改后再次保存');
                return false;
            }

            if(title==""){
                alert.show('创意标题不能为空，请修改后再次点击确定');
                return false;
            }

            warp.find('.title').text(title);
            warp.removeClass('editor');
        });

        //选择商品主图
        $(document).on('click.image_optimize.item_main_pic', '.item_main_pic li:not(.add)', function() {
            var that = this;
            IDM.draw($(this).find('img').attr('data-url'), function() {
                $('.item_main_pic li').removeClass('checked');
                $('.preview_layer').removeClass('checked');
                $(that).addClass('checked');

                updateStyleBox($(that).find('img').attr('data-url'));
            });
        });

        //上传商品主图
        $('#upload_item_img_input').on('change',function(){
            var file = this.files.item(0);
            if(!file.type.match("image.*")){
                alert.show('只允许图片格式的文件，如 jpg png gif');
                return false;
            }
            if(file.size>10485760){
                alert.show('图片过大请保证在10M以内');
                return false;
            }
            loading.show('正在上传图片，请稍候...','',true);
            $('#upload_item_img_form').submit();
        });

        //删除商品主图
        $(document).on('click.image_optimize.delete_main_pic','.item_main_pic i.delete',function(e){
            var img_id;

            e.stopPropagation();

            img_id=$(this).next().attr('data-img-id');

            confirm.show({
                body: '你确定要删除吗？',
                backdrop:false,
                okHidden: function() {
                    //在这里进行删除主图操作
                    ajax.ajax('delete_main_pic', {
                        'item_id': item_id,
                        'img_id': img_id
                    }, delete_main_pic_callback);
                }
            });
        });

        //选择本地上传图片
        $(document).on('click.image_optimize.preview_layer', '.preview_layer', function() {
            var that = this;
            IDM.draw($(this).find('img').attr('src'), function() {
                $('.item_main_pic li').removeClass('checked');
                $(that).addClass('checked');
                updateStyleBox($(that).find('img').attr('src'));
            });
        });

        //切换到图片优化选项卡
        $(document).on('click.image_optimize.switch_optimize', '#switch_optimize', function() {
            $('#switch_optimize').hide();
            $('#rechoose_img').show();
            $('.operation_box').addClass('optimize');
        });

        //切换到选择图片选项卡
        $(document).on('click.image_optimize.rechoose_img', '#rechoose_img', function() {
            $('#switch_optimize').show();
            $('#rechoose_img').hide();
            $('.operation_box').removeClass('optimize');
        });

        //图片剪裁
        $('#img_cut_modal').on('hidden.bs.modal', function (e) {
             $('#image_optimize_modal').css('z-index',$('#img_cut_modal').css('z-index'));
        });

        $(document).on('click.image_optimize.switch_img_cut', '#switch_img_cut', function() {
            var url = current_img_url() || $('#img_cut').attr('src');
            IDM.load_img(url, function() {
                //此函数的this就代表图像对象
                var that = this;
                $('#img_cut').attr('src', url);
                //按比例设置图片大小
                $('#img_cut').css({
                    width: ICM.options.width,
                    height: this.height * (ICM.options.width / this.width)
                });

                $('#img_cut_modal').modal({
                    'backdrop': false
                });

               ICM.cut('img_cut', this, function(coordinate) {
                    var zoom = that.width / ICM.options.width;
                    IDM.cut_img(-coordinate.x, -coordinate.y, coordinate.w, coordinate.h, zoom)
                }, function() {
                    Jcrop_api = this;
                });
            });

        });

        //取消剪裁
        $('#img_cut_modal').on('click','.btn-default', function() {
            var url = current_img_url() || $('#img_cut').attr('src');
            IDM.recover_cut_img();
            Jcrop_api.destroy();
            $('#img_cut_modal').modal('hide');
            // $('#image_optimize_modal').css('z-index',1050);
        });

        //确认剪裁
        $('#img_cut_modal').on('click','.btn-primary',function(){
            Jcrop_api.destroy();
            $('#img_cut_modal').modal('hide');
            // $('#image_optimize_modal').css('z-index',1050);
        });

        // $('#img_cut_modal').on('show.bs.modal',function(){
        //     $('#image_optimize_modal').css('z-index',1);
        // });

        $('#img_cut_modal').on('hidden.bs.modal',function(){
            $('body').addClass('modal-open');
        });

         //风格选择
        $(document).on('click.image_optimize.switch_style', '.style_box>li', function() {
            var temp_id;

            temp_id = $(this).find('img').attr('data-temp');
            IDM.init_draw(temp_id, function() {
                //控制文本框的显示
                var group_config = this.style_config[temp_id],
                    html = "";
                for (var g in group_config) {
                    var index,config_id,template;
                    index=group_config[g].index;
                    config_id=group_config[g].config_id;

                    if(config_id==undefined){
                        config_id=index;
                    }
                    var template = this.template[config_id];
                    for (var t in template) {
                        if(t.indexOf('color')!=-1||t.indexOf('fontsize')!=-1){
                            html += '<input type="hidden" data-index="' + group_config[g].index + '" data-text="' + t + '" value="' + template[t] + '">';
                        }else{
                            html += '<input type="text" data-index="' + group_config[g].index + '" data-text="' + t + '" value="' + template[t] + '">';
                        }
                    }
                }
                $('#text_control').html(html);
                $('#choose_tip').hide();
            });

            $('.style_box>li').removeClass('checked');
            $(this).addClass('checked');

            //发送一个请求，记录点击
            ajax.ajax('record_template_click',{'temp_id':$(this).find('img').attr('data-temp')},null);

        });

        //清除风格
        $('#clean_flag').on('click',function(){
            IDM.clear_group();
            IDM.redraw_layer();
            $('#text_control').html('');
            $('#choose_tip').show();
            $('.style_box li').removeClass('checked');
        });

        //风格分页切换
        $(document).on('click', '.optimize_style .pagination li:not(.active)', function() {
            var index;
            var warp = $(this).closest('.pagination');

            var page_count = 1;
            if(warp.data('count')){
                page_count = warp.data('count');
            }
            warp.find('li').removeClass('active');
            if($(this).hasClass('first')){
                index = 1;
                $(this).next().addClass('active');
            }else if($(this).hasClass('last')){
                index = page_count;
                $(this).prev().addClass('active');
            }else{
                index = Number($(this).text())
                $(this).addClass('active');
            }
            warp.prev().find('.style_box').css('marginTop', -($('.style_warp').height()) * (index - 1));

            if(page_count>7){
                reDrawPage(warp, page_count, index);
            }
        });

        //上传创意图片
        $('#local_upload_creative').on('change', function() {
            var file = this.files.item(0),
                url;

            if (file) {
                url = IDM.create_object_url(file);
                IDM.draw(url);
                updateStyleBox(url);
                $('.preview_layer img').attr('src', url);
                $('.local_pic .empty').removeClass('empty').addClass('rechoose');

                $('.item_main_pic li').removeClass('checked');
                $('.preview_layer').addClass('checked');
            }
        });

        //修改图片上的文字
        $('#text_control').on('keyup', 'input', function() {
            var temp_id,template={};;

            temp_id = $(".style_box>li.checked").find('img').attr('data-temp');

            $('#text_control input').each(function(){
                var group_id, text_type, obj=$(this);

                index = obj.attr('data-index');
                text_type = obj.attr('data-text');

                if(typeof template[index]=="undefined"){
                    template[index]={};
                }
                template[index][text_type]=this.value;
            });

            IDM.draw_by_custom(temp_id,template);
        });

        //设置为创意
        $('#image_optimize_modal').on('click','[action=confirm]',function(){
            IDM.get_base64(function(img_str){

                var title=$('.preview_box .title').text();
                var function_name = '';

                var callback;

                var data={
                    'item_id': item_id,
                    'adgroup_id': adgroup_id,
                    'campaign_id': campaign_id,
                    'title': title,
                    'img_str': img_str,
                    'auto_hide':0
                }

                if(box_model==0){
                    data['creative_id']=modify_creative_id;
                    function_name='super_update_creative';
                    loading.show('正在修改，请稍候...');
                    callback = update_creative_callback;
                }

                if(box_model==1){
                    function_name='super_add_creative';
                    loading.show('正在添加，请稍候...');
                    callback = add_creative_callback;
                }

                if(box_model==2){
                    function_name='create_waiting_creative';
                    loading.show('正在添加，请稍候...');
                    callback = function(){
                        loading.hide();
                        window.location.reload();
                    }
                }

                if(box_model==3){
                    data['id']=modify_waiting_creative_id;
                    function_name='super_update_waiting_creative';
                    loading.show('正在修改，请稍候...');
                    callback = function(){
                        loading.hide();
                        window.location.reload();
                    }
                }

                //这里发送请求
                 ajax.ajax(function_name,data,callback);
            });
        });

        //鼠标经过舞台的group
        IDM.group_mouseover=function(){
            $('body').addClass('poi');
        }

        IDM.group_mouseleave=function(){
            $('body').removeClass('poi');
        }

        //点击标签页显示图片
        $('.optimize_style .nav a').on('shown',function(){
            lazy_load($('.optimize_style .tab-pane.active img'));
        });

        //选择天数
        $('#select_days').on('change',function(){
            sdate = moment($(this).daterangepicker('getRange').start).format('YYYY-MM-DD');
            edate = moment($(this).daterangepicker('getRange').end).format('YYYY-MM-DD');
            var s = GetUrlParam('s');
            var e = GetUrlParam('e');
            if(s && e){
                var new_url = ChangeUrlArg(window.location.href, 's', sdate);
                window.location.href = ChangeUrlArg(new_url, 'e', edate);
            }else{
                window.location.href = window.location.href + '&s=' + sdate + '&e=' + edate;
            }
        });

        //从本地上传创意，用button触发upload
        $('#btn_local_upload').click(function(){
            $('#local_upload_creative').click();
        })

        $('.tips').tooltip();
    };

    //获取URL参数
    function GetUrlParam(name) {
        var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)"); //构造一个含有目标参数的正则表达式对象
        var r = window.location.search.substr(1).match(reg);  //匹配目标参数
        if (r != null) return unescape(r[2]); return null; //返回参数值
    }

    //修改URL参数值
    function ChangeUrlArg(url, arg, arg_val){
        var pattern=arg+'=([^&]*)';
        var replaceText=arg+'='+arg_val;
        if(url.match(pattern)){
            var tmp='/('+ arg+'=)([^&]*)/gi';
            tmp=url.replace(eval(tmp),replaceText);
            return tmp;
        }else{
            if(url.match('[\?]')){
                return url+'&'+replaceText;
            }else{
                return url+'?'+replaceText;
            }
        }
        return url+'\n'+arg+'\n'+arg_val;
    }

    //计算输入的长度
    var true_length = function(str){
        var l = 0;
        for (var i = 0; i < str.length; i++) {
            if (str[i].charCodeAt(0) < 299) {
                l++;
            } else {
                l += 2;
            }
        }
        return l;
    };

    //设置modal类型
    var set_box_model=function(type){
        var type_desc_dict={0:'编辑创意',1:'添加新创意',2:'添加测试创意',3:'编辑测试创意'},
            obj=$('#image_optimize_modal');

        obj.find('.modal-header h4').text(type_desc_dict[type]);
        obj.find('.modal-footer [action=confirm]').text(type_desc_dict[type].replace(/添加|编辑/,'提交'));
        box_model=type;
    }

    var current_img_url = function() {
        return $('.choose_pic_box .checked img').attr('data-url')||$('.choose_pic_box .checked img').attr('src');
    }

    var check_font = function() {
        WebFont.load({
            custom: {
                families: ['FZZZHJT', 'FZCHJT','FZYY','IMPACTR','LTH','ICON','HYYYT','LTCH']
            },
            loading: function() {
                // console.log('正在加载字体');
            },
            active: function() {
                // console.log('字体加载完成');
            }
        });
    }

    var lazy_load=function(objs){
        for(var i=0;i<objs.length;i++){
            if($(objs[i]).attr('data-src')==undefined){
                continue;
            }
            objs[i].src=$(objs[i]).attr('data-src');
            $(objs[i]).removeAttr('data-src');
        }
    }

    /*****************各种ajax回调*******************/
    var add_creative_callback = function() {
        loading.hide();
        window.location.reload();
    };
    var delete_creative_callback = function() {
            window.location.reload();
        };
    var create_waiting_creative_callback = function() {
            window.location.reload();
        };

    //修改标题回调
    var update_creative_callback = function(data) {
        if(data.reload){
            window.location.reload()
        }else{
            loading.hide();
            var obj;
            obj=$('#item_'+data.creative_id);

            obj.find('.title').text(data.title);
            lightMsg.show({body:'修改成功！'});
        }
    };

    //修改测试创意标题回调函数
    var update_test_title_callback = function(data){
            loading.hide();
            var obj;
            obj=$('.item_test_'+data.id);
            obj.find('.title').text(data.title);
            lightMsg.show({body:'修改成功！'});
        };

    //删除主图回调函数
    var delete_main_pic_callback = function(data){
            if(data.msg){
                alert.show(data.msg);
            }else{
                var obj=$('.item_main_pic img[data-img-id='+data.data.img_id+']').parent();

                if(obj.hasClass('checked')){
                    $('.item_main_pic li:eq(0)').trigger('click'); //选中第一个图片
                }

                obj.remove();

                $('.item_main_pic li.add').removeClass('hide');

                $('#upload_item_img_input').val(''); //将文件域置空，避免第二次上传不触发
            }
        };

    //全局回调函数
    upload_item_img_callback = function(data){
        loading.hide();
        $('.item_main_pic li.add').before('<li><i class="iconfont delete">&#xe627;</i> <img src="'+data.url+'_100x100.jpg" data-url="'+data.url+'" data-img-id="'+data.img_id+'"></li>');
        $('.item_main_pic li.add').prev().trigger('click');
        if($('.item_main_pic li:not(.add)').length>=5){
            $('.item_main_pic li.add').addClass('hide');
        }
    };

    var show_creative_trend = function(data){

            if (!$('#modal_camp_trend').length){
                $('body').append(pt_tpm["modal_camp_trend.tpm.html"]);
            }
            $('#camp_trend_title').text('创意');
            require(["modal_camp_trend"],function(modal){
                modal.show({
                    title: data.title
                },data.category_list, data.series_cfg_list);
            });
            $('#modal_camp_trend').modal();
        };

    var reDrawPage = function(obj,page_count, index){
        var HALF_SHOW_PAGE = 3; // 分页显示数量的一半
        var SHOW_PAGE = HALF_SHOW_PAGE * 2 + 1;
        var startPage = 1, endPage = 1;

        if(index <= HALF_SHOW_PAGE + 1){
            endPage = Math.min(SHOW_PAGE, page_count);
        }else{
            startPage = index - HALF_SHOW_PAGE;
            if(HALF_SHOW_PAGE > page_count){
                endPage = page_count;
            }else{
                endPage = index + HALF_SHOW_PAGE
            }
        }

        if((index + 3) > page_count && page_count > SHOW_PAGE){
            startPage = page_count - SHOW_PAGE + 1;
            endPage = page_count+1;
        }

        var pages = $(obj).find('li');
        for(var i=0;i<pages.length;i++){
            if(i>=startPage&&i<=endPage){
                $(pages[i]).removeClass('hide');
            }else{
                if(i!=0&&i!=(page_count+1)){
                    $(pages[i]).addClass('hide');
                }
            }
        }
    };

    var updateStyleBox=function(imgUrl){
        $('#image_optimize_modal .style_warp>ul>li').css('backgroundImage','url('+imgUrl+')');
    }

    return {
        init:function(){
            init();
            check_font();
            lazy_load($('.optimize_style .tab-pane.active img'));
        }
    }
});
