PT.namespace('NcrmBase');
PT.NcrmBase = function() {

    var psuser_cache;

    var load_js = function(file_name, namespace) {
        if (PT.hasOwnProperty(namespace)) {
            return false;
        }
        var script = document.createElement("SCRIPT");
        script.src = file_name;
        var heads = document.getElementsByTagName("HEAD");
        head = heads[0];
        head.appendChild(script);
    };

    var change_shop_or_nick = function(obj){
        var mark = obj.val().replace(/\s/g, "");
        if (/^[0-9]+$/.test(mark)) {
            obj.attr('name', 'ncr__shop_id__equal');
        } else {
            obj.attr('name', 'ncr__nick__constants');
        }
    };

    var init_dom = function() {
            $("input[type=text].identity").keydown(function(event) {
                // 修改该 form 表单 属性
                if( event.which == 13){       //13等于回车键(Enter)键值,ctrlKey 等于 Ctrl
                    var obj = $(this);
                    change_shop_or_nick(obj);
                }
            });

            $("input[type=text].identity").blur(function() {
                var obj = $(this);
                change_shop_or_nick(obj);
            });

            if ($('.psuser_input').length || $('.psuser_select').length) {
                PT.sendDajax({
                    'function': 'ncrm_get_psuser_list',
                    'namespace': 'NcrmBase.psuser_select_callBack'
                });
            }

	        //当鼠标经过该元素时，加上hover这个class名称，修复ie中css的hover动作
	        $(document).on('mouseover.PT.e','*[fix-ie="hover"]',function(){
	            $(this).addClass('hover');
	            $(this).mouseout(function(){
	                $(this).removeClass('hover');
	            });
	        });

            $(document).on('blur', '.psuser_input', function() {
                var link_id = $(this).attr('link');
                if ($(link_id).val() == '') {
                    $(this).val("");
                };
            })

            $(document).on('keydown', '.psuser_input', function(e) {
                var e = window.event || e,
                    link_id = $(this).attr('link');
                if (e.keyCode == 8 || e.keyCode == 46) {
                    $(this).val('');
                    $(link_id).val('')
                }
            })

            $('.edit_customer').click(function() {
                var cust_id = parseInt($(this).attr('cust_id'));
                $.ajax({
                    url: '/ncrm/edit_customer/',
                    data: {
                        'cust_id': cust_id
                    },
                    success: function(data, status) {
                        $('#customer_edit_box').html(data);
                        $('#customer_edit_layout').modal();
                        load_js('/site_media/jl5/ncrm_js/edit_customer.js?t=20141229', 'EditCustomer');

                        var timer = setInterval(function() {
                            if (PT.EditCustomer) {
                                PT.EditCustomer.init();
                                clearInterval(timer);
                            }
                        }, 500)
                    },
                    error: function() {
                        PT.alert("出错了，请联系管理员！");
                    }
                });
            });

            $('.edit_subscribe').click(function() {
                //var subscribe_id = parseInt($(this).attr('subscribe_id'));
                $.ajax({
                    url: '/ncrm/edit_subscribe/',
                    data: {
                        //'subscribe_id': subscribe_id,
                        //'nick':$(this).closest('tr').find('td:eq(0)').text(),
                        'subscribe_id': parseInt($(this).attr('subscribe_id')),
                        'nick':$(this).attr('nick'),
                        'approval_tag': $('#approval_tag').val() || ''
                    },
                    success: function(data, status) {
                        $('#subscribe_edit_box').html(data);
                        $('#subscribe_edit_layout').modal();
                        load_js('/site_media/jl5/ncrm_js/edit_subscribe.js', 'EditSubscribe');

                        var timer = setInterval(function() {
                            if (PT.EditSubscribe) {
                                PT.EditSubscribe.init();
                                clearInterval(timer);
                            }
                        }, 500)

                    },
                    error: function() {
                        PT.alert("出错了，请联系管理员！");
                    }
                });
            });
            
            //展开隐藏订单
            $('.order_switch').click(function () {
	            if ($(this).attr('flag')=='1') {
		            $('#order_list_'+$(this).attr('shop_id')).removeClass('h220');
		            $(this).attr('flag', '0').html('收起');
	            } else {
                    $('#order_list_'+$(this).attr('shop_id')).addClass('h220');
                    $(this).attr('flag', '1').html('展开');
	            }
            });

            //展开隐藏订单
            $('.show_order_more').on('click', function() {
                $(this).closest('.ovh').removeClass('h250 h220');
                $(this).remove();
            });

            $('#return_top').on('mouseover', function() {
                $(this).removeClass('opt3');
            });

            $('#return_top').on('mouseout', function() {
                $(this).addClass('opt3');
            });

            $(window).on('scroll', function() {
                var bodyOffsetTop = document.body.scrollTop | document.documentElement.scrollTop;
                if (bodyOffsetTop > 300) {
                    $('#return_top').fadeIn(300);
                } else {
                    $('#return_top').fadeOut(300);
                }
            });

            $('#return_top').on('click', function() {
                $("html,body").animate({
                    scrollTop: 0
                }, 300);
            });

            //删除确认
            $('.del_confirm').on('click',function(e){
                var title,link;

                e.preventDefault();

                title=$(this).attr('data-title');
                link=$(this).attr('href');

                PT.confirm(title,function(){
                    window.location.href=link;
                });
                return false;
            });

            //重置
            $('button[type=reset]').on('click',function(){
                var form_obj;
                form_obj=$(this).parents('form:first');
                form_obj.find('div input[type=text]').val('');
                form_obj.find('div select').val('0');
                form_obj.find('div input[type=checkbox]').attr('checked',false);
                return false;
            });
            
            //导出excel
            $("#report_export").click(function(){
                var consult = $("#server_id").val();
                var form_obj = $("#workbanch_search_form");
                form_obj.find("input[name=search_type]").val("query_global");
                var export_type = '0';
                var els = $("#export_last_subscribe").attr("checked");
                var e7d = $("#export_7days_data").attr("checked");
                if(els&&!e7d){
                    export_type='1';
                }else if(!els&&e7d){
                    export_type='2';
                }else if(els&&e7d){
                    export_type='3';
                }

                var params = '?export_type='+export_type;
                $(form_obj.serializeArray()).each(function(){
                    params=params+'&'+this.name+'='+this.value
                });
                window.open('../export_customer_data'+params);
            });

        },

        has_psuser_cache = function() {
            return psuser_cache instanceof Object;
        }

    return {
        init: function() {
            init_dom();
        },
        psuser_select_callBack: function(json) {
            if (json === undefined && has_psuser_cache()) {
                json = psuser_cache;
            } else {
                psuser_cache = json;
            }

            var i = 0,
                show_items = [],
                i_end = json.length;
            for (i; i < i_end; i++) {
                show_items.push(json[i].name_cn + ' ' + json[i].name + ' ' + json[i].position);
            }


            $('.psuser_input').typeahead({
                source: show_items,
                updater: function(item) {
                    var link_id, name_cn;
                    item_list = item.split(' ');
                    for (var j = 0; j < i_end; j++) {
                        if (json[j].name_cn == item_list[0] && json[j].position == item_list[2]) {
                            current_value = json[j].id;
                        }
                    }
                    link_id = this.$element.attr('link');
                    $(link_id).val(current_value);
                    return item;
                }
            });


            var html = '<option value="">---请选择---</option>',
                i = 0;
            for (i; i < json.length; i++) {
                html += '<option value="' + json[i].id + '">' + json[i].position + '&nbsp;&nbsp;:&nbsp;&nbsp;' + json[i].name_cn + '</option>'
            }
            // $('.psuser_select').html(html).each(function() {
            //     var initVaule = $(this).attr('data-init');
            //     if (initVaule) {
            //         $(this).val(initVaule);
            //     } else {
            //         $(this).val('0');
            //     }
            // });

            $('.psuser_select').each(function(){
                var position_list = $(this).attr('data-position')?$(this).attr('data-position').split(','):[],
                    initVaule = $(this).attr('data-init'),
                    special_html='<option value="">------</option>',
                    i=0;

                if(position_list.length>0){
                    for (i; i < json.length; i++) {
                        if ($.inArray(json[i].true_position, position_list)==-1) {
                            continue;
                        }
                        special_html += '<option value="' + json[i].id + '">' + json[i].position + '&nbsp;&nbsp;:&nbsp;&nbsp;' + json[i].name_cn + '</option>'
                    }
                    $(this).html(special_html);
                }else{
                    $(this).html(html);
                }

                if (initVaule) {
                    $(this).val(initVaule);
                } else {
                    $(this).val('');
                }

            })

            //// 缓存姓名ID映射到页面 by zhongchao 20160302
            //var psuser_cache_cn = {};
            //$.each(psuser_cache, function (i, obj) {
            //    psuser_cache_cn[obj.name_cn] = obj.id;
            //});
            //$('html').data('psuser_cache_cn', psuser_cache_cn);

        },
        has_psuser_cache: has_psuser_cache
    }
}();
