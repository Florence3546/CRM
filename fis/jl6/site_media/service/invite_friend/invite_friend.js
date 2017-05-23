define(["require", "template", 'widget/alert/alert','widget/lightMsg/lightMsg', 'widget/ajax/ajax', 'widget/share/share', 'widget/vaildata/vaildata', 'zclip'], function(require, template, alert, lightMsg, ajax, share) {
    "use strict";

    var share_somebody_remind = "亲，已复制订购信息到剪切板中，发送给您的小伙伴，如订购，系统会自动送分哦。";
    var share_anybody_remind = "亲，订购信息已复制到剪贴板，可以分享到朋友圈、旺旺或QQ群中，如小伙伴们订购并在会员中心填写您的主账号，系统会自动送分哟。";

    var share_anybody_content = function(){
        return $("#share_anybody").val();
    };

    var load_share = function(){
        var tpl = share.show(share_anybody_content());
        var show_obj = $("#share_component");
        show_obj.html(tpl);
    };

    var init = function() {
        var click_count = 0 ;
        $('[data-toggle="tooltip"]').tooltip();
        load_share();

        $("#share_btn").click(function(){
            var obj = $(this);
            if(click_count % 2 == 0){
	            var show_top = obj.parent().offset().top + obj.parent().height();
	            var show_left = obj.offset().left;
	            var desc_obj = $("#share_component");

	            desc_obj.css({top:show_top,left: show_left});
	            desc_obj.show();
	            obj.text('收起分享');
	        } else {
                $("#share_component").hide();
                obj.text('立即分享');
	        }
	        click_count += 1;
        });

        var generate_link_callback = function(){
            var nick,
                obj,
                last_version,
                last_cycle,
                last_data,
                tpl = __inline('invite_friend.html');


            nick = $.trim($("#recommend_nick").val());
            obj = $(tpl);
            $('body').append(obj);
            obj.find('input').on('change', function() {
                var order_version,
                    order_cycle,
                    order_version_text,
                    order_cycle_text;

                order_version = $('input[name=order_version]:checked', obj).val();
                order_cycle = $('input[name=order_cycle]:checked', obj).val();

                order_version_text = $('input[name=order_version]:checked', obj).parent().text();
                order_cycle_text = $('input[name=order_cycle]:checked', obj).parent().text();

                if (order_version && order_cycle) {
                    $('#recommend_box').removeClass('hide');
                    last_version = order_version;
                    last_cycle = order_cycle;

                    ajax.ajax("recommend_link", {
                        nick: nick,
                        order_version: order_version,
                        order_cycle: order_cycle
                    }, function(data) {
                        var btn = $('.btn-primary', obj);
                        obj.find('.order_version').text(order_version_text);
                        obj.find('.order_cycle').text(order_cycle_text);
                        obj.find('.current_price').text(data.current_price);
                        obj.find('.original_price').text(data.original_price);
                        obj.find('.url').text(data.url);

                        last_data = data;
                        //滚动到指定位置,修复复制位置定位错误
                        $("html,body").animate({scrollTop:0},0);
                        btn.removeClass('disabled');
                    });
                }
            });

            obj.find(".btn-primary").click(function(){
                var cur_obj = $(this);
                ajax.ajax('promotion_4shop', {
                    invited_name: nick,
                    order_version: last_version,
                    order_cycle: last_cycle,
                    current_price: last_data.current_price,
                    original_price: last_data.original_price,
                    url:last_data.url
                },function(){
                    get_invited();

                    cur_obj.zclip({
                        path: __uri('../../plugins/zclip/ZeroClipboard.swf'),
                        copy: function() {
                            return $('#recommend_box .alert').text().replace(/\s/g, '');
                        },
                    });

                    alert.show(share_somebody_remind);
                    obj.modal('hide');
                });
            });

            obj.on('hidden.bs.modal', function() {
                obj.remove();
            });

            obj.modal();
            return false;
        };

        $('#generate_link').on('click', function() {
            var check_link_permission_callback =function(result){
                if ( result.error_info.length > 0 ){
                    alert.show(result.error_info);
                } else {
	                generate_link_callback();
                }
            };

            var nick = $.trim($("#recommend_nick").val());
            var page_nick = $.trim($("#shop_nick").val());
            if (nick == '') {
                alert.show('请先输入店铺掌柜ID！');
                return false;
            } else if (page_nick == nick) {
                alert.show('亲，不能推荐自己哦！');
                return false;
            }

            ajax.ajax('check_link_permission', {
	            nick: nick
	        }, check_link_permission_callback);
        });

        $('#copy_link').zclip({
            path: __uri('../../plugins/zclip/ZeroClipboard.swf'),
            copy: function() {
                return share_anybody_content();
            },
            afterCopy: function() {
                alert.show(share_anybody_remind);
            }
        });

        $('#point_rule').on('click',function(){
            var obj,
                html=__inline("point_rule.html");

            obj=$(html);

            $("body").append(obj);

            obj.modal();

            obj.on('hidden.bs.modal',function(){
                obj.remove();
            });
        });
    }

    var get_invited = function() {
        var tpl = __inline("invited_box.html"),
            order_version_dict = {
                'ts-25811-1': '八引擎',
                'ts-25811-8': '双引擎'
            },
            order_cycle_dict = {
                '3': '一季度',
                '6': '半年',
                '12': '一年'
            },
            html;

        ajax.ajax('point_records', {
            type: 'promotion4shop'
        }, function(data) {
            for (var d in data.data) {
                var obj = data.data[d];

                obj.order_version_text = order_version_dict[obj.order_version]?order_version_dict[obj.order_version]:'未知';
                obj.order_cycle_text = order_cycle_dict[obj.order_cycle]?order_cycle_dict[obj.order_cycle]:'未知';

                obj.url = obj.url?obj.url:'http://tb.cn/r5Tt1By';
            }


            html = template.compile(tpl)(data);
            $('#invited_box').html(html);
            $('#invited_box').removeClass("dn");

            $('#invited_box .invited_copy').each(function(){
                $(this).zclip({
                    path: __uri('../../plugins/zclip/ZeroClipboard.swf'),
                    copy: function() {
                        return $(this).next().val();
                    },
                    afterCopy: function() {
                        alert.show(share_somebody_remind);
                    }
                });
            });

        });
    }

    return {
        init: function(){
            init();
            get_invited();
        }
    }
});

