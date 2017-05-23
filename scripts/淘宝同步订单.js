
// 批量下载订单
var batch_export_subscribe = function (dt_str_list, article_code) {
    localStorage.clear();
    var i = 0;
    var export_subscribe = function () {
        if (i < dt_str_list.length) {
            var dt_str0 = dt_str_list[i][0], dt_str1 = dt_str_list[i][1];
            $('#export_beginDate').val(dt_str0);
            $('#export_endDate').val(dt_str1);
            $('#export_articleCode').val(article_code);
            $.post(
                $('#orderExportForm').attr('action'),
                $('#orderExportForm').serialize(),
                function(data){
                    localStorage[dt_str0+'至'+dt_str1]=data;
                    console.log(dt_str0+'至'+dt_str1);
                    i++;
                    //export_subscribe();
                    setTimeout(export_subscribe, 1000);
                }
            );
        } else {
            // 后台收录处理，跨域请求
            $.ajax({
                'url':'http://127.0.0.1/ncrm/export_subscribe_fromTOP',
                'type':'GET',
                'data':{'article_code':article_code},
                'dataType':'jsonp',
                'success':function (data) {
                    console.log(data);
                    if (data=='1') {
	                    switch (article_code) {
	                        case 'ts-25811':
	                            export_web_subscribe(dt, end_dt, batch_no);
	                            break;
	                        case 'FW_GOODS-1921400':
	                            export_qn_subscribe(dt, end_dt, batch_no);
	                            break;
	                    }
                    }
                }
            });
        }
    }
    export_subscribe();
}

// 全局变量
var begin_dt = null, end_dt = null, dt = null, batch_no=null;

// web订单日期列表 2012-5-10 开始有订单，单次下载5天，批量下载30天
var export_web_subscribe = function (_begin_dt, _end_dt, _batch_no) {
    dt = _begin_dt?_begin_dt:new Date(2012, 4, 10);
    end_dt = _end_dt?_end_dt:new Date();
    begin_dt = begin_dt?begin_dt:new Date(dt.getFullYear(), dt.getMonth(), dt.getDate());
    batch_no = _batch_no?_batch_no:5;
    var dt_str_list = [], dt_str0 = '', dt_str1 = '';
    if (dt<=end_dt) {
        for (var i=0;i<6 && dt<=end_dt;i++) {
            dt_str0 = dt.getFullYear()+'-'+(dt.getMonth()+1)+'-'+dt.getDate();
            dt.setDate(dt.getDate()+batch_no-1);
            dt_str1 = dt.getFullYear()+'-'+(dt.getMonth()+1)+'-'+dt.getDate();
            dt_str_list.push([dt_str0, dt_str1]);
            dt.setDate(dt.getDate()+1);
        }
	    console.warn('开始批量下载开车精灵订单：');
        batch_export_subscribe(dt_str_list, 'ts-25811');
    } else {
        console.warn('批量下载开车精灵订单完成：'+begin_dt.toLocaleDateString()+' 至 '+end_dt.toLocaleDateString());
        begin_dt = null, end_dt = null, dt = null, batch_no=null;
    }
}

// 千牛订单日期列表 2014-2-11 开始有订单，单次下载1天，批量下载15天
var export_qn_subscribe = function (_begin_dt, _end_dt, _batch_no) {
    dt = _begin_dt?_begin_dt:new Date(2014, 1, 11);
    end_dt = _end_dt?_end_dt:new Date();
    begin_dt = begin_dt?begin_dt:new Date(dt.getFullYear(), dt.getMonth(), dt.getDate());
    batch_no = _batch_no?_batch_no:1;
    var dt_str_list = [], dt_str = '';
    if (dt<=end_dt) {
        for (var i=0;i<15 && dt<=end_dt;i++) {
            dt_str = dt.getFullYear()+'-'+(dt.getMonth()+1)+'-'+dt.getDate();
            dt_str_list.push([dt_str, dt_str]);
            dt.setDate(dt.getDate()+1);
        }
        console.warn('开始批量下载千牛订单：');
        batch_export_subscribe(dt_str_list, 'FW_GOODS-1921400');
    } else {
        console.warn('批量下载千牛订单完成：'+begin_dt.toLocaleDateString()+' 至 '+end_dt.toLocaleDateString());
        begin_dt = null, end_dt = null, dt = null, batch_no=null;
    }
}



