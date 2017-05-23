/*需要安装的插件
npm install -g fis3@3.3.0 fis3-hook-amd@0.1.9 fis3-postpackager-loader@1.3.5 fis-parser-less-2.x@0.1.4 fis-optimizer-html-to-js@0.1.0
*/

fis.set('new date', Date.now());
fis.match('*.{js,css,png,less,jpg}', {
    query: '?t=' + fis.get('new date')
});

//less转换为css
fis.match('/jl6/site_media/themes/**/theme.less', {
    rExt: '.css',
    parser: fis.plugin('less-2.x')
});

fis.match('/jl6/site_media/less/common/common.less', {
    rExt: '.css',
    parser: fis.plugin('less-2.x')
});

//独立模块less
fis.match('/jl6/site_media/service/**/*.less', {
    rExt: '.css',
    parser: fis.plugin('less-2.x')
});

//js模块化
fis.hook('amd', {
    baseUrl: './jl6/site_media',
    paths: {
        bootstrap: 'plugins/bootstrap/dist/bootstrap.min.js',
        jquery: 'plugins/jquery/jquery.min.js',
        template: 'plugins/artTemplate/template.js',
        mousewheel: 'plugins/jquery-mousewheel/jquery.mousewheel.min.js',
        highcharts: 'plugins/Highcharts/highcharts.js',
        dateRangePicker: 'plugins/jquery-ui-daterangepicker/jquery.comiseo.daterangepicker.min.js',
        moment: 'plugins/moment/moment.min.js',
        shiftcheckbox: 'plugins/shiftcheckbox/jquery.shiftcheckbox.js',
        jqueryUi: 'plugins/jquery-ui/jquery-ui.min.js',
        jslider: 'plugins/jslider/js/jquery.slider.js',
        store: 'plugins/store/store.min.js',
        dataTable: 'plugins/data-tables/dataTableExt.js',
        tag_editor: 'plugins/jquery-tag-editor/jquery.tag-editor.min.js',
        caret:'plugins/caret/jquery.caret.min.js',
        kinetic:'plugins/kinetic/kinetic-v5.1.0.min.js',
        Jcrop:'plugins/Jcrop/js/jquery.Jcrop.min.js',
        webfontloader:'plugins/webfontloader/webfontloader.js',
        json:'plugins/jquery.json-2.4.min.js',
        zclip:'plugins/zclip/jquery.zclip.min.js',
        pin:'plugins/jquery-pin/jquery.pin.min.js'
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
        bootstrap: {
            deps: ['jquery']
        },
        jslider: {
            deps: ['jquery']
        },
        dataTable:{
            deps: ['jquery','plugins/data-tables/dataTables.min.js','plugins/data-tables/FixedHeader.min.js','plugins/data-tables/TableTools.js']
        },
        json:{
            deps: ['jquery']
        },
        zclip:{
            deps:['jquery']
        },
        caret:{
            deps:['jquery']
        },
        tag_editor:{
            deps:['jquery']
        },
        pin:{
            deps:['jquery']
        }
    }
});

fis.match('/jl6/site_media/(widget|service)/**/*.js', {
    isMod: true, // 设置 widget 下都是一些组件，组件建议都是匿名方式 define
});

// fis.match('/jl6/site_media/widget/**/*.html', {
//     optimizer: fis.plugin('html-to-js'),
//     rExt: '.js'
// });


fis.match('::package', {
    // npm install [-g] fis3-postpackager-loader
    // 分析 __RESOURCE_MAP__ 结构，来解决资源加载问题
    postpackager: fis.plugin('loader', {
        resourceType: 'amd',
        include: '/jl6/site_media/{widget,service}/**/*.js',
        useInlineMap: true // 资源映射表内嵌
    })
});

//定义产出目录
fis.match('/jl6/site_media/(**)', {
    release: '/site_media/jl6_temp/$1'
});

fis.match('/jl6/(test/**)', {
    release: '/site_media/jl6_temp/$1'
});

fis.match('/jl6/(help/**)', {
    release: '/site_media/jl6_temp/$1'
});

fis.match('/jl6/templates/(*.html)', {
    release: '/templates/jl6_temp/$1',
    preprocessor: fis.plugin('replacer', {
        reg:/.*\.html$/,
        from:'__timeStamep',
        to:'?t=' + fis.get('new date')
    })
});

fis.match('release.bat', {
    release: false
});

//指定fis3 release 发布目录,请不要使用fis3 server clean命令，否则会清空项目
fis.match('*', {
  deploy: fis.plugin('local-deliver', {
    to: '../'
  })
})

fis.match('*.orig', {
    release: false
});

fis.match('/node_modules/**', {
    release: false
});

fis.match('/qnpc/**', {
    release: false
});

fis.match('/qnyd/**', {
    release: false
});


//上线的配置
fis.media('prod').match('/jl6/site_media/themes/**/*_theme.less', {
    rExt: '.css',
    parser: fis.plugin('less-2.x')
});

//压缩主题css
fis.media('prod').match('/jl6/site_media/themes/**/theme.less', {
    optimizer: fis.plugin('clean-css')
});

//压缩其他css
fis.media('prod').match('/jl6/site_media/static/css/quickLayout.css', {
    optimizer: fis.plugin('clean-css')
});

//压缩service独立模块中的css
fis.media('prod').match('/jl6/site_media/service/**/*.less', {
    optimizer: fis.plugin('clean-css')
});

//main.js 压缩
fis.media('prod').match('/jl6/site_media/service/main.js', {
    optimizer: fis.plugin('uglify-js',{
        compress: {
            drop_console: true
        }
    })
});

//widget组件

fis.media('prod').match('/jl6/site_media/widget/**/*.js', {
    packTo: '/site_media/jl6/static/js/widget.js',
    optimizer: fis.plugin('uglify-js',{
        compress: {
            drop_console: true
        }
    })
});

// service组件
fis.media('prod').match('/jl6/site_media/service/**/*.js', {
    packTo: '/site_media/jl6/static/js/service.js',
    optimizer: fis.plugin('uglify-js',{
        compress: {
            drop_console: true
        }
    })
}).match('/jl6/site_media/service/image_optimize/*.js',{
    packTo:null
});

//创意优化组件
fis.media('prod').match('/jl6/site_media/service/image_optimize/*.js', {
    packTo: '/site_media/jl6/static/js/image_optimize.js',
    optimizer: fis.plugin('uglify-js',{
        compress: {
            drop_console: true
        }
    })
});

fis.media('prod').match('/jl6/site_media/(**)', {
    release: '/site_media/jl6/$1'
});


fis.media('prod').match('/jl6/(test/**)', {
    release: false
});

fis.media('prod').match('/node_modules/**', {
    release: false
});

fis.media('prod').match('/jl6/(help/**)', {
    release: false
});

fis.media('prod').match('release.bat', {
    release: false
});

fis.media('prod').match('/jl6/templates/(**)', {
    release: '/templates/jl6/$1',
    preprocessor: fis.plugin('replacer', {  //将html下所有的jl6_temp替换为jl6
        reg:/.*\.html$/,
        from:'jl6_temp|__timeStamep',
        to:'jl6|?t='+fis.get('new date')
    })
});



//指定忽略文件
fis.set('project.ignore', ['package.json','fis-conf.js']); // set 为覆盖不是叠加


