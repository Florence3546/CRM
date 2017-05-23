# coding:utf-8
import init_environ
import datetime,time

from apps.common.utils.utils_log import log
from apilib import QNApp
from apps.web.models import AppComment
from apps.common.models import Config

def get_comment_by_date(date, page, app):
    """获取某一天的所有5分好评"""
    tapi = QNApp.init_tapi(None)
    temp_list, comment_list = [], []
    result = tapi.fuwu_sale_scores_get(current_page = page, page_size = 100, date = date)
    if result and result.score_result and  result.score_result.score_result:
        temp_list = result.score_result.score_result
    for comment in temp_list:
        if comment.avg_score == '5.0':
            comment_list.append(comment)
    return comment_list

def save_comment(comment_dict):
    """保存评论"""
    app_comment = AppComment()
    app_comment.id = comment_dict['id']
    app_comment.avg_score = comment_dict['avg_score']
    app_comment.suggestion = comment_dict['suggestion'] if 'suggestion' in comment_dict else ''
    app_comment.service_code = comment_dict['service_code'] if 'service_code' in comment_dict else ''
    app_comment.user_nick = comment_dict['user_nick'] if 'user_nick' in comment_dict else ''
    app_comment.gmt_create = comment_dict['gmt_create']
    app_comment.item_code = comment_dict['item_code'] if 'item_code' in comment_dict else ''
    app_comment.item_name = comment_dict['item_name'] if 'item_name' in comment_dict else ''
    app_comment.is_pay = comment_dict['is_pay'] if 'is_pay' in comment_dict else ''
    app_comment.is_recommend = 0
    app_comment.save()

def get_history_comment(app):
    """获取历史的某一天至今的好评"""
    key = 'web.SYNC_WEB_COMMENT' if app == 'web' else 'web.SYNC_QN_COMMENT'
    cfg = Config.objects.get(key = key)
    today = datetime.date.today()
    cur_date_count = 0
    date = datetime.datetime.strptime(cfg.value,  '%Y-%m-%d').date()
    page = 1
    now_date = time.strftime("%Y-%m-%d", time.localtime())
    while date<=today:
        try:
            comment_list = get_comment_by_date(date, page, app)
            comment_id_list = [comment.id for comment in comment_list]
            # 首先检查数据库中有没有这些评论，若有则无需保存
            temp_id_list = AppComment.objects.filter(id__in=comment_id_list).values_list('id', flat=True)
            for comment in comment_list:
                comment_dict = comment.to_dict()
                if 'suggestion' in comment_dict and comment_dict['suggestion'] and comment_dict['id'] not in temp_id_list:
                    cur_date_count += 1
                    save_comment(comment_dict)
            if len(comment_list)<100:
                # 如果本次取得的数据条数小于100条，当天无更多评论，然后取下一天
                log.info('%s：%s有%s条新好评' % (date, app, cur_date_count))
                date = date + datetime.timedelta(days = 1)
                page = 1
                cur_date_count = 0
            else:
                #如果本次取得的数据条数等于100条，则有可能还有数据，需要取下一页数据
                page += 1
        except:
            log.info('同步评论出现异常，暂停10秒')
            time.sleep(10)
        # 每次取数据后暂停5秒
        time.sleep(3)
    cfg.value = now_date
    cfg.save()

def main():
    get_history_comment('web')
    get_history_comment('qn')

if __name__ == "__main__":
    main()
