# coding=UTF-8
import init_environ
from apps.web.models import main_ad_coll
from apps.common.utils.utils_datetime import string_2datetime

def init_main_ad():
    if main_ad_coll.find().count() > 0:
        print 'already has init data'
        return
    init_ad_list = [{
            "ad_start_time" : string_2datetime('2015-11-06 00:00:00'),
            "ad_update_time" : string_2datetime('2015-11-06 20:00:00'),
            "ad_position" : "RightNotice",
            "ad_updater" : "张瑜",
            "ad_weight" : "33",
            "ad_frequency" : 0,
            "ad_display" : 1,
            "ad_title" : "关于开车精灵2016版发布后老用户的操作记录为空的说明",
            "ad_user_type" : "0",
            "ad_url" : "",
            "ad_end_time" : string_2datetime('2015-11-22 20:00:00'),
            "ad_status" : 2,
            "ad_level" : "0",
            "id" : 1,
            "ad_content" : "<div style='line-height:30px'>亲，您好，因为新版数据的变化，老用户的旧版本操作记录无法迁移，所以在新版上看不到旧版本的操作记录哦；注意，精灵的操作记录在计划主页上；同时，精灵只能记录您在精灵中的操作，在直通车后台和其它软件中的操作，精灵是无法记录的哦。</div>",
            "ad_checker" : "张瑜",
            "ad_check_time" : string_2datetime('2015-11-06 20:00:00'),
            "ad_put_time" : string_2datetime('2015-11-06 20:00:00'),
            "ad_show_times" : 0,
            "ad_click_times" : 0
        },
        {
            "ad_start_time" : string_2datetime('2015-11-06 00:00:00'),
            "ad_update_time" : string_2datetime('2015-11-06 20:00:00'),
            "ad_position" : "RightNotice",
            "ad_updater" : "张瑜",
            "ad_weight" : "32",
            "ad_frequency" : 0,
            "ad_display" : 1,
            "ad_title" : "关于开车精灵2016版发布后查询30天以上报表为空的说明",
            "ad_user_type" : "0",
            "ad_url" : "",
            "ad_end_time" : string_2datetime('2015-11-22 20:00:00'),
            "ad_status" : 2,
            "ad_level" : "0",
            "id" : 2,
            "ad_content" : "<div style='line-height:30px'>亲，您好，新版开车精灵可以查询关键词/创意的30天汇总报表，和宝贝/计划/账户维度的90天细分&汇总报表，但因老系统只保留30天报表，所以新版中暂时只有30天数据，随着时间推移，90天内的报表数据不会删除，你可以查到的历史数据就会越来越多哦。</div>",
            "ad_checker" : "张瑜",
            "ad_check_time" : string_2datetime('2015-11-06 20:00:00'),
            "ad_put_time" : string_2datetime('2015-11-06 20:00:00'),
            "ad_show_times" : 0,
            "ad_click_times" : 0
        },
        {
            "ad_start_time" : string_2datetime('2015-11-06 00:00:00'),
            "ad_update_time" : string_2datetime('2015-11-06 20:00:00'),
            "ad_position" : "RightNotice",
            "ad_updater" : "张瑜",
            "ad_weight" : "34",
            "ad_frequency" : 0,
            "ad_display" : 1,
            "ad_title" : "关于开车精灵2016新版的重要特性说明",
            "ad_user_type" : "0",
            "ad_url" : "",
            "ad_end_time" : string_2datetime('2015-11-22 20:00:00'),
            "ad_status" : 2,
            "ad_level" : "0",
            "id" : 3,
            "ad_content" : "<div style='line-height:30px'>亲，您好，由于新版刚刚发布上线，精灵的帮助视频&文档、使用指导都在准备中，暂时没有发布，这里先说一下新版的一些特性(自动抢排名正在开发内测中，亲耐心等待哦)：<br/>1）可以自由选择报表统计日期，报表数据有分平台细分数据；<br/>2）一共4种托管类型，除之前的长尾和重点之外，还添加了无线和ROI托管类型；<br/>3）可以针对托管宝贝的关键词设置自动优化/只改价/不托管，增强了用户的个性化定义；<br/>4）改变了选词方式，增加了选词易用性，同时对关键词区分转化包/流量包/移动包/高性价比包/系统推荐；<br/>5）托管算法大幅改进，效果让我们用数据说话，当然直通车也是个生意，有盈有亏的，算法比以前好，不代表亲一定可以挣钱啊，一起努力哦；<br/>6）各种页面体验、易用性改进，多的不胜枚举；不同季节不同心情，如果你是颜值控，如果你喜新厌旧，一种皮肤看久了，你还可以换肤哦。<br/>7）慢慢品味吧，希望多提改进意见；对了，好用你就推荐，好用你就好评，好用你就续订哦！小精灵先谢了！</div>",
            "ad_checker" : "张瑜",
            "ad_check_time" : string_2datetime('2015-11-06 20:00:00'),
            "ad_put_time" : string_2datetime('2015-11-06 20:00:00'),
            "ad_show_times" : 0,
            "ad_click_times" : 0
        },
        {
            "ad_start_time" : string_2datetime('2015-11-06 00:00:00'),
            "ad_update_time" : string_2datetime('2015-11-06 20:00:00'),
            "ad_position" : "TopBanner",
            "ad_blacklist" : "",
            "ad_show_condition" : "",
            "ad_weight" : "35",
            "ad_display" : 1,
            "ad_title" : "开车精灵2016版全新发布",
            "ad_updater" : "张瑜",
            "ad_end_time" : string_2datetime('2015-12-07 00:00:00'),
            "ad_delay_secs" : "2",
            "ad_show_secs" : "120",
            "ad_status" : 2,
            "condition_type" : "condition",
            "ad_show_condition":"left_days>-1",
            "id" : 4,
            "ad_content" : "<div><a href=\"/web/upgrade_suggest/\" target=\"_blank\"><img id=\"test_img\" src='https://img.alicdn.com/imgextra/i2/836440495/TB2uqPygVXXXXc5XXXXXXXXXXXX-836440495.jpg'/></a></div>",
            "ad_close_btn" : "1",
            "ad_frequency" : 2,
            "ad_checker" : "张瑜",
            "ad_check_time" : string_2datetime('2015-11-06 20:00:00'),
            "ad_put_time" : string_2datetime('2015-11-06 20:00:00'),
            "ad_show_times" : 0,
            "ad_click_times" : 0
        }
    ]

    try:
        main_ad_coll.insert(init_ad_list,continue_on_error = True, safe = True)
        print 'success'
    except Exception,e:
        print e

if __name__ == '__main__':
    init_main_ad()
