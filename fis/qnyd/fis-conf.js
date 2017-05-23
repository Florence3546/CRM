fis.set('new date', Date.now());
fis.match('*.{js,css,png,less,jpg}', {
    query: '?t=' + fis.get('new date')
});

//指定fis3 release 发布目录,请不要使用fis3 server clean命令，否则会清空项目
fis.match('*', {
  deploy: fis.plugin('local-deliver', {
    to: '../../'
  })
})

fis.match('*.orig', {
    release: false
});

fis.match('/node_modules/**', {
    release: false
});

//指定忽略文件
fis.set('project.ignore', ['package.json','fis-conf.js']); // set 为覆盖不是叠加

//less转换为css
fis.match('/site_media/themes/**/theme.less', {
    rExt: '.css',
    parser: fis.plugin('less-2.x')
});

//独立模块less
fis.match('/site_media/service/**/*.less', {
    rExt: '.css',
    parser: fis.plugin('less-2.x')
});

//定义产出目录
fis.match('/site_media/(**)', {
    release: '/site_media/qnyd_temp/$1'
});

fis.match('/templates/(*.html)', {
    release: '/templates/qnyd_temp/$1',
    preprocessor: fis.plugin('replacer', {
        reg:/.*\.html$/,
        from:'__timeStamep',
        to:'?t=' + fis.get('new date')
    })
});


//上线的配置
fis.media('prod').match('/site_media/themes/**/theme.less', {
    rExt: '.css',
    parser: fis.plugin('less-2.x'),
    optimizer: fis.plugin('clean-css')
});

fis.media('prod').match('/site_media/plugins/sui-mobile/css/*.css', {
    optimizer: fis.plugin('clean-css')
});

fis.media('prod').match('/site_media/service/app.js', {
    packTo: '/site_media/static/js/app.js',
    optimizer: fis.plugin('uglify-js',{
        compress: {
            drop_console: true
        },
        mangle: false
    })
});

fis.media('prod').match('/site_media/service/main.js', {
    packTo: '/site_media/static/js/main.js',
    optimizer: fis.plugin('uglify-js',{
        compress: {
            drop_console: true
        },
        mangle: false
    })
});

fis.media('prod').match('/site_media/(**)', {
    release: '/site_media/qnyd6/$1'
});

fis.media('prod').match('/node_modules/**', {
    release: false
});

fis.media('prod').match('/templates/(**)', {
    release: '/templates/qnyd6/$1',
    preprocessor: fis.plugin('replacer', {  //将html下所有的jl6_temp替换为jl6
        reg:/.*\.html$/,
        from:'qnyd_temp|__timeStamep',
        to:'qnyd6|?t='+fis.get('new date')
    })
});
