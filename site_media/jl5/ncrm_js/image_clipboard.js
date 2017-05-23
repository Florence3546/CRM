PT.namespace('ImageClipboard');
PT.ImageClipboard = function() {
    var imgReader = function (item, target) {
        var file = item.getAsFile(),
            reader = new FileReader();
        reader.onload = function (e) {
            var img = new Image();
            img.src = e.target.result;
            target.appendChild(img);
        }
        reader.readAsDataURL(file);
    }

    var init_dom = function(domId) {
        var target = document.getElementById(domId);
        target.contentEditable = true;
        target.addEventListener('paste', function(event) {
            event.preventDefault();
            var clipboardData = event.clipboardData;
            if (clipboardData) {
                var items = clipboardData.items,
                    types = clipboardData.types;
                if (items.length && types.length) {
                    var item = items[0],
                        type = types[0];
                    if (item && type==='Files' && item.kind==='file' && item.type.match(/^image\//i)) {
                        imgReader(item, target);
                    }
                }
            }
        })
    }

    return {
        init: init_dom
    }
}();
