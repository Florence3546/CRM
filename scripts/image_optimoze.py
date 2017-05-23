# coding=UTF-8
import init_environ
import requests
from apilib.binder import FileItem
from apilib import TopError, get_tapi
from apps.subway.models_adgroup import *
from apps.subway.models_creative import *
from apps.subway.download import Downloader
from apps.subway.upload import delete_creative
from apps.subway.models_upload import UploadRecord
from apps.common.utils.utils_datetime import *
from apps.common.utils.utils_log import log


SHOW_DAYS = 1 # 创意最少投放时间

class CreativeManage():
    def __init__(self, shop_id):
        self.shop_id = shop_id
        self.appease_time = get_start_datetime(datetime.date.today()) - datetime.timedelta(days = SHOW_DAYS)
        self.dler, _ = Downloader.objects.get_or_create(shop_id = shop_id)

        self.tapi = None
        if (get_start_datetime(self.dler.api_valid_time) > get_start_datetime(datetime.date.today() - datetime.timedelta(days = 2))):
            self.tapi = get_tapi(shop_id = self.shop_id)
        self.vaild_adgroup = self.bind_adgroup()

    def bind_adgroup(self):
        """绑定开启测试的推广组"""
#         self.waiting_adgroup, self.runing_adgroup = [], []
        return Adgroup.objects.filter(shop_id = self.shop_id, creative_test_switch = True)

    def bind_waiting_creative(self, adgroup_id):
        """绑定等待投放的创意"""
        self.waiting_creative_list = list(CustomCreative.objects.filter(shop_id = self.shop_id, adgroup_id = adgroup_id, status = 0))

    def sync_struct(self):
        """同步所有结构数据"""
        self.struct = Downloader.download_all_struct(shop_id = self.shop_id)

    def sync_creative_rpt(self, adgroup, rpt_days):
        """同步宝贝下创意报表数据"""
        Creative.download_crtrpt_byadgs(self.shop_id, self.tapi, self.dler.token , [(adgroup['adgroup_id'], adgroup['campaign_id'], datetime.datetime.now() - datetime.timedelta(days = rpt_days))])

    def get_creative_list(self, adgroup_id):
        creative_list = list(Creative.objects.filter(shop_id = self.shop_id, adgroup_id = adgroup_id))
        return creative_list

    def add_creative(self, creative):
        """添加等待的创意 #fixed 3953 zhongjinfeng 20170321 这边直接把远程的图片读取下来，因为发现直接用图片地址会报图片正在审核不能修改的问题"""
#         return CustomCreative.add_creative_inner(self.tapi, shop_id = creative.shop_id, campaign_id = creative.campaign_id, adgroup_id = creative.adgroup_id, num_iid = creative.num_iid, title = creative.title, file_item = creative.img_url.replace('_sum.jpg', ''))
        req = requests.get(creative.img_url.replace('_sum.jpg', ''))
        if req.status_code:
            img = FileItem('item_pic.jpg', req.content)
            result, record_list = CustomCreative.add_creative_inner(self.tapi, creative.shop_id, creative.campaign_id, creative.adgroup_id, creative.num_iid, creative.title, img, opter = 9, opter_name = '')
            if record_list: # 此处不能直接调用upload 接口，因为这边的的图片链接需要特殊处理上传，调用upload接口会直接调用creative的add_creative  不能添加创意
                rcd_list = [UploadRecord(**record) for record in record_list]
                UploadRecord.objects.insert(rcd_list)
            return result
        
        log.error('获取远程图片失败  shop_id = %s num_iid = %s'%(creative.shop_id,creative.num_iid))
        return False

    def appease_show_time(self, creative):
        """检查创意投放时间是否满足"""
        creaetime = isinstance(creative.create_time, datetime.datetime) and creative.create_time or string_2datetime(creative.create_time)
        if creaetime < self.appease_time:
            return True
        else:
            return False

    def check_imp(self, creative):
        """检查创意是否有展现"""
        return True
        for rpt in creative.rpt_list:
            if rpt.impressions > 0:
                return True
        return False

    def start_rotate(self, creative, current_waiting_creative):
        """开始轮换创意"""
        if delete_creative(tapi = self.tapi, shop_id = self.shop_id, creative_id = creative.creative_id, opter = 9):
            if self.add_creative(current_waiting_creative):
                # 删除等待的创意
                ccrt_coll.remove({'shop_id':self.shop_id, '_id':current_waiting_creative.id})
            else:
                log.error('[添加创意失败] fun:start_rotate shop_id:%s creative_id:%s' % (self.shop_id, creative.creative_id))
        else:
            log.error('[删除创意失败] fun:start_rotate shop_id:%s creative_id:%s' % (self.shop_id, creative.creative_id))

    def calc_best_two(self, adgroup_id):
        """根据算法获取已完成投放中最好的两个创意"""
#         new_id_list = [obj.creative_id for obj in creative_list if obj.status == 1]
        complate_creative_list = CustomCreative.objects.filter(shop_id = self.shop_id, adgroup_id = adgroup_id, status = 1)
        new_id_list = [obj.creative_id for obj in complate_creative_list]
        if new_id_list:
            rpt_dict = CustomCreative.Report.get_summed_rpt({'shop_id': self.shop_id, 'adgroup_id': adgroup_id, 'creative_id': {'$in': new_id_list}}, rpt_days = 7)
            for crt_id in new_id_list:
                if crt_id not in rpt_dict:
                    rpt_dict[crt_id] = CustomCreative.Report()
            rpt_list = sorted(rpt_dict.items(), key = lambda x: x[1].ctr, reverse = True)
            new_id_list = [creative_id for creative_id, rpt in rpt_list]
        return new_id_list[:4]

    def sync_creative(self):
        for adgroup in self.vaild_adgroup:
            self.bind_waiting_creative(adgroup.adgroup_id)
            creative_list = self.get_creative_list(adgroup.adgroup_id)

            self.sync_creative_rpt(adgroup, 15)

            all_complate = True

            for creative in creative_list:
                if self.check_complate(creative):
                    CustomCreative.sync_complate_creative(self.shop_id, adgroup.adgroup_id, creative.creative_id)
                else:
                    all_complate = False
                    log.info('[创意还没有投放完成]  fun:sync_creative shop_id:%s adgroup_id:%s creative_id:%s' % (self.shop_id, adgroup.adgroup_id, creative.creative_id))

            if all_complate and not self.waiting_creative_list: # 所有创意都已经测试完成，并且没有等待测试的创意
                self.do_complate(adgroup)

    def do_complate(self, adgroup):
        """一个adgroup完成测试后的操作"""
        self.add_best_creative(adgroup)

        # 关闭测试开关
        adgroup.creative_test_switch = False
        adgroup.save()

    def add_best_creative(self, adgroup):
        """计算最好的两个创意，替换当前投放的"""
        creative_list = self.get_creative_list(adgroup.adgroup_id)
        best_creative_id_list = self.calc_best_two(adgroup.adgroup_id)

        creative_id_list = [i.creative_id for i in creative_list]

        delete_creative_list = [i for i in creative_id_list if i not in best_creative_id_list]
        add_creative = [i for i in best_creative_id_list if i not in creative_id_list]

        for creative_id in delete_creative_list: # 删除差集的创意
            if delete_creative(tapi = self.tapi, shop_id = self.shop_id, creative_id = creative_id, opter = 9):
                add_creative_id = add_creative.pop()
                complate_creative = CustomCreative.objects.filter(shop_id = self.shop_id, creative_id = add_creative_id, status = 1)[0]
                self.add_creative(complate_creative)

    def check_complate(self, creative):
        """判断创意是否满足测试完成的条件"""
        if self.appease_show_time(creative):
            if self.check_imp(creative):
                return True
            else:
                log.info('[创意没有展现]  fun:sync_creative shop_id:%s  creative_id:%s' % (self.shop_id, creative.creative_id))
                return False
        else:
            log.info('[展现时间不足]  fun:sync_creative shop_id:%s  creative_id:%s' % (self.shop_id, creative.creative_id))
            return False

    def check_and_add_waiting_creative(self):
        for adgroup in self.vaild_adgroup:
            self.bind_waiting_creative(adgroup.adgroup_id)
            creative_list = self.get_creative_list(adgroup.adgroup_id)

#             if(len(creative_list) <= 3) and self.waiting_creative_list: # 当只有三个以下创意时，直接添加一个
#                 current_waiting_creative = self.waiting_creative_list.pop()
#                 self.add_creative(current_waiting_creative)

            for i in range(4 - len(creative_list)): # 计算有几个坑位，直接填上
                if not self.waiting_creative_list:
                    log.info('[没有等待创意_setp1]  fun:sync_creative shop_id:%s  adgroup_id:%s' % (self.shop_id, adgroup.adgroup_id))
                    break
                current_waiting_creative = self.waiting_creative_list.pop()
#                 self.add_creative(current_waiting_creative)
                if self.add_creative(current_waiting_creative):
                    # 删除等待的创意
                    ccrt_coll.remove({'shop_id':self.shop_id, '_id':current_waiting_creative.id})

            for creative in creative_list:
                if not self.waiting_creative_list:
                    log.info('[没有等待创意_setp2]  fun:sync_creative shop_id:%s  adgroup_id:%s creative_id:%s' % (self.shop_id, adgroup.adgroup_id, creative.creative_id))
                    break

                if self.check_complate(creative):
                    current_waiting_creative = self.waiting_creative_list.pop()
                    self.start_rotate(creative, current_waiting_creative)


    def run(self):
        self.sync_struct()
        # 先同步投放完成的创意到已完成
        log.info("SETUP 1 shop_id=%s" % (self.shop_id))
        self.sync_creative()

        # 检查所有推广组下的创意是否有排队的并轮换
        log.info("SETUP 2 shop_id=%s" % (self.shop_id))
        self.check_and_add_waiting_creative()

def main():
    shop_id_list = []
    adgroups = Adgroup.objects.filter(creative_test_switch = True)
    for adg in adgroups:
        if adg.shop_id in shop_id_list:
            continue
        shop_id_list.append(adg.shop_id)

    log.info("Total shop nums %s" % (len(shop_id_list)))

    num = 0

    for shop_id in shop_id_list:
        num = num + 1
        log.info("===============current num %s/%s========================" % (num , len(shop_id_list)))
        try:
            cm = CreativeManage(shop_id = shop_id)
            if cm.tapi:
                cm.run()
            else:
                log.info('tapi is None shop_id=%s' % (shop_id))
        except Exception, e:
            log.error('CreativeManage error e=%s,shop_id=%s' % (e, shop_id))

if __name__ == "__main__":
    main()
