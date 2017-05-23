PT.namespace('NcrmCreatePlan');
PT.NcrmCreatePlan = function() {

    var init_dom = function() {

        require('pt/pt-editor-mini,node', function(editor, $) {
            var editors = {};

            $('.editor').each(function() {
                var ed, id = $(this).attr('id');

                ed = new editor({
                    render: '#' + id,
                    textareaAttrs: {
                        name: id
                    },
                    height: '160px',
                    width: '960px'
                });
                ed.initData($(this).find('textarea').val());
                $(this).find('textarea').remove();
                ed.render();
                editors[id] = ed;
            });

        });

        $("#plan_save").submit(function(event){
            var form_obj = $(this);
            var title = form_obj.find("[name=plan_title]").val();
            var ps_id = form_obj.find("[name=ps_id]").val();
            var start_time = form_obj.find("[name=start_time]").val();
            var end_time = form_obj.find("[name=end_time]").val();
            var check_boxs=form_obj.find('input[type="checkbox"]:checked');

            if(parseInt(ps_id) <= 0){
                PT.alert("请填写责任人");
            }  else if(title==""){
                PT.alert("请填写计划标题");
            } else if(!/201[0-9]-[01][0-9]-[0-3][0-9]/.test(start_time)){
                PT.alert("请填写正确的起始时间");
            } else if(!/201[0-9]-[01][0-9]-[0-3][0-9]/.test(end_time)){
                PT.alert("请填写正确的结束时间");
            } else if(end_time <= start_time){
                PT.alert("您的起止范围有误");
            } else{
                return true;
            }
            return false;
        });

        //日期时间选择器
        require(['dom', 'gallery/datetimepicker/1.1/index'], function(DOM, Datetimepicker) {
            var b, c;
            b = new Datetimepicker({
                start: '#start_time',
                timepicker: false,
                closeOnDateSelect : true
            });
            c = new Datetimepicker({
                start: '#end_time',
                timepicker: false,
                closeOnDateSelect : true
            });

            new Datetimepicker({
                start: '.time',
                timepicker: false,
                closeOnDateSelect : true
            });

        });

        //计划搜索
        $('#search_related_plan_btn').on('click', function() {
            var plan_belong = $.trim($('#plan_belong').val()),
                create_time = $.trim($('#search_related_plan').find('.time').val());

            if (!plan_belong && !create_time) {
                PT.alert('请输入条件查询');
                return;
            }

            PT.sendDajax({
                'function': 'ncrm_related_plane_list',
                'plan_belong': plan_belong,
                'create_time': create_time,
                'call_back': 'PT.NcrmCreatePlan.related_plane_list_callback'
            });
        });

        $('#search_related_plan').on('click', '.choose_plan', function() {
            $('#related_id').val($(this).attr('data-palnId'));
            $('#related_show').val($(this).attr('data-title'));
            $('#start_time').val($(this).attr('data-start'));
            $('#end_time').val($(this).attr('data-end'));
            $('#search_related_plan').modal('hide');
        });
        
        $('#check_all_events').change(function () {
	        $('#plan_save :checkbox[name]:visible').attr('checked', this.checked);
        });
    },

    add_or_change_client_group = function(json) {
        var html='',i=0,obj=$('#client_group_id');
        if(json.length){
            for(var i;i<json.length;i++){
                html+='<option value="'+json[i][0]+'">'+json[i][1]+'</option>';
            }
            obj.html(html).show();
            obj.prev().hide();
        }else{
            obj.html('').hide();
            obj.prev().show();
        }
    }

    return {
        init: function() {
            init_dom();
        },
        related_plane_list_callback: function(json) {
            var i = 0,
                html = '';
            if (json) {
                for (var i; i < json.length; i++) {
                    html += "<tr class='tc'><td>" + json[i][0] + "</td><td>" + json[i][1] + "</td><td><a class='btn btn-mini choose_plan' data-title=" + json[i][1] + " data-palnId=" + json[i][2] + " data-start=" + json[i][3] + " data-end=" + json[i][4] + "  href='javascript:;'>选择 </a></td></tr>"
                }

                $('#search_related_plan table tbody').html(html);
            }
        },
        add_or_change_client_group:add_or_change_client_group
    }
}();
