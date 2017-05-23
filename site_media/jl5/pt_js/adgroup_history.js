PT.namespace('Adg_history');
PT.Adg_history = function () {
    var history_table=null,
        adg_id=$('#kw_search_btn').attr('value');
    var init_table=function(){
        history_table=$('#adg_history_table').dataTable({
            //"bRetrieve": true, 允许重新初始化表格
            "iDisplayLength": 100,
            "bPaginate" : true,
            "bDeferRender": true,
            "bAutoWidth":false,
            "bFilter": true,
            "bSort":false,
            "bServerSide": true,//开启服务器获取资源
            "fnServerData": send_date,//获取数据的处理函数
            "sDom":"<'row-fluid't<'row-fluid pt10 bg_white'<'span12 pl10'i><'span12 pr10 tr'p>>",
            "oLanguage": {
                "sProcessing" : "正在获取数据，请稍候...",
                "sInfo":"正在显示第_START_-_END_条信息，共_TOTAL_条信息 ",
                "sZeroRecords" : "30天内没有您要搜索的内容",
                "sEmptyTable":"没有数据",
                "sInfoEmpty": "显示0条记录",
                "sInfoFiltered" : "(全部记录数 _MAX_ 条)",
                "oPaginate": {
                    "sFirst" : "第一页",
                    "sPrevious": "上一页",
                    "sNext": "下一页",
                    "sLast" : "最后一页"
                }
            }
        });
    }

    var init_dom=function () {

        $('#kw_search_btn').click(function(){
            search_adg();
        });

        $('#kw_input').keyup(function(e){
            if (e.keyCode==13) {
                search_adg();
            }
        });
    }

    var search_adg=function(){
        var search_word=$('#kw_input').val();
        history_table.fnFilter(search_word);
    }

    //发送请求获取数据
    var send_date=function (sSource, aoData, fnCallback, oSettings){
        //发送请求获取数据
        //PT.show_loading('正在获取数据');
        page_info=get_userful_json(aoData);
        //第一次进入后会执行本函数，这里将必要的参数存入全局变量
        PT.Adg_history.page_info=page_info;
        PT.Adg_history.callBack=fnCallback;
        PT.sendDajax({
            'function':'web_get_adg_history',
            'page_info':page_info,
            'adg_id':adg_id
        });
    }

    var get_dom_4template=function (json){
        //将模板转化为dom对象
        var d,tr_arr=[];
        var index=1;
        for (d in json){
            json[d]['loop']=index;
            if(!isNaN(d)){
                tr_arr.push(template.compile(pt_tpm['adgroup_history.tpm.html'])(json[d]));
            }
            index++;
        }
        return tr_arr
    }

    var get_array=function(data){
        //将模板返回的html按td将其分割,以便datatable填充数据
        var array_data=[];
        for (var i=0;i<data.length;i++){
            var temp_tds=$(data[i]).find('td'),td_arr=[];
            for (var j=0;j<temp_tds.length;j++){
                td_arr.push(temp_tds[j].innerHTML);
            }
            array_data.push(td_arr);
        }
        return array_data;
    }

    //将datatable产生的分页数据格式化为字符串,以便后台接收
    var get_userful_json=function (aoData){
        var json={};
        for (var i=0; i<aoData.length; i++){
            json[aoData[i].name]=aoData[i].value;
        }
        return $.toJSON(json);
    }

    return {

        init: function (){
            $('ul.main.nav>li').eq(5).addClass('active');
            init_table();
            init_dom();
        },
        append_table_data:function(page_info_server,data){
            PT.hide_loading();
            var table=$('#adg_history_table'),template_data,datatable_arr;
            template_data=get_dom_4template(data);
            datatable_arr=get_array(template_data);
            table.find('tbody tr').remove();
            page_info_server['aaData']=datatable_arr;//构造dataTable能够识别的数据格式
            PT.Adg_history.callBack(page_info_server);//填充数据
            table.show();
            new FixedHeader(history_table);
        }
    };
}();
