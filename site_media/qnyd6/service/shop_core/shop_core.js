! function() {

    var getAdgroupList=function(keywordList){

        var adgroups={},
            adgroupList=[];

        for(var i in keywordList){
            var keyword=keywordList[i];

            if(adgroups[keyword.adgroup_id]){
                continue;
            }
            

            adgroups[keyword.adgroup_id]={
                adgroup_id:keyword.adgroup_id,
                pic_url:keyword.pic_url,
                click:keyword.click,
                title:keyword.title,
                camp_title:keyword.camp_title,
                mnt_opt_type:keyword.mnt_opt_type
            }
        }

        for(var adg_id in adgroups){
            adgroupList.push(adgroups[adg_id]);
        }

        return adgroupList;

    }

    //自定义过滤器
    APP.filter('myFilter',function(){
        return function(input, param){
            var temp=[],
                nullInput=true;

            for(var i in input){
                for(var p in param){

                    if(nullInput && param[p].length){
                        nullInput=false;
                    }

                    if(param[p] && input[i].hasOwnProperty(p) && $.inArray(input[i][p],param[p])!=-1){
                        temp.push(input[i]);
                    }
                }
            }

            if(nullInput){
                return input;
            }

            return temp;
        }
    });


    APP.controller('shopCoreCtrl', function($scope, $http, $filter, $timeout) {
        var inited = false,
            LIMIT_PRICE = 5,
            searchFilter = $filter('filter'),
            adgroupFilter = $filter('myFilter');

        $scope.changeNum = 0;
        $scope.mobileChangeNum=0;
        $scope.limitNum = 0;
        $scope.mobileLimitNum = 0;
        $scope.adgroupIdList=[];

        $scope.$on('shopCoreCtrl.shopCoreData', function(event) {

            if (inited) {
                return false;
            }

            inited = true;

            var dateFilter = $filter('date');

            if ($scope.day == undefined) {
                $scope.day = '0';
            }

            $scope.selectDays = function(day) {
                var endDay= dateFilter(new Date(), 'yyyy-MM-dd'),
                    startDay = dateFilter(new Date() - 1000 * 24 * 60 * 60 * Number(day), 'yyyy-MM-dd');

                $scope.day = day;

                num = 0;
                $.showPreloader();


                //查询核心词计算状态
                $http.post('/qnyd/ajax/', {
                    "function": 'calc_shop_core'
                }).success(function(data) {
                    if(data.condition=="doing"){
                        $.hidePreloader();
                        $scope.keyword_list=[];
                        $scope.errMsg="正在分析核心词，请稍后再来查看或手动刷新该页面（第一次使用时需要下载大量数据，平均每100个宝贝约需要等待6分钟）"
                    }

                    if(data.condition=="ok"){
                        //获取抢排名的数据
                        $http.post('/qnyd/ajax/', {
                            "function": 'shop_core_list',
                            "start_date": startDay,
                            "end_date": endDay
                        }).success(function(data) {
                            for (var i in data.keyword_list) {
                                data.keyword_list[i].custum_price=data.keyword_list[i].max_price;
                                data.keyword_list[i].custum_mobiles_price=data.keyword_list[i].max_mobile_price;
                            }

                            $scope.keyword_list = data.keyword_list;

                            $scope.errMsg = data.msg;

                            $scope.$emit('qnydCtl.chooseAdgroup', getAdgroupList($scope.keyword_list),$scope);

                            $.hidePreloader();
                        });
                    }
                });
            }

            //立即触发获取实时数据
            $scope.selectDays($scope.day);

        });

        //取消自动抢排名
        $scope.$on('shopCoreCtrl.cancleRobRank',function(event,keyword_id){
            for (var i in $scope.keyword_list){
                if($scope.keyword_list[i].keyword_id==keyword_id){
                    $scope.keyword_list[i].is_locked=0;
                    break;
                }
            }
        });

        $scope.chooseShopCore = function() {
            $.popup('.popup_choose_shop_core');
        }

        $scope.cancleShopCore = function() {
            $scope.adgroupIdList=[];
        }

        $scope.inputBlur = function(price,type) {
            if (isNaN(price) || Number(price) < 0.05 || Number(price) > 99.99) {
                1&type&&(this.kw.custum_price = this.kw.max_price);
                2&type&&(this.kw.custum_mobiles_price = this.kw.max_mobile_price);
            }

            1&type&&(this.kw.custum_price = Number(this.kw.custum_price).toFixed(2));
            2&type&&(this.kw.custum_mobiles_price = Number(this.kw.custum_mobiles_price).toFixed(2));

            $scope.updateStyle.apply(this.kw,[type]);
            $scope.calcChangeNum();
        }

        //更新样式
        $scope.updateStyle = function(type) {

            if(1&type){
                this.up = this.down = this.limit= false;
                if (Number(this.custum_price) > this.max_price) {
                    this.up = true;
                }

                if (Number(this.custum_price) < this.max_price) {
                    this.down = true;
                }

                if (Number(this.custum_price) > LIMIT_PRICE) {
                    this.limit = true;
                }
            }

            if(2&type){
                this.mobileUp = this.mobileDown = this.mobileLimit = false;
                if (Number(this.custum_mobiles_price) > this.max_mobile_price) {
                    this.mobileUp = true;
                }

                if (Number(this.custum_mobiles_price) < this.max_mobile_price) {
                    this.mobileDown = true;
                }

                if (Number(this.custum_mobiles_price) > LIMIT_PRICE) {
                    this.mobileLimit = true;
                }
            }
        }

        //计算改变的个数
        $scope.calcChangeNum = function() {
            var num = 0,
                mobileNum=0,
                limitNum=0,
                mobileLimitNum=0,
                keywordList=$scope.getKeywordList();

            for (var i in keywordList) {
                var keyword = keywordList[i];
                if (Number(keyword.custum_price) != keyword.max_price) {
                    num++;
                    if (Number(keyword.custum_price) > LIMIT_PRICE) {
                        limitNum++;
                    }
                }

                if (Number(keyword.custum_mobiles_price) != keyword.max_mobile_price) {
                    mobileNum++;
                    if(Number(keyword.custum_mobiles_price) > LIMIT_PRICE){
                        mobileLimitNum++;
                    }
                }

            }
            $scope.changeNum = num;
            $scope.mobileChangeNum = mobileNum;
            $scope.limitNum = limitNum;
            $scope.mobileLimitNum = mobileLimitNum;
        };

        //提交到直通车
        $scope.commit = function() {
            var msg;

            if ($scope.changeNum||$scope.mobileChangeNum) {
                msg = '您有PC:' + $scope.changeNum + '个,移动:'+$scope.mobileChangeNum+'个关键词做了改变';

                if ($scope.limitNum||$scope.mobileLimitNum) {
                    msg+=',其中';
                    if($scope.limitNum){
                        msg += 'PC:'+$scope.limitNum+'个';
                    }

                    if($scope.mobileLimitNum){
                        msg += ',移动:'+$scope.mobileLimitNum+'个';
                    }

                    msg += '超过了' + LIMIT_PRICE + '元';
                }


                msg += ',确定提交吗？'

                $.confirm(msg, '确认提交', function() {
                    var submitKeywordList = [],
                        keywordList=$scope.getKeywordList();

                    for (var i in keywordList) {
                        var keyword = keywordList[i];
                        if (Number(keyword.custum_price) != keyword.max_price||Number(keyword.custum_mobiles_price) != keyword.max_mobile_price) {
                            submitKeywordList.push({
                                'keyword_id': keyword.keyword_id,
                                'adgroup_id': keyword.adgroup_id,
                                'campaign_id': keyword.campaign_id,
                                'word': keyword.word,
                                'new_price': keyword.custum_price,
                                'max_price': keyword.max_price,
                                'match_scope': keyword.match_scope,
                                'max_mobile_price': keyword.custum_mobiles_price,
                                'mobile_old_price': keyword.max_mobile_price,
                                'mobile_is_default_price':0,
                                'is_del': false
                            });
                        }
                    }

                    $http.post('/qnyd/ajax/', {
                        "function": 'submit_keyword',
                        "submit_list": JSON.stringify(submitKeywordList),
                        "update_mnt_list":"[]",
                        "optm_type":0
                    }).success(function(data) {
                        var update_count = data.update_kw.length,
                            failed_count = data.failed_kw.lengthh;

                        var msg = '修改成功:' + update_count + '个';


                        if (failed_count) {
                            msg += '操作失败:' + failed_count + '个';
                        }

                        for (var u in data.update_kw){
                            for (var s in keywordList) {
                                if(data.update_kw[u]==keywordList[s].keyword_id){
                                    keywordList[s].max_price=keywordList[s].custum_price;
                                    keywordList[s].max_mobile_price=keywordList[s].custum_mobiles_price;
                                    $scope.updateStyle.apply(keywordList[s],[3]);
                                    continue;
                                }
                            }
                        }

                        $scope.calcChangeNum();

                        $.alert(msg);
                    });

                });

            } else {
                $.toast("没有关键词改变");
            }
        }

        $scope.getKeywordList=function(){
            return adgroupFilter(searchFilter($scope.keyword_list,{word:$scope.keyword}),{adgroup_id:$scope.adgroupIdList});
        }

        //过滤
        $scope.search=function(keyword){
            $scope.keyword=keyword;
            $scope.calcChangeNum();
        }

        //抢排名
        $scope.rob_rank=function(){
            $.showPreloader();
            var self=this;
            $http.post('/qnyd/ajax/', {
                "function": 'forecast_rt_rank',
                "keyword_id": this.kw.keyword_id,
                "adgroup_id": this.kw.adgroup_id
            }).success(function(data) {
                self.kw.pc_rank=data.data.pc_rank;
                self.kw.pc_rank_desc=data.data.pc_rank_desc;
                self.kw.mobile_rank=data.data.mobile_rank;
                self.kw.mobile_rank_desc=data.data.mobile_rank_desc;

                self.kw.rank={
                    pc_rank:data.data.pc_rank,
                    pc_rank_desc:data.data.pc_rank_desc,
                    mobile_rank:data.data.mobile_rank,
                    mobile_rank_desc:data.data.mobile_rank_desc
                }
                $scope.$emit('qnydCtl.setRobRank', self.kw);
            });
        }
    });

    APP.controller('chooseShopCoreCtl',function($scope,arrayGroup){

        $scope.$on('chooseShopCoreCtl.chooseAdgroup', function(event,adgroupList,scope) {
            if(adgroupList.length){
                $scope.adgroup_list = adgroupList;
                $scope.scope=scope;
            }else{
                $.toast("暂时没有数据");
            }
        });

        $scope.filter=function(){
            var filterAdg=[];
                for(var i in $scope.adgroup_list){
                    if($scope.adgroup_list[i].check){
                        filterAdg.push($scope.adgroup_list[i].adgroup_id);
                    };
                }
            // }
            $scope.scope.adgroupIdList=filterAdg;
            $scope.scope.calcChangeNum();
            $.closeModal('.popup_choose_shop_core');
        }
    });

}();
