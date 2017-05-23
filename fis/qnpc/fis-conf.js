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
fis.match('/site_media/themes/theme.less', {
    rExt: '.css',
    parser: fis.plugin('less-2.x')
});

//独立模块less
fis.match('/site_media/service/**/*.less', {
    rExt: '.css',
    parser: fis.plugin('less-2.x')
});

//js模块化
fis.hook('amd', {
    baseUrl: './site_media',
    paths: {
        jquery: 'plugins/jquery/jquery.min.js',
        sm: 'plugins/sui/js/sui.min.js',
        highcharts: 'plugins/highcharts/highcharts.js',
        moment: 'plugins/moment/moment.min.js',
        dataTable: 'plugins/data-tables/dataTableExt.js',
        template:'plugins/artTemplate/template.js',
        jslider: 'plugins/jslider/js/jquery.slider.js',
        zepto: 'plugins/zepto/zepto.min.js',
        json:'plugins/jquery.json-2.4.min.js',
        owlcarousel:'plugins/owlcarousel/owl.carousel.min.js',
        qn:'plugins/qn.js'
    },
    pkgs:[
        {
            name:'service',
            location:'service'
        },
        {
            name:'widget',
            location:'widget'
        }
    ],
    shim: {
        jslider: {
            deps: ['zepto']
        },
        sm: {
            deps: ['jquery']
        },
        json:{
            deps: ['jquery']
        },
        dataTable:{
            deps: ['jquery','plugins/data-tables/dataTables.min.js','plugins/data-tables/FixedHeader.min.js','plugins/data-tables/TableTools.js']
        }
    }
});

fis.match('/site_media/(widget|service)/**/*.js', {
    isMod: true, // 设置 widget 下都是一些组件，组件建议都是匿名方式 define
});

fis.match('::package', {
    // npm install [-g] fis3-postpackager-loader
    // 分析 __RESOURCE_MAP__ 结构，来解决资源加载问题
    postpackager: fis.plugin('loader', {
        resourceType: 'amd',
        include: '/site_media/{widget,service}/**/*.js',
        useInlineMap: true // 资源映射表内嵌
    })
});

//定义产出目录
fis.match('/site_media/(**)', {
    release: '/site_media/qnpc_temp/$1'
});

fis.match('/templates/(*.html)', {
    release: '/templates/qnpc_temp/$1',
    preprocessor: fis.plugin('replacer', {
        reg:/.*\.html$/,
        from:'__timeStamep',
        to:'?t=' + fis.get('new date')
    })
});

//上线的配置
fis.media('prod').match('/site_media/themes/**/*_theme.less', {
    rExt: '.css',
    parser: fis.plugin('less-2.x')
});

//压缩主题css
fis.media('prod').match('/site_media/themes/**/theme.less', {
    optimizer: fis.plugin('clean-css')
});

//压缩service独立模块中的css
fis.media('prod').match('/site_media/service/**/*.less', {
    optimizer: fis.plugin('clean-css')
});

// 千牛pc主题适配
fis.media('prod').match('/site_media/qnthemes/theme.less', {
    packTo: '/site_media/qnthemes/theme.less',
    optimizer: fis.plugin('clean-css')
});

//main.js 压缩
fis.media('prod').match('/qnpc/site_media/service/main.js', {
    optimizer: fis.plugin('uglify-js',{
        compress: {
            drop_console: true
        }
    })
});

//widget组件
fis.media('prod').match('/site_media/widget/**/*.js', {
    packTo: '/site_media/static/js/widget.js',
    optimizer: fis.plugin('uglify-js',{
        compress: {
            drop_console: true
        }
    })
});

// service组件
fis.media('prod').match('/site_media/service/**/*.js', {
    packTo: '/site_media/static/js/service.js',
    optimizer: fis.plugin('uglify-js',{
        compress: {
            drop_console: true
        }
    })
});


fis.media('prod').match('/site_media/(**)', {
    release: '/site_media/qnpc6/$1'
});


fis.media('prod').match('/templates/(**)', {
    release: '/templates/qnpc6/$1',
    preprocessor: fis.plugin('replacer', {  //将html下所有的qnpc_temp替换为qnpc6
        reg:/.*\.html$/,
        from:'qnpc_temp|__timeStamep',
        to:'qnpc6|?t='+fis.get('new date')
    })
});
