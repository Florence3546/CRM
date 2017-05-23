define(['require', 'sm'], function(require, $) {

    var initDom = function() {



    };

    var pcRank = {
        '-3': '请选择...',
        '-2': '创意未投放',
        '-1': '计划未投放',
        '0': '首页左侧位置',
        '1': '首页右侧第1',
        '2': '首页右侧第2',
        '3': '首页右侧第3',
        '4': '首页（非前三）',
        '5': '第2页',
        '6': '第3页',
        '7': '第4页',
        '8': '第5页',
        '9': '5页以后'
    };

    var pcRankList = [
        {id:0, name: '首页左侧位置'},
        {id:1, name: '首页右侧第1'},
        {id:2, name: '首页右侧第2'},
        {id:3, name: '首页右侧第3'},
        {id:4, name: '首页（非前三）'},
        {id:5, name: '第2页'},
        {id:6, name: '第3页'},
        {id:7, name: '第4页'},
        {id:8, name: '第5页'},
        {id:9, name: '5页以后'}
    ];

    var mobileRank =  {
            '-3': '请选择...',
            '-2': '创意未投放',
            '-1': '计划未投放',
            '0': '移动首条',
            '1': '移动前三',
            '2': '移动前三',
            '3': '移动4~6条',
            '4': '移动4~6条',
            '5': '移动4~6条',
            '6': '移动7~10条',
            '7': '移动7~10条',
            '8': '移动7~10条',
            '9': '移动7~10条',
            '10': '移动11~15条',
            '11': '移动16~20条',
            '12': '20条以后'
        };

    var mobileRankList = [
        {id:0, name: '移动首条'},
        {id:1, name: '移动前三'},
        {id:3, name: '移动4~6条'},
        {id:6, name: '移动7~10条'},
        {id:10, name: '移动11~15条'},
        {id:11, name: '移动16~20条'},
        {id:12, name: '20条以后'}
    ];

    return {
        init: initDom,
        mobileRank: mobileRank,
        mobileRankList: mobileRankList,
        pcRank:pcRank,
        pcRankList: pcRankList
    }

});