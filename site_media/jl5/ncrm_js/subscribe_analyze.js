PT.namespace('subscribeAnalyze');
PT.subscribeAnalyze = function() {

    var init_dom=function(){
        var self=this;
        //日期时间选择器
        require(['dom', 'gallery/datetimepicker/1.1/index'], function (DOM, Datetimepicker) {
            var b,c;
            b= new Datetimepicker({
                    start : '#start_date',
                    timepicker:false,
                    closeOnDateSelect : true
                });

            c= new Datetimepicker({
                    start : '#end_date',
                    timepicker:false,
                    closeOnDateSelect : true
                });
        });

        var datatable=$('#main_table').dataTable({
            bPaginate: false,
            bFilter: false,
            bInfo: false,
            bAutoWidth:false,//禁止自动计算宽度
            sDom: 'Tlfrtip',
            oTableTools: {
                sSwfPath: "/site_media/assets/swf/copy_csv_xls.swf",
                aButtons: [{
                        sExtends: "xls",
                        sTitle:$('#start_date').val().replace(/-/g,'')+'-'+$('#end_date').val().replace(/-/g,'')+'订单明细',
                        fnClick: function ( nButton, oConfig, flash ) {
                            this.fnSetText( flash, export_csv('#main_table') );
                        }
                }],
                custom_btn_id:"save_detial"
            },
            oLanguage: {
                "sZeroRecords": "没有数据"
            }
        });

        if($('#main_table tbody tr').length>1){
            new FixedHeader(datatable);
        }


        $('#summary_table tbody tr').each(function(){
            $(this).find('.js_calc').each(function(){
                var expression = this.childNodes[0].innerText;
                if($(this).hasClass('percent')){
                    this.innerText=(eval(expression)*100).toFixed(2);
                }else{
                    this.innerText=eval(expression);
                }
            });
        });

        $('#summary_table').dataTable({
            bPaginate: false,
            bFilter: false,
            bInfo: false,
            bAutoWidth:false,//禁止自动计算宽度
            sDom: 'Tlfrtip',
            oTableTools: {
                sSwfPath: "/site_media/assets/swf/copy_csv_xls.swf",
                aButtons: [{
                        sExtends: "xls",
                        sTitle:$('#start_date').val().replace(/-/g,'')+'-'+$('#end_date').val().replace(/-/g,'')+'订单汇总',
                        fnClick: function ( nButton, oConfig, flash ) {
                            this.fnSetText( flash, export_csv('#summary_table') );
                        }
                }],
                custom_btn_id:"save_summary"
            },
            oLanguage: {
                "sZeroRecords": "没有数据"
            }
        });
    }

    //导出明细
    var export_csv=function(element){
        var title_list='',data_list='';

        $(element).find('thead tr>th').each(function(){
            title_list+=$(this).text()+'\t';
        });

        title_list+='\n';

        $(element).find('tbody tr').each(function(){
            $(this).find('td').each(function(){
                data_list+=$(this).text()+'\t';
            });
            data_list+='\n';
        });

        return title_list+data_list;
    }

    return {
        init:function(){
            init_dom();
        }
    }

}();
