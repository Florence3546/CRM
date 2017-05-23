PT.namespace('ImageOptimoze');
PT.ImageOptimoze = function() {

    var Jcrop_api,box_model,modify_creative_id,modify_waiting_creative_id;

    var adgroup_id = $('#adgroup_id').val(),
        campaign_id = $('#campaign_id').val(),
        item_id = $('#item_id').val();

    var init_dom = function() {
        var IDM = new ImageDrawManager({
            id: 'stage'
        });

        var ICM = new ImageCutManager();


        //切换显示模式
        $('.show_model .iconfont').on('click', function() {
            var type=$(this).attr('data-type');
            $(this).parent().find('.iconfont').removeClass('active');
            $(this).addClass('active');
            $('.image_optimoze').addClass('hide');
            $('.image_optimoze.' + type).removeClass('hide');

            $('#show_type').val(type);
            page_name=window.location.href.replace(/table|list/,type);
            //改变浏览器URL,以便于刷新操作
            history.pushState&&history.pushState(page_name, "", page_name);
        });

        //显示修改标题框
        $(document).on('click.image_optimoze.modify_title', '.modify_title', function() {
            var title,warp = $(this).closest('.item');

            title=warp.find('.title').text();
            warp.find('textarea').val(title);
            warp.find('.j_text_len').text(PT.true_length(title));
            warp.addClass('editor');
        });

        //隐藏修改标题框
        $(document).on('click.image_optimoze.cancel_modify_title', '.cancel_modify_title', function() {
            var warp = $(this).closest('.item');
            warp.removeClass('editor');
        });

        //点击图片修改创意
        $('#list_add_box .img').on('click.image_optimoze.img.modify_creative', function() {
            var title,src = $(this).find('img').attr('src');
            modify_creative_id=$(this).find('img').attr('data-id');
            title=$(this).next().text();
            IDM.draw(src, function() {
                $('#img_cut').attr('src', src);
                set_box_model(0);
                $('.item_main_pic li:eq(0)').removeClass('checked');

                $('#switch_optimoze').trigger('click'); //切换弹窗选项卡

                $('#image_optimoze_modal').find('.title').text(title);

                $('#image_optimoze_modal').modal({keyboard:false,backdrop:'static'});
            });
        });

        //点击图片修改测试创意
        $('#list_add_test_box .img').on('click.image_optimoze.img.modify_creative', function() {
            var title,src = $(this).find('img').attr('src');
            modify_waiting_creative_id=$(this).find('img').attr('data-id');
            title=$(this).next().text();
            IDM.draw(src, function() {
                $('#img_cut').attr('src', src);
                set_box_model(3);
                $('.item_main_pic li:eq(0)').removeClass('checked');

                $('#switch_optimoze').trigger('click'); //切换弹窗选项卡

                $('#image_optimoze_modal').find('.title').text(title);

                $('#image_optimoze_modal').modal({keyboard:false,backdrop:'static'});
            });
        });

        //添加创意
        $(document).on('click.image_optimoze.list_add_box', '#list_add_box .add_creative', function() {
            var title=$('#list_add_box .item:first .title').text();

            $('#image_optimoze_modal').find('.title').text(title); //设置弹出曾标题为默认的创意标题

            $('.item_main_pic li:eq(0)').trigger('click'); //选中第一个图片
            set_box_model(1);
            $('#rechoose_img').trigger('click');
            $('#image_optimoze_modal').modal({keyboard:false,backdrop:'static'});
        });

        //添加测试的创意
        $(document).on('click.image_optimoze.list_add_test_box', '#list_add_test_box .add_creative', function() {
            var title=$('#list_add_box .item:first .title').text();

            $('#image_optimoze_modal').find('.title').text(title); //设置弹出曾标题为默认的创意标题

            $('.item_main_pic li:eq(0)').trigger('click'); //选中第一个图片
            set_box_model(2);
            $('#rechoose_img').trigger('click');
            $('#image_optimoze_modal').modal({keyboard:false,backdrop:'static'});
        });

        //删除创意
        $('#list_add_box .delete_creative').on('click.image_optimoze.delete_creative',function(){
            var creative_id;
            creative_id = $(this).attr('data-id');

            PT.confirm('您确定删除吗？',function(){
                PT.show_loading('正在删除');
                PT.sendDajax({
                    'function': 'web_delete_creative',
                    'creative_id': creative_id,
                    'namespace': 'ImageOptimoze'
                });
            });
        });

        //删除测试创意
        $('#list_add_test_box .delete_creative').on('click.image_optimoze.delete_creative',function(){
            var id;
            id = $(this).attr('data-id');

            PT.confirm('您确定删除吗？',function(){
                PT.show_loading('正在删除');
                PT.sendDajax({
                    'function': 'web_delete_waiting_creative',
                    'id': id,
                    'namespace': 'ImageOptimoze',
                    'auto_hide':0
                });
            });
        });

        //删除已完成的创意
        $('#complete_creatives_box .delete_creative').on('click.image_optimoze.delete_creative',function(){
            var id;
            id = $(this).attr('data-id');

            PT.confirm('您确定删除吗？',function(){
                PT.show_loading('正在删除');
                PT.sendDajax({
                    'function': 'web_delete_waiting_creative',
                    'id': id,
                    'namespace': 'ImageOptimoze',
                    'auto_hide':0
                });
            });
        });

        //将已完成的创意设置为投放的创意
        $('#complete_creatives_box .reset_creative').on('click.image_optimoze.reset_creative',function(){
            var title,src,warp = $(this).closest('.item'),creative_count=Number($('#creative_count').val());
            if(creative_count==4){
                PT.alert('请先删除一个投放中创意');
                return false;
            }
            title=warp.find('.title').text();
            src = warp.find('img').attr('src');

            IDM.draw(src, function() {
                $('#img_cut').attr('src', src);
                set_box_model(1);
                $('.item_main_pic li:eq(0)').removeClass('checked');

                $('#rechoose_img').trigger('click'); //切换弹窗选项卡

                $('#image_optimoze_modal').find('.title').text(title);

                $('#image_optimoze_modal').modal({keyboard:false,backdrop:'static'});
            });
        });

        //将已完成的创意设置为投放的创意
        $('#complete_creatives_box .reset_waiting_creative').on('click.image_optimoze.reset_waiting_creative',function(){
            var title,src,warp = $(this).closest('.item'),waiting_creatives_count=Number($('#waiting_creatives_count').val());
            if(waiting_creatives_count==4){
                PT.alert('请先删除一个排队中创意');
                return false;
            }
            title=warp.find('.title').text();
            src = warp.find('img').attr('src');

            IDM.draw(src, function() {
                $('#img_cut').attr('src', src);
                set_box_model(2);
                $('.item_main_pic li:eq(0)').removeClass('checked');

                $('#rechoose_img').trigger('click'); //切换弹窗选项卡

                $('#image_optimoze_modal').find('.title').text(title);

                $('#image_optimoze_modal').modal({keyboard:false,backdrop:'static'});
            });
        });

        //统计输入文字个数
        $('.editor_title textarea').on('keyup.image_optimoze',function(){
            var text_len=PT.true_length(this.value);

            $(this).next().find('.j_text_len').text(text_len);
        });

        //修改标题
        $('#list_add_box .save_title').on('click.image_optimoze.save_title',function(){
            var creative_id=$(this).attr('data-id'),warp = $(this).closest('.item'),obj,title,img_url;
            obj=$('#item_'+creative_id);
            title=obj.find('textarea').val();
            old_title=obj.find('.title').text();
            img_url=obj.find('.img img').attr('data-url');


            if(PT.true_length(title)>40){
                PT.alert('创意标题限制为40个字符之内，请修改后再次保存');
                return false;
            }

            if(PT.true_length(title)==0){
                PT.alert('创意标题不能为空，请修改后再次保存');
                return false;
            }

            warp.removeClass('editor');

            if (title==old_title){
                return false;
            }

            PT.show_loading('正在修改');

            PT.sendDajax({
                'function':'web_super_update_creative',
                'item_id': item_id,
                'adgroup_id': adgroup_id,
                'campaign_id': campaign_id,
                'creative_id': creative_id,
                'title': title,
                'img_str': img_url,
                'callback':'PT.ImageOptimoze.update_creative_callback'
            });
        });

        //修改等待标题
        $('#list_add_test_box .save_title').on('click.image_optimoze.save_title',function(){
            var id=$(this).attr('data-id'),warp = $(this).closest('.item'),obj,title;
            obj=$('#item_test_'+id);

            title=obj.find('textarea').val();
            old_title=obj.find('.title').text();

            if(PT.true_length(title)>40){
                PT.alert('创意标题限制为40个字符之内，请修改后再次保存');
                return false;
            }

            if(PT.true_length(title)==0){
                PT.alert('创意标题不能为空，请修改后再次保存');
                return false;
            }

            warp.removeClass('editor');

            if (title==old_title){
                return false;
            }


            PT.sendDajax({
                'function': 'web_update_waiting_creative',
                'id': id,
                'title': title,
                'namespace': 'ImageOptimoze'
            });
        });

        //显示创意趋势图
        $('.chow_chart').on('click',function(){
            var creative_id=$(this).attr('data-id');

            PT.sendDajax({
                'function': 'web_show_creative_trend',
                'creative_id': creative_id
            });
        });

        //同步弹窗的里修改的标题
        $('#image_optimoze_modal .sync_title').on('click.image_optimoze.sync_title',function(){
            var warp = $(this).closest('.item'),title;
            title=warp.find('textarea').val();

            if(PT.true_length(title)>40){
                PT.alert('创意标题限制为40个字符之内，请修改后再次保存');
                return false;
            }

            if(title==""){
                PT.alert('创意标题不能为空，请修改后再次点击确定');
                return false;
            }

            warp.find('.title').text(title);
            warp.removeClass('editor');
        });


        //选择商品主图
        $(document).on('click.image_optimoze.item_main_pic', '.item_main_pic li:not(.add)', function() {
            var that = this;
            IDM.draw($(this).find('img').attr('data-url'), function() {
                $('.item_main_pic li').removeClass('checked');
                $('.preview_layer').removeClass('checked');
                $(that).addClass('checked');
            });
        });

        //上传商品主图
        $('#upload_item_img_input').on('change',function(){
            var file = this.files.item(0);
            if(!file.type.match("image.*")){
                PT.alert('只允许图片格式的文件，如 jpg png gif');
                return false;
            }
            if(file.size>10485760){
                PT.alert('图片过大请保证在10M以内');
                return false;
            }
            $('#image_optimoze_modal').modal('shadeIn');
            PT.show_loading('正在上传图片','',true);
            $('#upload_item_img_form').submit();
        });

        //删除商品主图
        $(document).on('click.image_optimoze.delete_main_pic','.item_main_pic i.delete',function(e){
            var img_id;

            e.stopPropagation();

            img_id=$(this).next().attr('data-img-id');

            $('#image_optimoze_modal').modal('shadeIn');

            $.confirm({
                title:'精灵提醒',
                body:'您确定删除吗？',
                okHidden:function(){
                    PT.sendDajax({
                        'function': 'web_delete_main_pic',
                        'item_id': item_id,
                        'img_id': img_id,
                        'callback': 'PT.ImageOptimoze.delete_main_pic_callback'
                    });
                    $('#image_optimoze_modal').modal('shadeOut');
                },
                cancelHidden:function(){
                    $('#image_optimoze_modal').modal('shadeOut');
                }
            })
        });

        //选择本地上传图片
        $(document).on('click.image_optimoze.preview_layer', '.preview_layer', function() {
            var that = this;
            IDM.draw($(this).find('img').attr('src'), function() {
                $('.item_main_pic li').removeClass('checked');
                $(that).addClass('checked');
            });
        });

        //切换到图片优化选项卡
        $(document).on('click.image_optimoze.switch_optimoze', '#switch_optimoze', function() {
            $('#switch_optimoze').hide();
            $('#rechoose_img').show();
            $('.operation_box').addClass('optimoze');
        });

        //切换到选择图片选项卡
        $(document).on('click.image_optimoze.rechoose_img', '#rechoose_img', function() {
            $('#switch_optimoze').show();
            $('#rechoose_img').hide();
            $('.operation_box').removeClass('optimoze');
        });

        //图片剪裁
        $(document).on('click.image_optimoze.switch_img_cut', '#switch_img_cut', function() {
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

                $('#image_optimoze_modal').modal('shadeIn');

                $('#img_cut_modal').modal({
                    'backdrop': false
                });

                ICM.cut('img_cut', this, function(coordinate) {
                    var zoom = that.width / ICM.options.width;
                    IDM.cut_img(-coordinate.x, -coordinate.y, coordinate.w, coordinate.h, zoom)
                }, function() {
                    Jcrop_api = this;
                })
            });

        });

        //取消剪裁
        $('#img_cut_modal').on('cancelHidden', function() {
            var url = current_img_url() || $('#img_cut').attr('src');
            IDM.recover_cut_img();
            Jcrop_api.destroy();
            $('#img_cut_modal').removeAttr('style');
            $('#image_optimoze_modal').modal('shadeOut');
        });

        //确认剪裁
        $('#img_cut_modal').on('okHidden', function() {
            Jcrop_api.destroy();
            $('#img_cut_modal').removeAttr('style');
            $('#image_optimoze_modal').modal('shadeOut');
        });

        //风格选择
        $(document).on('click.image_optimoze.switch_style', '.style_box>li', function() {
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
            PT.sendDajax({
                'function':'web_record_template_click',
                'temp_id':$(this).find('img').attr('data-temp')
            });
        });

        //清除风格
        $('#clean_flag').on('click',function(){
            IDM.clear_group();
            IDM.redraw_layer();
            $('#text_control').html('');
            $('#choose_tip').show();
            $('.style_box li').removeClass('checked');
        });

        //预览
        // $('.style_box>li>img').on('mouseenter',function(){
        //     var src=$(this).attr('src'),that=this;
        //     IDM.load_img(src,function(){
        //         var img=this;

        //         $(img).css({
        //             height:'270px',
        //             width:'270px',
        //             position:'absolute',
        //             top:String($(that).parent().offset().top)+'px',
        //             left:String($(that).parent().offset().left)+'px',
        //             marginLeft:'-290px',
        //             zIndex: 1100,
        //             border:'1px solid #ddd',
        //             opacity:0,
        //         });

        //         $('body').append(img);
        //         $(img).stop().animate({marginLeft:-272,opacity:1},200);

        //         $(that).one('mouseout',function(){
        //             console.log('mouseout');
        //             $(img).stop().animate({marginLeft:-290,opacity:0},200).queue(function(e){
        //                 $(img).remove();
        //                 $(e).dequeue();
        //             });
        //         });
        //     })
        // });

        //风格分页切换
        $(document).on('click.image_optimozeoptimoze_style', '.optimoze_style .pagination li:not(.active)', function() {
            var index = Number($(this).text()),
                warp = $(this).closest('.pagination');
            warp.find('li').removeClass('active');
            $(this).addClass('active');
            warp.prev().find('.style_box').css('marginTop', -($('.style_warp').height()+2) * (index - 1));
        });

        //上传创意图片
        $('#local_upload_creative').on('change', function() {
            var file = this.files.item(0),
                url;

            if (file) {
                url = IDM.create_object_url(file);
                IDM.draw(url);
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
        $('#image_optimoze_modal').on('okHidden', function() {
            IDM.get_base64(function(img_str){

                var title=$('.preview_box .title').text();

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
                    data['function']='web_super_update_creative';
                    PT.show_loading('正在修改');
                }

                if(box_model==1){
                    data['function']='web_super_add_creative';
                    PT.show_loading('正在添加');
                }

                if(box_model==2){
                    data['function']='web_create_waiting_creative';
                    PT.show_loading('正在添加');
                }

                if(box_model==3){
                    data['id']=modify_waiting_creative_id;
                    data['function']='web_super_update_waiting_creative';
                    PT.show_loading('正在修改');
                }

                PT.sendDajax(data);
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
        $('.optimoze_style .nav a').on('shown',function(){
            lazy_load($('.optimoze_style .tab-pane.active img'));
        });

        //切换天数
        $('.select_rpt_days').on('change',function(e,val,obj){
            PT.show_loading('正在加载');
            window.location=obj[0].href+'&'+'type='+$('#show_type').val();
        });

        $('.tips').tooltip();
    }

    var current_img_url = function() {
        return $('.choose_pic_box .checked img').attr('data-url')||$('.choose_pic_box .checked img').attr('src');
    }

    var set_box_model=function(type){
        var type_desc_dict={0:'编辑创意',1:'添加新创意',2:'添加测试创意',3:'编辑测试创意'},
            obj=$('#image_optimoze_modal');

        obj.find('.modal-header h4').text(type_desc_dict[type]);
        obj.find('.modal-footer [action=confirm]').text(type_desc_dict[type].replace(/添加|编辑/,'提交'));

        box_model=type;
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

    return {
        init: function() {
            init_dom();
            check_font();

            lazy_load($('.optimoze_style .tab-pane.active img'));
        },
        add_creative_callback: function() {
            window.location.reload();
        },
        delete_creative_callback: function() {
            window.location.reload();
        },
        create_waiting_creative_callback: function() {
            window.location.reload();
        },
        update_creative_callback: function(creative_id, title) {
            var obj;
            obj=$('#item_'+creative_id);

            obj.find('.title').text(title);
            PT.light_msg('精灵提醒','修改成功');
        },
        update_test_title_callback:function(id, title){
            var obj;
            obj=$('#item_test_'+id);

            obj.find('.title').text(title);
            PT.light_msg('精灵提醒','修改成功');
        },
        delete_main_pic_callback:function(data){
            if(data.msg){
                PT.alert(data.msg)
            }else{
                var obj=$('.item_main_pic img[data-img-id='+data.data.img_id+']').parent();

                if(obj.hasClass('checked')){
                    $('.item_main_pic li:eq(0)').trigger('click'); //选中第一个图片
                }

                obj.remove();

                $('.item_main_pic li.add').removeClass('hide');

                $('#upload_item_img_input').val(''); //将文件域置空，避免第二次上传不触发
            }
        },
        upload_item_img_callback:function(data){
            PT.hide_loading()
            $('#image_optimoze_modal').modal('shadeOut');

            if(data.error){
                PT.alert(data.error);
            }else{
                $('.item_main_pic li.add').before('<li><i class="iconfont delete">&#xe623;</i> <img src="'+data.url+'_100x100.jpg" data-url="'+data.url+'" data-img-id="'+data.img_id+'"></li>');
                $('.item_main_pic li.add').prev().trigger('click');
                if($('.item_main_pic li:not(.add)').length>=5){
                    $('.item_main_pic li.add').addClass('hide');
                }

            }
        },
        show_creative_trend:function(camp_id, category_list, series_cfg_list){

            if (!$('#modal_camp_trend').length){
                $('body').append(pt_tpm["modal_camp_trend.tpm.html"]);
            }
            $('#camp_trend_title').text('创意');
            PT.draw_trend_chart( 'camp_trend_chart' , category_list, series_cfg_list);
            $('#modal_camp_trend').modal();
        }
    }
}();
