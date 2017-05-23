PT.namespace('Camp_history');
PT.Camp_history=function(){
  var init_data={
    'sEcho':'',
    'sSearch':'',
    'iDisplayLength':200,
    'iDisplayStart':0
  }
  return {
    init_data:init_data,
    append_table_data:function(page_info,result_list){
      var dom='';
      for (r in result_list){
        dom+=template.render('history_table_tr',result_list[r]);
      }
      $('#history_table_tbody').html(dom);
      $.alert({
        title:'历史记录',
        width:'large',
        body:$('#camp_history_table_box').html()
      });
    }
  }

}();


PT.namespace('Campaign_list');
PT.Campaign_list = function () {
    var checked_count = 0;
    var init_sort=function(){
        PT.campaign_table=$('#campaign_table').dataTable({
            //"bRetrieve": true, 允许重新初始化表格
            "bPaginate": false,
            "bFilter": false,
            "bInfo": false,
            "aaSorting":[[6,'asc'],[5,'desc'],[3,'desc']],
            "oLanguage": {
                "sZeroRecords": "亲，您还没有开启推广计划"
            },
            "aoColumns": [{"bSortable": false},{"bSortable": false},{"bSortable": true,"sSortDataType": "dom-text", "sType": "numeric"},{"bSortable": true,"sSortDataType": "dom-text", "sType": "numeric"},{"bSortable": true,"sSortDataType": "dom-text", "sType": "numeric"},{"bSortable": true,"sSortDataType": "dom-text", "sType": "numeric"},{"bSortable":  true,"sSortDataType": "dom-text", "sType": "numeric"},{"bSortable":  true,"sSortDataType": "dom-text", "sType": "numeric"}]
        });
    }

    var init_dom=function () {
        //启用、暂停、新建计划
        $('#camp_control .camp').click(function(){
            var camp_id_arr=[],
                oper=parseInt($(this).attr('oper')),
                obj=$('#campaign_table tbody input:checked');
            obj.each(function(){
                camp_id_arr.push(parseInt($(this).val()));
            });
            if (oper==-1) {
                PT.Base.goto_ztc(1,0,0,'');
            } else if (checked_count) {
                if (oper==0){
                    PT.confirm('确定要暂停选中的'+checked_count+'个计划吗？',set_update_camps,[oper,camp_id_arr]);
                }else if(oper==1){
                    set_update_camps(oper,camp_id_arr);
                }
            }else{
                PT.alert('请至少选择一个计划');
            }
        });

//      $("#camp_history").fancybox({
//          minWidth    : '66%',
//          fitToView   : false,
//          width       : '80%',
//          height      : '80%',
//          autoSize    : false,
//          closeClick  : false,
//      });

        $('#camp_history').click(function(){
          PT.show_loading('正在获取数据');
          PT.sendDajax({
            function:'web_get_camp_history',
            page_info:$.toJSON(PT.Camp_history.init_data)
          });
        });
    }

    var init_help=function(){
        var help_list=([
            {
                element:'#campaign_table td:eq(1)',
                content:'1/2 点铅笔可编辑标题,点击图表可以查看趋势',
                placement:'right'
            },
            {
                element: "#campaign_table td:eq(2)",
                content: "2/2 这里点铅笔是修改计划限额",
                placement:'top'
            }
        ]);
        PT.help(help_list);
    }


    //发送请求获取数据
    var get_date=function (){
        PT.show_loading('正在获取数据');
        PT.sendDajax({'function':'web_get_campaign_list','last_day':1});
    }

    var update_checked_count=function() {
        checked_count = $('input[class*="kid_box"]:checked').length;
        $('#checked_count').text(checked_count);
    }

    var set_update_camps=function(oper,camp_id_arr) {
        PT.sendDajax({'function':'web_update_camps_status','camp_id_list':camp_id_arr,'mode':oper,'name_space':'Campaign_list'});
    }

    //给修改计划日限额的弹窗弹中的"确定"和"取消"加上关闭弹窗件
    var budget_popover_after=function (){
        App.initTooltips();
        budget_popover_set(this);

//      $('#budget_submit').click(function(){
//          if(modify_camp_budget(e)){
//              $(e.target).popover('hide');
//          }
//      });

//      $('#budget_cancel').click(function(){
//          $(e.target).popover('hide');
//      });

        //控制日限额显示，当选中不限时隐藏下面的框
        $('#edit_budget_box').find('input[name="budget_radio"]').click(function(){
            if($(this).val()=='1'){
                $('#put_setting').show();
                $('#budget_value').attr('disabled',false);
            }else{
                $('#put_setting').hide();
                $('#budget_value').attr('disabled',true);
            }
        });
    }

    //页面显示时设置弹出层显示状态是不限制日限额还是已设置
    var budget_popover_set=function (iDom){
        var budget=parseInt($(iDom).prev().text());
        if(!isNaN(budget)){
            var smooth=parseInt($(iDom).parent().find('[id^="is_smooth"]').val());
            $('#set_budget').attr('checked',true);
            $('#budget_value').val(budget);
            $('#put_setting').find('[name="smooth_radio"]').eq(smooth).attr('checked',true);
        }else{
            $('#noset_budget').attr('checked',true);
            $('#put_setting').hide();
            $('#budget_value').attr('disabled',true);
        }
    }

    var modify_camp_budget=function (){
        var budget,
            use_smooth=true,
            camp_id=$(this).parent().parent().parent().find('td:first input').val(),
            is_set_budget=parseInt($('input[name="budget_radio"]:checked').val());
        //判断是否设置日限额
        if(is_set_budget){
            budget=$('#budget_value').val();
            use_smooth=$('#put_setting').find('[name="smooth_radio"]').eq(1).attr('checked')=='checked';
            if(!check_budget(budget)){
                return false;
            }
        }else{
            budget=20000000;
        }
        PT.show_loading('正在修改计划日限额');
        PT.sendDajax({
            'function':'web_modify_camp_budget',
            'camp_id':camp_id,
            'budget':parseInt(budget,10),
            'use_smooth':use_smooth
        });
        return true;
    }

    var check_budget=function (budget){
        var re=/^[1-9]+[0-9]*]*$/ ;
        if(budget==''){
            PT.alert('日限额不能为空');
            return false;
        }
        if(parseInt(budget)>=100000){
            PT.alert('<div style="text-indent:2em">日限额不能超过10万元 ! </div></br><div style="text-indent:2em">因为淘宝只允许第三方软件修改日限额最大为10万，如果您确定要修改为'+budget+'元，请到直通车后台修改</div>');
            return false;
        }
        if(parseInt(budget)<30){
            PT.alert('日限额不能低于30元');
            return false;
        }
        if(!re.test(budget)){
            PT.alert('日限额只能为整数');
            return false;
        }
        return true;
    }

/*  //修改标题弹出层显示前调用
    var title_popover_before=function (e){
        $('#campaign_table .edit_title').not($(e.target)).popover('hide');
    }*/

    //修改标题弹出层显示后调用
    var title_popover_after=function (){

        title_popover_set(this);

//      //确定按钮
//      $(e.target).next().find('button:first').click(function(){
//          if(modify_camp_title(e)){
//              $(e.target).popover('hide');
//          }
//      });
//
//      //取消按钮
//      $(e.target).next().find('button:eq(1)').click(function(){
//          $(e.target).popover('hide');
//      });
    }

    //设置弹出默认计划名称
    var title_popover_set=function (obj){
        $('#edit_title_input').val($(obj).prev().text());
    }

    //设置计划标题
    var modify_camp_title=function (){
        var old_title=$(this).prev().text(),
            new_title=$('#edit_title_input').val(),
            camp_id=$(this).parent().prev().find('input').val();
        if(check_camp_title(old_title,new_title,this)){
            PT.show_loading('正在修改计划名称');
            PT.sendDajax({
                'function':'web_modify_camp_title',
                'camp_id':camp_id,
                'new_title':new_title
                });
            return true;
        }else{
            return false;
        }
    }

    //检测输入标题是否合法
    var check_camp_title=function (old_title,new_title,obj){
        if($.trim(new_title)==''){
            PT.alert('标题不能为空');
            return false;
        }
        if(old_title==new_title){
            $.alert({
              backdrop:false,
              body:'标题没有修改过哦！'
            })
            return false;
        }
        return true;
    }

    //用于ajax调用之后初始化dom元素,避免使用live方法
    var ajax_init_dom=function (){

        var edit_budget_temp=$('#edit_budget_temp').html()
            ,budget_popover_temp=$('#budget_popover_temp').html()
            ,title_popover_temp=$('#title_popover_temp').html();

//      $('.edit_btn').popover({
//          'trigger':'click',
//          'title':'修改计划日限额',
//          'content':edit_budget_temp,
//          'html':true,
//          'placement':'bottom',
//          'fnAfterShow':budget_popover_after,
//          'template':budget_popover_temp,
//          'multi':true    //同屏只显示一个
//      });

        $('.edit_btn').click(function(){
          var that=this;
          $.confirm({
            backdrop: 'static',
            bgColor: '#000',
            title:'修改计划日限额',
            body:edit_budget_temp,
            show:$.proxy(budget_popover_after,that),
            okHide:$.proxy(modify_camp_budget,that)
          })

        });

        //App.initUniform(); //重绘Ajax新生成的form元素

//      $('.edit_title').popover({
//          'trigger':'click',
//          'html':true,
//          'placement':'bottom',
//          'title':'修改计划标题（不超过20个汉字）',
//          'content':title_popover_temp,
//          'fnAfterShow':title_popover_after,
//          'multi':true   //同屏只显示一个
//      });

        $('.edit_title').click(function(){
          var that=this;
          $.confirm({
            backdrop: 'static',
            width:'small',
            bgColor: '#000',
            title:'修改计划标题（不超过20个汉字）',
            body:title_popover_temp,
            show:$.proxy(title_popover_after,that),
            shown:function(){$(this).html()},
            okHide:$.proxy(modify_camp_title,that)
          })

        });

        $('.show_trend_chart').click(function(){
            var camp_id=$(this).parents('td').prev().find('input').val();
            PT.sendDajax({'function':'web_show_camp_trend','camp_id':camp_id});
        });

        // 复选框事件
        $('.father_box').click(function(){
            var area_id=$(this).attr('link'),
                kid_box=$('#'+area_id).find('input[class*="kid_box"]'),
                now_check=this.checked;
            kid_box.each(function(){
                if (this.checked!=now_check) {
                    this.checked=now_check;
                    $(this).parent().toggleClass('check_box_color');
                }
            });
            update_checked_count();
        });

        // $('input[class*="kid_box"]').click(function(){
        //     update_checked_count();
        //     $(this).parent().toggleClass('check_box_color');
        // });

        $('input[class*="kid_box"]').click(function(){
            update_checked_count();
            $(this).parent().toggleClass('check_box_color');

            var all_num = $('input[class*="kid_box"]').length;
            var checked_num = $('input[class*="kid_box"]:checked').length;
            if(all_num == checked_num)
                $('.father_box').attr("checked", true);
            else
                $('.father_box').attr("checked", false);
        });

    }

    return {

        //main function to initiate the module
        init: function (){
            PT.initDashboardDaterange();
            PT.Base.set_nav_activ(2,0);
            get_date();
            init_dom();
        },
        append_table_data:function(data){
            var tr_str='',table=$('#campaign_table'),total_camp_count;
            for (d in data){
                if(!isNaN(d)){
                    tr_str+=template.render('campaign_tr',data[d]);
                }
            }
            total_camp_count=data.length;
            PT.hide_loading();
            if(PT.hasOwnProperty('campaign_table')){
                PT.campaign_table.fnDestroy(); //删除datetable
            }
            table.find('tbody tr').remove();
            table.find('tbody').append(tr_str);
            //table.show();
            init_sort();
            $('#total_camp_count').text(total_camp_count);
            ajax_init_dom();
            App.initTooltips();
            init_help();
        },
        select_call_back:function(value){
            PT.sendDajax({'function':'web_get_campaign_list','last_day':value});
        },
        modify_title_call_back:function(result){
            PT.hide_loading();
            if(result.status){
//              PT.light_msg('修改计划名称','修改成功！');
                $('#title_'+result.camp_id).text(result.new_title);
            }else{
                PT.alert(result.err);
            }
        },
        modify_budget_call_back:function(result){
            PT.hide_loading();
            if(result.status){
//              PT.light_msg('修改日限额','修改成功！');
                var budget_hide=$('#budget_value_hide_'+result.camp_id);
                var budget_show=$('#budget_value_show_'+result.camp_id);
                if(result.budget<20000000){
                    budget_hide.text(result.budget);
                    budget_show.text(result.budget).prev().show();
                }else{
                    budget_hide.text(result.budget);
                    budget_show.text('不限').prev().hide();
                }

                $("#is_smooth_"+result.camp_id).val(result.use_smooth=='true'?1:0);

                PT.campaign_table.fnDestroy();//日限额改变后重新加载datatable
                init_sort();
            }else{
                PT.alert(result.err);
            }
        },
        update_status_back:function(oper, succ_camp_ids, failed_camp_ids) {
            for (var i=0; i<succ_camp_ids.length; i++){
                var camp_id=succ_camp_ids[i],
                    jq_status=$('#status_'+camp_id);
                jq_status.prev().text(oper);
                if(oper){
                    jq_status.text('推广中');
                    jq_status.parents('tr').removeClass('mnt_tr');
                }else{
                    jq_status.text('已暂停');
                    jq_status.parents('tr').addClass('mnt_tr');
                }
            }
            if(failed_camp_ids && failed_camp_ids.length > 0){
                var status_desc = (oper? '启用' : '暂停');
                PT.alert(status_desc+"失败"+failed_camp_ids.length+"个计划");
            }
        },
        show_camp_trend:function(camp_id, category_list, series_cfg_list) {
            var cmap_title = $('#title_'+camp_id).text();
            $.alert({
              title:cmap_title,
              body:$('#modal_camp_trend_temp').html(),
              width:'680px',
              shown:function(){PT.draw_trend_chart( 'camp_trend_chart' , category_list, series_cfg_list);}
            })

        }
    };
}();
