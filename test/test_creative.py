# coding=UTF-8
import init_environ
# 
# from subway.models_creative import *
# from apps.subway.upload import delete_creative,update_custom_creative,update_creative
from apilib.binder import FileItem
# from apilib import get_tapi
# 
# 
# 
# shop_id = '63518068'
# campaign_id = '4123069'
# adgroup_id ='747019647'
# item_id = '547080702745'
# creative_id = '883345252'
# title = '测试啊'
# opter_name ='测试啊'
# tapi = get_tapi(shop_id = shop_id)



# tapi = get_tapi_by_user(shop_id = 63518068)
# result = delete_creative(tapi = None, shop_id = 63518068, creative_id = 671545389)
# print result
import requests
# fp = open('https://img.alicdn.com/bao/uploaded/i3/1340505033245324899/TB2Tz.wj4xmpuFjSZFNXXXrRXXa_!!0-saturn_solar.jpg_240x240.jpg','rb')
# print fp.read()
req = requests.get('https://img.alicdn.com/bao/uploaded/i3/1340505033245324899/TB2Tz.wj4xmpuFjSZFNXXXrRXXa_!!0-saturn_solar.jpg_240x240.jpg')
print req.status_code
img = FileItem('item_pic.jpg', req.content)
print img
print isinstance(img, (str, unicode))

# fp = open('test.jpg', 'rb')
# img = FileItem(fp.name, fp.read())
# 
# img='https://img.alicdn.com/imgextra/i1/454449631/TB2l.8gkpXXXXayXXXXXXXXXXXX_!!454449631.jpg'
# result = update_custom_creative(tapi = tapi, shop_id = int(shop_id), \
#                                 campaign_id = campaign_id, adgroup_id = adgroup_id, \
#                                 item_id = item_id, creative_id = creative_id, title = title, \
#                                 file_item = img, opter = 1, opter_name = opter_name)
# result = update_creative(tapi=tapi, shop_id=shop_id,\
#                           adgroup_id = adgroup_id, creative_id=creative_id, title=title\
#                           , img_url=img, opter=1, opter_name='')
# print result

# CustomCreative.sync_complate_creative(63518068, 547878580)

# 上传图片
# fp = open('test.jpg', 'rb')
# img = FileItem(fp.name, fp.read())
# img_id, img_url, recovery_dict = CustomCreative.item_img_upload(tapi, image = img, num_iid = 42817551307, shop_id = 63518068)
#
# print img_id
# print img_url
# print recovery_dict


# 删除图片
# print CustomCreative.item_img_delete(tapi, picture_ids = '196310101372836638')


# 创建图片分类
# print CustomCreative.get_or_create_pic_catid(tapi, shop_id = 63518068)

# 上传图片
# fp = open('test.jpg', 'rb')
# img = FileItem(fp.name, fp.read())
# print CustomCreative.upload_picture(tapi, img = img, shop_id = 63518068)

# 更新图片主图
# print CustomCreative.update_item_main_pic(tapi = tapi, shop_id = 63518068, pic_path = "http://img04.taobaocdn.com/imgextra/i4/454449631/TB2qBPycVXXXXXDXXXXXXXXXXXX_!!454449631.jpg", num_iid = 42817551307)


# 上传等待创意图
# fp = open('test.jpg', 'rb')
# img = FileItem(fp.name, fp.read())
# img_id, img_url, recovery_dict = CustomCreative.create_waiting_creative(tapi, image = img, num_iid = 42817551307, shop_id = 63518068)
