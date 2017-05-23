! function() {
    var inited = false;

    var get_series_4list = function(data) {
        var series_list = [];
        for (var i = 0; i < data.length; i++) {
            series_list.push({
                'name': data[i].name,
                'color': data[i].color,
                'data': data[i].value_list
            });
        }
        return series_list;
    }

    var drawChart = function(id, category_list, series_cfg_list) {
        if (!$('#' + id).length) {
            return;
        }

        lalal = new Highcharts.Chart({
            chart: {
                renderTo: id,
                type: 'spline'
            },
            title: null,
            credits: {
                text: null,
            },
            xAxis: {
                gridLineColor: '#ddd',
                gridLineDashStyle: 'Dash',
                gridLineWidth: 1,
                tickPosition: 'inside',
                tickmarkPlacement: 'on',
                labels: {
                    rotation: 30 //45度倾斜
                },
                categories: category_list
            },
            yAxis: {
                gridLineColor: '#ddd',
                gridLineDashStyle: 'Dash',
                min: 0,
                title: null
            },
            tooltip: {
                formatter: function() {
                    var obj_list = lalal.series;
                    var result = this.x + '日 ' + "<br/>";
                    for (var i = 0; i < obj_list.length; i++) {
                        if (obj_list[i].visible) {
                            result = result + (obj_list[i].name) + " " + obj_list[i].data[this.point.x].y + (series_cfg_list[i].unit) + "<br/>"
                        }
                    }
                    return result;
                }
            },
            series: get_series_4list(series_cfg_list),
            legend: {
                verticalAlign: 'top',
                borderWidth: 0
            }
        });
    }

    APP.controller('homeCtrl', function($scope, $http, $filter) {

        $scope.balance = '--';

        $scope.$on('homeCtrl.homeData', function(event) {

            if (inited) {
                return false;
            }

            inited = true;

            var num;
            dateFilter = $filter('date');

            $scope.day = '0';

            var hidePreloader = function() {
                num++;
                if (num == 2) {
                    $.hidePreloader();
                }
            }

            $scope.selectDays = function(day) {
                var endDay= dateFilter(new Date(), 'yyyy-MM-dd'),
                    startDay = dateFilter(new Date() - 1000 * 24 * 60 * 60 * Number(day), 'yyyy-MM-dd');

                num = 0;
                $.showPreloader();

                //获取账户数据
                $http.post('/qnyd/ajax/', {
                    "function": 'account',
                    "start_date": startDay,
                    "end_date": endDay
                }).success(function(data) {
                    for (var d in data.account_data_dict) {
                        $scope[d] = data.account_data_dict[d];
                    }
                    hidePreloader();
                });

                //获取曲线图数据
                $http.post('/qnyd/ajax/', {
                    "function": 'show_chart',
                    "start_date": startDay,
                    "end_date": endDay
                }).success(function(data) {
                    var series_list = [],
                        series_fields = ['cost', 'pay', 'click', 'roi'];

                    for (var i in data.chart_data.series_cfg_list) {
                        var series_item = data.chart_data.series_cfg_list[i];
                        if (series_fields.indexOf(series_item.field_name) != -1) {
                            series_list.push(series_item);
                        }
                    }
                    drawChart('account_chart', data.chart_data.category_list, series_list);
                    hidePreloader();
                });

                //获取推广计划
                $http.post('/qnyd/ajax/', {
                    "function": 'campaign_list',
                    "start_date": startDay,
                    "end_date": endDay
                }).success(function(data) {
                    $scope.campaign_list = data.json_campaign_list;
                    hidePreloader();
                });
            }

            //获取账户数据
            $http.post('/qnyd/ajax/', {
                "function": 'balance'
            }).success(function(data) {
                if (data.errMsg == '') {
                    $scope.balance = data.balance;
                } else {
                    $.alert(data.errMsg);
                }
            });

            //立即触发获取实时数据
            $scope.selectDays(0);

            //判断用户是否需要填写手机号
            $scope.$emit("qnydCtl.getPhone");
        });

        $scope.editCampaign = function() {
            var self = this;
            var buttons1 = [{
                text: '请选择',
                label: true
            }, {
                text: '修改日限额',
                bold: true,
                onClick: function() {
                    $scope.$emit("qnydCtl.editBudget", self.camp);
                }
            }, {
                text: '参与推广',
                onClick: function() {
                    $.confirm('您确定要参与推广吗？', function() {
                        $http.post('/qnyd/ajax/', {
                            "function": 'set_online_status',
                            "mode": 1,
                            "camp_id_list": [self.camp.campaign_id]
                        }).success(function(data) {
                            if (data.errMsg == '') {
                                self.camp.online_status = 'online';
                                $.toast("操作成功");
                            } else {
                                $.alert(data.errMsg);
                            }
                        });
                    });
                }
            }, {
                text: '暂停推广',
                color: 'danger',
                onClick: function() {
                    $.confirm('您确定要暂停推广吗？', function() {
                        $http.post('/qnyd/ajax/', {
                            "function": 'set_online_status',
                            "mode": 0,
                            "camp_id_list": [self.camp.campaign_id]
                        }).success(function(data) {
                            if (data.errMsg == '') {
                                self.camp.online_status = 'offline';
                                $.toast("操作成功");
                            } else {
                                $.alert(data.errMsg);
                            }
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
    });

    APP.controller('budgetCtl', function($scope, $http, $timeout) {

        $scope.$on('budgetCtl.editBudget', function(event, camp) {

            $.popup('.popup_edit_budget');

            //使得angular知道页面做了修改，需要立即刷新数据
            $timeout(function() {
                $scope.budget = camp.budget;
                $scope.is_smooth = camp.is_smooth;


                if ($scope.budget == '20000000') {
                    $scope.is_limit = 1;
                    $scope.newBudget = 50;
                } else {
                    $scope.is_limit = 0;
                    $scope.newBudget = camp.budget;
                }

                $scope.submit = function() {
                    var tempBudget;

                    if (Number($scope.is_limit)) {
                        tempBudget = '20000000';
                    } else {
                        tempBudget = Number($scope.newBudget);

                        if (tempBudget > 99999 || tempBudget < 30) {
                            $.alert('日限额的范围为30~99999');
                            return false;
                        }
                    }

                    $http.post('/qnyd/ajax/', {
                        "function": 'set_budget',
                        "budget": tempBudget,
                        "camp_id": camp.campaign_id,
                        "use_smooth": ($scope.is_smooth == 0) ? false : true
                    }).success(function(data) {
                        if (data.errMsg == '') {
                            camp.budget = tempBudget;
                            camp.is_smooth = $scope.is_smooth;
                            $.toast("操作成功");
                        } else {
                            $.alert(data.errMsg);
                        }
                        $.closeModal('.popup_edit_budget')
                    });
                }
            }, 0);
        });

    });

    APP.controller('phoneCtl', function($scope, $http) {

        $scope.$on('phoneCtl.getPhone', function(event) {
            if ($scope.isneed_phone) {
                //$.popup('.popup_phone');
            }
        });

        $scope.submit = function() {

            if (isNaN($scope.phone) || !(/^1[3|4|5|7|8]\d{9}$/.test($scope.phone))) {
                $.alert("手机号码填写不正确！");
                return false;
            }

            $http.post('/qnyd/ajax/', {
                "function": 'submit_userinfo',
                "phone": $scope.phone,
                "qq": $scope.qq
            }).success(function(data) {
                if (data.errMsg) {
                    $.alert(data.errMsg);
                    return false;
                }

                $.toast("感谢您的支持");
                $.closeModal('.popup_phone');
            });
        }
    });
}();
