! function() {

    var inited = false;

    var robSettings;

    APP.controller('robRankCtrl', function($scope, $http, $filter, $timeout) {
        var refresh = false;
        // 添加'refresh'监听器
        $(document).on('refresh', '#rob_rank .pull-to-refresh-content', function(e) {
            refresh = true;
            inited = false;
            $scope.$emit('qnydCtl.rob_rankData', self.kw);
        });

        $scope.$on('robRankCtrl.robRankData', function(event) {

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
                if (!refresh) {
                    $.showPreloader();
                } else {
                    refresh = false;
                }

                //获取抢排名的数据
                $http.post('/qnyd/ajax/', {
                    "function": 'rob_list',
                    "start_date": startDay,
                    "end_date": endDay
                }).success(function(data) {
                    $scope.keyword_list = data.keyword_list;

                    $scope.errMsg = data.errMsg;

                    if($scope.keyword_list.length){
                        $scope.batchRobRank();
                    }else{
                        $.hidePreloader();
                    }
                });
            }

            //立即触发获取实时数据
            $scope.selectDays($scope.day);
        });

        $scope.$on('robRankCtrl.setInited', function(event) {
            inited = false;
        });

        //批量查排名
        $scope.batchRobRank = function() {
            if (!$scope.keyword_list.length) {
                return false;
            }

            var adgroupId = $scope.keyword_list[0].adgroup_id;
            keywordIdList = [];

            for (var i in $scope.keyword_list) {
                keywordIdList.push($scope.keyword_list[i].keyword_id);
            }

            $http.post('/qnyd/ajax/', {
                "function": 'batch_forecast_rt_rank',
                "adgroup_id": adgroupId,
                "keyword_list": keywordIdList
            }).success(function(data) {

                for (var i in $scope.keyword_list) {
                    $scope.keyword_list[i]['rank'] = data.data[$scope.keyword_list[i].keyword_id];
                }

                $.hidePreloader();
                $.pullToRefreshDone('.pull-to-refresh-content');
            });
        }

        $scope.setKeyword = function() {
            var self = this;
            var buttons1 = [{
                text: '请选择',
                label: true
            }, {
                text: '设置',
                bold: true,
                onClick: function() {
                    $.showPreloader();
                    $scope.$emit('qnydCtl.setRobRank', self.kw);
                }
            }, {
                text: '查看历史',
                onClick: function() {
                    $scope.$emit('qnydCtl.RobRankHistory', self.kw.keyword_id);
                }
            }, {
                text: '取消自动抢排名',
                color: 'danger',
                onClick: function() {
                    $.confirm('我要取消自动抢排名', function() {
                        $http.post('/qnyd/ajax/', {
                            "function": 'rob_cancle',
                            "keyword_id": self.kw.keyword_id
                        }).success(function(data) {
                            $.toast("操作成功");
                            $timeout(function(){
                                $scope.del(self.kw.keyword_id);
                            },0);
                             $scope.$emit('qnydCtl.cancleRobRank', self.kw.keyword_id);
                        });
                    });
                }
            }];

            var buttons2 = [{
                text: '取消',
                bg: 'danger'
            }];

            var groups = [buttons1, buttons2];
            $.actions(groups);
        }

        //删除
        $scope.del = function(keyword_id) {
            for (var index in $scope.keyword_list) {
                if (keyword_id == $scope.keyword_list[index].keyword_id) {
                    $scope.keyword_list.splice(index, 1);
                }
            }
        }

        $scope.keyword = '';

        //过滤
        $scope.search = function(keyword) {
            $scope.keyword = keyword;
        }
    });

    APP.controller('robRankSetCtl', function($scope, $http, $timeout) {

        $scope.$on('robRankSetCtl.setRobRank', function(event, kw) {


            $http.post('/qnyd/ajax/', {
                "function": 'rob_config',
                "keyword_id": kw.keyword_id,
                "login_from": 'qnyd'
            }).success(function(data) {

                $.popup('.popup_rob_rank');

                //没有数据就默认值
                if ($.isEmptyObject(data.data)) {
                    data.data = {
                        method:'auto',
                        end_time: "17:00",
                        limit: undefined,
                        nearly_success: 1,
                        platform: "pc",
                        start_time: "08:00",
                        rank_start_desc:'',
                        rank_end_desc:''
                    }

                    data.data=angular.extend({},data.data,robSettings);
                }

                $timeout(function() {
                    $scope.kw = kw;
                    $scope.max_price = kw.max_price;
                    $scope.max_mobile_price = kw.max_mobile_price;
                    $scope.wireless_qscore = kw.qscore_dict.wireless_qscore;
                    $scope.qscore = kw.qscore_dict.qscore;
                    $scope.mobile_rank = kw.rank.mobile_rank;
                    $scope.mobile_rank_desc = kw.rank.mobile_rank_desc;
                    $scope.pc_rank = kw.rank.pc_rank;
                    $scope.pc_rank_desc = kw.rank.pc_rank_desc;


                    for (var key in data.data) {
                        $scope[key] = data.data[key]
                    }

                    $scope.rank_start_desc_map = data.rank_start_desc_map;
                    $scope.rank_end_desc_map = data.rank_end_desc_map;
                    $scope.exceptTime = $scope.start_time + ' - ' + $scope.end_time;
                    if($scope.rank_start_desc&&$scope.rank_end_desc){
                        $scope.rank_pc =$scope.rank_yd = $scope.rank_start_desc + ' - ' + $scope.rank_end_desc;
                    }else{
                        $scope.rank_pc =$scope.rank_yd = '';
                    }
                    $scope.limit&&($scope.limit = ($scope.limit / 100).toFixed(2));
                    // $scope.method = 'auto';

                    $scope.initTimePicker($scope.start_time, $scope.end_time);
                    $scope.initRankPicker($scope.rank_start_desc, $scope.rank_end_desc);
                }, 0);

                $.hidePreloader();
            });
        });

        //提交
        $scope.submit = function() {
            var errMsg = "",
                start_time = $scope.exceptTime.split(' - ')[0],
                end_time = $scope.exceptTime.split(' - ')[1];

            //if (!String($scope.rank_start).match(/^([1-9]\d?|100)$/) || !String($scope.rank_end).match(/^([1-9]\d?|100)$/) || (Number($scope.rank_end) < Number($scope.rank_start))) {
            //    errMsg += '请正确填写期望排名,期望排名必须是1到100的正整数</br>';
            //}

            $scope.rank_start = $scope.rank_start_desc_map[$scope.platform][$.trim($scope['rank_'+$scope.platform].split('-')[0])];
            $scope.rank_end = $scope.rank_end_desc_map[$scope.platform][$.trim($scope['rank_'+$scope.platform].split('-')[1])];

            if ($scope.rank_start == undefined || $scope.rank_end == undefined || parseInt($scope.rank_start) > parseInt($scope.rank_end)) {
                errMsg += '请正确选择期望排名</br>';
            }

            if (!$scope.limit || isNaN($scope.limit) || (Number($scope.limit) < 0.05) || (Number($scope.limit) > 99.99)) {
                errMsg += '请正确填写最高限价,限价必须是0.05到99.99的整数</br>';
            }

            if (start_time >= end_time) {
                errMsg += '自动抢排名结束时间必须大于起始时间';
            }

            if (errMsg != "") {
                $.alert(errMsg, '错误提示');
                return false;
            }

            if ($scope.method == 'auto') {
                $http.post('/qnyd/ajax/', {
                    "function": 'auto_rob_rank',
                    "keyword_id": $scope.kw.keyword_id,
                    "exp_rank_start": $scope.rank_start,
                    "exp_rank_end": $scope.rank_end,
                    "limit_price": parseInt($scope.limit * 100 + 0.5),
                    "platform": $scope.platform,
                    "start_time": start_time,
                    "end_time": end_time,
                    "nearly_success": $scope.nearly_success
                }).success(function(data) {
                    if (data.limitError == 'nums_limit') {
                        $.alert('亲，自动抢位的关键词已达到50个上限！', '错误提示');
                        return false;
                    }

                    if (data.limitError == 'version_limit') {
                        $.alert('亲，请联系顾问修改权限！', '错误提示');
                        return false;
                    }

                    if (data.limitError == 'others') {
                        $.alert('亲，请刷新页面重试！', '错误提示');
                        return false;
                    }

                    //更新view
                    $scope.kw.exp_rank_start = $scope.rank_start;
                    $scope.kw.exp_rank_start_desc = $.trim($scope['rank_'+$scope.platform].split('-')[0]);
                    $scope.kw.exp_rank_end = $scope.rank_end;
                    $scope.kw.exp_rank_end_desc = $.trim($scope['rank_'+$scope.platform].split('-')[1]);
                    $scope.kw.limit_price = $scope.limit;
                    $scope.kw.platform = $scope.platform;
                    $scope.kw.is_locked = 1;

                    $.alert("系统将会在您指定的时间段内每30-60分钟自动为关键词抢排名");

                    $scope.$emit('qnydCtl.setInited');

                    $.closeModal('.popup_rob_rank');
                });
            }

            if ($scope.method == 'manual') {
                //手动抢排名
                $scope.$emit('qnydCtl.manualRobRank', $scope);
            }
        }

        $scope.initTimePicker = function(start_time, end_time) {
            $('.popup_rob_rank .time').picker({
                value: [start_time, "-", end_time],
                toolbarTemplate: '<header class="bar bar-nav">\
                                      <button class="button button-link pull-right close-picker">确定</button>\
                                      <h1 class="title">请选择抢排名时间</h1>\
                                  </header>',
                cols: [{
                    textAlign: 'center',
                    values: ['00:00','01:00', '02:00', '03:00', '04:00', '05:00', '06:00', '07:00', '08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00', '22:00', '23:00', '24:00']
                }, {
                    textAlign: 'center',
                    values: ['-']
                }, {
                    textAlign: 'center',
                    values: ['00:00','01:00', '02:00', '03:00', '04:00', '05:00', '06:00', '07:00', '08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00', '22:00', '23:00', '24:00']
                }]
            });
        }

        $scope.initRankPicker = function(rank_start_desc, rank_end_desc) {
            var optionsDict={
                pc:['首页左侧位置', '首页右侧第1', '首页右侧第2', '首页右侧第3', '首页(非前三)', '第2页', '第3页', '第4页', '第5页', '5页以后'],
                yd:['移动首条', '移动前三', '移动4~6条', '移动7~10条', '移动11~15条', '移动16~20条', '20条以后']
            }
            $('.popup_rob_rank [name=rank_pc]').picker({
                value: [rank_start_desc, "-", rank_end_desc],
                cssClass:'min-picker',
                toolbarTemplate: '<header class="bar bar-nav">\
                                      <button class="button button-link pull-right close-picker">确定</button>\
                                      <h1 class="title">请选择PC端期望排名</h1>\
                                  </header>',
                cols: [{
                    textAlign: 'center',
                    values: optionsDict.pc,
                }, {
                    textAlign: 'center',
                    values: ['-']
                }, {
                    textAlign: 'center',
                    values: optionsDict.pc
                }]
            });

            $('.popup_rob_rank [name=rank_mobil]').picker({
                value: [rank_start_desc, "-", rank_end_desc],
                cssClass:'min-picker',
                toolbarTemplate: '<header class="bar bar-nav">\
                                      <button class="button button-link pull-right close-picker">确定</button>\
                                      <h1 class="title">请选择移动端期望排名</h1>\
                                  </header>',
                cols: [{
                    textAlign: 'center',
                    values: optionsDict.yd,
                }, {
                    textAlign: 'center',
                    values: ['-']
                }, {
                    textAlign: 'center',
                    values: optionsDict.yd,
                }]
            });

            if (rank_start_desc === '' && rank_end_desc === '') {
                $('.popup_rob_rank [name=rank_pc]').picker('setValue', ['首页右侧第2', '-', '首页(非前三)']);
                $('.popup_rob_rank [name=rank_mobil]').picker('setValue', ['移动前三', '-', '移动4~6条']);
            }
        }
    });

    APP.controller('manualRobRankCtl', function($scope, $http, $timeout) {
        var reset;

        $scope.keyword_list = [];
        $scope.info = '';

        $scope.$on('manualRobRankCtl.manualRobRank', function(event, kw) {
            reset = false;
            $scope.keyword_list = [];
            $scope.info = '正在手动抢排名...';

            $.popup('.popup_rob_rank_manual');

            robSettings= {
                method:'manual',
                limit: parseInt(kw.limit * 100 + 0.5),
                rank_start_desc:$.trim(kw['rank_'+kw.platform].split('-')[0]),
                rank_end_desc:$.trim(kw['rank_'+kw.platform].split('-')[1]),
                nearly_success:kw.nearly_success
            };

            $('.popup_rob_rank_manual').off('opened').on('opened', function() {
                $scope.startWebSocket(kw);
            });

            $('.popup_rob_rank_manual').off('closed').on('closed', function() {
                if (reset) {
                    $scope.$emit('qnydCtl.setRobRank', kw.kw);
                }
            });
        });

        $scope.startWebSocket = function(kw) {
            var url,
                ws;

            url = 'ws://' + window.location.host + '/websocket/?keyword_id=' + kw.kw.keyword_id

            ws = new WebSocket(url);

            ws.onmessage = function(msg) {
                if (msg != '' && msg != undefined) {
                    if (msg.data == 'ready') {
                        $scope.startRobRank(kw);
                        return false;
                    }
                    var content = JSON.parse(msg.data);
                    $scope.showRobMsg(kw, content, ws);
                } else {
                    $.alert(msg,'错误提示');
                }
            };
        }

        $scope.startRobRank = function(kw) {
            //发送手动抢排名请求
            $http.post('/qnyd/ajax/', {
                "function": 'manual_rob_rank',
                "keyword_id": kw.kw.keyword_id,
                "adgroup_id": kw.kw.adgroup_id,
                "exp_rank_start": kw.rank_start,
                "exp_rank_end": kw.rank_end,
                "limit_price": parseInt(kw.limit * 100 + 0.5),
                "platform": kw.platform,
                "nearly_success": kw.nearly_success
            }).success(function(data) {

                if (data.limitError == 'others') {
                    $.alert('亲，请刷新页面重试！', '错误提示');
                    return false;
                }
            });
        }

        $scope.showRobMsg = function(kw, content, ws) {

            $timeout(function() {
                $scope.keyword_list.push({
                    rob_time: content.rob_time,
                    price: Number(content.price).toFixed(2),
                    msg: content.msg
                });

                if (content.result_flag == 'ok' || content.result_flag == 'nearly_ok') {

                    $scope.info = '执行成功';
                    ws.close();
                }

                if (content.result_flag == 'done' || content.result_flag == 'failed') {
                    $scope.info = '执行失败';
                    ws.close();
                }
            }, 0);
        }

        $scope.reset = function() {
            reset = true;
            $.closeModal('.popup_rob_rank');
        }

    });

    APP.controller('robRankHistoryCtl', function($scope, $http, $timeout) {
        $scope.info_list = [];

        $scope.$on('robRankHistoryCtl.RobRankHistory', function(event, keyword_id) {
            $scope.info_list = [];

            $.showPreloader();
            $http.post('/qnyd/ajax/', {
                "function": 'rob_record',
                "keyword_id": keyword_id
            }).success(function(data) {
                $.hidePreloader();
                $.popup('.popup_rob_rank_history');

                for (var index in data.data[keyword_id]) {
                    $scope.info_list.push(JSON.parse(data.data[keyword_id][index]));
                }
            });

            $scope.formatDate=function(dt){
                return dt.slice(5,16)
            }
        });
    });
}();
