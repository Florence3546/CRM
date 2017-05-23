-- ﻿【SQL语句示例】：
-- 删除字段（多个）：
ALTER TABLE gather_GatherTask DROP COLUMN sync1_time, DROP COLUMN sync2_time;
-- 修改字段：
ALTER TABLE auto_swap MODIFY COLUMN period SMALLINT(6) NOT NULL DEFAULT 1;
-- 添加字段：
ALTER TABLE auto_swap ADD COLUMN stat_period SMALLINT(6) NOT NULL DEFAULT 1 AFTER condition2;
-- 重命名字段：
ALTER TABLE auto_swap CHANGE stat_period stat_periods Integer;
-- 一条语句同时修改、添加字段：
ALTER TABLE auto_swap MODIFY COLUMN period SMALLINT(6) NOT NULL DEFAULT 1,
ADD COLUMN condition2 VARCHAR(100) AFTER modified_time,
ADD COLUMN stat_period SMALLINT(6) NOT NULL AFTER condition2;

-- 【修改记录，时间最近放在最前】：
--==========================================================================

--2017-05-17 ncrm_subscribe 表添加字段 pre_sales_advice_id 售前咨询id，关联ncrm_presalesadvice表，conversion_time 售前咨询转化时间
ALTER TABLE `ncrm_subscribe`
ADD COLUMN `pre_sales_advice_id`  int(11) NULL AFTER `consult_xfgroup_id`,
ADD COLUMN `conversion_time`  datetime NULL AFTER `pre_sales_advice_id`;

--2017-05-16 ncrm_presalesadvice 表添加字段 business 咨询业务
ALTER TABLE `ncrm_presalesadvice` ADD COLUMN `business`  varchar(50) NULL AFTER `note`;


--2017-05-12 ncrm_subscribe 表添加字段 has_contract 是否有合同,chat_file_path 聊天文件路径
ALTER TABLE ncrm_subscribe ADD COLUMN has_contract INT(11) NOT NULL DEFAULT 0 AFTER approval_status;
ALTER TABLE ncrm_subscribe ADD COLUMN chat_file_path VARCHAR(500) AFTER has_contract;

--2017-5-11 ncrm_customer 表添加字段 is_goldmember
ALTER TABLE ncrm_customer ADD COLUMN is_goldmember INT(1) NOT NULL DEFAULT 0 AFTER consult_id;

--2016-12-21 ncrm_customer 表添加字段 temp_flag
ALTER TABLE ncrm_customer ADD COLUMN temp_flag INT(11) NOT NULL DEFAULT 0 AFTER consult_id;


--2016-07-25 ncrm_subscribe 表添加字段 refund_fee
ALTER TABLE ncrm_subscribe ADD COLUMN refund_fee INT(11) NOT NULL DEFAULT 0 AFTER fee;


--2016-07-11 添加 ncrm_activitycode 表
CREATE TABLE `ncrm_activitycode` (
  `activity_code` varchar(50) NOT NULL,
  `name_cn` varchar(30) DEFAULT NULL,
  `creater_id` int(11) DEFAULT NULL,
  `create_time` datetime(6) NOT NULL,
  PRIMARY KEY (`activity_code`),
  KEY `ncrm_activitycode_creater_id_fk_ncrm_psuser_id` (`creater_id`),
  CONSTRAINT `ncrm_activitycode_creater_id_fk_ncrm_psuser_id` FOREIGN KEY (`creater_id`) REFERENCES `ncrm_psuser` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


--2016-05-27 ncrm_xiaofugroup 表中添加 开始生效时间 字段
alter table ncrm_xiaofugroup
add column start_time datetime default '2016-03-01',
add column end_time datetime;


--2016-05-11 添加 ncrm_xiaofugroup 表

CREATE TABLE ncrm_xiaofugroup (
  id int(11) NOT NULL auto_increment primary key,
  department varchar(50) NOT NULL,
  consult_id int(11) NOT NULL,
  seller_id int(11) NOT NULL,
  is_active tinyint(1) NOT NULL,
  create_time datetime NOT NULL,
  freeze_time datetime NULL,
  name varchar(30),
  CONSTRAINT xfg_consult_fk_psuser_id FOREIGN KEY (consult_id) REFERENCES ncrm_psuser (id),
  CONSTRAINT xfg_seller_fk_psuser_id FOREIGN KEY (seller_id) REFERENCES ncrm_psuser (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `ncrm_xfgroupperformance` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `xfgroup_id` int(11) NOT NULL,
  `identify` varchar(50) NOT NULL DEFAULT '',
  `data_json` longtext NOT NULL,
  `result_date` date NOT NULL,
  `create_time` datetime NOT NULL,
  `modify_time` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `xfgroup_id` (`xfgroup_id`,`identify`,`result_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

ALTER TABLE ncrm_subscribe
ADD COLUMN xfgroup_id INT(11) null default null,
ADD COLUMN consult_xfgroup_id INT(11) null default null,
ADD CONSTRAINT subscribe_xfgid_fk_xfgid FOREIGN KEY (xfgroup_id) REFERENCES ncrm_xiaofugroup (id),
ADD CONSTRAINT subscribe_consult_xfgid_fk_xfgid FOREIGN KEY (consult_xfgroup_id) REFERENCES ncrm_xiaofugroup (id);


--2016-04-18 ncrm_customer 表中添加 字段 cat_id           暂不修改 by zhongchao
--alter table ncrm_customer add column cat_id int(11);

--2016-03-24 ncrm_customer 表中添加 字段 current_highest_version
alter table ncrm_customer add column current_highest_version VARCHAR(20)

--2016-03-24 ncrm_xfgroup 表中添加 字段 seller_id。 为了平稳过渡，先加字段，过段时间再删除 saler_id
alter table ncrm_xfgroup add column seller_id int(11) not null, add foreign key (seller_id) references ncrm_psuser (id)

--2016-03-22 添加 ncrm_xfgroup 表
CREATE TABLE `ncrm_xfgroup` (
  `consult_id` int(11) NOT NULL,
  `saler_id` int(11) NOT NULL,
  PRIMARY KEY (`consult_id`),
  KEY `ncrm_xfgroup_saler_id_53636f66_fk_ncrm_psuser_id` (`saler_id`),
  CONSTRAINT `ncrm_xfgroup_consult_id_3489f3c9_fk_ncrm_psuser_id` FOREIGN KEY (`consult_id`) REFERENCES `ncrm_psuser` (`id`),
  CONSTRAINT `ncrm_xfgroup_saler_id_53636f66_fk_ncrm_psuser_id` FOREIGN KEY (`saler_id`) REFERENCES `ncrm_psuser` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--2016-03-22 添加新表 ncrm_contractfile
create table if not exists ncrm_contractfile (
    id int(11) not null auto_increment primary key,
    create_time datetime,
    modify_time datetime,
    file_data mediumblob,
    file_name varchar(30),
    subscribe_id int(11)
)

--2016-03-04 ncrm_subscribe表添加字段 审计人、审计时间、审计状态
ALTER TABLE ncrm_subscribe
ADD COLUMN approver_id INT(11),
ADD COLUMN approval_time DATETIME,
ADD COLUMN approval_status INT(11),
ADD FOREIGN KEY (approver_id) REFERENCES ncrm_psuser (id);

--2016-02-23 ncrm_subscribe表添加字段xf_flag, pay_type, pay_type_no;ncrm_clientgroup表添加字段group_type
ALTER TABLE ncrm_subscribe
ADD COLUMN xf_flag INT(11),
ADD COLUMN pay_type INT(11),
ADD COLUMN pay_type_no VARCHAR(80);
ALTER TABLE ncrm_clientgroup ADD COLUMN group_type INT(11);

--2015-12-29 初始化评论同步的config配置
INSERT INTO `common_config` VALUES (19001,'web.SYNC_WEB_COMMENT','','2015-12-29','','','同步开车精灵好评异常时间');
INSERT INTO `common_config` VALUES (19002,'web.SYNC_QN_COMMENT','','2015-12-29','','','同步千牛好评异常时间');


--2015-12-29 修改评论表，添加id，gmt_create索引
alter table web_appcomment
ADD INDEX (id),
ADD INDEX (is_recommend),
ADD INDEX (user_nick),
ADD INDEX (gmt_create);

--2015-12-29 删除旧版好评表 web_appraise
drop table web_appraise;

--==========================================================================
--2015-12-01 修改推广链接表(web_salelink)，删除ad_id字段,添加link_name字段
alter table web_salelink
add column link_name varchar(200) null default null,
drop column ad_id;



--==========================================================================
--2015-11-23 修改ncrm_customer表结构
alter table ncrm_customer
add column zip_code varchar(10) null default null,
add column receiver varchar(30) null default null,
add column receive_address varchar(100) null default null;

--==========================================================================
--2015-11-19 修改web_feedback表结构
ALTER TABLE web_feedback
ADD COLUMN shop_id INT(11),
ADD COLUMN consult_id INT(11),
ADD COLUMN note varchar(500),
ADD COLUMN handle_status TINYINT(1);
update web_feedback wf left join router_user ru on wf.user_id=ru.id set wf.shop_id=ru.shop_id;
update web_feedback wf left join ncrm_customer nc on wf.shop_id=nc.shop_id set wf.consult_id=nc.consult_id;
update web_feedback set handle_status=1 where handle_status is null;


--==========================================================================
--2015-10-07 修改User表数据，加入一个选择主题的字段|添加用户是否开启短信提醒字段
ALTER TABLE router_user ADD COLUMN theme varchar(20) DEFAULT 'orange' AFTER subs_msg;
ALTER TABLE ncrm_customer ADD COLUMN remind SMALLINT(6) DEFAULT 0 AFTER address;

--==========================================================================
--2015-09-14 修改ncrm_customer表，添加通用客户群和快搜相关的字段和相关索引
ALTER TABLE ncrm_customer
ADD COLUMN latest_category VARCHAR(20),
ADD COLUMN latest_end DATE,
ADD COLUMN is_pausing TINYINT(1),
ADD COLUMN advertise_effect TINYINT(1),
ADD COLUMN contact_fail TINYINT(1),
ADD COLUMN bad_comment TINYINT(1),
ADD COLUMN is_pawn TINYINT(1),
ADD COLUMN unknown_subscribe TINYINT(1),
ADD COLUMN contact_count TINYINT(1),
ADD COLUMN latest_contact DATE,
ADD COLUMN latest_operate DATE,
ADD COLUMN rjjh_unmnt DATE,
ADD COLUMN rjjh_frozen TINYINT(1),
ADD COLUMN is_discontent TINYINT(1),
ADD COLUMN is_potential TINYINT(1),
ADD INDEX (latest_category),
ADD INDEX (latest_end),
ADD INDEX (is_pausing),
ADD INDEX (advertise_effect),
ADD INDEX (contact_fail),
ADD INDEX (bad_comment),
ADD INDEX (is_pawn),
ADD INDEX (unknown_subscribe),
ADD INDEX (contact_count),
ADD INDEX (latest_contact),
ADD INDEX (latest_operate),
ADD INDEX (rjjh_unmnt),
ADD INDEX (rjjh_frozen),
ADD INDEX (is_discontent),
ADD INDEX (is_potential);

--==========================================================================
--2015-09-14 修改ncrm_psuser表数据，给市场人员和研发人员添加首页广告管理模块权限
UPDATE ncrm_psuser SET perms=concat(perms,'F') where position in ('MKT','DEV');

--==========================================================================
--2015-09-08 修改ncrm_customer表，添加creator_id, saler_id, operater_id, consult_id字段
ALTER TABLE ncrm_customer
ADD COLUMN creator_id INT(11),
ADD COLUMN saler_id INT(11),
ADD COLUMN operater_id INT(11),
ADD COLUMN consult_id INT(11),
ADD FOREIGN KEY (creator_id) REFERENCES ncrm_psuser (id),
ADD FOREIGN KEY (saler_id) REFERENCES ncrm_psuser (id),
ADD FOREIGN KEY (operater_id) REFERENCES ncrm_psuser (id),
ADD FOREIGN KEY (consult_id) REFERENCES ncrm_psuser (id);

--==========================================================================
--2015-07-22 修改ncrm_subscribe数据，同步router_articlebizorder表中的fee字段
update ncrm_subscribe ns set ns.fee = (select ra.fee from router_articlebizorder ra where ra.order_id = ns.order_id);

--==========================================================================
--2015-07-21 ncrm_subscribe，添加‘fee(原价)’字段
ALTER TABLE ncrm_subscribe ADD COLUMN fee int AFTER item_name;

--==========================================================================
--2015-07-21 修改ncrm_clientgroup表，添加‘note(备注)’字段
ALTER TABLE ncrm_clientgroup ADD COLUMN note varchar(200) AFTER checked;

--==========================================================================
--2015-07-20 修改ncrm_customer表，将phone为‘--’的修改为null
UPDATE ncrm_customer SET phone=null where phone='--' or phone='None';

--==========================================================================
--2015-07-10 给高管、指战员及研发人员添加工作台导出权限
UPDATE ncrm_psuser SET perms=concat(perms,'E') where position in ('SMANAGER','DEV','COMMANDER');

-- =========================================================================
-- 2015-06-23 在ncrm_psuser中添加字段 probation_date
ALTER TABLE ncrm_psuser ADD COLUMN probation_date date AFTER note;

-- 2015-06-23 在ncrm_subscribe中添加字段 consult_id, category
ALTER TABLE ncrm_subscribe
ADD COLUMN consult_id int AFTER operater_id,
ADD COLUMN category varchar(50) AFTER order_id;

-- 2015-06-23 校正订单对应的客服和操作人以及类别数据
UPDATE ncrm_subscribe SET category='qn', article_code='FW_GOODS-1921400' WHERE item_code in ('FW_GOODS-1921400-1', 'FW_GOODS-1921400-v2', 'FW_GOODS-1921400-v3');
UPDATE ncrm_subscribe SET category='kcjl' WHERE article_code='ts-25811';
UPDATE ncrm_subscribe SET category='vip' WHERE item_code='ts-25811-v9' and start_date>='2014-09-16';

UPDATE ncrm_subscribe ns1 join ncrm_subscribe ns2 on ns1.order_id=ns2.order_id and ns2.article_code='ts-25811' and ns2.item_code='ts-25811-6'
SET ns1.article_code='ts-25811', ns1.consult_id=ns2.operater_id, ns1.category='rjjh'
WHERE ns1.article_code='ts-25811-6' and ns1.item_code='ts-25811-6';
DELETE FROM ncrm_subscribe WHERE pay=0 and (item_code='ts-25811-6' or order_id=0);
UPDATE ncrm_subscribe SET article_code='ts-25811', item_code='ts-25811-6', category='rjjh' WHERE article_code='ts-25811-6' or item_code='ts-25811-6';

UPDATE ncrm_subscribe SET category='ztc', item_code=article_code WHERE article_code='tp-001';
UPDATE ncrm_subscribe SET category='zz', item_code=article_code WHERE article_code='tp-002';
UPDATE ncrm_subscribe SET category='zx', item_code=article_code WHERE article_code='tp-003';
UPDATE ncrm_subscribe SET category='dyy', item_code=article_code WHERE article_code='tp-004';
UPDATE ncrm_subscribe SET category='other', item_code=article_code WHERE article_code='tp-005';
UPDATE ncrm_subscribe SET category='other' WHERE category is null;
UPDATE ncrm_subscribe ns join ncrm_psuser np on ns.operater_id=np.id
SET ns.consult_id=ns.operater_id, ns.operater_id=null
WHERE np.position in ('CONSULT', 'CONSULTLEADER');


-- =========================================================================
-- 2015-05-25 修改ncrm_psuser的字段名称, type -> position, consult_type -> department
ALTER TABLE ncrm_psuser
CHANGE type position varchar(40),
CHANGE consult_type department varchar(50),
CHANGE create_time entry_date datetime,
ADD COLUMN contract_start date,
ADD COLUMN contract_end date,
ADD COLUMN birthday date,
ADD COLUMN id_no varchar(20),
ADD COLUMN residence varchar(100),
ADD COLUMN education varchar(100),
ADD COLUMN school varchar(50),
ADD COLUMN major varchar(50),
ADD COLUMN gender varchar(10),
ADD COLUMN status varchar(10),
ADD COLUMN tel varchar(20) AFTER phone;
ALTER TABLE ncrm_psuser MODIFY COLUMN entry_date date;
-- 2015-05-25 修改ncrm_psuser表的权限相关的数据内容, type -> position, consult_type -> department
UPDATE ncrm_psuser SET status='转正', perms='0';
UPDATE ncrm_psuser SET status='离职', position=null, department=null, perms='' where position='OUTER';
UPDATE ncrm_psuser SET position='DEV', department='DEV', perms='012aABC' where position='DEVER';
UPDATE ncrm_psuser SET position='MKT', department='MKT', perms='0a' where position='MARKET';
UPDATE ncrm_psuser SET position='PRESELLER', department='MKT' where position='PRESELLER';
UPDATE ncrm_psuser SET position='QC', department='QC', perms='01B' where position='TPMNG';
UPDATE ncrm_psuser SET department='GROUP1' where position in ('CONSULT','SELLER','TPSALES','PHONESELLER','TPAE','TPAM','RJJH') and manager like '%汪金%';
UPDATE ncrm_psuser SET department='GROUP2' where position in ('CONSULT','SELLER','TPSALES','PHONESELLER','TPAE','TPAM','RJJH') and manager like '%吴杰%';
UPDATE ncrm_psuser SET department='GROUP3' where position in ('CONSULT','SELLER','TPSALES','PHONESELLER','TPAE','TPAM','RJJH') and manager like '%邱梦雪%';
UPDATE ncrm_psuser SET department='GROUP4' where position in ('CONSULT','SELLER','TPSALES','PHONESELLER','TPAE','TPAM','RJJH') and manager like '%雷燕%';
UPDATE ncrm_psuser SET position='OPTAGENT', department='OPTAGENT' where manager like '%吕蒙%';
UPDATE ncrm_psuser SET position='SELLER' where position='PHONESELLER';
UPDATE ncrm_psuser SET position='SELLER' where position='TPSALES';
UPDATE ncrm_psuser SET position='DESIGNER', department='DESIGN' where position in ('DESCONSULT','DESIGNER');
UPDATE ncrm_psuser SET position='HR', department='HR', perms='0C' where position='OTHER';
UPDATE ncrm_psuser SET position='COMMANDER', department='GROUP1', perms='01' where name_cn='汪金';
UPDATE ncrm_psuser SET position='SALELEADER', department='GROUP1', perms='01' where name_cn='田傲';
UPDATE ncrm_psuser SET position='TPLEADER', department='GROUP1', perms='01' where name_cn='罗沙沙';
UPDATE ncrm_psuser SET position='CONSULTLEADER', department='GROUP1', perms='01' where name_cn='汪锋';
UPDATE ncrm_psuser SET position='RJJHLEADER', department='GROUP1', perms='01' where name_cn='王美云';
UPDATE ncrm_psuser SET position='COMMANDER', department='GROUP2', perms='01' where name_cn='吴杰';
UPDATE ncrm_psuser SET position='SALELEADER', department='GROUP2', perms='01' where name_cn='张志威';
UPDATE ncrm_psuser SET position='TPLEADER', department='GROUP2', perms='01' where name_cn='董翠';
UPDATE ncrm_psuser SET position='CONSULTLEADER', department='GROUP2', perms='01' where name_cn='李文杰';
UPDATE ncrm_psuser SET position='RJJHLEADER', department='GROUP2', perms='01' where name_cn='唐婷';
UPDATE ncrm_psuser SET position='COMMANDER', department='GROUP3', perms='01' where name_cn='邱梦雪';
UPDATE ncrm_psuser SET position='SALELEADER', department='GROUP3', perms='01' where name_cn='聂路宁';
UPDATE ncrm_psuser SET position='TPLEADER', department='GROUP3', perms='01' where name_cn='朱静';
UPDATE ncrm_psuser SET position='CONSULTLEADER', department='GROUP3', perms='01' where name_cn='杨勇';
UPDATE ncrm_psuser SET position='RJJHLEADER', department='GROUP3', perms='01' where name_cn='吴传奇';
UPDATE ncrm_psuser SET position='COMMANDER', department='GROUP4', perms='01' where name_cn='雷燕';
UPDATE ncrm_psuser SET position='SALELEADER', department='GROUP4', perms='01' where name_cn='邱梦婷';
UPDATE ncrm_psuser SET position='TPLEADER', department='GROUP4', perms='01' where name_cn='陈静';
UPDATE ncrm_psuser SET position='CONSULTLEADER', department='GROUP4', perms='01' where name_cn='熊钰馨';
UPDATE ncrm_psuser SET position='RJJHLEADER', department='GROUP4', perms='01' where name_cn='葛霁峰';
UPDATE ncrm_psuser SET position='COMMANDER', perms='01' where name_cn in ('吕蒙', '刘伟', '刘财延');
UPDATE ncrm_psuser SET position='COMMANDER', perms='01aA' where name_cn='吴洋';
UPDATE ncrm_psuser SET position='SMANAGER', department='HR', perms='012aABC' where name_cn in ('何浩', '张瑜', '王凯', '李朝晖');

-- =========================================================================
-- 2015-05-08 将common_config表中的字段value的长度增加到3000
alter table common_config modify column `value` varchar(3000)

-- =========================================================================
-- 2015-05-07 在auth_user表中添加 f7 字段，来记录每天用户使用选词预览的次数，以做限制
ALTER TABLE auth_user ADD COLUMN f7 int DEFAULT 0;

-- =========================================================================
-- 2015-04-24 将全自动的基础权限码修改为S，注意，发布前一定要执行该SQL，否则正常用户可能会有问题
update auth_user set f3 = concat(f3, 'S') where id != 1 and f3 != '';
update router_articleitem set perms_code = concat(perms_code, "S");

-- =========================================================================
-- 2015-04-16 在事件相关表格里添加字段visible
ALTER TABLE ncrm_contact ADD COLUMN visible int DEFAULT 0 AFTER note;
ALTER TABLE ncrm_operate ADD COLUMN visible int DEFAULT 0 AFTER note;
ALTER TABLE ncrm_comment ADD COLUMN visible int DEFAULT 0 AFTER note;
ALTER TABLE ncrm_subscribe ADD COLUMN visible int DEFAULT 0 AFTER note;
ALTER TABLE ncrm_reintro ADD COLUMN visible int DEFAULT 0 AFTER note;
ALTER TABLE ncrm_unsubscribe ADD COLUMN visible int DEFAULT 0 AFTER note;
-- =========================================================================

--=========================================================================
-- 2015-04-17 积分活动的数据
TRUNCATE TABLE router_upgradeconf;
INSERT INTO `router_upgradeconf` VALUES (5,'upgrade','ts-25811-1',899,879,'12','续订','http://tb.cn/WWjFtBy');
INSERT INTO `router_upgradeconf` VALUES (6,'upgrade','ts-25811-1',499,479,'6','续订','http://tb.cn/A5hFtBy');
INSERT INTO `router_upgradeconf` VALUES (7,'upgrade','ts-25811-1',429,409,'3','续订','http://tb.cn/qTuFtBy');
INSERT INTO `router_upgradeconf` VALUES (9,'upgrade','ts-25811-8',699,679,'12','续订','http://tb.cn/OnJFtBy');
INSERT INTO `router_upgradeconf` VALUES (10,'upgrade','ts-25811-8',399,379,'6','续订','http://tb.cn/U2PFtBy');
INSERT INTO `router_upgradeconf` VALUES (11,'upgrade','ts-25811-8',329,309,'3','续订','http://tb.cn/zNYFtBy');
INSERT INTO `router_upgradeconf` VALUES (13,'upgrade','FW_GOODS-1921400-v3',600,600,'12','升级','http://tb.cn/sJmvhZy');
INSERT INTO `router_upgradeconf` VALUES (14,'upgrade','FW_GOODS-1921400-v3',300,300,'6','升级','http://tb.cn/s5nvhZy');
INSERT INTO `router_upgradeconf` VALUES (15,'upgrade','FW_GOODS-1921400-v3',150,150,'3','升级','http://tb.cn/LalvhZy');
INSERT INTO `router_upgradeconf` VALUES (16,'upgrade','FW_GOODS-1921400-v3',50,50,'1','升级','http://tb.cn/7jqvhZy');
INSERT INTO `router_upgradeconf` VALUES (17,'upgrade','ts-25811-v9',6000,6000,'3','续订','http://tb.cn/i04BtBy');
INSERT INTO `router_upgradeconf` VALUES (18,'upgrade','ts-25811-6',2599,2599,'6','续订','http://tb.cn/zkf9tBy');
INSERT INTO `router_upgradeconf` VALUES (20,'upgrade','ts-25811-6',1399,1399,'3','续订','http://tb.cn/zYl9tBy');
INSERT INTO `router_upgradeconf` VALUES (21,'upgrade','ts-25811-6',4999,4999,'12','续订','http://tb.cn/UiX9tBy');
INSERT INTO `router_upgradeconf` VALUES (22,'upgrade','ts-25811-6',499,499,'1','续订','http://tb.cn/EH1AtBy');
TRUNCATE TABLE `router_discount`;
INSERT INTO `router_discount` VALUES (2,'ts-25811-8','3',329,20000,'{\"param\":{\"aCode\":\"ACT_836440495_150414143815\",\"itemList\":[\"ts-25811-1:3*2\"],\"promIds\":[1000212977],\"type\":1},\"sign\":\"3851F1C7303795CF9D32422C45F8A6E1\"}');
INSERT INTO `router_discount` VALUES (4,'ts-25811-8','6',399,20000,'{\"param\":{\"aCode\":\"ACT_836440495_150414143815\",\"itemList\":[\"ts-25811-1:6*2\"],\"promIds\":[1000212977],\"type\":1},\"sign\":\"1D9CBEF2ADF734B621E7CE28718FCF4A\"}');
INSERT INTO `router_discount` VALUES (5,'ts-25811-8','12',699,20000,'{\"param\":{\"aCode\":\"ACT_836440495_150414143815\",\"itemList\":[\"ts-25811-1:12*2\"],\"promIds\":[1000212977],\"type\":1},\"sign\":\"3F65E5FB89C44CF4EF4DE2EA02B3A05B\"}');
INSERT INTO `router_discount` VALUES (6,'ts-25811-8','3',329,15000,'{\"param\":{\"aCode\":\"ACT_836440495_150414143636\",\"itemList\":[\"ts-25811-8:3*2\"],\"promIds\":[1000213088],\"type\":1},\"sign\":\"E7E80F2BA54655884711C09DDF66E85D\"}');
INSERT INTO `router_discount` VALUES (7,'ts-25811-8','6',399,15000,'{\"param\":{\"aCode\":\"ACT_836440495_150414143636\",\"itemList\":[\"ts-25811-1:6*2\"],\"promIds\":[1000213086],\"type\":1},\"sign\":\"58BC171A5225629B0D0135150E1F05E0\"}');
INSERT INTO `router_discount` VALUES (9,'ts-25811-8','12',699,15000,'{\"param\":{\"aCode\":\"ACT_836440495_150414143636\",\"itemList\":[\"ts-25811-8:12*2\"],\"promIds\":[1000213088],\"type\":1},\"sign\":\"7C956A4263666A0351C9283E58A0374F\"}');
INSERT INTO `router_discount` VALUES (13,'ts-25811-8','3',329,10000,'{\"param\":{\"aCode\":\"ACT_836440495_140321153544\",\"itemList\":[\"ts-25811-8:12*2\"],\"promIds\":[10263248],\"type\":1},\"sign\":\"3D9FF41BCD657EA91E2E3DBCE9F96577\"}');
INSERT INTO `router_discount` VALUES (14,'ts-25811-8','6',399,10000,'{\"param\":{\"aCode\":\"ACT_836440495_150414143538\",\"itemList\":[\"ts-25811-8:3*2\"],\"promIds\":[1000212864],\"type\":1},\"sign\":\"8D2E851BE460ED4C78C17109B7A7B66C\"}');
INSERT INTO `router_discount` VALUES (15,'ts-25811-8','12',699,10000,'{\"param\":{\"aCode\":\"ACT_836440495_150414143538\",\"itemList\":[\"ts-25811-8:6*2\"],\"promIds\":[1000212864],\"type\":1},\"sign\":\"CD345ADAE980B29CAC0C439D2F3FE6B5\"}');
INSERT INTO `router_discount` VALUES (16,'ts-25811-8','6',399,5000,'{\"param\":{\"aCode\":\"ACT_836440495_150414143223\",\"itemList\":[\"ts-25811-8:6*2\"],\"promIds\":[1000213445],\"type\":1},\"sign\":\"FAB64840C1B2F14664BB4A71DEC58DC7\"}');
INSERT INTO `router_discount` VALUES (17,'ts-25811-8','12',699,5000,'{\"param\":{\"aCode\":\"ACT_836440495_150414143223\",\"itemList\":[\"ts-25811-8:12*2\"],\"promIds\":[1000213445],\"type\":1},\"sign\":\"B7DB9B35D87F365D00A680CF3F03489C\"}');
INSERT INTO `router_discount` VALUES (19,'ts-25811-1','3',429,20000,'{\"param\":{\"aCode\":\"ACT_836440495_150414143815\",\"itemList\":[\"ts-25811-1:3*2\"],\"promIds\":[1000212977],\"type\":1},\"sign\":\"3851F1C7303795CF9D32422C45F8A6E1\"}');
INSERT INTO `router_discount` VALUES (20,'ts-25811-1','6',499,20000,'{\"param\":{\"aCode\":\"ACT_836440495_150414143815\",\"itemList\":[\"ts-25811-1:6*2\"],\"promIds\":[1000212977],\"type\":1},\"sign\":\"1D9CBEF2ADF734B621E7CE28718FCF4A\"}');
INSERT INTO `router_discount` VALUES (21,'ts-25811-1','12',899,20000,'{\"param\":{\"aCode\":\"ACT_836440495_150414143815\",\"itemList\":[\"ts-25811-1:12*2\"],\"promIds\":[1000212977],\"type\":1},\"sign\":\"3F65E5FB89C44CF4EF4DE2EA02B3A05B\"}');
INSERT INTO `router_discount` VALUES (22,'ts-25811-1','3',429,15000,'{\"param\":{\"aCode\":\"ACT_836440495_150414143636\",\"itemList\":[\"ts-25811-1:3*2\"],\"promIds\":[1000213086],\"type\":1},\"sign\":\"E473B4CB3C38A8E4A0902F222376D0AC\"}');
INSERT INTO `router_discount` VALUES (23,'ts-25811-1','6',499,15000,'{\"param\":{\"aCode\":\"ACT_836440495_150414143636\",\"itemList\":[\"ts-25811-1:6*2\"],\"promIds\":[1000213086],\"type\":1},\"sign\":\"58BC171A5225629B0D0135150E1F05E0\"}');
INSERT INTO `router_discount` VALUES (24,'ts-25811-1','12',899,15000,'{\"param\":{\"aCode\":\"ACT_836440495_150414143636\",\"itemList\":[\"ts-25811-1:12*2\"],\"promIds\":[1000213086],\"type\":1},\"sign\":\"E57389DE039BF4BF8C7CB3E4BE4EB676\"}');
INSERT INTO `router_discount` VALUES (25,'ts-25811-1','3',429,10000,'{\"param\":{\"aCode\":\"ACT_836440495_150414143538\",\"itemList\":[\"ts-25811-1:3*2\"],\"promIds\":[1000212862],\"type\":1},\"sign\":\"698913A31A3D91E200F087A02E242683\"}');
INSERT INTO `router_discount` VALUES (28,'ts-25811-1','6',499,10000,'{\"param\":{\"aCode\":\"ACT_836440495_150414143538\",\"itemList\":[\"ts-25811-1:6*2\"],\"promIds\":[1000212862],\"type\":1},\"sign\":\"C4C6530600093C8CCD3B2F007F95BA2D\"}');
INSERT INTO `router_discount` VALUES (29,'ts-25811-1','12',899,10000,'{\"param\":{\"aCode\":\"ACT_836440495_150414143538\",\"itemList\":[\"ts-25811-1:12*2\"],\"promIds\":[1000212862],\"type\":1},\"sign\":\"F1B2645BCA085A1F05636AB485D4FE0B\"}');
INSERT INTO `router_discount` VALUES (30,'ts-25811-1','3',429,5000,'{\"param\":{\"aCode\":\"ACT_836440495_150414143223\",\"itemList\":[\"ts-25811-1:3*2\"],\"promIds\":[1000213443],\"type\":1},\"sign\":\"142D772D838A3027EBE4A5350EBD188C\"}');
INSERT INTO `router_discount` VALUES (31,'ts-25811-1','6',499,5000,'{\"param\":{\"aCode\":\"ACT_836440495_150414143223\",\"itemList\":[\"ts-25811-1:6*2\"],\"promIds\":[1000213443],\"type\":1},\"sign\":\"0837AD32BCF16578DA85EE573075E265\"}');
INSERT INTO `router_discount` VALUES (32,'ts-25811-1','12',899,5000,'{\"param\":{\"aCode\":\"ACT_836440495_150414143223\",\"itemList\":[\"ts-25811-1:12*2\"],\"promIds\":[1000213443],\"type\":1},\"sign\":\"1E0FECB43756B7D618BC34FF9BB6098B\"}');
INSERT INTO `router_discount` VALUES (36,'ts-25811-8','3',329,5000,'{\"param\":{\"aCode\":\"ACT_836440495_150414143223\",\"itemList\":[\"ts-25811-8:3*2\"],\"promIds\":[1000213445],\"type\":1},\"sign\":\"0DF84C9F2567C8EB8C03E97E587E65A1\"}');
--=========================================================================
-- 2015-01-13 ncrm_comment 添加字段 comment_type,top_comment_time，modify_comment_time
ALTER TABLE ncrm_comment ADD COLUMN comment_type int AFTER comment_score,
ADD COLUMN top_comment_times int AFTER comment_type,
ADD COLUMN modify_comment_time datetime AFTER top_comment_times;
update ncrm_comment set comment_type=200 where comment_score<=4;
update ncrm_comment set comment_type=110 where comment_score=5;
update ncrm_comment set note=comment_detail;
update ncrm_comment set comment_detail='';
ALTER TABLE ncrm_comment MODIFY COLUMN comment_score int NULL;
--=========================================================================
-- 2014-08-19 router_lotteryinfo 添加字段 last_show_time
ALTER TABLE router_lotteryinfo ADD COLUMN last_show_time DATETIME DEFAULT NULL
--=========================================================================
-- 2014-07-28 管控表的一些字段添加与删除（请先router上的mysql备份数据库再操作）
update crm_customer c,crm_appraisal a set c.phone=a.phone where a.customer_id=c.id and c.phone='';
update crm_customer c,crm_appraisal a set c.qq=a.qq where a.customer_id=c.id and c.qq='';
update crm_customer c,crm_appraisal a set c.ww=a.wangwang where a.customer_id=c.id and c.ww='';

update crm_customer c,crm_navy n set c.phone=n.phone where n.customer_id=c.id and c.phone='';
update crm_customer c,crm_navy n set c.qq=n.qq where n.customer_id=c.id and c.qq='';
update crm_customer c,crm_navy n set c.ww=n.wangwang where n.customer_id=c.id and c.ww='';

update crm_customer c,crm_referrals r set c.phone=r.phone where r.customer_id=c.id and c.phone='';
update crm_customer c,crm_referrals r set c.qq=r.qq where r.customer_id=c.id and c.qq='';
update crm_customer c,crm_referrals r set c.ww=r.wangwang where r.customer_id=c.id and c.ww='';


alter table crm_appraisal drop column is_good_appraisal,
                          drop column edited_score,
                          drop column is_refund,
                          drop column refund_fee,
                          drop column used_date,
                          drop column track_after_name,
                          drop column wangwang,
                          drop column qq,
                          drop column phone;

alter table crm_navy drop column qq,
                     drop column wangwang,
                     drop column phone;

alter table crm_referrals drop column qq,
                          drop column wangwang,
                          drop column phone;

alter table crm_refund drop column order_fee;

alter table crm_appraisal add column is_used smallint after edit_appraisal_time;
alter table crm_appraisal add column last_evaluate smallint after is_used;
--=========================================================================
-- 2014-06-23 crm_refund 表中去掉 order_time, order_cycle,last_time 添加 refund_type,cat_name
alter table crm_refund drop COLUMN order_time,drop COLUMN order_cycle,drop COLUMN last_time;
alter table crm_refund add COLUMN refund_type int after refund_time;
alter table crm_refund add COLUMN cat_name varchar(100) after refund_time;
update crm_customer set dangerous_status=6 where comment_status=7;

--=========================================================================
-- 2014-06-13 router_point 表中去掉 shop_id_1, shop_id_2, 添加 nick_1, nick_2
alter table router_point add column nick_1 varchar(30) after id, add column nick_2 varchar(30) after nick_1;
update router_point r set
    r.nick_1 = (select a1.username from auth_user a1 where a1.f2=r.shop_id_1),
    r.nick_2 = (select a2.username from auth_user a2 where a2.f2=r.shop_id_2);
alter table router_point drop column shop_id_1, drop column shop_id_2;

--=========================================================================
-- 2014-06-09 router_upgradeconf表添加续订数据
INSERT INTO `router_upgradeconf` VALUES (1,'mnt','ts-25811-1',999,929,'12','升级','http://tb.cn/VmWjUby');
INSERT INTO `router_upgradeconf` VALUES (2,'mnt','ts-25811-1',599,549,'6','升级','http://tb.cn/X6KYBdy');
INSERT INTO `router_upgradeconf` VALUES (3,'mnt','ts-25811-1',419,399,'3','升级','http://tb.cn/v7qXBdy');
INSERT INTO `router_upgradeconf` VALUES (4,'mnt','ts-25811-1',319,319,'1','升级','http://tb.cn/5ECTEby');
INSERT INTO `router_upgradeconf` VALUES (5,'upgrade','ts-25811-1',999,929,'12','续订','http://tb.cn/VmWjUby');
INSERT INTO `router_upgradeconf` VALUES (6,'upgrade','ts-25811-1',599,549,'6','续订','http://tb.cn/X6KYBdy');
INSERT INTO `router_upgradeconf` VALUES (7,'upgrade','ts-25811-1',419,399,'3','续订','http://tb.cn/v7qXBdy');
INSERT INTO `router_upgradeconf` VALUES (8,'upgrade','ts-25811-1',319,319,'1','续订','http://tb.cn/5ECTEby');
INSERT INTO `router_upgradeconf` VALUES (9,'upgrade','ts-25811-8',719,649,'12','续订','http://tb.cn/JkZaBdy');
INSERT INTO `router_upgradeconf` VALUES (10,'upgrade','ts-25811-8',399,349,'6','续订','http://tb.cn/pfscHdy');
INSERT INTO `router_upgradeconf` VALUES (11,'upgrade','ts-25811-8',289,269,'3','续订','http://tb.cn/DdOLMdy');
INSERT INTO `router_upgradeconf` VALUES (12,'upgrade','ts-25811-8',229,229,'1','续订','http://tb.cn/o17yhZy');
INSERT INTO `router_upgradeconf` VALUES (13,'mnt','FW_GOODS-1921400-v3',899,899,'12','升级','http://tb.cn/sJmvhZy');
INSERT INTO `router_upgradeconf` VALUES (14,'mnt','FW_GOODS-1921400-v3',469,469,'6','升级','http://tb.cn/s5nvhZy');
INSERT INTO `router_upgradeconf` VALUES (15,'mnt','FW_GOODS-1921400-v3',299,299,'3','升级','http://tb.cn/LalvhZy');
INSERT INTO `router_upgradeconf` VALUES (16,'mnt','FW_GOODS-1921400-v3',259,259,'1','升级','http://tb.cn/7jqvhZy');
--=========================================================================

-- 2014-04-16 router_lotteryinfo表添加字段exec_model
ALTER TABLE router_lotteryinfo ADD COLUMN exec_model int NOT NULL DEFAULT 1 AFTER reminder_flag;

--=========================================================================
-- 2014-04-16 将router_accessToken表token_type字段名改为platform，并修改类型和赋值
ALTER TABLE router_accessToken DROP COLUMN token_type;
ALTER TABLE router_accessToken ADD COLUMN platform VARCHAR(10) NOT NULL DEFAULT '' AFTER nick;

update router_accessToken a set a.platform='qn' where a.platform='';

--=========================================================================
-- 2014-04-08 修改auth_user表f4字段
-- 将auth_user.f4字段置空
update auth_user r set r.f4='' where r.f4 <> '';

-- 更新只订购Web的用户
update auth_user u set u.f4='web' where u.username in(
select s.nick  from router_articleusersubscribe s where s.article_code = 'ts-25811' and
NOT EXISTS (select * from router_articleusersubscribe a where a.article_code = 'FW_GOODS-1921400' and a.nick=s.nick)
);

-- 更新只订购千牛的用户
update auth_user u set u.f4='qn' where u.username in(
select s.nick  from router_articleusersubscribe s where s.article_code = 'FW_GOODS-1921400' and
NOT EXISTS (select * from router_articleusersubscribe a where a.article_code = 'ts-25811' and a.nick=s.nick)
);

-- 更新同时订购了Web和千牛的用户
update auth_user u set u.f4='all' where u.username in(
select distinct s.nick from router_articleusersubscribe s where s.article_code = 'ts-25811' and
EXISTS (select * from router_articleusersubscribe a where a.article_code = 'FW_GOODS-1921400' and a.nick=s.nick)
);

-- 给first_name字段(uid)创建索引
CREATE INDEX first_name ON auth_user(first_name);
--=========================================================================
-- 2014-03-23 修改router_articleusersubscribe表article_code的长度
ALTER TABLE router_articleusersubscribe MODIFY COLUMN article_code VARCHAR(30) NULL;
update router_articleusersubscribe r set r.article_code='ts-25811' where r.item_code like 'ts-25811%';
update router_articleusersubscribe r set r.article_code='FW_GOODS-192140' where r.item_code like 'FW_GOODS-192140%';

--=========================================================================
-- 2013-09-26 修改用户私人消息的表字段， 发布时需要先执行SQL，再syncdb
ALTER TABLE web_usermessage ADD is_show TINYINT(1) DEFAULT 0;

--=========================================================================
-- 2013-09-26 修改消息相关的表和字段， 发布时需要先执行SQL，再syncdb
DROP TABLES web_usercommonmessage, router_commonmessage, web_usermessage, tpm_feedback;
-- =========================================================================

-- 2015-06-16 添加评价词条字段， 发布时需要先执行SQL，再syncdb  (现在不需要了)
-- ALTER TABLE web_appraise ADD item_code VARCHAR(30) NULL;
-- =========================================================================

