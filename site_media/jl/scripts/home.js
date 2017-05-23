PT.namespace('Home');
PT.Home = function () {

	//第一次进入时，发送请求第一天的数据
	var send_date=function(){
		PT.show_loading('正在获取数据');
		PT.sendDajax({'function':'web_get_account','last_day':1});
	};

	var init_detailed_table=function(){
		var detailed_table=$('#detailed_table').dataTable({
			"bPaginate": false,
			"bFilter": false,
			"bInfo": false,
			"aaSorting":[[0,'desc']],
			"oLanguage": {
				"sZeroRecords": "亲，没有符合条件的数据",
				"sInfoEmpty": "亲，没有符合条件的数据"
				},
			"aoColumns":[null, null, null, null, null, null,
			                        {"sSortDataType":"td-text", "sType":"numeric"},
                                    {"sSortDataType":"td-text", "sType":"numeric"},
                                    {"sSortDataType":"td-text", "sType":"numeric"},
			                        null, null]
		});
	};
	
	var popup_win=function(){
        $.fancybox.open([{href:'#popup_win'}], {helpers:{
            title : {type : 'outside'},
            overlay : {closeClick: false}
        }});
	}

	var init_dom=function() {

		var r_width=$('#right_box').css('width');
		$('#right_box').css('width',r_width);

		$('#btn_recharge').click(function(){
			PT.confirm('确认跳转到直通车后台立即充值？',function(){
				PT.Base.goto_ztc(6,'','','');
			});
		});

		$(document).on('click','.close_msg', function() {
			var temp_list = $(this).attr('href').slice(1).split('_');
            $(this).removeClass('close_msg');
            $(this).find('i').removeClass('r_color').addClass('s_color');
			PT.Base.change_msg_count();
			PT.sendDajax({'function':'web_close_msg','msg_id':temp_list[0],"is_common":temp_list[1]});
		});

        $(document).on('click', '#modal_usermsg .close', function() {
            var jq_modal = $('#modal_usermsg'),
                jq_target = $('#header_inbox_bar');
            move_effect(jq_modal, jq_target);
        });

        $(document).on('click', '#modal_referer .close_modal_referer', function() {
            var jq_modal = $('#modal_referer'),
                jq_target = $('#point_info');
            move_effect(jq_modal, jq_target);

        });

        $(document).on('click','#receive_recount_home',function(){
            var user_name = $('#input_referrer').val().replace(/^\s+|\s+$/g,"");
            if (user_name){
                $('#error_msg').hide();
                $('#loading_tips').fadeIn();
                PT.sendDajax({'function':'web_receive_recount','nick':user_name,'namespace':'Home'});
            }else{
                $('#error_msg').text('请先输入推荐人的店铺主旺旺').fadeIn();
                $('#input_referrer').focus();
            }
        });

		//无线推广计划申请，需要设置一个消息，并连接id命名为hdbm_20131202
		$('#hdbm_20131202').live('click.PT.e',function(){
			PT.confirm("开通后将占用您的一个推广计划并只能用于无线推广，您确认申请开通无线推广计划吗？",function(){
				PT.show_loading('正在登记申请');
				PT.sendDajax({'function':'web_record_hd_20131202'});
			});
		});

	};

	var init_help=function(){

		var help_list=[
			{
				element:'#contact_consult .tips',
				content:'1/4 这里可以联系您的专属顾问',
				placement:'right'
			},
			{
				element:'#header_inbox_bar',
				content:'2/4 这里可以查看您的消息和系统公告',
				placement:'bottom'
			},
			{
				element:'#account_p',
				content:'3/4 显示您店铺的整体数据',
				placement:'bottom'
			},
			{
				element:'#dashboard-report-range',
				content:'4/4 切换天数以便查看一段时间内的数据',
				placement:'bottom'
			}
		];
		PT.help(help_list);
	};

    var move_effect = function (jq_modal, jq_target) {
        var now_left = jq_modal.offset()['left'],
            now_top = jq_modal.offset()['top']-4,

            offset_left = jq_target.offset()['left'],
            offset_top = jq_target.offset()['top'],
            width = jq_target.width(),
            height = jq_target.height();

        jq_modal.css({'marginTop':0,'marginLeft':0,'top':now_top,'left':now_left,'overflow':'hidden'});
        jq_modal.animate({'height':height, 'width':width, 'top':offset_top, 'left':offset_left, 'opacity':0},300);
        jq_modal.modal('hide');
        jq_target.find('a').pulsate({color: "#FF0000",repeat: 3});
    };

    return {

        init: function () {
			PT.initDashboardDaterange();
			PT.Base.set_nav_activ(0,0);
			send_date();
			init_dom();
			init_detailed_table();
			init_help();
			popup_win();
        },
        initIntro: function () {
            if ($.cookie('intro_show')) {
                return;
            }

            $.cookie('intro_show', 1);

            setTimeout(function () {
                var unique_id = $.gritter.add({
                    // (string | mandatory) the heading of the notification
                    title: '开车精灵研发团队！',
                    // (string | mandatory) the text inside the notification
                    text: '欢迎使用开车精灵!此消息由jquery的gritter方法控制，您可以在index中添加多个消息，当用户第一次进入时会显示',
                    // (string | optional) the image to display on the left
                    image: '/site_media/jl/img/logo.png',
                    // (bool | optional) if you want it to fade out on its own or just sit there
                    sticky: true,
                    // (int | optional) the time you want it to be alive for before fading out
                    time: '',
                    // (string | optional) the class name you want to apply to that specific message
                    class_name: 'my-sticky-class'
                });

                // You can have it return a unique id, this can be used to manually remove it later using
                setTimeout(function () {
                    $.gritter.remove(unique_id, {
                        fade: true,
                        speed: 'slow'
                    });
                }, 12000);
            }, 2000);
        },
		select_call_back: function(value){
			PT.sendDajax({'function':'web_get_account','last_day':value});
		},
		append_account_data: function(data){
			PT.hide_loading();
			$('#account_p').html(template.render('account_c',data[0]));
			App.initTooltips();
		},
		receive_recount_back:function(result){
			if (result.error_msg) {
				$('#loading_tips').hide();
				$('#error_msg').text(result.error_msg).fadeIn();
			}else{
				$('#modal_referer').modal('hide');
				var msg="恭喜您获得精灵赠送的<span class='r_color'>"+result.point_1+"</span>个精灵币";
				PT.alert(msg);
			}
		},

    };

}();
