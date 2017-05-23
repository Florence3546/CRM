define(['template','service/common/common'],function(template,common){
    template.helper('dateFormat', function (date, format) {

        date = new Date(date);

        var map = {
            "M": date.getMonth() + 1, //月份
            "d": date.getDate(), //日
            "h": date.getHours(), //小时
            "m": date.getMinutes(), //分
            "s": date.getSeconds(), //秒
            "q": Math.floor((date.getMonth() + 3) / 3), //季度
            "S": date.getMilliseconds() //毫秒
        };

        format = format.replace(/([yMdhmsqS])+/g, function(all, t){
            var v = map[t];
            if(v !== undefined){
                if(all.length > 1){
                    v = '0' + v;
                    v = v.substr(v.length-2);
                }
                return v;
            }
            else if(t === 'y'){
                return (date.getFullYear() + '').substr(4 - all.length);
            }
            return all;
        });
        return format;
    });

    template.helper('format', function (numerator , format) {
        var formatList=format.split(',');
        return (numerator * formatList[0] / formatList[1]).toFixed(formatList[2]);
    });

    template.helper('truncate', function (str , max_len) {
        var x = 0;
        for (var i in str) {
            x += common.true_length(str[i]);
            if (x>max_len) {
                return str.slice(0, i-3) + '...';
            }
        }
        return str;
    });
});
