PT.namespace('CrmKwManage');
PT.CrmKwManage = function () {

    var kw_page_size=100, kw_table={}, n_editing = null, cat_id = 0,  tab_id = 0, select_index=0, word_type='prodword';
    var cat_select=$('[id^="cat_level"]'),
        table_arr=['prodword_table','saleword_table','metaword_table','synoword_table','forbidword_table','includeword_table','brandword_table','elemword_table','meanword_table'],
        input_css='type="text" class="normally" style="width:100%; padding:6px 0px; "';

    var page_info=function (){
        if(PT.CrmKwManage.hasOwnProperty('page_info')){
            return PT.CrmKwManage.page_info;
        }else{
            return '{"sEcho":1,"iDisplayLength":'+kw_page_size+',"iDisplayStart":0}';
        }
    };

    var init_table=function() {
        if (word_type=='prodword' || word_type=='saleword' || word_type=='meanword') {
            kw_table[tab_id] = $('#'+table_arr[tab_id]).dataTable({
                        "iDisplayLength": kw_page_size,
                        "bPaginate" : true,
                        "bDeferRender": true,
                        "bAutoWidth":false,
                        "bFilter": true,
                        "bSort":false,
                        "bServerSide": true,//开启服务器获取资源
                        "fnServerData": send_date,//获取数据的处理函数
                        "sDom": "<'row-fluid'r>t",
                        "sPaginationType": "bootstrap",
                        "oLanguage": {
                                "sEmptyTable":"没有数据",
                                "sInfoEmpty": "显示0条记录",
                                "sInfoFiltered" : "(全部记录数 _MAX_ 条)"
                        }
                });
        } else {
            kw_table[tab_id] = $('#'+table_arr[tab_id]).dataTable({
                        "iDisplayLength": kw_page_size,
                        "bPaginate" : true,
                        "bDeferRender": true,
                        "bAutoWidth":false,
                        "bFilter": true,
                        "bSort":false,
                        "bServerSide": true,//开启服务器获取资源
                        "fnServerData": send_date,//获取数据的处理函数
                        "sPaginationType": "bootstrap",
                        "oLanguage": {
                                "sProcessing" : "正在获取数据，请稍候...",
                                "sInfo":"正在显示第_START_-_END_条信息，共_TOTAL_条信息 ",
                                "sZeroRecords" : "没有您要搜索的内容",
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
    };

    //改变类目ID时，清除表格
    var destroy_table=function () {
        del_len = table_arr.length - 2;
        for (var i=0; i< del_len; i++) {
            if (kw_table[i]) {
                kw_table[i].fnDestroy();
                kw_table[i]=null;
            }
        }
    };

    var init_dom=function () {
        $('[id^="cat_level"]').change( function(){
            select_index = $(this).parent().index();
            var temp_cat_id=$(this).val();

            if (temp_cat_id) {
                //使 select 自适应所选项的宽度
                var temp_obj=document.createElement("select");
                temp_obj.length=1;
                temp_obj.options[0].text=this.options[this.selectedIndex].text;
                this.parentNode.appendChild(temp_obj);
                this.style.width=temp_obj.offsetWidth+'px';
                this.parentNode.removeChild(temp_obj);

                if (temp_cat_id=='all') {
                    temp_cat_id=null;//当前项为“请选择”时
                    cat_id = cat_select[select_index-2].value;
                } else {
                    cat_id = temp_cat_id;
                }
                $('#cat_id_input').attr('placeholder',cat_id);
            }

            if ($(this).attr('id') != 'cat_level_4') {
                if (temp_cat_id) {
                    PT.sendDajax({'function':'crm_get_sub_cat','cat_id':temp_cat_id,"pt_obj":"CrmKwManage"});
                }else{
                    PT.CrmKwManage.set_sub_cat([]);
                }
            } else {
                var jq_cat_path=$('#init_cat_path'),
                    jq_jump_type=$('#jump_type');
                if (jq_cat_path.val() && jq_jump_type.val()) { //首次进入页面时，跳转到目的标签页
                    $('#kw_manage_tab a[href=#'+jq_jump_type.val()+'_tab]').click();
                    jq_jump_type.val(''); // 清空该值，防止影响搜索类目。
                } else {
                    destroy_table();// 子类目变动后，除了原子词、无意义词，其他表格都要清空。
                    if (word_type != 'elemword' && word_type != 'meanword') {
                        init_table();
                    }
                }
                jq_cat_path.val('');
            }

        });

        $('#cat_search_btn').click( function() {
            search_cat_id();
        });
        $('#cat_id_input').keyup(function(e){
            if (e.keyCode==13) {
                search_cat_id();
            }
        });

        $('#kw_search_btn').click( function() {
            search_kw();
        });
        $('#word_input').keyup(function(e){
            if (e.keyCode==13) {
                search_kw();
            }
        });

        $('[id$="word_li"]').click( function() {
            if (n_editing) {
                restore_row(kw_table[tab_id], n_editing);
                n_editing = null;
            }
            tab_id=$(this).index();
            word_type=table_arr[tab_id].split('_')[0];
            // 如果还没有创建当前表格，或者当前表格没有被初始化成 DataTable 类，则初始化当前表格
            //if ( ! kw_table.hasOwnProperty(tab_id) || ! kw_table[tab_id]) {
            var jq_table=$('#'+table_arr[tab_id]);
            if (! $.fn.dataTable.fnIsDataTable(jq_table[0])){
                init_table();
            }
        });

        $('#word_table_new').click(function () {
                if (n_editing) {
                    restore_row(kw_table[tab_id], n_editing);
                    n_editing = null;
                }
                if (word_type=='saleword' || word_type=='prodword') {
                    PT.light_msg('不能添加','请在当前记录上操作！');
                    return false;
                }
                var select_objs=$("[id^=cat_level]").find("option:selected");
                var top_cat_name=$("#cat_level_1").find("option:selected").text(), cat_name=top_cat_name;
                for (var i=1; i<select_objs.length; i++) {
                    var temp_cat_name=select_objs.eq(i).text();
                    if (temp_cat_name!='请选择') {
                        cat_name+=">"+temp_cat_name;
                    }
                }

                var input_td='<td><input '+ input_css +' ></td>';
                var cat_id_td='<td><input '+ input_css +' value='+cat_id+'></td>';
                var cat_name_td='<td><input '+ input_css +' value="'+cat_name+'"></td>';
                var top_cat_id_td='<td><input '+ input_css +' value='+$('#cat_level_1').val()+'></td>';
                var top_cat_name_td='<td><input '+ input_css +' value="'+top_cat_name+'"></td>';
                var oper_td='<td><a class="btn gray new_save" href="javascript:void(0)" >保存</a><a class="btn gray marl_3 cancel" data-mode="new" href="javascript:void(0)">取消</a>';
                var test_td='<a class="btn gray marl_3 test" data-mode="new" href="javascript:;">测试</a></td>';

                if (word_type=='prodword') {
                    kw_table[tab_id].prepend('<tr class="even"><td></td>'+ cat_id_td + cat_name_td + input_td + input_td + oper_td + test_td + '</tr>');
                }else if (word_type=='metaword') {
                    kw_table[tab_id].prepend('<tr class="even"><td></td>'+ cat_id_td + cat_name_td + input_td + input_td + oper_td +'</td></tr>');
                }else if (word_type=='elemword') {
                    kw_table[tab_id].prepend('<tr class="even"><td></td>'+ input_td + input_td + oper_td +'</td></tr>');
                }else if (word_type=='synoword') {
                    kw_table[tab_id].prepend('<tr class="even"><td></td>'+ cat_id_td + cat_name_td + input_td + oper_td+'</td></tr>');
                }else if (word_type=='forbidword') {
                    kw_table[tab_id].prepend('<tr class="even"><td></td>'+ cat_id_td + input_td + input_td + oper_td +'</td></tr>');
                }else if (word_type=='includeword') {
                    kw_table[tab_id].prepend('<tr class="even"><td></td>'+ cat_id_td + input_td + input_td + oper_td +'</td></tr>');
                }else if (word_type=='brandword') {
                    kw_table[tab_id].prepend('<tr class="even"><td></td>'+ top_cat_id_td + input_td + oper_td +'</td></tr>');
                }else if (word_type=='meanword') {
                    kw_table[tab_id].prepend('<tr class="even"><td></td>'+ input_td + input_td + oper_td+'</td></tr>');
                }
        });

        $('[id$="word_table"]').on('click','a.delete', function (e) {
                e.preventDefault();
                var n_row = $(this).parents('tr')[0];
                PT.confirm("您确定要删除 ?",delete_word,[kw_table[tab_id], n_row]);
        });

        $('[id$="word_table"]').on('click','a.cancel', function (e) {
                e.preventDefault();
                if ($(this).attr("data-mode") == "new") {
                        var n_row = $(this).parents('tr');
                        n_row[0].parentNode.removeChild(n_row[0]);
                } else {
                        restore_row(kw_table[tab_id], n_editing);
                        n_editing = null;
                }
        });

        $('[id$="word_table"]').on('click','a.edit', function (e) {
                e.preventDefault();
                var n_row = $(this).parents('tr')[0];
                if (n_editing !== null && n_editing != n_row) {
                        /* 如果页面已有处于编辑状态的行，且不是当前行，则先恢复原来的行，再处理当前行 */
                        restore_row(kw_table[tab_id], n_editing);
                        edit_row(kw_table[tab_id], n_row);
                        n_editing = n_row;
                } else if (n_editing == n_row && this.innerHTML == "保存") {
                        /* 如果页面已有处于编辑状态的行是当前行，则保存当前行 */
                        var check_flag=check_kw(n_row,kw_table[tab_id]);
                        if (check_flag==-1) {
                            PT.alert('某些字段为空，请重新编辑');
                        } else if (check_flag==0) {/*当前信息没有改变，只需修改页面*/
                            save_row(kw_table[tab_id], n_editing);
                        } else {
                    var start = 1, kw_id = $('.kw_id',n_row).val(), kw_arr = get_editing_data(n_row);
                    PT.show_loading('正在保存数据');
                    PT.sendDajax({'function':'crm_save_word','word_type':word_type,'kw_id':kw_id,'keyword':kw_arr});
                        }
                } else {
                        /* 页面没有处于编辑状态的行，则直接编辑当前行 */
                        edit_row(kw_table[tab_id], n_row);
                        n_editing = n_row;
                }
        });

        //实行后台分页后，新添加的一行纪录不能被DataTable实例化，所以其“保存”功能不能通用，要另外写。
        $('[id$="word_table"]').on('click','a.new_save', function() {
            var n_row = $(this).parents('tr')[0];
            var check_flag=check_kw(n_row);
                if (check_flag==-1) {
                    PT.alert('某些字段为空，请重新编辑');
                } else {
                    var kw_arr = get_editing_data(n_row);
                    PT.show_loading('正在保存数据');
                    PT.sendDajax({'function':'crm_save_word','word_type':word_type,'keyword':kw_arr});
                }
        });

        $('[id$="word_table"]').on('click','a.test', function (e) {
                var kw_arr = [], n_row = $(this).parents('tr')[0];
                if( $(this).attr("data-mode") == "new" || n_editing) {
                    kw_arr = get_editing_data(n_row);
                } else {
                    kw_arr = kw_table[0].fnGetData(n_row).slice(1,-1);
                }
                if(kw_arr==[]){
                    PT.alert('获取当前数据失败，请刷新页面后重试');
                    return;
                }
                PT.show_loading('正在获取测试数据');
                PT.sendDajax({'function':'crm_test_prod_word','keyword':kw_arr});
        });

        $('#refresh_elemword_mem').on('click',function(){
            if (cat_id){
                PT.confirm('确认刷新当前类目的原子词缓存信息？（非研发人员勿用！）',refresh_elemword_mem);
            }else{
                PT.alert('请先选择类目ID');
            }
        });

        //将中文逗号转化为英文逗号
        $('table').on('blur','td input,td textarea',function(){
            var text=$(this).val().replace(/，/g, ",");
            text=text.replace(/ /g,"");
            $(this).val(text);
        });

    };

    var refresh_elemword_mem=function(){
        PT.show_loading('正在当前类目的原子词缓存信息');
        PT.sendDajax({'function':'crm_refresh_elemword_mem'});
    };

    var send_date=function (sSource, aoData, fnCallback, oSettings){
        //发送请求获取数据
        PT.show_loading('正在获取数据');
        page_info=get_userful_json(aoData);
        //第一次进入后会执行本函数，这里将必要的参数存入全局变量
        PT.CrmKwManage.page_info=page_info;
        PT.CrmKwManage.callBack=fnCallback;
        PT.sendDajax({
            'function':'crm_get_kw_list',
            'cat_id':cat_id,
            'word_type':word_type,
            'page_info':page_info
        });
    };

    var get_dom_4template=function (json){
        //将模板转化为dom对象
        var tr_arr=[];
        index=1;
        for (d in json){
            json[d]['loop']=index;
            if(!isNaN(d)){
                tr_arr.push($(template.render(table_arr[tab_id]+'_tr', json[d])));
            }
            index++;
        }
        return tr_arr;
    };

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
    };

    var get_userful_json=function (aoData){
        //将datatable产生的分页数据格式化为字符串,以便后台接收
        var json={};
        for (var i=0; i<aoData.length; i++){
            json[aoData[i].name]=aoData[i].value;
        }
        return $.toJSON(json);
    };

    var restore_row=function (o_table, n_row) {
        var aData = o_table.fnGetData(n_row);
        var jq_tds = $('>td', n_row);

        for (var i = 0; i < jq_tds.length; i++) {
            o_table.fnUpdate(aData[i], n_row, i, false);
        }
        //o_table.fnDraw();
    };

    var edit_row=function (o_table, n_row) {
        var aData = o_table.fnGetData(n_row),
            jq_tds = $('>td', n_row),
            temp_h=$(n_row).outerHeight(),
            iLen=jq_tds.length,
            i = 1;
        if(word_type=='saleword'){
            i = 3;
        }
        $(n_row).css('max-height',temp_h+'px');
        for ( i; i < iLen-1; i++) {
            var temp_w=$(jq_tds[i]).outerWidth();
            $(jq_tds[i]).css('max-width',temp_w+'px');
            if (word_type=='prodword' && PT.true_length( aData[3])>60) {
                jq_tds[i].innerHTML = '<textarea class="normally" style="resize: none;width:100%; height:'+ temp_h +'px; padding:6px 0px; ">' + aData[i] + '</textarea>';
            } else {
                jq_tds[i].innerHTML = '<input '+ input_css +' value="' + aData[i] + '">';
            }
        }

        var oper_td='<a class="btn gray edit" href="" name="save">保存</a><a class="btn gray marl_3 cancel" href="">取消</a>',
            oper_test='<a class="btn gray marl_3 test" href="javascript:;">测试</a>';
        if (word_type=='prodword') {
            oper_td += oper_test;
        }
        jq_tds[iLen-1].innerHTML = oper_td;
    };

    var save_row=function (o_table, n_row) {
        kw_arr = get_editing_data(n_row);
        var i_len = kw_arr.length;
        if (word_type=='saleword'){
            o_table.fnUpdate(kw_arr[0], n_row, 3, false);
            o_table.fnUpdate(kw_arr[1], n_row, 4, false);
            o_table.fnUpdate(kw_arr[2], n_row, 5, false);
            i_len=5;
        }else{
            for (var i = 0; i < i_len; i++) {
                o_table.fnUpdate(kw_arr[i], n_row, i+1, false);
            }
        }
        var oper_td='<a class="btn gray edit" href="">编辑</a>',
            oper_a_1='<a class="btn gray marl_3 delete" href="">删除</a>',
            oper_a_2='<a class="btn gray marl_3 test" href="javascript:;">测试</a>';
        if (word_type=='prodword') {
            oper_td += oper_a_2;
        } else if (word_type!='saleword'){
            oper_td += oper_a_1;
        }
        o_table.fnUpdate(oper_td, n_row, i_len+1, false);

    };

    var get_editing_data=function(n_row) {
        var kw_arr=[];
        var jq_inputs = $('input[type="text"]', n_row);
        var jq_tareas = $('textarea ', n_row);
        if (tab_id==0 && jq_tareas.length>0) {
            jq_inputs = jq_tareas;
        }
        for (var i=0; i<jq_inputs.length; i++) {
            kw_arr.push(jq_inputs[i].value);
        }
        return kw_arr;
    };

    var delete_word=function(o_table, n_row) {
        var kw_id = $('.kw_id',n_row).val(),
            aData = o_table.fnGetData(n_row),
            kw_arr = aData.slice(1, aData.length-1);
        PT.sendDajax({'function':'crm_delete_word','word_type':word_type,'kw_id':kw_id, 'kw_list':kw_arr});
        // kw_table[tab_id].fnDeleteRow(n_row);
    };

    var check_kw=function(n_row,o_table) {
        var is_change=false;
        if (o_table) {
            var aData = o_table.fnGetData(n_row);
        }
        var kw_arr = get_editing_data(n_row);
        for (var i = 0; i < kw_arr.length; i++) {
            if(o_table && kw_arr[i]!=aData[i+1]) {is_change=true;}
            if((word_type=='prodword' && (i==2||i==3)) || (word_type=='metaword' && i==2) || (word_type=='forbidword' && i<2) || word_type=='synoword' || word_type=='saleword' ) {
                continue;
            }
            if(kw_arr[i]==='') {return -1; }
        }
        if( (word_type=='prodword' && kw_arr[2]=='' && kw_arr[3]==='') || (word_type=='synoword' && kw_arr[1]=='' && kw_arr[2]=='' && kw_arr[3]=='') || (word_type=='includeword' && kw_arr[1]=='' && kw_arr[2]=='' )) {
            return -1;
        }
        return is_change ? 1 : 0;
    };

    var search_cat_id=function(){
        var temp_cat_id=$('#cat_id_input').val();
        var new_id=parseInt(temp_cat_id);
        if (!temp_cat_id) {
            PT.alert('请输入搜索内容');
        } else if (!new_id) {
            PT.alert('请输入数字');
        } else if (cat_id ==temp_cat_id ) {
            PT.alert('搜索的类目ID与当前ID相同，请重新输入');
        } else {
            PT.show_loading('正在校验类目ID');
            PT.sendDajax({'function':'crm_check_cat_id','cat_id':temp_cat_id, 'is_manual':true});
        }
    };

    var search_kw=function(){
        if (word_type!='synoword' && word_type!='meanword' && word_type!='elemword') {
            PT.light_msg('', '暂不支持该操作');
            return;
        }
        var word=$('#word_input').val();
            kw_table[tab_id].fnFilter(word);
    };

    return {

        init: function () {
            PT.show_loading('正在加载数据');
            PT.sendDajax({'function':'crm_get_sub_cat','cat_id':0,"pt_obj":"CrmKwManage"});
            if (!jQuery().dataTable) {
                return;
            }
            init_dom();
        },

        append_table_data:function (check_id_result,page_info_server,data){
            //后台回调函数
            PT.hide_loading();
            if (check_id_result) {
                var table=$('#'+table_arr[tab_id]),template_data,datatable_arr,result;
                template_data=get_dom_4template(data);
                datatable_arr=get_array(template_data);
                table.find('tbody tr').remove();
                page_info_server['aaData']=datatable_arr;//构造dataTable能够识别的数据格式
                PT.CrmKwManage.callBack(page_info_server);//填充数据
                table.show();
            } else {
                PT.alert('数据库中不存在该类目ID：'+cat_id,'red');
            }

        },

        //多级联动下拉选择框,动态获取下一级
        set_sub_cat:function (data) {
            var StrObj = cat_select[select_index];
            StrObj.length = 0;
            data.sort(function(a, b) { return a.cat_name.localeCompare(b.cat_name); });

            //显示下一级所有下拉列表的内容
            if (data.length>0) {
                for(var i=0;i<data.length;i++) {
                    StrObj.options[i] = new Option(data[i].cat_name, data[i].cat_id);
                }
                if (select_index!==0) {
                    $(StrObj).prepend("<option value='all'>请选择</option>");
                }
                var init_cat_list=$('#init_cat_path').val().split(' ');
                if (init_cat_list && init_cat_list[select_index]) {
                    $(StrObj).val(parseInt(init_cat_list[select_index]));
                }else{
                    $(StrObj).find('option').first().attr('selected',true);
                }
                $(StrObj).parent().show();
            } else {
                $(StrObj).parent().hide();
            }

            //激发下一级的onchange事件以实现多级级联
            $(StrObj).change();

        },

        //返回产品词的测试结果
        test_result:function(source_flag,data){
            PT.hide_loading();
            var temp_str='',source_str=(source_flag?'本地数据库':'淘宝');
            for (var i=0;i<data.length;i++){
                temp_str += template.render('test_table_tr', data[i]);
            }
            $('#test_table_body').html(temp_str);
            $('#items_source').text(source_str);
            $('#modal_prodword_test').modal();
        },

        refresh_men_back:function(flag){
            PT.hide_loading();
            if(flag){
                PT.light_msg('刷新结果','刷新缓存信息成功');
            }else{
                PT.alert("刷新缓存信息失败，请查看日志");
            }
        },

        delete_mem_back:function(flag){
            PT.hide_loading();
            if(flag){
                PT.light_msg('操作结果','清空宝贝缓存成功');
            }else{
                PT.alert("清空宝贝缓存失败，请查看日志");
            }
        },

        check_id_back:function (flag,temp_cat_id,cat_id_list){
            PT.hide_loading();
            if (flag===0) {
                PT.alert('数据库中不存在该类目ID：'+temp_cat_id);
            } else {
                $('#init_cat_path').val(cat_id_list);
                PT.sendDajax({'function':'crm_get_sub_cat','cat_id':0,"pt_obj":"CrmKwManage"});
                select_index = 0;
            }
        },

        save_word_back:function (msg) {
            if (msg!=='') {
                PT.alert(msg);
            } else if (n_editing) {//n_editing 存在，则当前是修改记录
                save_row(kw_table[tab_id], n_editing);
                n_editing = null;
            } else {//当前操作是添加记录时
                kw_table[tab_id].fnClearTable();
            }
        },

        delete_word_back:function (result) {
            if (result) {
                kw_table[tab_id].fnClearTable();
            } else{
                PT.alert('删词失败', 'red');
            }
        }
    };

}();
