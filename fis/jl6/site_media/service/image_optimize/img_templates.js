/**
 * Created by Administrator on 2015/12/23.
 */
define(function(){
    var templates = {
        '1': {
            price: '79',
            desc1: "包邮",
            color1: '#c40000'
        },
        '2': {
            price: '79.00',
            desc1: "新品特惠",
            color1: '#c40000'
        },
        '3': {
            desc1: "月销千件即将涨价",
            color1: '#c40000'
        },
        '4': {
            price: "38.00",
            desc1: "包邮",
            color1: '#c40000'
        },
        '5': {
            price: "38.00",
            desc1: "包邮",
            desc2: "月销千件",
            color1: '#c40000'
        },
        '6': {
            price: "38.00",
            desc1: "月销千件",
            color1: '#c40000'
        },
        '7': {
            desc1: "热卖",
            color1: '#c40000'
        },
        '8': {
            desc1: "热卖",
            color1: '#c40000'
        },
        '9': {
            desc1: "劲减",
            desc2: "30%",
            color1: '#c40000'
        },
        '10': {
            desc1: "劲减",
            desc2: "30%",
            price1: "199",
            price2: "249",
            color1: '#ff417e',
            color2: '#393939'
        },
        '11': {
            desc1: "20",
            desc2: "SALE",
            color1: '#7fc3c0',
            color2: '#35395c'
        },
        '12': {
            desc1: "20",
            desc2: "SALE",
            color1: "#f18cab",
            color2: "#35395c"
        },
        '13': {
            desc1: "fantastic",
            desc2: "offer",
            color1: "#e24675",
            color2: "#2f3557"
        },
        '14': {
            desc1: "limited",
            desc2: "offer",
            color1: "#2f3557",
            color2: "#3bb6c7"
        },
        '15': {
            desc1: "Sale",
            color1: "#e24675",
            color2: "#2f3557"
        },
        '16': {
            desc1: "年中大促限时抢购"
        },
        '17': {
            desc1: "年中大促限时抢购",
            color1: "#d52527",
            color2: "#d87f30"
        },
        '18': {
            desc1: "年中大促",
            desc2: "大码",
            color1: "#c40000"
        },
        '19': {
            desc1: "年中大促",
            color1: "#c40000"
        },
        '20': {
            desc1: '76元包邮'
        },
        '21': {
            desc1: '大爱',
            desc2: '小清新'
        },
        '22': {
            desc1: '109',
            desc2: '包邮',
            color1: '#00f5ff'
        },
        '23': {
            desc1: '夏季女装',
            desc2: '清新脱俗',
            color1: '#00a8ff'
        },
        '24': {
            desc1: '热卖',
            color1: '#6eb92b'
        },
        '25': {
            desc1: '199',
            desc2: '特卖',
            color1: '#aacd06',
            color2: '#6eb92b'
        },
        '26': {
            desc1: '热销千件',
            desc2: '买二送一',
            color1: '#6eb92b'
        },
        '27': {
            desc1: '88元'
        },
        '28': {
            desc1: '热卖',
            desc2: '热销千件厂家直销'
        },
        '29': {
            desc1: '69元',
            desc2: '包邮'
        },
        '30': {
            desc1: '热销千件',
            desc2: '厂家直销'
        },
        '31': {
            desc1: '经典时尚',
            desc2: '精致美观',
            color1: '#deff00',
            color2: '#272c3d',
            fontsize1: 60,
            fontsize2: 60
        },
        '32': {
            desc1: '¥88元包邮'
        },
        '33': {
            desc1: '奢华精品',
            color1: '#ffea03'
        },
        '34': {
            desc1: '¥288元包邮',
            color1: '#000',
            color2: '#ffea03'
        },
        '35': {
            desc1: '奢华',
            desc2: '精致'
        },
        '36': {
            desc1: '79元',
            desc2: '包邮'
        },
        '37': {
            desc1: '79元',
            desc2: '包邮'
        },
        '38': {
            desc1: '热卖',
            desc2: '热销千件厂家直销'
        },
        '39': {
            desc1: '79元',
            desc2: '包邮'
        },
        '40': {
            desc1: '奢华',
            desc2: '精致'
        },
        '41': {
            desc1: '188元'
        },
        '42': {
            desc1: '经典时尚精致美观'
        },
        '43': {
            desc1: '热卖'
        },
        '44': {
            desc1: '经典',
            desc2: '精致'
        },
        '45': {
            desc1: '热销千件厂家直销',
            desc2: '¥188'
        },
        '46': {
            desc1: '199',
            desc2: '包邮',
            desc3: '特卖',
            color1: '#ff2400'
        },
        '47': {
            desc1: '周年庆典',
            desc2: '特惠促销',
            color1: '#ff2400',
            color2: '#fff'
        },
        '48': {
            desc1: '299.00',
            desc2: '199',
            desc3: '包邮',
            color1: '#f30100',
            color2: '#fff',
            color3: '#000',
            color4: "#ffd800"
        },
        '49': {
            desc1: '99',
            desc2: '包邮'
        },
        '50': {
            desc1: '引领',
            desc2: '时尚',
            color1: '#e80000',
            color2: '#fff'
        },
        '51': {
            desc1: '特价',
            desc2: '¥58.00'
        },
        '52': {
            desc1: '夏季新款特价热卖'
        },
        '53': {
            desc1: '夏季新款',
            desc2: '特价热卖'
        },
        '54': {
            desc1: '¥188.00',
            desc2: '包邮'
        },
        '55': {
            desc1: '99',
            desc2: '包邮'
        },
        '56': {
            desc1: '热销千件厂家直销',
            color1: '#f00'
        },
        '57': {
            desc1: '单品热卖顺丰包邮'
        },
        '58': {
            desc1: '199',
            desc2: '包邮'
        },
        '59': {
            desc1: '欧美时尚',
            desc2: 'FASHION'
        },
        '60': {
            desc1: '特卖',
            desc2: '299'
        },
        '61': {
            desc1: 'HOT'
        },
        '62': {
            desc1: '199',
            desc2: '包邮'
        },
        '63': {
            desc1: '热卖单品',
            desc2: '欧美简约'
        },
        '64': {
            desc1: '¥158.00',
            desc2: '包邮'
        },
        '65': {
            desc1: '158',
            desc2: '包邮'
        },
        '66': {
            desc1: '夏季新款特价热卖'
        },
        '67': {
            desc1: '夏季新款'
        },
        '68': {
            desc1: '199元'
        },
        '69': {
            desc1: '199',
            desc2: '包邮'
        },
        '70': {
            desc1: '特卖'
        },
        '71': {
            desc1: '简约而不简单'
        },
        '72': {
            desc1: '热卖',
            desc2: '99',
            desc3: '包邮'
        },
        '73': {
            desc1: '夏季新款特价热卖'
        },
        '74': {
            desc1: '¥158.00'
        },
        '75': {
            desc1: '188',
            desc2: '包邮'
        },
        '76': {
            desc1: '夏季新款特价热卖'
        },
        '77': {
            desc1: '199'
        },
        '78': {
            desc1: '单品热卖顺丰包邮'
        },
        '79': {
            desc1: '199',
            desc2: '包邮'
        },
        '80': {
            desc1: '单品热卖顺丰包邮'
        },
        '81': {
            desc1: '单品热卖顺丰包邮'
        },
        '82': {
            desc1: 'HOT'
        },
        '83': {
            desc1: '188',
            desc2: '包邮'
        },
        '84': {
            desc1: '不一样的魅力'
        },
        '85': {
            desc1: '198',
            desc2: '包邮'
        },
        '86': {
            desc1: '夏季',
            desc2: '女装'
        },
        '87': {
            desc1: '198',
            desc2: '包邮'
        },
        '88': {
            desc1: '特价热卖'
        },
        '89': {
            desc1: '热卖单品'
        },
        '90': {
            desc1: '限时折扣',
            desc2: '¥199',
            desc3: '包邮'
        },
        '91': {
            desc1: '单卖热品',
            desc2: '888'
        },
        '92': {
            desc1: '299',
            desc2: '促销'
        },
        '93': {
            desc1: '限时折扣',
            desc2: '¥199.00'
        },
        '94': {
            desc1: '热卖单品',
            desc2: '欧美简约'
        },
        '95': {
            desc1: '聚划算',
            desc2: '¥199.00',
            desc3: '16日开团'
        },
        '96': {
            desc1: '我行我素',
            desc2: '纯棉修身'
        },
        '97': {
            desc1: '休闲T恤',
            desc2: '品牌价：189元',
            desc3: '品牌价：¥99'
        },
        '98': {
            desc1: '活动价',
            desc2: '¥199.00'
        },
        '99': {
            desc1: 'HOT IN SUMMER',
            desc2: '夏季热卖/2件包邮'
        },
        '100': {
            desc1: '夏季新款特价热卖'
        },
        '101': {
            desc1: '特价',
            desc2: '99',
            desc3: '包邮'
        },
        '102': {
            desc1: '聚划算',
            desc2: '￥99.00',
            desc3: '188.00'
        },
        '103': {
            desc1: '限时包邮'
        },
        '104': {
            desc1: '原价：299.00元',
            desc2: 'HOT',
            desc3: '￥199.00'
        },
        '105': {
            price1: '89元',
            desc1: '包邮'
        },
        '106': {
            desc1: '单品热卖 顺丰包邮'
        },
        '107': {
            desc1: '热卖单品',
            desc2: '欧美时尚'
        },
        '108': {
            desc1: '限时折扣',
            price1: '￥99.00'
        },
        '109': {
            desc1: '现价',
            price1: '￥99.00'
        },
        '110': {
            desc1: 'HOT IN SUMMER',
            desc2: '夏季热卖/两件包邮'
        },
        '111': {
            desc1: '我行我素 纯棉修身',
            price1: '89',
            desc2: '元',
            price2: '188.00'
        },
        '112': {
            desc1: '卡通T'
        },
        '113': {
            desc1: '双12必备'
        },
        '114': {
            price1: '￥69.00',
            price2: '￥199.00'
        },
        '115': {
            desc1: '￥138包邮'
        },
        '116': {
            desc1: '羊绒+羊毛',
            desc2: '限500件'
        },
        '117': {
            desc1: '年度盛典'
        },
        '118': {
            desc1: '年度盛典',
            desc2: '元',
            price1: '￥59.00'
        },
        '119': {
            desc1: '不一样的风格',
            price1: '￥69.00'
        },
        '120': {
            desc1: '预售',
            price1: '￥29.00元'
        },
        '121': {
            desc1: '年度盛典'
        },
        '122': {
            desc1: '精致美观',
            desc2: '经典时尚'
        },        
        '123': {
            desc1: '先买先优惠',
            price1: '￥88.00'
        },
        '124': {
            desc1: '好礼满就送，满就送'
        },
        '125': {
            desc1: '惊爆价',
            desc2: '元',
            price1: '99'
        },
        '126': {
            desc1: 'HOT'
        },
        '127': {           
            desc1: '单品热卖 顺丰包邮'
        },
        '128': {
            price1: '99',
            desc1: '元'
        },        
        '129': {           
            desc1: '抢'
        },
        '130': {           
            desc1: '好礼满就送',
            desc2: '元',
            price1: '99.00',
            price2: '180.00'
        },
        '131': {           
            desc1: '正品包邮'
        },
        '132': {
            desc1: '包邮',
            desc2: '元',
            price1: '79'
        },         
        '133': {
            desc1: '甜美女装',
            desc2: '舒适气质上档次',
            desc3: 'HOT'
        }, 
        '134': {           
            desc1: '年终大促 大甩卖',
            price1: '199.00'
        },
        '135': {           
            desc1: '元',
            desc2: '抢',
            price1: '89'
        },
        '136': {           
            desc1: '正品包邮',
            desc2: '年终大促',
            desc3: '3折',
            desc4: '销售'
        },        
        '137': {
            price1: '79',
            desc1: '元'
        },        
        '138': {
            desc1: '199',
            desc2: '元包邮',
            color1: '#ffffff',
            color2:'#0066ff'
        },
        '139': {
            desc1: '引领时尚',
            desc2: '奢华时尚',
            color1: '#0066ff'
        },
        '140': {
            desc1: '原价',
            desc2: '299.00',
            color1: '#2400ff',
            color2: '#ffffff'
        },
        '141': {
            desc1: '199',
            desc2: '元 包邮',
            color1: '#f9005b',
            color2: '#ffffff'
        },
        '142': {
            desc1: 'HOT',
            color1: '#f9005b',
            color2: '#ffffff'
        },
        '143': {
            desc1: '简约而不简单',
            color1: '#fcff00',
            color2: '#000000'
        },
        '144': {
            desc1: '热卖',
            desc2: '99',
            desc3: '元包邮',
            desc4: '199.00元',
            color1: '#fcff00',
            color2: '#000000',
            color3: '#0035ff',
            color4: '#ffffff'
        },
        '145': {
            desc1: '夏季新款 特价热卖',
            color1: '#ff0000'
        },
        '146': {
            desc1:'年末促销',
            desc2:'￥58.00',
            color1:'#ff0000',
            color2:'#ffffff',
            color3:'#fcff00',
            color4:'#000000'
        },
        '147': {
            desc1:'89',
            desc2:'元',
            desc3:'158.00',
            color1:'#fcff00',
            color2:'#000000'
        },
        '148': {
            desc1:'买！买！买！',
            color1:'#ff0000'
        },
        '149': {
            desc1:'89',
            desc2:'RMB',
            desc3:'299.00',
            color1:'#fff000',
            color2:'#ff0000',
            color3:'#000000',
            color4:'#ffffff'
        },
        '150': {
            desc1:'已售2000个',
            desc2:'最舒适 最新款',
            color1:'#fff000',
            color2:'#000000'
        },
        '151': {
            desc1:'HOT',
            color1:'#ff0000',
            color2:'#fff000'
        },
        '152': {
            desc1:'￥288包邮',
            color1:'#fff000'
        },
        '153': {
            desc1:'奢华精品',
            color1:'#000000',
            color2:'#fff000'
        },
        '154': {
            desc1:'好评3000+ 买!买!买!',
            color1:'#fff000',
            color2:'#000000'
        },
        '155': {
            desc1:'79',
            desc2:'元',
            color1:'#fff000',
            color2:'#fff600',
            color3:'#000000'
        },
        '156': {
            desc1:'热销千件 厂家直销',
            color1:'#ffdd00',
            color2:'#000000'
        },
        '157': {
            desc1:'￥79.00',
            desc2:'199.00元',
            color1:'#ff0000',
            color2:'#ffffff',
            color3:'#ffdd00',
            color4:'#000000'
        },
        '158': {
            desc1: '热销千件 厂家直销',
            desc2: '￥89.00',
            desc3: '260.00',
            color1: '#ffdd00',
            color2: '#000000',
            color3: '#ff0000'
        },
        '159': {
            desc1:'经典时尚 精致美观',
            color1:'#000000',
            color2:'#ffdd00'
        },
        '160': {
            desc1:'188',
            desc2:'元',
            desc3:'388.00',
            color1:'#fff000',
            color2:'#ffde00',
            color3:'#000000',
            color4:'#ffba00',
            color5:'#ff0000'
        },
        '161':{
            desc1:'热销千件 厂家直销',
            color1:'#ffffff',
            color2:'#ffff00'
        },
        '162':{
            desc1:'￥188.00',
            desc2:'388.00',
            color1:'#ffff00',
            color2:'#ff0000',
            color3:'#000000'
        },
        '163':{
            desc1:'经典精致',
            color1:'#ffffff',
            color2:'#ffff00'
        },
        '164':{
            desc1:'单品热卖     顺丰包邮',
            color1:'#ffffff',
            color2:'#000000'
        },
        '165': {
            desc1:'89',
            desc2:'元',
            desc3:'199.00',
            color1:'#ff0000',
            color2:'#000000',
            color3:'#ffff00'
        },
        '166': {
            desc1:'不起球纯棉修身保暖',
            desc2:'一条包邮',
            desc3:'满50减5元',
            color1:'#ff0000',
            color2:'#a40000',
            color3:'#ffffff'
        },
        '167': {
            desc1:'HOT',
            color1:'#ffffff',
            color2:'#ff0000'
        },
        '168': {
            desc1:'热卖单品',
            desc2:'欧美',
            desc3:'时尚',
            color1:'#ffffff',
            color2:'#ff0000',
            color3:'#000000'
        },
        '169': {
            desc1:'79',
            desc2:'元',
            desc3:'包邮',
            color1:'#ffffff',
            color2:'#ff0000'
        },
        '170': {
            desc1:'热卖单品',
            color1:'#ffffff',
            color2:'#00a2ff'
        },
        '171': {
            desc1:'FASHION',
            color1:'#ffffff',
            color2:'#000000'
        },
        '172': {
            desc1:'狂砍价',
            desc2:'￥89.00',
            desc3:'元',
            desc4:'299.00',
            color1:'#ffffff',
            color2:'#ff0078',
            color3:'#00a2ff',
            color4:'#000000'
        },
        '173': {
            desc1:'夏季新款 特价热卖',
            color1:'#ffffff',
            color2:'#000000'
        },
        '174': {
            desc1:'99',
            desc2:'元',
            desc3:'299.00',
            color1:'#ffff00',
            color2:'#ff0000',
            color3:'#000000'
        },
        '175': {
            desc1:'夏季新款 热销千件',
            desc2:'￥99.00',
            desc3:'299.00',
            color1:'#ffffff',
            color2:'#ff0000',
            color3:'#ffcc00',
            color4:'#000000'
        },
        '176': {
            price1: '99',
            desc1: '元',
            desc2: '全球狂欢价'
        },
        '177': {
            price1: '89',
            desc1: '元',
            desc2: '满99减5元',
            desc3: '全球狂欢价'
        },
        '178': {
            desc1: '抢',
            desc2: '全球狂欢价'
        },
        '179': {
            desc1: '￥89.00元'
        },
	'180': {
            desc1: '全球狂欢价',
            price1: '58',
            desc2: '元'
        },
        '181': {
            desc1: '全球狂欢价',
            color1: '#ff0000',
            color2: '#ffffff'
        },
        '182': {
            desc1: '98.00',
            desc2: '元',
            desc3: '299.00',
            color1: '#ff0000',
            color2: '#000000',
            color3: '#ffffff'
        },
        '183': {
            desc1: '￥98.00',
            desc2: '398.00',
            desc3: '正品包邮',
            color1: '#ff0000',
            color2: '#ffffff',
            color3: '#ffff00'
        },
        '184': {
            desc1: '全球狂欢价',
            color1: '#ff0000',
            color2: '#ffffff'
        },
        'c_1': {
            desc1: '引领时尚',
            desc2: '奢华时尚',
            color1: '#ff2400',
            color2: '#000000'
        },
        'c_2': {
            desc1: '夏季新款',
            desc2: '特价热卖',
            color1: '#000',
            color2: '#ff0000',
            fontsize1: 80,
            fontsize2: 70
        },
        'c_3': {
            desc1: '热卖单品欧美时尚',
            color1: '#ff7e00'
        },
        'c_4': {
            desc1: '引领时尚',
            desc2: '奢华时尚',
            color1: '#bb1d57',
            color2: '#000000'
        },
        'c_5': {
            desc1: '299.00',
            desc2: '199',
            desc3: '包邮',
            color1: '#42235f',
            color2: '#fff',
            color3: '#bb1d57',
            color4: "#fff"
        },
        'c_6': {
            desc1: '单品热卖',
            desc2: '顺丰包邮',
            color1: '#000',
            color2: '#000',
            fontsize1: 50,
            fontsize2: 50
        },
        'c_7': {
            desc1: '热卖单品欧美时尚',
            color1: '#fff'
        }
    }

    return templates;
});