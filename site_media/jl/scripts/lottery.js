$(document).ready(function() {
    $('#lottery').modal();
    startmarquee(20, 40, 0);
    var zp_list = ['background: url(/site_media/jl5/images/lottery/zps.png) no-repeat 0px 0px;',
                   'background: url(/site_media/jl5/images/lottery/zps.png) no-repeat -447px 0px;',
                   'background: url(/site_media/jl5/images/lottery/zps.png) no-repeat -894px 0px;',
                   'background: url(/site_media/jl5/images/lottery/zps.png) no-repeat -1341px 0px;',
                   'background: url(/site_media/jl5/images/lottery/zps.png) no-repeat -1788px 0px;',
                   'background: url(/site_media/jl5/images/lottery/zps.png) no-repeat -2235px 0px;',
                   'background: url(/site_media/jl5/images/lottery/zps.png) no-repeat -2682px 0px;',
                   'background: url(/site_media/jl5/images/lottery/zps.png) no-repeat -3129px 0px;'
                   ];

    function Trim(str) {
        return str.replace(/(^\s*)|(\s*$)/g, "");
    }
    $('.start_game').click(function() {
        gstart();
    });

    function GetSide(m, n) {
        var arr = [];
        for (var i = 0; i < m; i++) {
            arr.push([]);
            for (var j = 0; j < n; j++) {
                arr[i][j] = i * n + j;
            }
        }
        var resultArr = [],
            tempX = 0,
            tempY = 0,
            direction = "Along",
            count = 0;
        while (tempX >= 0 && tempX < n && tempY >= 0 && tempY < m && count < m * n) {
            count++;
            resultArr.push([tempY, tempX]);
            if (direction == "Along") {
                if (tempX == n - 1) tempY++;
                else tempX++; if (tempX == n - 1 && tempY == m - 1) direction = "Inverse";
            } else {
                if (tempX === 0) tempY--;
                else tempX--; if (tempX === 0 && tempY === 0) break;
            }
        }
        return resultArr;
    }
    var index = 0,
        prevIndex = 0,
        Speed = 300,
        Time, arr = GetSide(5, 5),
        EndIndex = 0,
        tb = document.getElementById("tb"),
        cycle = 0,
        EndCycle = 0,
        flag = false,
        quick = 0,
        btn = document.getElementById("btn1");

    function save_lottery(index) {
        var jq_div = $('#chou_jiang');
        $('.game_before').fadeOut().remove();
        jq_div.find('.start_game, #zps, .wrap').remove();
        $('#win').fadeIn().pulsate({
            color: "#FAFAA1",
            repeat: 8
        });
        index = index * 37 + 1;
        jq_div.find('img').attr('src', '/site_media/jl5/images/lottery/result_' + index + '.gif');
        // PT.sendDajax({'function': 'web_save_lottery_info'});
    }

    function gstart() {
        if (!$('.game_before').length) {
            return false;
        }
        var ware_index = parseInt($('#notice_board').attr('data') || 5);
        if (ware_index != 3 && ware_index != 6) {
            ware_index = 5;
        }
        EndIndex = ware_index;
        clearInterval(Time);
        cycle = 0;
        flag = false;
        EndCycle = 3;
        Time = setInterval(Star, Speed);
    }

    function Star(num) {
        if (flag === false) {
            if (quick == 8) {
                clearInterval(Time);
                Speed = 80;
                Time = setInterval(Star, Speed);
            }
            var temp = EndIndex - 5 > 0 ? EndIndex - 5 : EndIndex + 8 - 5;
            if (cycle == EndCycle + 1 && index == parseInt(temp)) {
                clearInterval(Time);
                Speed = 300;
                flag = true;
                Time = setInterval(Star, Speed);
            }
        }
        if (index >= arr.length) {
            index = 0;
            cycle++;
        }
        if (flag === true && index == parseInt(EndIndex - 1)) {
            quick = 12;
            clearInterval(Time);
            save_lottery(EndIndex);
        } else {
            tb.rows[arr[index][0]].cells[arr[index][1]].className = "playcurr";
            if (index > 0) {
                prevIndex = index - 1;
            } else {
                prevIndex = arr.length - 1;
            }
            tb.rows[arr[prevIndex][0]].cells[arr[prevIndex][1]].className = "playnormal";
            index++;
            quick++;
            if (index > 8) {
                var indexx = index - 8;
                document.getElementById("zps").innerHTML = "<div class='zps' style='" + zp_list[indexx - 1] + "'></div>";
            } else {
                document.getElementById("zps").innerHTML = "<div class='zps' style='" + zp_list[index - 1] + "'></div>";
            }
        }
    }

    function startmarquee(lh, speed, delay) {
        var t;
        var p = false;
        var o = document.getElementById("notice_board");
        o.innerHTML += o.innerHTML;
        o.onmouseover = function() {
            p = true;
        };
        o.onmouseout = function() {
            p = false;
        };
        o.scrollTop = 0;

        function start() {
            t = setInterval(scrolling, speed);
            if (!p) {
                o.scrollTop += 1;
            }
        }

        function scrolling() {
            if (o.scrollTop % lh !== 0) {
                o.scrollTop += 1;
                if (o.scrollTop >= o.scrollHeight / 2) {
                    o.scrollTop = 0;
                }
            } else {
                clearInterval(t);
                setTimeout(start, delay);
            }
        }
        setTimeout(start, delay);
    }
});
