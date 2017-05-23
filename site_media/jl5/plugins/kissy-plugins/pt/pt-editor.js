define(function(Node, Editor, FontSize, SourceArea, ForeColor, Preview, Images, Center, Left, Right, Links, Maximize, BackColor, Underline, StrikeThrough, Heading, Undo, Table) {
    var _myEditor, dufault;

    dufault = {
        focused: false,
        attachForm: true,
        width: '100%',
        customLink: ["/site_media/jl5/css/bootstrap.min.css", "/site_media/jl5/css/quick_layout.min.css"],
        plugins: [SourceArea, Preview,Table, Left, Center, Right, new Images({defaultMargin:0}), Links, ForeColor, BackColor, Underline, StrikeThrough, Heading, Undo, Maximize]
    }

    myEditor = function(options) {
        var options = $.extend({}, dufault, options);
        Editor.call(this, options)
    }

    myEditor.prototype = Editor.prototype;

    //初始内容
    myEditor.prototype.initData = function(str) {
        this.set('data', str);
    }

    // //获取内容
    myEditor.prototype.value = function(str) {
        // return this.getData();
        if (str) {
            this.setData(str);
        } else {
            return this.getData();
        }
    }
    return myEditor;
}, {
    requires: [
        'node',
        'editor',
        'kg/editor-plugins/1.1.4/font-size',
        'kg/editor-plugins/1.1.4/source-area',
        'kg/editor-plugins/1.1.4/fore-color',
        'kg/editor-plugins/1.1.4/preview',
        'kg/editor-plugins/1.1.4/image',
        'kg/editor-plugins/1.1.4/justify-center',
        'kg/editor-plugins/1.1.4/justify-left',
        'kg/editor-plugins/1.1.4/justify-right',
        'kg/editor-plugins/1.1.4/link',
        'kg/editor-plugins/1.1.4/maximize',
        'kg/editor-plugins/1.1.4/back-color',
        'kg/editor-plugins/1.1.4/underline',
        'kg/editor-plugins/1.1.4/strike-through',
        'kg/editor-plugins/1.1.4/heading',
        'kg/editor-plugins/1.1.4/draft',
        'kg/editor-plugins/1.1.4/table'
    ]
});
