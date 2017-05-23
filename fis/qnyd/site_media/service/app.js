var APP = angular.module("qnyd", [], function($httpProvider) {
    $httpProvider.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded;charset=utf-8';
    $httpProvider.defaults.headers.post['Accept'] = 'application/json, text/javascript, */*; q=0.01';
    $httpProvider.defaults.headers.post['X-Requested-With'] = 'XMLHttpRequest';

    var param = function(obj) {
        var query = '',
            name, value, fullSubName, subName, subValue, innerObj, i;

        for (name in obj) {
            value = obj[name];

            if (value instanceof Array) {
                for (i = 0; i < value.length; ++i) {
                    subValue = value[i];
                    fullSubName = name + '[]';
                    innerObj = {};
                    innerObj[fullSubName] = subValue;
                    query += param(innerObj) + '&';
                }
            } else if (value instanceof Object) {
                for (subName in value) {
                    subValue = value[subName];
                    fullSubName = name + '[' + subName + ']';
                    innerObj = {};
                    innerObj[fullSubName] = subValue;
                    query += param(innerObj) + '&';
                }
            } else if (value !== undefined && value !== null)
                query += encodeURIComponent(name) + '=' + encodeURIComponent(value) + '&';
        }

        return query.length ? query.substr(0, query.length - 1) : query;
    };

    // Override $http service's default transformRequest
    $httpProvider.defaults.transformRequest = [function(data) {
        return angular.isObject(data) && String(data) !== '[object File]' ? param(data) : data;
    }];

}).config(['$interpolateProvider', function($interpolateProvider) {
    $interpolateProvider.startSymbol('{?');
    $interpolateProvider.endSymbol('?}');
}]);


APP.filter('formatNum',function(){
    return function(input, param){
        return Number(input).toFixed(2);
    }
});

APP.factory('arrayGroup',function(){
    return {
        group:function(arr,num){
            var newArray=[],
                sliceLength=Math.ceil(arr.length/num);

            for(var i=0,i_end=sliceLength;i<i_end;i++){
                newArray.push(arr.slice(i*num,(i+1)*num));
            }
            return newArray;
        }
    }
});

APP.controller('qnydCtl', function($scope) {
    //获取首页数据
    $scope.$on('qnydCtl.homeData', function(event) {
        $scope.$broadcast("homeCtrl.homeData");
    });

    //获取抢排名数据
    $scope.$on('qnydCtl.rob_rankData', function(event) {
        $scope.$broadcast("robRankCtrl.robRankData");
    });

    //获取核心词数据
    $scope.$on('qnydCtl.shop_coreData', function(event) {
        $scope.$broadcast("shopCoreCtrl.shopCoreData");
    });

    //重置抢排名的词，使其点击后重新获取数据
    $scope.$on('qnydCtl.setInited', function(event) {
        $scope.$broadcast("robRankCtrl.setInited");
    });

    //修改计划日限额广播
    $scope.$on('qnydCtl.editBudget', function(event, campaign) {
        $scope.$broadcast("budgetCtl.editBudget", campaign);
    });

    //设置抢排名
    $scope.$on('qnydCtl.setRobRank', function(event, keyword) {
        $scope.$broadcast("robRankSetCtl.setRobRank", keyword);
    });

    //取消抢排名
    $scope.$on('qnydCtl.cancleRobRank', function(event, keywordId) {
        $scope.$broadcast("shopCoreCtrl.cancleRobRank", keywordId);
    });

    //手动抢排名
    $scope.$on('qnydCtl.manualRobRank', function(event, keyword) {
        $scope.$broadcast("manualRobRankCtl.manualRobRank", keyword);
    });

    //抢排名历史
    $scope.$on('qnydCtl.RobRankHistory', function(event, keyword) {
        $scope.$broadcast("robRankHistoryCtl.RobRankHistory", keyword);
    });

    //核心词筛选
    $scope.$on('qnydCtl.chooseAdgroup', function(event, adgroup_list,scope) {
        $scope.$broadcast("chooseShopCoreCtl.chooseAdgroup", adgroup_list,scope);
    });

    //核心词筛选
    $scope.$on('qnydCtl.suggestion', function(event) {
        $scope.$broadcast("suggestionCtl.suggestion");
    });

    //核心词筛选
    $scope.$on('qnydCtl.getPhone', function(event) {
        $scope.$broadcast("phoneCtl.getPhone");
    });
});
