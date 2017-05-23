!function(){

    APP.controller('myCtrl', function($scope, $http) {

        //同步数据
        $scope.sync=function(){
            $.showPreloader('正在同步，请稍后');
            //获取抢排名的数据
            $http.post('/qnyd/ajax/', {
                "function": 'sync_data'
            }).success(function(data) {
                $.hidePreloader();
                $.alert(data.msg)
            });
        }

        //联系顾问
        $scope.contact_ww=function(){
            TOP.mobile.ww.chat({
                chatNick: '派生科技',
                text: '来自千牛移动：',
                domain_code: "taobao"
            });
        }

        //意见反馈
        $scope.suggestion=function(){
            $scope.$emit('qnydCtl.suggestion');
        }

    });

    APP.controller('suggestionCtl',function($scope, $http){

        $scope.$on('suggestionCtl.suggestion', function(event) {
            $.popup('.popup_suggestion');
        });

        //提交意见
        $scope.submit=function(){

            $.showPreloader('正在提交，请稍后...');

            $http.post('/qnyd/ajax/', {
                "function": 'add_suggest',
                "suggest":$scope.suggestions
            }).success(function(data) {
                if(data.errMsg){
                    $.alert(data.errMsg);
                    return false;
                }

                $.toast("感谢您的反馈");
                $.closeModal('.popup_suggestion');
                $.hidePreloader();
            });
        }

    });

}();
