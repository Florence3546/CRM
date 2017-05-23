# coding=UTF-8

import init_environ
import datetime

from apps.alg.models import cmd_cfg_coll, strat_cfg_coll, CommandConfig, StrategyConfig


def init_cmdcfg():
    """初始化指令配置"""

    org_dict = {
        # 'Common-1G': {'cond': 'kw.online_days>=7', 'operate': 'del_kw()', 'desc': '7天无展现词'}, # online_days 需要重新计算
        # 'Common-2G': {'cond': 'kw.online_days>=15', 'operate': 'del_kw()', 'desc': '养词15天无点击'},
        'Common-3G': {'cond': 'kw.is_garbage==True',
                      'operate': 'del_kw()',
                      'desc': '淘宝判定垃圾词',
                      },
        'Common-4F': {'cond': 'kw.rpt7.click<3 and kw.rpt7.roi==0',
                      'operate':'upd_price(kw.max_price-random.randint(2,5))',
                      'desc': '7天无转化，并且基本无点击，降价5分',
                      },

        # 检查限价
        'CheckPrice': {'cond': 'True',
                       'operate': 'check_price(kw.max_price)',
                       'desc': '检查当前关键词是否超过限价',
                       },

        # 无点击
        'IncClick-3D': {'cond': 'kw.rpt7.click==0 and kw.max_price>=kw.proposed_max_price and kw.create_days>7',
                        'operate': 'del_kw()',
                        'desc': '出价高，无点击, 删除',
                        },

        # 点击少时，增加点击量
        'IncClick-7P': {'cond': 'kw.match_scope!=4 and kw.rpt7.click<10 and kw.max_price>kw.regular_price',
                        'operate': 'upd_match(4)',
                        'desc': '流量低，修改匹配模式为广泛匹配',
                        },
        'IncClick-1D': {'cond': 'kw.rpt7.click==0 and kw.max_price>=min(kw.limit_price, kw.proposed_max_price) and kw.create_days>7',
                        'operate': 'del_kw()',
                        'desc': '出价高，无点击, 删除',
                        },
        'IncClick-2P': {'cond': 'kw.max_price<min(kw.limit_price, kw.proposed_max_price) and 0<kw.rpt7.roi<camp.rpt7.roi',
                        'operate':'upd_price(kw.max_price*1.07)',
                        'desc':'有转化，加价',
                        },
        'IncClick-3P': {'cond': 'kw.max_price<min(kw.limit_price, kw.proposed_max_price) and kw.rpt7.roi>camp.rpt7.roi',
                        'operate':'upd_price(kw.max_price*1.10)',
                        'desc':'转化不错，加价',
                        },
        'IncClick-4P': {'cond': 'kw.max_price<min(kw.limit_price, kw.proposed_max_price) and kw.rpt7.ctr>=adg.kwrpt7.ctr',
                        'operate': 'upd_price(kw.max_price*1.05)',
                        'desc': '点击率高，加价',
                        },
        'IncClick-5P': {'cond': 'kw.max_price<kw.regular_price*0.95 and kw.rpt7.click<3',
                        'operate': 'upd_price((kw.regular_price*kw.regular_price+kw.max_price*kw.max_price)/(kw.regular_price+kw.max_price))',
                        'desc': '出价低，加价',
                        },
        'IncClick-6P': {'cond': 'kw.max_price<min(kw.limit_price, kw.proposed_max_price)*0.8',
                        'operate':'upd_price(kw.max_price*1.05)',
                        'desc':'出价比较低，加价',
                        },

        # 点击率低
        'IncCTR-1M': {'cond': 'kw.match_scope==4 and kw.rpt7.roi==0 and kw.rpt7.ctr<adg.kwrpt7.ctr*0.5',
                      'operate': 'upd_match(1)',
                      'desc': '点击率小，改匹配模式',
                      },
        'IncCTR-3D': {'cond': 'kw.match_scope==1 and kw.rpt7.roi==0 and kw.rpt7.ctr<adg.kwrpt7.ctr*0.5 and kw.create_days>7',
                      'operate': 'del_kw()',
                      'desc': '点击率小，删除',
                      },
        'IncCTR-4P': {'cond': 'kw.rpt7.ctr>adg.kwrpt7.ctr+0.5 and kw.max_price<kw.regular_price*1.5',
                      'operate':'upd_price(kw.max_price*1.05)',
                      'desc':'点击率高，加价',
                      },
        'IncCTR-5P': {'cond': 'kw.rpt7.roi>adg.kwrpt7.roi+0.5',
                      'operate':'upd_price(kw.max_price*1.05)',
                      'desc':'ROI高,加价',
                      },
        'IncCTR-6F': {'cond': 'kw.rpt7.roi==0 and kw.rpt7.ctr<adg.kwrpt7.ctr*0.8',
                      'operate':'upd_price(min(kw.max_price*0.97,kw.max_price-5))',
                      'desc':'点击率低，并且无转化，降价',
                      },

        # PPC高
        'RedPPC-1F': {'cond': 'kw.rpt7.roi==0 and kw.rpt3.cpc>adg.kwrpt3.cpc',
                      'operate': 'upd_price(min(kw.max_price*0.9,kw.max_price-6))',
                      'desc': 'PPC高，降价',
                      },
        'RedPPC-2F': {'cond': 'kw.rpt7.roi>0 and kw.rpt7.roi<adg.kwrpt7.roi*0.8 and kw.rpt7.roi<camp.rpt7.roi',
                      'operate': 'upd_price(min(kw.max_price*0.95,kw.max_price-4))',
                      'desc': 'PPC高，降价',
                      },
        'RedPPC-3P': {'cond': 'kw.rpt7.roi>max(adg.kwrpt7.roi*1.2,camp.rpt7.roi*1.2,3)',
                      'operate': 'upd_price(min(kw.max_price*1.03,kw.max_price+2))',
                      'desc': 'ROI高，加价，(为了智能优化的用户体验)',
                      },

        # 降低花费
        'RedCost-1F': {'cond': 'kw.rpt7.click>0 and kw.rpt7.roi==0',
                       'operate': 'upd_price(min(kw.max_price*0.92,kw.max_price-7))',
                       'desc': '无转化，降价',
                       },
        'RedCost-2F': {'cond': '0<kw.rpt7.roi<=min(adg.kwrpt7.roi*0.8,camp.rpt7.roi*0.8)',
                       'operate': 'upd_price(min(kw.max_price*0.95,kw.max_price-4))',
                       'desc':'低转化，降价',
                       },
        'RedCost-3F': {'cond': '0<kw.rpt7.roi<=min(adg.kwrpt7.roi,camp.rpt7.roi*1.2)',
                       'operate': 'upd_price(min(kw.max_price*0.97,kw.max_price-3))',
                       'desc':'转化不高',
                       },
        'RedCost-4F': {'cond': 'kw.rpt7.cost>adg.kwrpt7.cost*0.8 and kw.rpt7.roi<camp.rpt7.roi*1.5',
                       'operate':'upd_price(min(kw.max_price*0.97,kw.max_price-3))',
                       'desc':'花费过高，降价',
                       },

        # 转化率低
        'IncCVR-1F': {'cond': 'kw.rpt7.click>2 and kw.rpt7.roi==0 and adg.kwrpt7.roi>0',
                      'operate': 'upd_price(min(kw.max_price-kw.max_price*kw.rpt7.click*0.05*0.01/(kw.rpt7.favcount+1),kw.max_price-5))',
                      'desc': '无转化，降价',
                      },
        'IncCVR-2F': {'cond': 'kw.rpt7.click>0 and kw.rpt7.roi<min(adg.kwrpt7.roi*0.8,camp.rpt7.roi)',
                      'operate': 'upd_price(min(kw.max_price-kw.max_price*kw.rpt7.click*0.03*0.01/(kw.rpt7.favcount+1),kw.max_price-3))',
                      'desc':'转化率低，降价',
                      },
        'IncCVR-3P': {'cond': 'kw.rpt7.roi>adg.kwrpt7.roi>=camp.rpt7.roi+0.5 and adg.kwrpt7.roi>3.0',
                      'operate': 'upd_price(kw.max_price*1.10)',
                      'desc':'高转化，加价',
                      },
        'IncCVR-4P': {'cond': 'kw.rpt7.roi>adg.kwrpt7.roi>camp.rpt7.roi and adg.kwrpt7.roi<max(camp.rpt7.roi+0.5,3.0)',
                      'operate': 'upd_price(kw.max_price*1.07)',
                      'desc':'高转化，加价',
                      },
        'IncCVR-5P': {'cond': 'kw.rpt7.roi>max(adg.kwrpt7.roi,camp.rpt7.roi)',
                      'operate': 'upd_price(kw.max_price*1.05)',
                      'desc': '高转化，加价',
                      },

        # 降价省油
        'RedCost-6F':{'cond': 'adg.kwrpt7.pay==0 and kw.max_price>adg.kwavg_price',
                      'operate': 'upd_price((kw.max_price*kw.max_price+adg.kwavg_price*adg.kwavg_price)/(kw.max_price+adg.kwavg_price))',
                      'desc':'降价省油',
                      },
        'RedCost-7F':{'cond': 'adg.kwrpt7.pay==0 and kw.max_price==adg.kwavg_price',
                      'operate': 'upd_price(min(kw.max_price*0.97,kw.max_price-5))',
                      'desc':'降价省油',
                      },

        #
        'Default-1P': {'cond': 'kw.rpt7.roi>=camp.rpt7.roi+0.5>0.5',
                       'operate': 'upd_price(kw.max_price*1.08)',
                       'desc':'转化高，加价',
                       },
        'Default-2P': {'cond': 'camp.rpt7.roi+0.5>kw.rpt7.roi>0',
                       'operate': 'upd_price(kw.max_price*1.05)',
                       'desc': '有转化，加价',
                       },
        'Default-3P': {'cond': 'kw.rpt7.favcount>1 and max(adg.kwrpt7.roi,camp.rpt7.roi)<0.8',
                       'operate': 'upd_price(kw.max_price*1.03)',
                       'desc': '有收藏，加价',
                       },
    }

    insert_list = []
    now = datetime.datetime.now()
    for k, v in org_dict.items():
        new_instrcn_dict = v
        new_instrcn_dict.update({'name': k, 'date': now})
        insert_list.append(new_instrcn_dict)

    cmd_cfg_coll.remove({'name': {'$in': org_dict.keys()}})
    cmd_cfg_coll.insert(insert_list)

    print 'init cmd cfg ok: insert %s count' % len(insert_list)
    return


def init_stgcfg():

    insert_list = [{'desc': '标准策略',
                    'name': 'Default',
                    'adg_cmd_list': ['optm_qscore'],
                    'kw_cmd_list': ['IncClick-3D', 'IncCVR-2F', 'IncCVR-3P', 'IncCVR-4P', 'IncCVR-5P'],
                    },
                   {'desc': '减少投入', # 日限额用满了，计划中表现不是特别优异的执行此策略
                    'name': 'ReduceCost',
                    'kw_cmd_list': ['RedCost-1F', 'RedCost-2F', 'RedCost-3F', 'RedCost-4F'],
                    'adg_cmd_list': []
                    },
                   {'desc': '无点击', # 计划流量非常低，计划中所有的宝贝执行此策略
                    'name': 'IncreaseClickSepcial',
                    'kw_cmd_list': ['IncClick-7P', 'IncClick-1D', 'IncClick-5P', 'IncClick-6P', 'IncClick-2P', 'IncClick-3P', 'IncClick-4P'],
                    'adg_cmd_list': ['add_word', 'optm_qscore']
                    },
                   {'desc': '增加点击量', # 计划流量比较低，计划中表现比较好的执行此策略
                    'name': 'IncreaseClick',
                    'kw_cmd_list': ['IncClick-7P', 'IncClick-1D', 'IncClick-2P', 'IncClick-3P', 'IncClick-4P', 'IncClick-6P'],
                    'adg_cmd_list': ['add_word', 'optm_qscore']
                    },
                   {'desc': '加词', # 计划流量比较低，计划中表现比较差的宝贝执行此策略
                    'name': 'Default2',
                    'kw_cmd_list': ['IncClick-6P', 'IncCVR-3P', 'IncCVR-4P', 'IncCVR-5P', 'Default-1P', 'Default-2P', 'Default-3P'],
                    'adg_cmd_list': ['add_word', 'optm_qscore']
                    },
                   {'desc': '提升点击率', # 点击率不够
                    'name': 'IncreaseCTR',
                    'kw_cmd_list': ['IncCTR-1M', 'IncCTR-2M', 'IncCTR-3D', 'IncCTR-4P', 'IncCTR-5P', 'IncCTR-6F'],
                    'adg_cmd_list': ['add_word', 'optm_qscore']
                    },
                   {'desc': '降低PPC', # PPC太高
                    'name': 'ReducePPC',
                    'kw_cmd_list': ['RedPPC-1F', 'RedPPC-2F', 'RedPPC-3P'],
                    'adg_cmd_list': ['optm_qscore']
                    },
                   {'desc': '提升转化率', # 转化率较差
                    'name': 'IncreaseCVR',
                    'kw_cmd_list': ['IncCVR-1F', 'IncCVR-2F', 'IncCVR-3P', 'IncCVR-4P', 'IncCVR-5P'],
                    'adg_cmd_list': ['optm_qscore']
                    },
                   {'desc': '加价引流', # 智能优化，加价引流
                    'name': 'IncreaseCost',
                    'kw_cmd_list': ['IncClick-2P', 'IncClick-3P', 'IncClick-4P', 'IncClick-5P', 'IncClick-6P'],
                    'adg_cmd_list': []
                    },
                   {'desc': '降价省油', # 智能优化，降价省油
                    'name': 'ReduceCost2',
                    'kw_cmd_list':['RedCost-6F', 'RedCost-7F', 'RedCost-1F', 'RedCost-2F', 'RedCost-3F', 'RedCost-4F'],
                    'adg_cmd_list':[],
                    },
                   {'desc': '校验出价',
                    'name': 'CheckPrice',
                    'kw_cmd_list': ['CheckPrice'],
                    'adg_cmd_list': []
                    },
                   {'desc':'根据流量调整出价',
                    'name':'CheckPrice2',
                    'kw_cmd_list':['IncClick-7P', 'IncClick-5P', 'IncClick-6P', 'IncClick-2P', 'IncClick-3P', 'IncClick-4P'],
                    'adg_cmd_list':[],
                    },
                   {'desc':'根据流量调整出价',
                    'name':'CheckPrice3',
                    'kw_cmd_list':['IncClick-7P', 'IncClick-2P', 'IncClick-3P', 'IncClick-4P', 'IncClick-6P'],
                    'adg_cmd_list':[],
                    },
                   {'desc':'只加词',
                    'name':'PureAddWord',
                    'kw_cmd_list':[],
                    'adg_cmd_list':['add_word']
                    },
                   {'desc':'只优化质量得分',
                    'name':'PureOptQscore',
                    'kw_cmd_list':[],
                    'adg_cmd_list':['optm_qscore']
                    },
                   ]

    key_list = [k['name'] for k in insert_list]
    strat_cfg_coll.remove({'name': {'$in': key_list}})
    strat_cfg_coll.insert(insert_list)

    print 'init stg cfg ok: insert %s count' % len(insert_list)
    return


if __name__ == '__main__':
    # init_cmdcfg()
    init_stgcfg()
    CommandConfig.refresh_all_configs()
    # StrategyConfig.refresh_all_configs()
