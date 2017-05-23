define(["require", "template", "dataTable", "../common/common", 'store', "json", 'widget/templateExt/templateExt', '../report_detail/report_detail', 'widget/selectSort/selectSort', 'moment','jquery'], function(require, template, dataTable, common, store, json, _, report_detail, __, moment,$) {
    "use strict"

    var weirdSwitch,
        rank_desc,
        search_type=0,
        robSetting;

    $.fn.dataTableExt.afnSortData['custom-weird'] = function(oSettings, iColumn) {
        return $.map(oSettings.oApi._fnGetTrNodes(oSettings), function(tr, i) {
            var td = oSettings.oApi._fnGetTdNodes(oSettings, i)[iColumn],
                weird = Number(tr.getAttribute('data-weird-' + oSettings.aaSorting[0][1])),
                val;

            if (td.className.indexOf('sort_custom') != -1) {
                val = Number($(td).find('span:first').text());
            } else {
                val = Number($(td).text().replace('%', ''));
            }
            if (tr.className.indexOf('unsort') != -1) {
                return 'unsort'
            } else {
                if (weirdSwitch && weird) {
                    return weird + val;
                } else {
                    return val;
                }
            }
        });
    };

    var filter = function(options) {
        var html,
            obj,
            tpl = __inline('filter.html');

        html = template.compile(tpl)(options);

        obj = $(html);

        options.element.next().remove();

        //清空条件
        $('#filter_label').html('').removeClass('active')

        options.element.after(obj);

        obj.on('click.data.filter', function(e) {
            e.stopPropagation();
        });
    }

    var isValidInput = function(str) {
        if (isNaN(str) || str < 0.05 || str > 99.99) {
            return false;
        }
        return true;
    }

    var Row = function(nRow, warnPrice, mobileWarnPrice) {
        this.checked = false;
        this.up = false;
        this.down = false;
        this.del = false;

        this.nRow = nRow;
        this.warnPrice = warnPrice;
        this.mobileWarnPrice=mobileWarnPrice;

        this.mnt = null;
        this.match = null;

        this.initData();
        this.initEvent();
    }

    //初始化数据
    Row.prototype.initData = function() {
        this.data = $(this.nRow).data();

        this.keywordId = this.nRow.id;
        this.maxPrice = Number(this.data.max_price);
        this.maxMobilePrice = Number(this.data.max_mobile_price);
        this.match = Number(this.data.match);
        this.mnt = this.data.mnt;
        this.adgroupId = this.data.adgroup_id;
        this.campaignId = this.data.campaign_id;
        this.word = $(this.nRow).find('.word').text();

        this.limit = false;
        this.mobuleLimit = false;
        if (this.maxPrice >= this.warnPrice) {
            this.limit = true;
        }
        if(this.maxMobilePrice >= this.mobileWarnPrice){
            this.mobileLimit=true;
        }

        this.newPriceInput = $(this.nRow).find('.new_price');
        this.newMobilePriceInput = $(this.nRow).find('.new_mobile_price');
        this.checkboxInput = $(this.nRow).find('[type=checkbox]');
        this.sortSpan = $(this.nRow).find('.main_sort');
    }

    Row.prototype.initEvent = function() {
        var self = this;

        //改变价格
        $(this.nRow).on('change.Row.new_price', '.new_price', function() {
            if (!isValidInput(this.value)) {
                self.newPriceInput.val(self.maxPrice);
            } else {
                self.newPriceInput.val(Number(this.value).toFixed(2));
            }

            self.updateStyle(1);
            self.calcChangeNum();
        });

        $(this.nRow).on('change.Row.new_price', '.new_mobile_price', function() {
            if (!isValidInput(this.value)) {
                self.newMobilePriceInput.val(self.maxMobilePrice);
            } else {
                self.newMobilePriceInput.val(Number(this.value).toFixed(2));
            }

            self.updateStyle(2);
            self.calcChangeNum();
        });

        //恢复出价
        $(this.nRow).on('click.Row.recovery', '.recovery', function(e) {
            self.recovery(e, 1);
            if (!self.data.locked) {
                self.newPriceInput.attr('disabled', false);
            }
            self.calcChangeNum();
        });

        //恢复出价
        $(this.nRow).on('click.Row.recovery_mobile', '.recovery_mobile', function(e) {
            self.recovery(e, 2);
            if (!self.data.locked) {
                self.newMobilePriceInput.attr('disabled', false);
            }
            self.calcChangeNum();
        });


        //标记为删除
        $(this.nRow).on('click.Row.del', '.del', function() {
            self.del = self.del ? false : true;
            self.updateStyle();
            self.calcChangeNum();
            // self.newPriceInput.attr('disabled', true);
        });

        //报表
        report_detail.init(0, 1);
        $(this.nRow).on('click.Row.chart', '.chart', function() {
            var word;
            word = $(self.nRow).find('.word').text();
            report_detail.show('关键词明细：' + word, 'keyword', $('#shop_id').val(), null, self.adgroupId, null, self.nRow.id);
            //common.sendAjax.ajax('show_kw_trend', {
            //                'keyword_id': self.keywordId,
            //                'adgroup_id': $('#adgroup_id').val()
            //            }, function(data) {
            //                require(["../chart/chart"], function(modal) {
            //                    modal.show({
            //                        title: word,
            //                        highcharts: data
            //                    });
            //                });
            //            })
        });

        //自动优化设置
        $(this.nRow).find('i.mnt').popoverList({
            trigger: 'click',
            placement: 'bottom',
            content: __inline("mnt.html"),
            html: true,
            onChange: function(data) {
                self.setMntType(data.value);
                self.calcChangeNum();
            }
        });

        $(this.nRow).find('i.mnt').on('shown.bs.popoverList', function() {
            $(this).find('li[data-value=' + self.mnt + ']').addClass('active');
        });

        //匹配方式
        $(this.nRow).find('i.match').popoverList({
            trigger: 'click',
            placement: 'bottom',
            content: __inline("match.html"),
            html: true,
            onChange: function(data) {
                self.setMatchScorp(data.value);
                self.calcChangeNum();
            }
        });

        $(this.nRow).find('i.match').on('shown.bs.popoverList', function() {
            $(this).find('li[data-value=' + self.match + ']').addClass('active');
        });

        //pc质量得分详情
        $(this.nRow).find('td.qscore').popoverList({
            trigger: 'hover',
            placement: 'right',
            html: true,
            content: function() {
                return template.compile(__inline("qscore.html"))({
                    yd_qscore: Number($(this).attr('yd_qscore')),
                    yd_creative_score: $(this).attr('yd_creative_score'),
                    yd_rele_score: $(this).attr('yd_rele_score'),
                    yd_cvr_score: $(this).attr('yd_cvr_score'),
                    pc_qscore: $(this).attr('pc_qscore'),
                    pc_creative_score: $(this).attr('pc_creative_score'),
                    pc_rele_score: $(this).attr('pc_rele_score'),
                    pc_cvr_score: $(this).attr('pc_cvr_score'),
                    plflag: $(this).attr('plflag'),
                    matchflag: $(this).attr('matchflag')
                });
            }
        });

        $(this.nRow).find('td.qscore').on('shown.bs.popoverList', function() {
            $(self.nRow).find('.popover i[data-toggle=tooltip]').tooltip();
        });


        $(this.nRow).on('click.rob', '.rob', function(e) {
            $(self.nRow).trigger('show.rob', [$.extend({},robSetting,{
                method: 'manual',
            })]);
        });

        //抢排名设置
        $(this.nRow).on('show.rob', function(e, options) {
            var avgs;

            avgs = {
                keywordId: self.keywordId,
                adgroupId: self.adgroupId,
                word: self.word,
                maxPrice: self.maxPrice,
                maxMobilePrice: self.maxMobilePrice,
                qscore: self.data.qscore,
                wirelessQscore: self.data.wireless_qscore,
                pcRank: $(self.nRow).find('.pc_rank_desc').text(),
                ydRank: $(self.nRow).find('.mobile_rank_desc').text()
            }

            avgs = $.extend({}, avgs, options);

            require(['../rob_rank/rob_rank'], function(modal) {
                if(!rank_desc){
                    common.sendAjax.ajax('rank_desc_map', {}, function(data) {
                        rank_desc=data.result;
                        avgs['rank_desc_map']=rank_desc;
                        modal.show(avgs);
                    });
                }else{
                    avgs['rank_desc_map']=rank_desc;
                    modal.show(avgs);
                }
            });
            return false;
        });

        //抢排名记录
        $(this.nRow).on('click.rob_record', '.rob_record', function() {
            require(['../rob_rank/rob_record'], function(modal) {
                modal.show({
                    keywordId: self.keywordId
                })
            });
            return false;
        });

        //自动抢排名设置
        $(this.nRow).on('click.rob_set', '.rob_set', function() {

            common.sendAjax.ajax('rob_config', {
                'keyword_id': self.keywordId
            }, function(data) {
                $(self.nRow).trigger('show.rob', {
                    method: 'auto',
                    platform: data.data.platform,
                    rank_start: data.data.rank_start,
                    rank_end: data.data.rank_end,
                    limit: (data.data.limit / 100).toFixed(2),
                    nearly_success: data.data.nearly_success,
                    start_time: data.data.start_time,
                    end_time: data.data.end_time
                });
            });

            return false;
        });

        //取消自动抢排名
        // $(this.nRow).on('click.rob_cancle', '.rob_cancle', function() {
        //     common.confirm.show({
        //         body: '您确定取消“' + self.word + '”的自动抢排名吗？',
        //         okHidden: function() {
        //             common.sendAjax.ajax('rob_cancle', {
        //                 'keyword_id': self.keywordId
        //             }, function() {
        //                 $(self.nRow).trigger('update.rob_rank', ['nomal']);
        //             });
        //         }
        //     });
        // });

        //更新排名
        $(this.nRow).on('update.rank', function(e, pc_rank, mobile_rank, pc_rank_desc, mobile_rank_desc) {
            $(this).find('.pc_rank').text(pc_rank);
            $(this).find('.mobile_rank').text(mobile_rank);
            $(this).find('.pc_rank_desc').text(pc_rank_desc);
            $(this).find('.mobile_rank_desc').text(mobile_rank_desc);
        });

        //保存抢排名配置
        $(this.nRow).on('saveOptions.rank', function(e, options) {
            robSetting = options;
        });

        //更新抢排名
        $(this.nRow).on('update.rob_rank', function(e, type, new_price, platform) {
            var html;

            self.data.locked = 0;

            if (type == "nomal") {
                html = '<a href="javascript:;" class="rob">抢</a>';
            }

            if (type == "fail") {
                html = '<a href="javascript:;" class="rob_record">手动抢失败</a><a href="javascript:;" class="rob ml5">再抢</a>';
            }

            if (type == "success") {
                if (platform == 'pc') {
                    self.maxPrice = new_price;
                    self.data.max_price = new_price;
                    self.newPriceInput.val(new_price);
                    $(this).find('.max_price').text(new_price);
                }else {
                    self.maxMobilePrice = new_price;
                    self.data.max_mobile_price = new_price;
                    self.newMobilePriceInput.val(new_price);
                    $(this).find('.max_mobile_price').text(new_price);
                }

                html = '<a href="javascript:;" class="rob_record">手动抢成功</a><a href="javascript:;" class="rob ml5">再抢</a>';
            }

            if (type == "auto") {
                self.data.locked = 1;
                html = '<a href="javascript:;" class="rob_record">已设为自动</a><a href="javascript:;" class="rob_set ml5">设置</a>';
            }

            if (type == "doing") {
                html = '<a href="javascript:;" class="rob_doing">正在抢排名，请稍候</a>';
            }

            $(this).find('.rob_rank').html(html);
            self.updateStyle();
        });
    }

    //更新状态
    Row.prototype.updateStatus = function(type) {
        type == undefined ? type = 3 : '';

        if (type & 1) {
            var value = Number(this.newPriceInput.val());

            this.up = false;
            this.down = false;
            this.limit = false;

            if (value > this.maxPrice) {
                this.up = true;
            }

            if (value < this.maxPrice) {
                this.down = true;
            }

            if (value > this.warnPrice) {
                this.limit = true;
            }
        }

        if (type & 2) {
            var mobileValue = Number(this.newMobilePriceInput.val());
            this.mobileUp = false;
            this.mobileDown = false;
            this.mobileLimit = false;

            if (mobileValue > this.maxMobilePrice) {
                this.mobileUp = true;
            }

            if (mobileValue < this.maxMobilePrice) {
                this.mobileDown = true;
            }

            if (mobileValue > this.mobileWarnPrice) {
                this.mobileLimit = true;
            }
        }
    }

    //更新样式
    Row.prototype.updateStyle = function(type) {
        type == undefined ? type = 3 : '';
        this.updateStatus(type);

        if (type & 1) {
            $(this.nRow).removeClass('up down limit del');
            this.newPriceInput.attr('disabled', false);
            if (this.up) {
                $(this.nRow).addClass("up");
            }

            if (this.down) {
                $(this.nRow).addClass("down");
            }

            if (this.limit) {
                $(this.nRow).addClass("limit");
            }
        }

        if (type & 2) {
            $(this.nRow).removeClass('del mobileUp mobileDown mobileLimit');
             this.newMobilePriceInput.attr('disabled', false);
            if (this.mobileUp) {
                $(this.nRow).addClass("mobileUp");
            }

            if (this.mobileDown) {
                $(this.nRow).addClass("mobileDown");
            }

            if (this.mobileLimit) {
                $(this.nRow).addClass("mobileLimit");
            }
        }


        if (this.del) {
            this.newPriceInput.attr('disabled', true);
            this.newMobilePriceInput.attr('disabled', true);
            $(this.nRow).addClass("del");
        }

        if (this.data.locked) {
            this.newPriceInput.attr('disabled', true);
            this.newMobilePriceInput.attr('disabled', true);
        }
    }

    //重置
    Row.prototype.recovery = function(e, type) {
        this.del = false;
        this.up = false;
        this.down = false;

        this.mobileUp = false;
        this.mobileDown = false;
        this.limit = false;
        this.mobileLimit = false;

        if (this.maxPrice > this.warnPrice) {
            this.limit = true;
        }

        if (this.maxMobilePrice>this.mobileWarnPrice){
            this.mobileLimit=true;
        }

        // 1&1=1 2&1=0 1&3=1
        if (this.newPriceInput.val() != this.maxPrice && type & 1) {
            this.newPriceInput.val(this.maxPrice.toFixed(2));
        }

        // 1&2=0  2&2=2 2&3=2
        if (this.newMobilePriceInput.val() != this.maxMobilePrice && type & 2) {
            this.newMobilePriceInput.val(this.maxMobilePrice.toFixed(2));
        }

        this.updateStyle();
    }

    //将显示行显示到前面
    Row.prototype.setRowUp = function(checked, num) {
        // num != undefined ? this.checkboxInput.prev().text(num) : this.checkboxInput.prev().text(1);
        // checked != undefined ? this.checkboxInput[0].checked = checked : '';
        num != undefined ? this.sortSpan.text(num) : this.sortSpan.text(1);
        checked != undefined ? this.checkboxInput[0].checked = checked : '';
    }

    //将显示行显示到后面
    Row.prototype.setRowDown = function(checked) {
        // this.checkboxInput.prev().text(0);
        this.sortSpan.text(0);
        checked != undefined ? this.checkboxInput[0].checked = checked : '';
    }

    //加价
    Row.prototype.bulkPlus = function(baseType, baseNum, delta, mode, limit, type) {
        if (this.del || this.data.locked) {
            return false;
        }
        var currentPrice;
        if (baseType == 'max_price' || baseType == 'g_cpc') {
            if (mode == 'int') {
                currentPrice = baseNum + delta
            } else {
                currentPrice = baseNum * (1 + delta / 100);
            }
        } else {
            currentPrice = baseNum;
        }

        if (currentPrice > limit) {
            currentPrice = limit;
        }

        // if (currentPrice < this.maxPrice && baseType == 'max_price') {
        //     type & 1 && this.newPriceInput.val(this.maxPrice.toFixed(2));
        //     type & 2 && this.newMobilePriceInput.val(this.maxMobilePrice.toFixed(2));
        //     this.updateStyle(type);
        //     return;
        // }

        if(baseType == 'max_price'){
            if(type & 1 && currentPrice < this.maxPrice){
                this.newPriceInput.val(this.maxPrice.toFixed(2));
                this.updateStyle(type);
                return;
            }
            if(type & 2 && currentPrice < this.maxMobilePrice){
                this.newMobilePriceInput.val(this.maxMobilePrice.toFixed(2));
                this.updateStyle(type);
                return;
            }
        }

        if (currentPrice < 0.05) {
            currentPrice = 0.05;
        }

        if (currentPrice > 99.99) {
            currentPrice = this.maxPrice;
        }

        type & 1 && this.newPriceInput.val((parseInt(Math.ceil((currentPrice * 100).toFixed(1))) / 100).toFixed(2));
        type & 2 && this.newMobilePriceInput.val((parseInt(Math.ceil((currentPrice * 100).toFixed(1))) / 100).toFixed(2));
        this.updateStyle(type);
    }

    //降价
    Row.prototype.fallPlus = function(baseType, baseNum, delta, mode, limit, type) {
        if (this.del || this.data.locked) {
            return false;
        }
        var currentPrice;
        if (mode == 'int') {
            currentPrice = baseNum - delta
        } else {
            currentPrice = baseNum * (1 - delta / 100);
        }

        if (currentPrice < limit) {
            currentPrice = limit;
        }

        // if (currentPrice > this.maxPrice && baseType == 'max_price') {
        //     type & 1 && this.newPriceInput.val(this.maxPrice.toFixed(2));
        //     type & 2 && this.newMobilePriceInput.val(this.maxMobilePrice.toFixed(2));
        //     this.updateStyle();
        //     return;
        // }
        if(baseType == 'max_price'){
            if(type & 1 && currentPrice > this.maxPrice){
                this.newPriceInput.val(this.maxPrice.toFixed(2));
                this.updateStyle(type);
                return;
            }
            if(type & 2 && currentPrice > this.maxMobilePrice){
                this.newMobilePriceInput.val(this.maxMobilePrice.toFixed(2));
                this.updateStyle(type);
                return;
            }
        }

        if (currentPrice < 0.05) {
            currentPrice = 0.05;
        }

        if (currentPrice > 99.99) {
            currentPrice = this.maxPrice;
        }
        type & 1 && this.newPriceInput.val((parseInt(Math.floor((currentPrice * 100).toFixed(1))) / 100).toFixed(2));
        type & 2 && this.newMobilePriceInput.val((parseInt(Math.floor((currentPrice * 100).toFixed(1))) / 100).toFixed(2));
        this.updateStyle();
    }

    //设置匹配
    Row.prototype.setMatchScorp = function(scorp) {
        if (this.del) {
            return false;
        }

        var icon = {
            4: '&#xe623;',
            2: '&#xe624;',
            1: '&#xe622;'
        };

        this.match = scorp;
        $(this.nRow).find('.match').html(icon[scorp]);
    }

    //设置自动优化类型
    Row.prototype.setMntType = function(mntType) {
        if (this.del) {
            return false;
        }

        var icon = {
            0: '&#xe653;',
            1: '&#xe654;',
            2: '&#xe655;'
        };

        this.mnt = mntType;
        $(this.nRow).find('.mnt').html(icon[mntType]);
    }

    //获取表格
    Row.prototype.getTableElement = function() {
        return $(this.nRow).parent().parent();
    }

    //计算改变的值
    Row.prototype.calcChangeNum = function() {
        var table = this.getTableElement();
        table.trigger('calcChangeNum');
    }


    var Table = function(options) {
        this.config = {
            warnPrice: 5,
            mobileWarnPrice:5,
            weird: false,
            hideColumn: ["cpm", "avgpos", "favcount", "favctr", "favpay", "s_favcount", "a_favcount", "carttotal", "z_paycount", "j_paycount", "z_pay", "j_pay", "g_pv", "g_click", "g_cpc", "g_ctr", "g_competition", "create_days", "g_paycount", "g_roi", "g_coverage"],
            classDict: {
                'ROI': [6000000000, 1000000000, '有转化'],
                'FAV': [5000000000, 2000000000, '有收藏，无转化'],
                'CLICK': [4000000000, 3000000000, '有点击，无收藏，无转化'],
                'PV': [3000000000, 4000000000, '有展现，无点击'],
                'NOPV': [2000000000, 5000000000, '无展现'],
                'FRESH': [1000000000, 6000000000, '今日新加词']
            },
            classBase: 'data-tree-code',
            headerMarginTop:0,
            useStore: true, //默认开启关键词分类的本地存储
            aoColumns: [{
                bSortable: false
            }, {
                bSortable: true,
                "sSortDataType": "custom-weird",
                "sType": "custom",
            }, {
                bSortable: false
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: false,
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: false,
            }, {
                bSortable: false,
                "sType": "custom",
                "sSortDataType": "custom-weird"
            }, {
                bSortable: false
            }, {
                bSortable: false,
                "sType": "custom",
                "sSortDataType": "custom-weird"
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird"
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }, {
                bSortable: true,
                "sType": "custom",
                "sSortDataType": "custom-weird",
                "asSorting": ["desc", "asc"]
            }]
        }


        this.options = $.extend({}, this.config, options);

        if (this.options.useStore && (weirdSwitch || store.get('weird_switch'))) {
            $('#weird_switch').addClass('on');
            weirdSwitch = true;
        }

        var tableRows = this.options.element.find('tbody tr').length;
        $('.keywords_count').text(tableRows - 1); //除去推广组的定向数据
        if (tableRows > 1) {
            $('#operation_bar').removeClass('hide');
            this.sortTable();
            this.fixTableWidth();
            this.options.element.addClass('active');
            $('#keyword_no_data').hide();
        } else {
            $('#keyword_no_data').addClass('active');
            this.options.element.hide();
        }

        this.initEvent();

        //触发一次查排名
        // $('#rank_all').trigger('click');

        this.startWeirdClass();

        this.options.layoutCallback && this.options.layoutCallback.apply(this);
    }

    //用来隐藏列对应的字典
    Table.prototype.COLUM_DICT = {
        'keyword': 2,
        'max_price': 3,
        'new_price': 4,
        'max_mobile_price': 5,
        'new_mobile_price': 6,
        'rank': 7,
        'rob': 8,
        'qscore': 9,
        'create_days': 10,
        'impressions': 11,
        'click': 12,
        'ctr': 13,
        'cost': 14,
        'ppc': 15,
        'cpm': 16,
        'avgpos': 17,
        'favcount': 18,
        's_favcount': 19,
        'a_favcount': 20,
        'favctr': 21,
        'favpay': 22,
        'carttotal': 23,
        'paycount': 24,
        'z_paycount': 25,
        'j_paycount': 26,
        'pay': 27,
        'z_pay': 28,
        'j_pay': 29,
        'conv': 30,
        'roi': 31,
        'g_pv': 32,
        'g_click': 33,
        'g_ctr': 34,
        'g_coverage': 35,
        'g_roi': 36,
        'g_cpc': 37,
        'g_competition': 38,
        'g_paycount': 39
    };

    Table.prototype.sortTable = function() {
        var self = this,
            hideColumn;

        this.rowCache = {},

            hideColumn = this.options.hideColumn.length ? this.options.hideColumn : this.config.hideColumn;


        for (var i in hideColumn) {
            if (typeof this.COLUM_DICT[hideColumn[i]] != "undefined") {
                this.options.aoColumns[this.COLUM_DICT[hideColumn[i]]]['bVisible'] = false;
            }
        }

        this.table = this.options.element.dataTable({
            bRetrieve: true, //允许重新初始化表格
            bPaginate: false,
            bFilter: false,
            bInfo: false,
            bAutoWidth: false, //禁止自动计算宽度
            sDom: 'Tlfrtip',
            aaSorting: [
                [1, 'desc']
            ],
            aoColumns: this.options.aoColumns,
            fnCreatedRow: function(nRow, aData, iDisplayIndex, iDisplayIndexFull) {
                var row;
                if (nRow.className.indexOf('unsort') == -1) {
                    row = new Row(nRow, self.options.warnPrice, self.options.mobileWarnPrice);
                    row.aData = aData;
                    row.iDisplayIndex = iDisplayIndex;
                    self.rowCache[row.keywordId] = row;

                    //打标签
                    if (row.data.treeCode) {
                        var lable = row.data.treeCode;
                        nRow.setAttribute('data-weird-desc', self.options.classDict[lable][0]);
                        nRow.setAttribute('data-weird-asc', self.options.classDict[lable][1]);
                    } else {
                        nRow.setAttribute('data-weird-desc', 0);
                        nRow.setAttribute('data-weird-asc', 0);
                    }
                }
            },
            fnHeaderCallback: function(nHead, aData, iStart, iEnd, aiDisplay) {
                //此处删除th的hide避免表头浮动出问题
                $(nHead).find('th').removeClass('hide');
            },
            oTableTools: {
                sSwfPath: __uri('/jl6/site_media/swf/copy_csv_xls.swf'),
                aButtons: [{
                    sExtends: "xls",
                    sTitle: self.getAdgroupTitle(),
                    fnClick: function(nButton, oConfig, flash) {
                        this.fnSetText(flash, self.getCsvData());
                    }
                }],
                custom_btn_id: "save_as_csv"
            },
            oLanguage: {
                "sZeroRecords": "没有关键词记录"
            },
            fnDrawCallback: function() {
                var table = this;

                //shift input操作开始
                table.find('.check_column').off('.shiftcheckbox').shiftcheckbox({
                    checkboxSelector: 'input',
                    complete: function() {
                        self.checkCallback();
                    }
                });

                table.find('.check_column').off('click.checkCallback').on('click.checkCallback', 'input', function() {
                    self.checkCallback();
                });

                //全选
                table.find('.all input').off('change').on('change', function() {
                    var that = this;

                    table.find('tbody>tr>td>input[type=checkbox]').each(function() {
                        this.checked = that.checked;
                    });

                    self.setChecked();
                });

                self.startWeirdClass();

                //tooltip提示
                // table.find("[data-toggle=tooltip]").tooltip({html:true});
            }
        });
    }

    Table.prototype.initEvent = function() {
        var self = this;


        //表头固定
        if ($('.fixedHeader').length) {
            $('.fixedHeader').remove();
        }

        self.table && (self.fixHeader = new FixedHeader(self.table,{offsetTop:self.options.headerMarginTop}));


        //全部重置
        $('#recovery_all').off('click.Table.recovery_all').on('click.Table.recovery_all', function(e) {
            for (var i in self.rowCache) {
                self.rowCache[i].recovery(e, 1);
                self.rowCache[i].newPriceInput.attr('disabled', false);
            }
            self.calcChangeNum();
        });

        //全部重置
        $('#recovery_mobile_all').off('click.Table.recovery_mobile_all').on('click.Table.recovery_mobile_all', function(e) {
            for (var i in self.rowCache) {
                self.rowCache[i].recovery(e, 2);
                self.rowCache[i].newMobilePriceInput.attr('disabled', false);
            }
            self.calcChangeNum();
        });


        //批量查询
        $('#rank_all').off('click.Table.rank_all').on('click.Table.rank_all', function() {

            if ($(this).hasClass('disabled')) {
                return false;
            }

            var keywordList = [],
                oldText=$(this).text(),
                that = this;

            $(this).addClass('disabled').text('正在更新');

            for (var i in self.rowCache) {
                keywordList.push({
                    adgroup_id: self.rowCache[i].adgroupId,
                    keyword_id: self.rowCache[i].keywordId
                });
            }

            common.sendAjax.ajax('batch_get_rt_kw_rank', {
                'keyword_id_list': $.toJSON(keywordList)
            }, function(data) {
                for (var keywordId in data.rank_result) {
                    var rankInfo = data.rank_result[keywordId];
                    var obj = $(self.rowCache[keywordId].nRow);

                    $(self.rowCache[keywordId].nRow).find('.pc_rank_desc').text(rankInfo.pc_rank_desc);
                    $(self.rowCache[keywordId].nRow).find('.mobile_rank_desc').text(rankInfo.mobile_rank_desc);
                    $(self.rowCache[keywordId].nRow).find('.pc_rank').text(rankInfo.pc_rank < 0 ? rankInfo.pc_rank * 100 : rankInfo.pc_rank);
                    $(self.rowCache[keywordId].nRow).find('.mobile_rank').text(rankInfo.mobile_rank < 0 ? rankInfo.mobile_rank * 100 : rankInfo.mobile_rank);
                }

                $(document).trigger('batch_rt_kw_rank',[data.rank_result]);

                $(that).removeClass('disabled').text(oldText);
                $('#rank_time').text(moment().format('H:mm'));
            });
        });

        //过滤
        $('#filter_warp').off('change.Table.filter').on('change.Table.filter', 'input[type=checkbox]', function() {
            self.filterKwList();
        });

        //label反选
        $('#filter_label').off('click.Table.select').on('click.Table.select', '.select', function() {
            var i = 0,
                filterList = $(this).find('i').data().value.split(',');

            for (var i, i_end = filterList.length; i < i_end; i++) {
                if ($('#filter_warp li[data-id=' + filterList[i] + ']').length) {
                    $('#filter_warp li[data-id=' + filterList[i] + ']').find('input[type=text]').val('');
                } else {
                    $('#filter_warp input[type=checkbox][value=' + filterList[i] + ']').attr('checked', false);
                }
            }
            self.filterKwList();
        });

        //筛选条件点击确定
        $('#filter_warp .dropdown-menu .btn-primary').off('click.Table.btn-primary').on('click.Table.btn-primary', function() {
            $('#filter_warp').removeClass('open');
            self.filterKwList();
        });

        //筛选条件点击取消
        $('#filter_warp .dropdown-menu .btn-default').off('click.Table.btn-default').on('click.Table.btn-default', function() {
            $('#filter_warp').removeClass('open');
        });

        //改价中自动选中radio
        $('#price_warp .radio:lt(6)').find('select,input[type=text]').off('focus.Table.select').on('focus.Table.select', function() {
            $(this).parent().find('input[type=radio]')[0].checked = true;
        });

        //自动补全改价限价后面的00
        $('#price_warp .radio:eq(2) input[type=text],#price_warp .radio:eq(4) input[type=text]').off('change.autoComplate').on('change.autoComplate', function() {
            if (!isNaN(this.value)) {
                $(this).val(Number(this.value).toFixed(2));
            } else {
                $(this).val('');
            }
        });

        //自动补全改价限价后面的00
        $('#price_warp .radio:eq(0) input[type=text],#price_warp .radio:eq(6) input[type=text]').off('change.autoComplate').on('change.autoComplate', function() {
            if (isValidInput(this.value)) {
                $(this).val(Number(this.value).toFixed(2));
            } else {
                $(this).val('');
            }
        });

        //改价操作点击取消
        $('#price_warp .dropdown-menu .btn-default').off('click.Table.btn-default').on('click.Table.btn-default', function() {
            $('#price_warp').removeClass('open');
        });

        //改价操作点击确定
        $('#price_warp .dropdown-menu .btn-primary').off('click.Table.btn-primary').on('click.Table.btn-primary', function() {
            var changeType,
                checkedRow,
                limitPrice;

            changeType = $('#price_warp input[type=radio]:checked').val();
            limitPrice = parseFloat($('#price_limit').val());

            if (changeType) {
                checkedRow = self.checkedRow();

                if (checkedRow.length) {
                    self['changePrice8' + changeType](checkedRow, limitPrice, 1);
                    self.calcChangeNum();
                } else {
                    common.lightMsg.show('没有选中任何关键词！');
                    $('#price_warp').removeClass('open');
                }
            } else {
                common.lightMsg.show('请选择改价类型');
            }
        });

        //改价中自动选中radio
        $('#mobile_price_warp .radio:lt(6)').find('select,input[type=text]').off('focus.Table.select').on('focus.Table.select', function() {
            $(this).parent().find('input[type=radio]')[0].checked = true;
        });

        //自动补全改价限价后面的00
        $('#mobile_price_warp .radio:eq(2) input[type=text],#mobile_price_warp .radio:eq(4) input[type=text]').off('change.autoComplate').on('change.autoComplate', function() {
            if (!isNaN(this.value)) {
                $(this).val(Number(this.value).toFixed(2));
            } else {
                $(this).val('');
            }
        });

        //自动补全改价限价后面的00
        $('#mobile_price_warp .radio:eq(0) input[type=text],#mobile_price_warp .radio:eq(6) input[type=text]').off('change.autoComplate').on('change.autoComplate', function() {
            if (isValidInput(this.value)) {
                $(this).val(Number(this.value).toFixed(2));
            } else {
                $(this).val('');
            }
        });

        //改价操作点击取消
        $('#mobile_price_warp .dropdown-menu .btn-default').off('click.Table.btn-default').on('click.Table.btn-default', function() {
            $('#mobile_price_warp').removeClass('open');
        });

        //移动改价操作点击确定
        $('#mobile_price_warp .dropdown-menu .btn-primary').off('click.Table.btn-primary').on('click.Table.btn-primary', function() {
            var changeType,
                checkedRow,
                limitPrice;

            changeType = $('#mobile_price_warp input[type=radio]:checked').val();
            limitPrice = parseFloat($('#price_limit_mobile').val());

            if (changeType) {
                checkedRow = self.checkedRow();

                if (checkedRow.length) {
                    self['changePrice8' + changeType](checkedRow, limitPrice, 2);
                    self.calcChangeNum();
                } else {
                    common.lightMsg.show('没有选中任何关键词！');
                    $('#mobile_price_warp').removeClass('open');
                }
            } else {
                common.lightMsg.show('请选择改价类型');
            }
        });

        //批量删除
        $('#bluk_del').off('click.Table.del').on('click.Table.del', function() {
            var checkedRow = self.checkedRow();

            if (checkedRow.length) {
                for (var i = 0, i_end = checkedRow.length; i < i_end; i++) {
                    var obj = self.rowCache[checkedRow[i][0].id];

                    obj.del = true;
                    obj.updateStyle();

                    // obj.newPriceInput.attr('disabled', true);
                    self.calcChangeNum();
                }
                self.calcChangeNum();
            } else {
                common.lightMsg.show('没有选中任何关键词！');
            }
        });

        //修改匹配点击确定
        $('#match_warp .dropdown-menu .btn-primary').off('click.Table.btn-primary').on('click.Table.btn-primary', function() {
            var matchType = Number($('#match_warp .dropdown-menu input[type=radio]:checked').val()),
                checkedRow = self.checkedRow();

            if (checkedRow.length) {

                for (var i = 0, i_end = checkedRow.length; i < i_end; i++) {
                    var obj = self.rowCache[checkedRow[i][0].id];
                    obj.setMatchScorp(matchType);
                }

                $('#match_warp').removeClass('open');
                self.calcChangeNum();
            } else {
                common.lightMsg.show('没有选中任何关键词！');
            }
            $('#match_warp').removeClass('open');
        });

        //修改匹配点击取消
        $('#match_warp .dropdown-menu .btn-default').off('click.Table.btn-default').on('click.Table.btn-default', function() {
            $('#match_warp').removeClass('open');
        });


        //设置自动优化点击确定
        $('#mnt_warp .dropdown-menu .btn-primary').off('click.Table.btn-primary').on('click.Table.btn-primary', function() {
            var mntType = Number($('#mnt_warp .dropdown-menu input[type=radio]:checked').val()),
                checkedRow = self.checkedRow();

            if (checkedRow.length) {

                for (var i = 0, i_end = checkedRow.length; i < i_end; i++) {
                    var obj = self.rowCache[checkedRow[i][0].id];
                    obj.setMntType(mntType);
                }

                $('#mnt_warp').removeClass('open');
                self.calcChangeNum();
            } else {
                common.lightMsg.show('没有选中任何关键词！');
            }

            $('#mnt_warp').removeClass('open');
        });

        //设置自动优化点击取消
        $('#mnt_warp .dropdown-menu .btn-default').off('click.Table.btn-default').on('click.Table.btn-default', function() {
            $('#mnt_warp').removeClass('open');
        });

        //桥接每个row触发的计算改变数量的事件
        this.table && this.table.off('calcChangeNum').on('calcChangeNum', function() {
            self.calcChangeNum();
        });

        //桥接删除行
        this.table && this.table.off('delete_row').on('delete_row', function(e, keywordId) {
            self.delete_row(keywordId);
        });

        //显示更多数据中的checkedbox联动
        $('#show_more_keyword .dropdown-menu>ul').each(function() {
            $(this).find('.checkbox-inline').shiftcheckbox({
                checkboxSelector: 'input',
                selectAll: $(this).find('.title')
            });
        });

        //列头显示
        $('#show_more_keyword').off('shown.bs.dropdown').on('shown.bs.dropdown', function() {
            var obj = $(this).find('ul'),
                hideColumn = self.getHideColumn();

            $('input[type=checkbox]', obj).each(function() {
                this.checked = true;
            });

            for (var i in hideColumn) {
                if (typeof self.COLUM_DICT[hideColumn[i]] != "undefined") {
                    $('input[value=' + hideColumn[i] + ']', obj).trigger('click');
                }
            }


            // for(var i=0,i_end=hideColumn.length;i<i_end;i++){
            //     $('input[value='+hideColumn[i]+']',obj).trigger('click');
            // }
        });

        //隐藏列
        $('#show_more_keyword .btn-primary').off('click.Table.btn-primary').on('click.Table.btn-primary', function() {
            var hideColumn = [],
                hideColumnNum = [];

            $('#show_more_keyword input[type=checkbox][value]').each(function() {
                if (!this.checked && typeof self.COLUM_DICT[this.value] != "undefined") {
                    hideColumnNum.push(self.COLUM_DICT[this.value]);
                    hideColumn.push(this.value);
                }
            });

            //默认隐藏抢排名,等强排名开发完成后打开 #TODO zhongjinfeng
            // hideColumnNum.push(self.COLUM_DICT['rob']);
            // hideColumn.push('rob');

            self.setHideCloumn(hideColumnNum);
            $('#show_more_keyword').removeClass('open');

            common.sendAjax.ajax('save_custom_column', {
                'column': hideColumn
            }, null);
        });

        $('#show_more_keyword .btn-default').off('click.Table.btn-default').on('click.Table.btn-default', function() {
            $('#show_more_keyword').removeClass('open');
        });


        //关键词分类
        $('#weird_switch').off('change.Table').on('change.Table', function(e, checked) {
            if (checked) {
                weirdSwitch = true;

                self.table.fnSort([
                    [1, 'desc']
                ]);

                // self.startWeirdClass();
                // $('.select_status').removeClass('tdl');

                store.set('weird_switch', true);
            } else {
                weirdSwitch = false;
                self.closeWeirdClass();
                // $('.select_status').addClass('tdl');

                store.set('weird_switch', false);
            }
        });

        //关键词搜索
        $('.search_btn').off('click.Table').on('click.Table', function() {
            var searchWord = $(this).prev().val();
            $('.search_btn').prev().val(searchWord);
            if (searchWord != '') {
                self.searchWordAndSort(searchWord);
            } else {
                common.lightMsg.show('请填写要搜索的关键词');
            }
        });

        $('.search_val').off('keyup.Table').on('keyup.Table', function(e) {
            if (e.keyCode == 13) {
                $(this).siblings('.search_btn').click();
                $(this).focus();
            }
        });

        $('.select_status').off('click.Table').on('click.Table', function() {
            var mode = parseInt($(this).attr('mode'));

            for (var keywordId in self.rowCache) {
                var obj = self.rowCache[keywordId],
                    judge = false;

                switch (mode) {
                    case 0:
                        if (obj.up) {
                            judge = true;
                        }
                        break;
                    case 1:
                        if (obj.down) {
                            judge = true;
                        }
                        break;
                    case 2:
                        if (obj.del) {
                            judge = true;
                        }
                        break;
                    case 3:
                        if (obj.match != obj.data.match) {
                            judge = true;
                        }
                        break;
                    case 4:
                        if (obj.mnt != obj.data.mnt) {
                            judge = true;
                        }
                        break;
                    case 5:
                        if (obj.mobileUp) {
                            judge = true;
                        }
                        break;
                    case 6:
                        if (obj.mobileDown) {
                            judge = true;
                        }
                        break;
                }

                if (judge) {
                    obj.setRowUp(true);
                } else {
                    obj.setRowDown(false);
                }

            }

            // self.setChecked();

            if (!weirdSwitch) {
                self.table.fnSort([
                    [1, 'desc']
                ]);
                // self.closeWeirdClass();
            }

            self.checkCallback();
        });

        //pc端限价
        $('#warn_price .edit i').off('click.Table').on('click.Table', function() {
            if ($(this).hasClass('disabled')) {
                return false;
            }
            var limit_price = Number($('#warn_price .edit span').text()).toFixed(2);
            $('#warn_price .save input').val(limit_price);
            $('#warn_price ').addClass('active');
        });

        //移动端限价
        $('#mobile_warn_price .edit i').off('click.Table').on('click.Table', function() {
            if ($(this).hasClass('disabled')) {
                return false;
            }
            var limit_price = Number($('#mobile_warn_price .edit span').text()).toFixed(2);
            $('#mobile_warn_price .save input').val(limit_price);
            $('#mobile_warn_price ').addClass('active');
        });

        //pc端现价提交
        $('#warn_price .save a').off('click.Table').on('click.Table', function() {
            var warnPrice = $('#warn_price .save input').val();

            if (isValidInput(warnPrice)) {

                $('#warn_price ').removeClass('active');

                //没有做出改动
                if (Number($('#warn_price .edit span').text()) == Number(warnPrice)) {
                    return
                }

                $('#warn_price .edit span').text(Number(warnPrice).toFixed(2));
                for (var keywordId in self.rowCache) {
                    var obj = self.rowCache[keywordId];

                    obj.warnPrice = Number(warnPrice);
                    obj.updateStyle();
                }
                self.options.warnPrice = warnPrice;
                common.sendAjax.ajax('set_adg_limit_price', {
                    'adgroup_id': $('#adgroup_id').val(),
                    'limit_price': warnPrice
                }, function() {
                    common.lightMsg.show('修改PC限价成功');
                });
            } else {
                common.lightMsg.show('限价不能为空，必须为0.05元~99.99元之间');
            }

            return false;
        });

        //移动端限价提交
        $('#mobile_warn_price .save a').off('click.Table').on('click.Table', function() {
            var mobileWarnPrice = $('#mobile_warn_price .save input').val();

            if (isValidInput(mobileWarnPrice)) {

                $('#mobile_warn_price ').removeClass('active');

                //没有做出改动
                if (Number($('#mobile_warn_price .edit span').text()) == Number(mobileWarnPrice)) {
                    return
                }

                $('#mobile_warn_price .edit span').text(Number(mobileWarnPrice).toFixed(2));
                for (var keywordId in self.rowCache) {
                    var obj = self.rowCache[keywordId];

                    obj.mobileWarnPrice = Number(mobileWarnPrice);
                    obj.updateStyle();
                }
                self.options.mobileWarnPrice = mobileWarnPrice;
                common.sendAjax.ajax('set_adg_limit_price', {
                    'adgroup_id': $('#adgroup_id').val(),
                    'mobile_limit_price': mobileWarnPrice
                }, function() {
                    common.lightMsg.show('修改移动限价成功');
                });
            } else {
                common.lightMsg.show('限价不能为空，必须为0.05元~99.99元之间');
            }

            return false;
        });

        $('.edit_mobdiscount').off('click.Table').on('click.Table', function() {
            var discount_obj = $('#adg_mobdiscount'),
                discount = discount_obj.text(),
                campaign_id = $('#campaign_id').val(),
                adgroup_id = $('#adgroup_id').val();

            require(["../edit_mobdiscount/edit_mobdiscount"], function(modal) {
                modal.show({
                    value: discount,
                    obj: discount_obj,
                    campaign_id: campaign_id,
                    adgroup_id: adgroup_id
                });
            });
        });

        //恢复默认显示的列
        $('#reset_show_cloumn').off('click.Table').on('click.Table', function() {
            var hideColumn = [],
                hideColumnNum = [];

            for (var i in self.config.hideColumn) {
                hideColumnNum.push(self.COLUM_DICT[self.config.hideColumn[i]]);
                hideColumn.push(self.config.hideColumn[i]);
            }

            self.setHideCloumn(hideColumnNum);
            common.sendAjax.ajax('save_custom_column', {
                'column': hideColumn
            }, null);
        });

        var do_submit_keyword = function(submit_list, update_mnt_list) {
            common.loading.show("正在提交");
            common.sendAjax.ajax('submit_keyword_optimize', {
                    'submit_list': $.toJSON(submit_list),
                    'update_mnt_list': $.toJSON(update_mnt_list),
                    'campaign_id': $('#campaign_id').val(),
                    'optm_type': 0,
                    'mnt_type': $('#mnt_type').val()
                },
                function(json) {
                    var del_count = json.del_kw.length,
                        update_count = json.update_kw.length,
                        failed_count = json.failed_kw.length,
                        top_del_count = json.top_del_kw.length,
                        mnt_change_list = json.mnt_change_kw.length;

                    var del_list = $.merge(json.top_del_kw, json.del_kw);
                    var change_list = $.merge(json.update_kw, json.mnt_change_kw);

                    var msg = '修改成功:' + update_count + '个，删除成功:' + del_count + '个';

                    if (mnt_change_list) {
                        msg += '，其中优化方式修改成功：' + mnt_change_list + '个';
                    }

                    if (top_del_count) {
                        msg += '，其中' + top_del_count + '个关键词已在淘宝被删除！';
                    }
                    if (failed_count) {
                        msg += '，操作失败:' + failed_count + '个';
                    }
                    for (var i = 0; i < del_list.length; i++) {
                        self.delete_row(del_list[i]);
                    }
                    for (var j = 0; j < change_list.length; j++) {
                        self.update_row(change_list[j])
                    }
                    /*
                    for (var i=0;i<del_count;i++){
                        self.delete_row(json.del_kw[i]);
                    }
                    for (var i=0;i<top_del_count;i++){
                        self.delete_row(json.top_del_kw[i]);
                    }
                    for (var i=0;i<update_count;i++){
                        self.update_row(json.update_kw[i]);
                    }*/
                    self.calcChangeNum();
                    var keywords_count = parseInt($('.keywords_count:first').text());
                    $('.keywords_count').text(keywords_count - del_list.length);
                    common.alert.show({
                        body: msg
                    });

                    self.startWeirdClass();

                    if ($.isEmptyObject(self.rowCache)) {
                        $('#keyword_no_data').addClass('active').show();
                        $('#operation_bar').addClass('hide');
                        self.options.element.hide().removeClass('active');
                        self.fixHeader.fnGetSettings().aoCache[0].nWrapper.remove();
                    }

                });
            common.loading.hide();
        }

        //提交关键词改动（调价、调整匹配方式、删除）
        $('#submit_keywords').off('click.Table').on('click.Table', function() {
            var submit_list = [],
                update_mnt_list = [];
            var limit_count = 0;
            var mobile_limit_count = 0;
            for (var keywordId in self.rowCache) {
                var obj = self.rowCache[keywordId];
                if (obj.del || obj.up || obj.down || obj.mobileUp || obj.mobileDown || (obj.match && obj.match != obj.data.match)) {
                    if (obj.limit) {
                        limit_count++;
                    }
                    if(obj.mobileLimit){
                        mobile_limit_count++;
                    }
                    submit_list.push({
                        'keyword_id': obj.keywordId,
                        'adgroup_id': obj.adgroupId,
                        'campaign_id': obj.campaignId,
                        'word': obj.word,
                        'new_price': Number(obj.newPriceInput.val()),
                        'max_price': Number(obj.maxPrice),
                        'max_mobile_price': Number(obj.newMobilePriceInput.val()),
                        'mobile_old_price': Number(obj.maxMobilePrice),
                        'mobile_is_default_price':0,
                        'match_scope': obj.match,
                        'is_del': obj.del
                    });
                }
                if (obj.mnt != obj.data.mnt) {
                    update_mnt_list.push({
                        'keyword_id': obj.keywordId,
                        'adgroup_id': obj.adgroupId,
                        'mnt_opt_type': obj.mnt
                    });
                }
            }
            if (submit_list.length > 0 || update_mnt_list.length > 0) {
                var msg = "即将提交：";
                var up_num = parseInt($('#up_num').text()),
                    down_num = parseInt($('#down_num').text()),
                    del_num = parseInt($('#del_num').text()),
                    match_num = parseInt($('#match_num').text()),
                    mnt_num = parseInt($('#mnt_num').text()),
                    mobile_up = parseInt($('#up_mobile_num').text()),
                    mobile_down = parseInt($('#down_mobile_num').text());

                if (up_num) {
                    msg += "PC加价" + up_num + "个，";
                }
                if (down_num) {
                    msg += "PC降价" + down_num + "个，";
                }
                if(mobile_up){
                     msg += "移动加价" + mobile_up + "个，";
                }
                if(mobile_down){
                     msg += "移动降价" + mobile_down + "个，";
                }
                if (del_num) {
                    msg += "删除" + del_num + "个，";
                }
                if (match_num) {
                    msg += "修改匹配方式" + match_num + "个，";
                }
                if (mnt_num) {
                    msg += "修改全自动优化类型" + mnt_num + "个，";
                }
                if (limit_count) {
                    msg += "有" + limit_count + "个关键词超出了PC限价" + self.options.warnPrice + "元！"
                }
                if (mobile_limit_count) {
                    msg += "有" + mobile_limit_count + "个关键词超出了移动限价" + self.options.mobileWarnPrice + "元！"
                }

                msg += "亲，确定提交到直通车吗？"

                common.confirm.show({
                    body: msg,
                    okHidden: function() {
                        do_submit_keyword(submit_list, update_mnt_list);
                    }
                });
            } else {
                common.lightMsg.show('没有关键词改变，请进行操作');
            }
        });

        //显示过滤条件后重定位表头位置
        $('#filter_label').off($.support.transition.end).on($.support.transition.end, function(e) {
            if (e.elapsedTime < 0.1) {
                return;
            }
            self.fixHeader.fnUpdate();
            $('.fixedHeader').show();
        });

        //切换关键词搜索模式
        $('#search_type').off('change').on('change',function(e,v){
            console.log(v);
            search_type=v;
        });
    }


    Table.prototype.checkedRow = function() {
        var rowList = [];
        this.table.find('tbody tr:not(.unsort)').each(function() {
            var inputObj = $(this).find('td.check_column input');
            if (inputObj[0].checked) {
                rowList.push($(this));
            }
        });
        return rowList;
    }

    //获得自动过滤条件
    Table.prototype.getLabelCodeList = function() {
        var codeLsit = [],
            temp;
        $('#filter_warp li').each(function(i) {
            temp = [];
            if ($('input:checked', this).length) {
                $('input:checked', this).each(function() {
                    temp.push(this.value);
                });
                codeLsit.push(temp);
            }
        });
        return codeLsit;
    }

    //获得自定义过滤条件
    Table.prototype.getCustomLabelCodeList = function() {
        var customLimit = [];

        $('#filter_warp li').each(function() {
            var min, max, obj = $(this);
            min = Number(obj.find('input[type=text]:eq(0)').val());
            max = Number(obj.find('input[type=text]:eq(1)').val());
            if (min || max) {
                customLimit.push([obj.attr('data-id').replace('refine_', ''), min, max]);
            }
        });
        return customLimit;
    }

    //显示过滤条件
    Table.prototype.showFilterLabel = function(filterList, customLimit) {
        var filterStr = '',
            obj = $('#filter_label'),
            custom_dict = {
                'max_price': 'PC当前出价',
                'max_mobile_price': '移动当前出价',
                'ctr': '点击率',
                'click': '点击量',
                'cpc': '花费',
                'roi': 'ROI',
                'qscore': 'PC质量分',
                'wireless_qscore': '移动质量分'
            };

        for (var c = 0, c_end = filterList.length; c < c_end; c++) {
            var title = $('#filter_warp input[type=checkbox][value=' + filterList[c][0] + ']').data().title,
                status = '';
            for (var t = 0, t_end = filterList[c].length; t < t_end; t++) {
                status += $('#filter_warp input[type=checkbox][value=' + filterList[c][t] + ']').data().status + '，';
            }
            filterStr += '<li class="select"><a href="javascript:;">' + title + '：' + status.slice(0, -1) + '<i data-value="' + filterList[c] + '"></i></a></li>';
        }

        for (var j = 0, j_end = customLimit.length; j < j_end; j++) {
            if (customLimit[j][1] && customLimit[j][2]) {
                filterStr += '<li class="select"><a href="javascript:;">' + custom_dict[customLimit[j][0]] + ':' + customLimit[j][1] + '~' + customLimit[j][2] + '<i data-value="' + customLimit[j][0] + '"></i></a></li>';
            } else {
                if (customLimit[j][1]) {
                    filterStr += '<li class="select"><a href="javascript:;">' + custom_dict[customLimit[j][0]] + ':大于' + customLimit[j][1] + '<i data-value="' + customLimit[j][0] + '"></i></a></li>';
                } else {
                    filterStr += '<li class="select"><a href="javascript:;">' + custom_dict[customLimit[j][0]] + ':小于' + customLimit[j][2] + '<i data-value="' + customLimit[j][0] + '"></i></a></li>';
                }
            }
        }

        obj.html(filterStr);

        if (filterStr != "") {
            obj.addClass('active');
        } else {
            obj.removeClass('active');
        }

        $('.fixedHeader').hide();
    }

    //主要过滤函数
    Table.prototype.filterKwList = function() {
        var self = this;
        setTimeout(function() {
            var filterList,
                customLimit,
                rowList;

            filterList = self.getLabelCodeList();
            customLimit = self.getCustomLabelCodeList();
            rowList = self.table.find('tbody tr:not(.unsort)');

            if (filterList.length || customLimit.length) {
                for (var i = 0, i_end = rowList.length; i < i_end; i++) {
                    var lableJudge = 0,
                        obj = self.rowCache[rowList[i].id],
                        lable = obj.data.labelCode;

                    for (var c = 0, c_end = filterList.length; c < c_end; c++) {
                        var lableTempJudge = 0;
                        for (var f = 0, f_end = filterList[c].length; f < f_end; f++) {
                            if (lable.indexOf(filterList[c][f]) != -1) {
                                lableTempJudge = 1;
                                break;
                            }
                        }

                        if (lableTempJudge) {
                            continue;
                        } else {
                            break;
                        }
                    }

                    for (var j = 0, j_end = customLimit.length; j < j_end; j++) {
                        var current_val,
                            customJudge = 0,
                            key = customLimit[j][0];

                        current_val = parseFloat(obj.data[key]);

                        if (!isNaN(current_val)) {
                            if (customLimit[j][1] && customLimit[j][2] && (current_val < customLimit[j][1] || current_val > customLimit[j][2])) {
                                //存在最小值和最大值
                                customJudge = 0;
                            } else if ((customLimit[j][1] && (current_val < customLimit[j][1])) || (customLimit[j][2] && (current_val > customLimit[j][2]))) {
                                //存在一个值
                                customJudge = 0;
                            } else {
                                customJudge = 1;
                            }
                            if (customJudge == 0) {
                                break;
                            }
                        } else {
                            customJudge = 0;
                        }
                    }

                    lableTempJudge === undefined ? lableJudge = customJudge : customJudge === undefined ? lableJudge = lableTempJudge : lableJudge = customJudge && lableTempJudge;

                    if (lableJudge) {
                        obj.setRowUp(true);
                    } else {
                        obj.setRowDown(false);
                    }
                }
            } else {
                self.table.find('[type=checkbox]').attr('checked', false);
            }

            if (!weirdSwitch) {
                self.table.fnSort([
                    [1, 'desc']
                ]);
            }

            self.showFilterLabel(filterList, customLimit);
            self.setChecked();
            // self.calcChangeNum();
        }, 17);
    }

    //自定义改价
    Table.prototype.changePrice8custom = function(checkedRow, limitPrice, type) {
        var warp = type == 1 ? $('#price_warp') : $('#mobile_price_warp');
        var baseNum = Number(warp.find('.radio:eq(0) input[type=text]').val());

        if (isValidInput(baseNum)) {
            for (var i = 0, i_end = checkedRow.length; i < i_end; i++) {
                this.rowCache[checkedRow[i][0].id].bulkPlus('custom', baseNum, null, null, limitPrice, type);
            }
            warp.removeClass('open');

            //清空自定义出价
            warp.find('.radio:eq(0) input[type=text]').val('');
        } else {
            common.lightMsg.show('自定义出价不合法，必须为0.05-99.99');
        }
    }

    //根据具体值降价
    Table.prototype.changePrice8yuanDown = function(checkedRow, limitPrice, type) {
        var warp = type == 1 ? $('#price_warp') : $('#mobile_price_warp');
        var delta = Number(warp.find('.radio:eq(2) input[type=text]').val());

        if (!isNaN(delta)) {
            for (var i = 0, i_end = checkedRow.length; i < i_end; i++) {
                var obj = this.rowCache[checkedRow[i][0].id];

                obj.fallPlus('max_price', type == 1 ?obj.maxPrice:obj.maxMobilePrice, delta, 'int', limitPrice, type);
            }
            warp.removeClass('open');
        } else {
            common.lightMsg.show('根据调价金额降价的出价不合法');
        }
    }

    //根据幅度降价
    Table.prototype.changePrice8parcentDown = function(checkedRow, limitPrice, type) {
        var warp = type == 1 ? $('#price_warp') : $('#mobile_price_warp');
        var delta = Number(warp.find('.radio:eq(3) input[type=text]').val());

        if (!isNaN(delta)) {
            for (var i = 0, i_end = checkedRow.length; i < i_end; i++) {
                var obj = this.rowCache[checkedRow[i][0].id];

                obj.fallPlus('max_price', type == 1 ?obj.maxPrice:obj.maxMobilePrice, delta, 'parcent', limitPrice, type);
            }
            warp.removeClass('open');
        } else {
            common.lightMsg.show('根据调价金额降价的幅度不合法');
        }
    }

    //根据具体值加价
    Table.prototype.changePrice8yuanUp = function(checkedRow, limitPrice, type) {
        var warp = type == 1 ? $('#price_warp') : $('#mobile_price_warp');
        var delta = Number(warp.find('.radio:eq(4) input[type=text]').val());

        if (!isNaN(delta)) {
            for (var i = 0, i_end = checkedRow.length; i < i_end; i++) {
                var obj = this.rowCache[checkedRow[i][0].id];

                obj.bulkPlus('max_price', type == 1 ?obj.maxPrice:obj.maxMobilePrice, delta, 'int', limitPrice, type);
            }
            warp.removeClass('open');
        } else {
            common.lightMsg.show('根据调价金额加价的出价不合法');
        }
    }

    //根据具体值加价
    Table.prototype.changePrice8parcentUp = function(checkedRow, limitPrice, type) {
        var warp = type == 1 ? $('#price_warp') : $('#mobile_price_warp');
        var delta = Number(warp.find('.radio:eq(5) input[type=text]').val());

        if (!isNaN(delta)) {
            for (var i = 0, i_end = checkedRow.length; i < i_end; i++) {
                var obj = this.rowCache[checkedRow[i][0].id];

                obj.bulkPlus('max_price', type == 1 ?obj.maxPrice:obj.maxMobilePrice, delta, 'parcent', limitPrice, type);
            }
            warp.removeClass('open');
        } else {
            common.lightMsg.show('根据调价金额加价的幅度不合法');
        }
    }

    //根据市场均价改价
    Table.prototype.changePrice8gPrice = function(checkedRow, limitPrice, type) {
        var warp = type == 1 ? $('#price_warp') : $('#mobile_price_warp');
        var delta = warp.find('.radio:eq(1) select').val();

        if (!$.isNumeric(delta)) {
            common.lightMsg.show('请选择出价幅度');
            return false;
        }

        for (var i = 0, i_end = checkedRow.length; i < i_end; i++) {
            var obj = this.rowCache[checkedRow[i][0].id];

            obj.bulkPlus('g_cpc', obj.data.g_cpc, (Number(delta) - 100), 'parcent', limitPrice, type);
        }
        warp.removeClass('open');
    }

    //设置checkbox选中
    Table.prototype.setChecked = function() {
        var self = this;

        this.table.find('tbody tr:not(.unsort)').each(function() {
            var inputObj = $(this).find('td.check_column input'),
                obj = self.rowCache[$(this).attr('id')];
            if (inputObj[0].checked) {
                obj.checked = true;
            } else {
                obj.checked = false;
            }
        });
        this.calcChangeNum();
    }

    //计算所有改动的数量
    Table.prototype.calcChangeNum = function() {
        var checked = 0,
            up = 0,
            down = 0,
            del = 0,
            match = 0,
            mnt = 0,
            mobileUp = 0,
            mobileDown = 0;

        for (var keywordId in this.rowCache) {
            var obj = this.rowCache[keywordId];
            if (obj.checked) {
                checked++;
            }
            if (obj.del) {
                del++;
                continue;
            }
            if (obj.up) {
                up++;
            }
            if (obj.down) {
                down++;
            }
            if (obj.mobileUp) {
                mobileUp++;
            }
            if (obj.mobileDown) {
                mobileDown++;
            }
            if (obj.match && obj.match != obj.data.match) {
                match++;
            }
            if (obj.mnt != obj.data.mnt) {
                mnt++;
            }
        }

        $('#checked_num').text(checked);
        $('#up_num').text(up);
        $('#down_num').text(down);
        $('#del_num').text(del);
        $('#match_num').text(match);
        $('#mnt_num').text(mnt);
        $('#up_mobile_num').text(mobileUp);
        $('#down_mobile_num').text(mobileDown);
    }

    //获取隐藏列
    Table.prototype.getHideColumn = function() {
        var data = [],
            obj = this.table.fnSettings().aoColumns;
        for (var i = 0, i_end = obj.length; i < i_end; i++) {
            if (!obj[i].bVisible) {
                for (var c in this.COLUM_DICT) {
                    if (this.COLUM_DICT[c] == i) {
                        data.push(c);
                    }
                }
            }
        }
        return data;
    }

    //设置隐藏列
    Table.prototype.setHideCloumn = function(hideColumn) {
        var obj = this.table.fnSettings().aoColumns;

        for (var i = 1, i_end = obj.length; i < i_end; i++) {
            if (hideColumn.indexOf(i) != -1) {
                this.table.fnSetColumnVis(i, false);
            }

            if (!obj[i].bVisible && hideColumn.indexOf(i) == -1) {
                this.table.fnSetColumnVis(i, true);
            }
        }

        this.fixTableWidth();
        this.startWeirdClass();
    }

    //删除行
    Table.prototype.delete_row = function(keywordId) {
        this.table.fnDeleteRow(this.table.fnGetPosition(this.rowCache[keywordId].nRow))
        delete this.rowCache[keywordId];
    }

    //修改行
    Table.prototype.update_row = function(keywordId) {
        var row = this.rowCache[keywordId];
        var new_price = Number(row.newPriceInput.val());
        var mobile_new_price = Number(row.newMobilePriceInput.val());

        // dom更新、data更新
        row.data.match = row.match;
        row.data.mnt = row.mnt;

        if(row.maxPrice!=new_price){
            row.maxPrice = new_price;
            row.data.max_price = new_price;
        }
        $('#' + keywordId).find('.max_price').html('<span class="hide">'+new_price.toFixed(2)+'</span>'+new_price.toFixed(2));
        if(row.maxMobilePrice!=mobile_new_price){
            row.maxMobilePrice=mobile_new_price;
            row.data.max_mobile_price = mobile_new_price;
        }
        $('#' + keywordId).find('.max_mobile_price').html('<span class="hide">'+mobile_new_price.toFixed(2)+'</span>'+mobile_new_price.toFixed(2));
        row.updateStyle();
    }

    //关键词分类
    Table.prototype.startWeirdClass = function() {
        if (!this.table || !weirdSwitch) {
            return
        }

        //删除上次的分类
        this.table.find('tbody>tr.weird').remove();

        for (var c in this.options.classDict) {
            var trObj = $('tr[' + this.options.classBase + '= ' + c + ']', this.table);
            trObj.first().before('<tr class="noSearch weird unsort" style="background-color: aliceblue;"> <td class="all"><input class="kid_box" type="checkbox" rule="' + c + '"> </td> <td colspan="' + (this.table.find('th').length - 2) + '" class="tl b poi" rule="' + c + '"><span class="iconfont">&#xe603;</span>' + this.options.classDict[c][2] + '<span>(' + trObj.length + '个)</span> </td> </tr>');
        }

        this.bingWeirdChecked();
        this.toggleWeird();
        this.checkCallback();
        weirdSwitch = true;
    }

    //关闭关键词分类
    Table.prototype.closeWeirdClass = function() {
        $('#weird_switch').removeClass('on');
        $('#select_class').trigger('choose.data-select', ['0']);
        // this.startSort();
        this.table.find('tbody>tr.weird').remove();
        this.table.find('tbody>tr').removeClass('hidden');
        this.checkCallback();
        weirdSwitch = false;
    }


    //分类的复选框事件绑定
    Table.prototype.bingWeirdChecked = function() {
        var self = this;

        this.table.find('tr.weird .all').on('click', function(e) {

            var input = $(this).find('input'),
                labelCode = input.attr('rule');

            self.table.find('tr[' + self.options.classBase + '=' + labelCode + ']>td>input[type=checkbox]').each(function() {
                this.checked = input[0].checked;
            });

            self.checkCallback();
            e.stopPropagation();
        });
    }

    //显示隐藏分类
    Table.prototype.toggleWeird = function() {
        var self = this;
        this.table.find('tr.weird .poi').on('click', function() {
            var labelCode = $(this).attr('rule'),
                objs = self.table.find('tr[' + self.options.classBase + '="' + labelCode + '"]').toggleClass('hidden');
            if (objs.first().hasClass('hidden')) {
                $(this).find('.iconfont').html('&#xe630;');
            } else {
                $(this).find('.iconfont').html('&#xe603;');
            }
        });
    }

    //关键词搜索
    Table.prototype.searchWordAndSort = function(searchWord) {
        var self = this,
            hasMatch = false;

        for (var keywordId in this.rowCache) {
            var obj = this.rowCache[keywordId],
                word = $.trim($(obj.nRow).find('.word').text());

            if(search_type){
                if (word == searchWord) {
                    obj.setRowUp(true);
                    hasMatch = true;
                } else {
                    obj.setRowDown(false);
                }
            }else{
                if (word.indexOf(searchWord) != -1) {
                    obj.setRowUp(true);
                    hasMatch = true;
                } else {
                    obj.setRowDown(false);
                }
            }

        }

        if (!hasMatch) {
            common.lightMsg.show('没有符合条件的关键词');
        }

        if (weirdSwitch) {
            self.closeWeirdClass();
        }

        this.table.fnSort([
            [1, 'desc']
        ]);
        this.setChecked();
    }

    Table.prototype.generateCsvData = function(data) {
        var title = ["关键词",
                "PC当前出价",
                "移动当前出价",
                "养词天数",
                "展现量",
                "点击量",
                "点击率",
                "总花费",
                "平均点击花费",
                "千次点击花费",
                "昨日平均排名",
                "收藏量",
                "店铺收藏量",
                "宝贝收藏量",
                "收藏率",
                "收藏成本",
                "购物车总数",
                "成交量",
                "直接成交量",
                "间接成交量",
                "成交额",
                "直接成交额",
                "间接成交额",
                "转化率",
                "投资回报",
                "全网展现指数",
                "全网点击指数",
                "全网点击率",
                "全网点转化率",
                "全网点ROI",
                "全网市场均价",
                "全网竞争度",
                "全网成交指数",
                "计算机质量得分",
                "移动质量得分"
            ],
            content = [
                "word",
                "max_price",
                "max_mobile_price",
                "create_days",
                "impr",
                "click",
                "ctr",
                "cost",
                "cpc",
                "cpm",
                "avgpos",
                "favcount",
                "favshopcount",
                "favitemcount",
                "favctr",
                "favpay",
                "carttotal",
                "paycount",
                "directpaycount",
                "indirectpaycount",
                "pay",
                "directpay",
                "indirectpay",
                "conv",
                "roi",
                "g_pv",
                "g_click",
                "g_ctr",
                "g_coverage",
                "g_roi",
                "g_cpc",
                "g_competition",
                "g_paycount"
            ],
            contentStr = "";

        for (var i = 0, i_end = data.length; i < i_end; i++) {
            for (var s = 0, s_end = content.length; s < s_end; s++) {
                contentStr += (data[i][content[s]] || 0) + '\t';
            }
            contentStr += (data[i]['qscore_dict']['qscore'] || 0) + '\t';
            contentStr += (data[i]['qscore_dict']['wireless_qscore'] || 0) + '\t';
            contentStr += '\n'
        }

        this.exportCsvStr = title.join('\t') + '\n' + contentStr;
    }

    Table.prototype.getCsvData = function() {
        return this.exportCsvStr;
    }

    Table.prototype.getAdgroupTitle = function() {
        return $('#adgroup_title').val();
    }

    Table.prototype.getweirdSwitch = function() {
        return weirdSwitch;
    }

    Table.prototype.setWeirdSwitch = function(flag) {
        weirdSwitch = flag;
    }

    Table.prototype.checkCallback = function() {
        var self = this,
            inputs = this.options.element.find('tbody>tr>td'),
            classList = [];

        if (weirdSwitch) {
            for (var i in this.options.classDict) {
                classList.push(i);

                var objs = self.options.element.find('tbody>tr[' + self.options.classBase + '=' + i + ']>td')

                if (objs.find('input[type=checkbox]').length == objs.find('input[type=checkbox]:checked').length) {
                    self.options.element.find('input[rule=' + i + ']').length && (self.options.element.find('input[rule=' + i + ']')[0].checked = true);
                } else {
                    self.options.element.find('input[rule=' + i + ']').length && (self.options.element.find('input[rule=' + i + ']')[0].checked = false);
                }

            }
        }

        if (inputs.find('input[type=checkbox]').length == inputs.find('input[type=checkbox]:checked').length) {
            $('.fixedHeader .all>input')[0].checked = true;
            this.options.element.find('thead .all>input')[0].checked = true;
        } else {
            $('.fixedHeader .all>input')[0].checked = false;
            this.options.element.find('thead .all>input')[0].checked = false;
        }

        setTimeout(function() {
            self.setChecked();
        }, 17);
    }

    //设置排序标志
    Table.prototype.setSortfalg = function() {
        for (var row in this.rowCache) {
            var nRow = this.rowCache[row].nRow,
                lable = nRow.getAttribute(this.options.classBase);

            nRow.setAttribute('data-weird-desc', this.options.classDict[lable][0]);
            nRow.setAttribute('data-weird-asc', this.options.classDict[lable][1]);

        }
    }

    //修复表格宽度，使得前几列一直固定宽度
    Table.prototype.fixTableWidth = function() {
        var thTotalWidth = 0,
            tableWidh = document.body.offsetWidth - 62;;

        this.options.element.find('thead>tr>th').each(function() {
            thTotalWidth += Number(this.className.match(/w(\d+)/)[1]);
        });

        if (thTotalWidth > tableWidh) {
            this.options.element.removeClass('auto-width');
        } else {
            this.options.element.addClass('auto-width');
        }
    }

    return {
        filter: filter,
        Table: Table,
        Row: Row
    }

});
