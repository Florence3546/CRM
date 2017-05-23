# coding=UTF-8
import init_environ
from apps.web.models import ad_coll
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.cachekey import CacheKey

def init_ad_cfg():
    if ad_coll.find().count() > 0:
        print '已有初始化记录'
        return

    data = [{'id':1,
             'type':'menu',
             'title':'免费专家指导',
             'weight':'1',
             'flag':1,
             'create_time':'11/13 17:57:14',
             'html':'''<div class="w900 auto"> <a target=_blank href="http://wpa.qq.com/msgrd?v=3&amp;uin=2093327936&amp;site=qq&amp;menu=yes"> <img src=/site_media/jl5/images/pxhb1.jpg /> </a> </div>'''
             },
            {'id':2,
             'type':'menu',
             'title':'人工托管',
             'weight':'2',
             'flag':1,
             'create_time':'11/13 17:57:15',
             'html':'''<div class=rel style="width:900px;margin: 0 auto"> <a href="aliim:sendmsg?uid=cntaobao&amp;siteid=cntaobao&amp;touid=cntaobao人工托管服务"> <img src=/site_media/jl5/images/rgtg1113.gif /> </a> <div id=timer class="timer hide"> <div class=dd><span>8</span><span class=ml4>8</span></div> <div class=hh><span class=ml-10>8</span><span class=ml5>8</span></div> <div class=mm><span class=ml-10>8</span><span class=ml3>8</span></div> <div class=ss><span class=ml-10>8</span><span class=ml3>8</span></div> </div> </div>'''
             },
            {'id':3,
             'type':'menu',
             'title':'创意优化服务',
             'weight':'3',
             'flag':1,
             'create_time':'11/13 17:57:16',
             'html':'''<div class="w900 auto" id=carousel_box> <div id=myCarousel class="carousel slide">  <div class=carousel-inner> <div class="item active"> <img src=/site_media/jl5/images/optimize_creative_2.gif usemap=#talk_map_1 /> <map name=talk_map_1 id=talk_map_1> <area coords=845,249,899,294 href="aliim:sendmsg?uid=cntaobao&amp;siteid=cntaobao&amp;touid=cntaobao派生科技:设计顾问" onclick=PT.sendDajax({&quot;function&quot;:&quot;web_record_click&quot;}) /> <area coords=0,0,900,800 href="http://wpa.qq.com/msgrd?v=3&amp;uin=1460309795&amp;site=qq&amp;menu=yes" target=_blank onclick=PT.sendDajax({&quot;function&quot;:&quot;web_record_click&quot;}) /> </map> </div>  </div>  </div> </div>'''
             }
            ]

    ad_coll.insert(data)
    CacheAdpter.delete(CacheKey.WEB_AD_MENU, 'web')
    print 'finished'

if __name__ == '__main__':
    init_ad_cfg()
