define(['template', 'jl6/site_media/widget/ajax/ajax', 'jl6/site_media/widget/loading/loading','jl6/site_media/widget/alert/alert'],
    function (template, ajax, loading, alert) {
        "use strict"
        var init_dom = function () {
            var html = __inline('select_feedback.html');
            if ($('#modal_select_feedback').length==0) {
                $('body').append(html);
            } else {
                $('#modal_select_feedback').replaceWith(html);
            }
            
            //打开模态框
            $('#select_feedback').unbind('click');
            $('#select_feedback').click(function () {
                $('#modal_select_feedback .nick').html($('#nick').val());
                $('#modal_select_feedback .cat_name').html($('#cat_info').html());
                $('#modal_select_feedback .item_title').html($('#item_title').html());
                $('#prblm_descr').val('');
                $('#modal_select_feedback').modal();
            });
            
            //提交反馈
            $('#btn_select_feedback').unbind('click');
            $('#btn_select_feedback').click(function () {
                if ($.trim($('#prblm_descr').val())=='') {
                    alert.show('请填写反馈内容');
                    return;
                }
                loading.show('正在提交反馈，请稍候...');
                $('#modal_select_feedback').modal('hide');
                ajax.ajax(
                    'select_feedback',
                    {
                        'nick':$('#nick').val(),
                        'cat_id':$('#cat_info').attr('cat_id'),
                        'cat_name':$('#cat_info').html(),
                        'item_title':$('#item_title').html(),
                        'item_url':$('#item_url').val(),
                        'prblm_descr':$('#prblm_descr').val(),
                        'fellback_source':$('#fellback_source').val()
                    },
                    function (data) {
                        loading.hide();
                    }
                );
            });
        }
        
        return {
            init: init_dom
        }
    }
);