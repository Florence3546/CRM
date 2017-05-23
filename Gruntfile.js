// 包装函数
module.exports = function(grunt) {

  // 任务配置
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
    concat: {
      bootstrap_js: {
        options: {
          //定义一个字符串插入没个文件之间用于连接输出
          separator: ''
        },
        src: [
          'site_media/jl5/bootstrap_js/bootstrap-transition.js',
          'site_media/jl5/bootstrap_js/bootstrap-alert.js',
          'site_media/jl5/bootstrap_js/bootstrap-button.js',
          'site_media/jl5/bootstrap_js/bootstrap-carousel.js',
          'site_media/jl5/bootstrap_js/bootstrap-collapse.js',
          'site_media/jl5/bootstrap_js/bootstrap-dropdown.js',
          'site_media/jl5/bootstrap_js/bootstrap-modal.js',
          'site_media/jl5/bootstrap_js/bootstrap-tooltip.js',
          'site_media/jl5/bootstrap_js/bootstrap-popover.js',
          'site_media/jl5/bootstrap_js/bootstrap-scrollspy.js',
          'site_media/jl5/bootstrap_js/bootstrap-tab.js',
          'site_media/jl5/bootstrap_js/bootstrap-affix.js',
          'site_media/jl5/bootstrap_js/bootstrap-typeahead.js',
          'site_media/jl5/bootstrap_js/jquery-alert.js',
          'site_media/jl5/bootstrap_js/jquery-bootpag.js',
          'site_media/jl5/bootstrap_js/jquery-validata.js',
          'site_media/jl5/bootstrap_js/jquery-json.js',
          'site_media/jl5/bootstrap_js/jquery-switch.js',
          'site_media/jl5/bootstrap_js/jquery-overflow-scroll.js'
        ],
        dest: 'site_media/jl5/js/bootstrap.js'
      },
      pt_js: {
        options: {
          //定义一个字符串插入每个文件之间用于连接输出
          separator: '\n'
        },
        src: [
          'site_media/jl5/pt_js/common.js',
          'site_media/jl5/pt_js/base.js',
          'site_media/jl5/pt_js/base_adg.js',
          'site_media/jl5/pt_js/web_home.js',
          'site_media/jl5/pt_js/campaign_list.js',
          'site_media/jl5/pt_js/adgroup_list.js',
          'site_media/jl5/pt_js/duplicate_check.js',
          'site_media/jl5/pt_js/common_table.js',
          'site_media/jl5/pt_js/adgroup_optimize.js',
          'site_media/jl5/pt_js/smart_optimize.js',
          'site_media/jl5/pt_js/select_keyword.js',
          'site_media/jl5/pt_js/choose_mnt_campaign.js',
          'site_media/jl5/pt_js/mnt_campaign.js',
          'site_media/jl5/pt_js/add_item_box3.js',
          'site_media/jl5/pt_js/rob_rank.js',
          'site_media/jl5/pt_js/invite_friend.js',
          'site_media/jl5/pt_js/upgrade_suggest.js',
          'site_media/jl5/pt_js/delete_keyword.js',
          'site_media/jl5/pt_js/title_optimize.js',
          'site_media/jl5/pt_js/manage_elemword.js',
          'site_media/jl5/pt_js/adgroup_history.js',
          'site_media/jl5/pt_js/creative_box.js',
          'site_media/jl5/pt_js/mnt_optimize.js',
          'site_media/jl5/pt_js/schedule.js',
          'site_media/jl5/pt_js/platform.js',
          'site_media/jl5/pt_js/cf_home.js',
          'site_media/jl5/pt_js/cf_consult.js',
          'site_media/jl5/pt_js/area.js',
          'site_media/jl5/pt_js/lottery.js',
          'site_media/jl5/pt_js/campaign_history.js',
          'site_media/jl5/pt_js/all_history.js',
          'site_media/jl5/pt_js/mnt_forecast.js',
          'site_media/jl5/pt_js/history.js',
          'site_media/jl5/pt_js/spring.js',
          'site_media/jl5/pt_js/attention_list.js',
          'site_media/jl5/pt_js/point_praise.js'
        ],
        dest: 'site_media/jl5/js/ptui.js'
      },
      qnyd_js:{
    	  options: {
    	      separator: '\n'
    	  },
    	  src:[
    	       'site_media/qnyd/scripts/zepto.min.js',
    	       'site_media/jl/scripts/artTemplate.js',
    	       'site_media/jl/scripts/dajax.js',
    	       'site_media/qnyd/plugins/js/adapters/standalone-framework.js',
    	       'site_media/qnyd/scripts/base.js',
    	       'site_media/qnyd/scripts/common.js'
    	  ],
          dest: 'site_media/qnyd/scripts/qnyd.js'
      },
      creative_js:{
        options: {
            separator: '\n'
        },
        src:[
          'site_media/jl5/pt_js/image_manage.js',
          'site_media/jl5/pt_js/creative_config.js',
          'site_media/jl5/pt_js/image_optimoze.js'
        ],
          dest: 'site_media/jl5/js/creative.js'
      },
      css: {
        options: {
          //定义一个字符串插入每个文件之间用于连接输出
          separator: '\n'
        },
        src: [
          'site_media/jl5/pt_css/base.css',
          'site_media/jl5/pt_css/bootstrap.css',
          'site_media/jl5/pt_css/quick_layout.css',
          'site_media/jl5/pt_css/cf_home.css'
        ],
        dest: 'site_media/jl5/css/ptui.css'
      },
      qnyd_css: {
    	  options: {
    		  separator: '\n'
    	  },
    	  src:[
    	       'site_media/qnyd/css/base.css',
    	       'site_media/qnyd/css/common.css',
    	       'site_media/qnyd/css/detail.css'
    	       ],
    	  dest:'site_media/qnyd/css/qnyd.css'
      }
    },
    less: {
      development: {
        options: {
          paths: ["site_media/jl5/"]
        },
        files: {
          "site_media/jl5/css/bootstrap.css": "site_media/jl5/bootstrap_less/bootstrap.less"
        }
      },
      production: {
        options: {
          paths: ["site_media/jl5/"],
          cleancss: true
        },
        files: {
          "site_media/jl5/css/bootstrap.min.css": "site_media/jl5/bootstrap_less/bootstrap.less"
        }
      }
    },
    connect: { //装插件自动刷新
      livereload: {
        options: {
          port: 9000,
        }
      }
    },
    regarde: { //装插件自动刷新
      less: {
        files: 'site_media/jl5/less/help.less',
        tasks: ['toLess', 'livereload']
      },
      html: {
        files: 'template_jl5/*.html',
        tasks: ['livereload']
      },
      css: {
        files: ['site_media/jl5/pt_css/*.css'],
        tasks: ['cssconcat', 'cssmin', 'livereload']
      },
      js: {
        files: ['site_media/jl5/bootstrap_js/*.js'],
        tasks: ['jsconcat', 'livereload']
      }
    },
    watch: {
      less: {
        files: ['site_media/jl5/bootstrap_less/*.less', 'site_media/jl5/less/*.less'],
        tasks: ['toLess']
      },
      css: {
        files: ['site_media/jl5/pt_css/*.css'],
        tasks: ['cssconcat', 'cssmin', ]
      },
      bootstrap_js: {
        files: ['site_media/jl5/bootstrap_js/*.js'],
        tasks: ['jsconcat']
      },
      pt_js: {
        files: ['site_media/jl5/pt_js/*.js'],
        tasks: ['jsconcat']
      },
      tpm: {
        files: ['site_media/jl5/pt_tpm/*.tpm.html'],
        tasks: ['tpmconcat']
      }
    },
    cssmin: {
      minify: {
        expand: true,
        cwd: 'site_media/jl5/css/',
        src: [
          'ptui.css',
          'quick_layout.css'
        ],
        dest: 'site_media/jl5/css/',
        ext: '.min.css'
      }
    },
    uglify: { //压缩js
      bootstrap_js: {
        options: {
          mangle: true
        },
        files: {
          'site_media/jl5/js/bootstrap.min.js': ['<%= concat.bootstrap_js.dest %>']
        }
      },
      pt_js: {
        options: {
          mangle: true
        },
        files: {
          'site_media/jl5/js/ptui.min.js': ['<%= concat.pt_js.dest %>']
        }
      },
      jlcb_js:{
        options: {
          mangle: true
        },
        files: {
          'site_media/jl5/js/select_keyword_order.min.js': ['site_media/jl5/pt_js/select_keyword_order.js']
        }
      },
      creative_js:{
        options: {
          mangle: true
        },
        files: {
          'site_media/jl5/js/creative.min.js': ['site_media/jl5/js/creative.js']
        }
      },
      dataTables: {
        options: {
          mangle: true
        },
        files: {
          'site_media/jl5/plugins/data-tables/dataTables.min.js': ['site_media/jl5/plugins/data-tables/dataTables.1.1.0.js', 'site_media/jl5/plugins/data-tables/DT_bootstrap.js', 'site_media/jl5/plugins/data-tables/FixedHeader.js']
        }
      },
      artTemplate: {
        options: {
          mangle: true
        },
        files: {
          'site_media/jl5/plugins/artTemplate.min.js': ['site_media/jl5/plugins/artTemplate.js']
        }
      },
      templates: {
        options: {
          mangle: true
        },
        files: {
          'site_media/jl5/js/templates.min.js': ['site_media/jl5/js/templates.js']
        }
      }
    },
    jshint: {
      options: {
        "asi": true, //忽略分号警告
        "browser": true,
        "eqeqeq": false, //忽略使用==和!=
        "eqnull": true, //忽略==null警告
        "es3": true, //这个选项告诉JSHint你的代码需要遵循的ECMAScript3规范。如果你需要你的程序必须是可执行的在旧的浏览器，如Internet Explorer6/7/8/9-and其他传统的JavaScript环境中使用此选项
        "expr": true,
        "jquery": true,
        "latedef": true,
        "laxbreak": true,
        "nonbsp": true,
        "strict": true,
        "undef": true,
        "unused": false,
        "laxcomma": true,
        "boss": true,
        "scripturl": true
      },
      files: ['site_media/jl5/pt_js/*.js']
    },
    htmlConvert: {
      options: {
        base: "site_media/jl5/pt_tpm/"
      },
      pt_tpm: {
        src: ['site_media/jl5/pt_tpm/*.tpm.html'],
        dest: 'site_media/jl5/js/templates.js'
      }
    },
    clean: {
      js: ["<%= concat.bootstrap_js.dest %>", "<%= concat.pt_js.dest %>","site_media/jl5/js/templates.js"],
      css:["site_media/jl5/css/bootstrap.css","site_media/jl5/css/ptui.css"]
    }
  });

  // 任务加载
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-contrib-less');

  //装插件自动刷新
  grunt.loadNpmTasks('grunt-regarde');
  grunt.loadNpmTasks('grunt-contrib-connect');
  grunt.loadNpmTasks('grunt-contrib-livereload');


  //  grunt.loadNpmTasks('grunt-browser-sync');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-contrib-cssmin');

  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-jshint');
  //转换html为js的template
  grunt.loadNpmTasks('grunt-html-convert');
  grunt.loadNpmTasks('grunt-contrib-clean');


  // 自定义任务

  //装插件自动刷新
  grunt.registerTask('init', ['livereload-start', 'connect', 'regarde']); //生成一个简单服务器，并监视css,js,html的改变
  grunt.registerTask('develop', ['concat', 'toLess', 'tpmconcat', 'minjsall', 'mincssall', 'live']); //合并所有文件,并监视所以文件变动
  grunt.registerTask('minjsall', ['uglify']); //压缩js
  grunt.registerTask('mincssall', ['cssmin']); //压缩css
  grunt.registerTask('toLess', ['less']); //将less转化为css
  grunt.registerTask('live', ['watch']); //监视文件变动
  grunt.registerTask('jsconcat', ['concat:bootstrap_js', 'concat:pt_js', 'concat:creative_js']); //合并js
  grunt.registerTask('cssconcat', ['concat:css']); //合并css
  grunt.registerTask('allconcat', ['concat']); //合并js，css
  grunt.registerTask('tpmconcat', ['htmlConvert']) //合并模板文件
  grunt.registerTask('jscheck', ['jshint']); //js语法检查
  grunt.registerTask('jlcb', ['uglify:jlcb_js']); //js语法检查
  grunt.registerTask('default', ['concat', 'toLess', 'tpmconcat', 'minjsall', 'mincssall','clean']);
};

//注意：开发阶段执行合并方便调试，每次完成一个模块时，请压缩代码测试是否有问题
