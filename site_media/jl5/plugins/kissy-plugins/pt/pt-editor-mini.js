define(function(Node, Editor, SourceArea, FontSize, ForeColor, Links, Maximize, BackColor, Underline) {
    var _myEditor, dufault;

    dufault = {
        focused: false,
        attachForm: true,
        width: '100%',
        height: '300px',
        customLink: [],
        plugins: [Links, ForeColor, BackColor, Underline, Maximize]
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
        'kg/editor-plugins/1.1.4/source-area',
        'kg/editor-plugins/1.1.4/font-size',
        'kg/editor-plugins/1.1.4/fore-color',
        'kg/editor-plugins/1.1.4/link',
        'kg/editor-plugins/1.1.4/maximize',
        'kg/editor-plugins/1.1.4/back-color',
        'kg/editor-plugins/1.1.4/underline'
    ]
});
