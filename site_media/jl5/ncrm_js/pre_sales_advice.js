PT.namespace('PreSalesAdvice');
PT.PreSalesAdvice = function () {


    var init_dom = function () {
        require(['dom', 'gallery/datetimepicker/1.1/index'], function (DOM, Datetimepicker) {
            new Datetimepicker({
                start: '#id_start_date',
                timepicker: false,
                closeOnDateSelect: true
            });

            new Datetimepicker({
                start: '#id_end_date',
                timepicker: false,
                closeOnDateSelect: true
            });

        });

        /*var editorBox;
        $(".show_note_btn").click(function () {
            var note = $(this).attr("note");
            var show_note_box = $("#show_note_box");
            show_note_box.find(".modal-body:first").html(note);
            show_note_box.attr("style", "");
            show_note_box.modal('toggle');
        });

        $(".cloose_note_box").click(function () {
            var show_note_box = $("#show_note_box");
            show_note_box.modal("hide");
        });
        $(".edit_btn").click(function () {
            createBox = $("#create");
            var _this = $(this);
            var id = _this.attr("subscribe_id");
            var nick = _this.attr("nick");
            var psuser_id = _this.attr("psuser_id");
            var name_cn = _this.attr("name_cn");
            var note = _this.attr("note");
            createBox.find(".box_title:first").text("编辑");
            createBox.find("#id").val(id);
            createBox.find("#nick").next("span").text(nick);
            createBox.find("#nick").val(nick);
            createBox.find("#nick").hide();
            createBox.find("#id_psuser_id").val(psuser_id);
            createBox.find("#name_cn").val(name_cn);
            createBox.find("#note").val(note);
            createBox.modal();
            PreSalesAdvice.init_editors("#noteEdit", note);
        });

        $(".add_btn").click(function () {
            createBox = $("#create");
            createBox.find(".box_title:first").text("添加");
            createBox.find("#id").val('');
            createBox.find("#nick").val('');
            createBox.find("#nick").show();
            createBox.find("#nick").next("span").text('');
            //createBox.find("#id_psuser_id").val('');
            createBox.find("#name_cn").val('');
            createBox.find("#note").val('');
            createBox.modal();
            PreSalesAdvice.init_editors("#noteEdit", "");
        });

        $(".save_btn").click(function () {
            PreSalesAdvice.save();
        });

        $(".del_btn").click(function () {
            var id = $(this).attr("subscribe_id");
            PT.confirm("确定删除？", function () {
                PT.sendDajax({
                    'function': 'ncrm_del_pre_sales_advice',
                    'id': id,
                    'callback': 'PreSalesAdvice.delCallback'
                });
            });
        });

        $(".search_btn").click(function () {
            PT.show_loading("正在查询");
            $("#form_search_psa").submit();
        });*/

    };

    return {
        init: function () {
            init_dom();
        },

        /*save: function () {
            var id, nick, psuser_id, note;
            id = $("#id").val();
            nick = $("#nick").val();
            psuser_id = $("#id_psuser_id").val();
            note = editorBox.getSource();
            PT.sendDajax({
                'function': 'ncrm_save_pre_sales_advice',
                'id': id,
                'nick': nick,
                'psuser_id': psuser_id,
                'note': note,
                'callback': 'PreSalesAdvice.saveCallback'
            });
        },

        saveCallback: function (msg, status) {
            if (status == 1) {
                PT.alert(msg, '', function () {
                    window.location.reload();
                });
            } else {
                PT.alert(msg);
            }
        },

        delCallback: function (msg, status, id) {
            if (status == 1) {
                PT.alert(msg, '', function () {
                    $("#" + id).remove();
                });
            } else {
                PT.alert(msg);
            }
        },

        init_editors: function (selector, value) {
            editorBox = $("#noteEdit").xheditor({
                tools: 'Blocktag,Fontface,FontSize,Bold,Italic,Underline,Strikethrough,FontColor,BackColor,|,Align,List,Outdent,Indent,|,Link,Emot,Fullscreen',
                height: 200
            });
            editorBox.setSource(value);
        }*/

    };
}();
