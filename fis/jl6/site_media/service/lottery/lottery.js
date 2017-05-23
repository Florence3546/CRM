/**
 * Created by Administrator on 2015/12/7.
 */
define(['jquery','../common/poster_store','template','widget/ajax/ajax',
        'widget/alert/alert','scrolList','zclip'],
    function ($,posterStore,template,ajax,alert) {

    var share_anybody_remind = "亲，分享信息已复制到剪贴板，分享到朋友圈、旺旺或QQ群，小伙伴订购后系统会自动送您2500积分(等同25元)哟。";
    var share_content = "20元就能试用原价220元一个月的直通车优化软件--开车精灵双引擎版，订购后还有机会抽到iPhone 6S！订购链接：http://tb.cn/W1Xgsfx";

    var click=false;//记录点击状态
    //后台中间编号与前台突变映射，比如获取一号奖品,既prizes[1],对应的就是前台中的第8个
    var prizes = [0,8,1,9,4,2,6,7,3,5,10];
    var lottery = {
        index: -1,	//当前转动到哪个位置，起点位置
        count: 0,	//总共有多少个位置
        timer: 0,	//setTimeout的ID，用clearTimeout清除
        speed: 50,	//初始转动速度
        times: 0,	//转动次数
        cycle: 50000,	//转动基本次数：即至少需要转动多少次再进入抽奖环节
        prize: -1,	//中奖位置
        awards_detail:{},
        init: function (id) {
            if ($("#" + id).find(".lottery-unit").length > 0) {
                $lottery = $("#" + id);
                $units = $lottery.find(".lottery-unit");
                this.obj = $lottery;
                this.count = $units.length;
                $lottery.find(".lottery-unit-" + this.index).addClass("active");
            }
            ;
        },
        roll: function () {
            var index = this.index;
            var count = this.count;
            var lottery = this.obj;
            $(lottery).find(".lottery-unit-" + index).removeClass("active");
            index += 1;
            if (index > count - 1) {
                index = 0;
            }
            $(lottery).find(".lottery-unit-" + index).addClass("active");
            this.index = index;
            return false;
        },
        stop: function (index) {
            this.prize = index;
            return false;
        }
    };

    var init = function(){
        ajax.ajax('get_lottery_active',{},function(data){
            var lotteryObj = data['lottery_dict'];
            //需要提醒领奖
            if(lotteryObj['need_exchange']){
                lottery.awards_detail = lotteryObj['lottery_detail'];
                $('.bg_layer').fadeIn(200);
                initAward();
                /*var awards_type = lotteryObj['lottery_detail']['awards_type'];
                var sale_url = lotteryObj['lottery_detail']['sale_url'];
                if(awards_type==1||awards_type==2){
                    sale_url = '/web/lottery_coupon';
                }
                var tpl, html;
                tpl = __inline('award_sign.html');
                html = template.compile(tpl)({award_desc:lotteryObj['lottery_detail']['awards_desc'], sale_url: sale_url});
                $('#account_warp').before(html);
                $('#award-alert').slideDown('fast');
                $('#share_link').zclip({
                    path: __uri('../../plugins/zclip/ZeroClipboard.swf'),
                    copy: function() {
                        return share_content;
                    },
                    afterCopy: function() {
                        alert.show(share_anybody_remind);
                    }
                });*/
                return false;
            }

            if(lotteryObj['need_lottery']){
                initLottery();
            }
        });
    }

    var initLottery = function(){
        var tpl, html;
        tpl = __inline('lottery.html');

        /**
         * 获取中奖列表，然后渲染抽奖页面
         */
        ajax.ajax('get_winner_list',{},function(data){
            html = template.compile(tpl)({list:data.winner_list});
            //渲染ui
            $('#account_warp').before(html);
            //初始化抽奖页面
            lottery.init('lottery');

            /**
             * 点击抽奖按钮
             */
            $("#start_lottery").click(function(){
                if (click) {
                    return false;
                }else{
                    $('#hide_lottery').hide();//抽奖时，隐藏关闭按钮
                    lottery.speed=200;
                    roll();
                    lottery.prize = 9;
                    click=true;
                    $('#start_lottery').addClass('un_click');
                    //后台抽奖，返回抽奖结果
                    ajax.ajax('lucky_draw',{},function(data){
                        lottery.prize = prizes[data['awards_detail']['awards_type']]-1;
                        lottery.cycle = 50;
                        lottery.awards_detail = data['awards_detail'];
                    });
                    return false;
                }
            });
            $('.bg_layer').fadeIn(200);

            $('#show_decide_lottery').slideDown(500);

            $('#hide_lottery').click(function(){
                //正在抽奖时，不能关闭
                if(click){
                    return false;
                }
                $('#lottery').fadeOut(200);
                $('.bg_layer').fadeOut(200);
                $('#show_decide_lottery').remove();
            });
            $('#lottery_user_list').scrolList({
                speed: 40,
                rowHeight: 22,
                showCount:6
            });

            /**
             * 点击领奖后 关闭抽奖窗口
             */
            $('#lottery_award').click(function(){
                $('#lottery').slideUp('fast');
                $('.bg_layer').slideUp(200);
                $('#show_decide_lottery').remove();
            });

            /**
             * 分享
             */
            $('#share_btn').zclip({
                path: __uri('../../plugins/zclip/ZeroClipboard.swf'),
                copy: function() {
                    return share_content;
                },
                afterCopy: function() {
                    alert.show(share_anybody_remind);
                }
            });
        });
    }

    /**
     * 抽奖旋转
     * 第一圈，每次速度加10
     * @returns {boolean}
     */
    var roll = function(){
        lottery.times += 1;
        lottery.roll();
        if (lottery.times > lottery.cycle+10 && lottery.prize==lottery.index) {
            clearTimeout(lottery.timer);
            lottery.prize=-1;
            lottery.times=0;
            click = false;
            setTimeout(initAward,1000);
            $("#start_lottery").unbind('click');
        }else{
            if (lottery.times<lottery.cycle) {
                lottery.speed -= 10;
            }else{
                if (lottery.times > lottery.cycle+10 && ((lottery.prize==0 && lottery.index==0) || lottery.prize==lottery.index+1)) {
                    lottery.speed += 110;
                }else{
                    lottery.speed += 20;
                }
            }
            if (lottery.speed<60) {
                lottery.speed=60;
            };
            lottery.timer = setTimeout(roll,lottery.speed);
        }
        return false;
    }

    /**
     * 渲染领奖页面
     */
    var initAward = function(){

        var obj = lottery.awards_detail;
        var awards_type = obj.awards_type;
        var sale_url;
        var tpl, html;
        tpl = __inline('lottery_award.html');
        if(awards_type==1||awards_type==2){
            sale_url = '/web/lottery_coupon';
        }else{
            sale_url = obj.sale_url;
        }
        html = template.compile(tpl)({award_img:'/site_media/jl6/service/lottery/images/award_'+awards_type+'.png', sale_url: sale_url});
        $('#account_warp').before(html);
        $('#lottery_share').zclip({
            path: __uri('../../plugins/zclip/ZeroClipboard.swf'),
            copy: function() {
                return share_content;
            },
            afterCopy: function() {
                alert.show(share_anybody_remind);
            }
        });
        setTimeout('javascript:$("#lottery_award").show();',200);

        $('#close_lottery').click(function(){
            $("#lottery_award").slideUp(500,function(){
                $('.bg_layer').fadeOut(100);
                $("#lottery_award").remove();
            });
        });

        /**
         * 去掉抽奖页面
         */
        if($('#show_decide_lottery')){
            $('#show_decide_lottery').fadeOut(200,function(){
                $('#show_decide_lottery').remove();
            });
        }
    };

    /**
     * 中奖提示
     */
    var lotterySign = function(){
        var obj = lottery.awards_detail;
        var awards_type = obj.awards_type;
        var awards_img = $('#lottery_award img').attr('src')
        awards_img = awards_img.replace('award_1.png','award_'+awards_type+'.png');
        $('#lottery_award img').attr('src',awards_img);
        if(awards_type==1||awards_type==2){
            $('#lottery_award a').attr('href','/web/lottery_coupon');
        }else{
            $('#lottery_award a').attr('href',obj.sale_url);
        }
        $("#lottery_award").slideDown('fast');
    };

    return{
        init:init
    }
});