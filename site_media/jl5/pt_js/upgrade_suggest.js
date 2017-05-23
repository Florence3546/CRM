PT.namespace('UpfradeSuggest');

PT.UpfradeSuggest = function () {

    var init_dom = function () {

        // $('.btn[index]').click(function () {
        //     if ($(this).text().indexOf('立即兑换')!==-1) {
        //       PT.sendDajax({
        //       'function':'web_generate_wait_point',
        //       'discount_id':$(this).attr('index'),
        //       });
        //       return false;
        //     }
        //   return true;
        // });
        $('.point_convert').on('click',function(){
            var dis_id=$(this).attr('data-id');

            PT.confirm('您确定要兑换吗？',function(){
              PT.sendDajax({
                'function': 'web_generate_wait_point',
                'discount_id': dis_id
              });
            });

            return false;
        });
    }

    return {
        'init': function () {
            init_dom();
        }
      }
}();
