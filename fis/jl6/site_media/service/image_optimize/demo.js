    /**
        直线
        var line1 = new Kinetic.Line({
            points: [14, 138, 124 * 2 + 14, 138],
            stroke: "#fff",
            strokeWidth: 2
        });

        虚线
        var line1 = new Kinetic.Line({
            points: [14, 138, 124 * 2 + 14, 138],
            stroke: "#fff",
            strokeWidth: 2
        });
        line1.dash([10, 8]);

        绘画文本
        var text = new Kinetic.Text({
            text: 'test',
            fontFamily: 'FZZZHJT',
            fontSize: 60,
            padding: 10,
            fill: 'white',
            width: 360,
            align: 'center',
            draggable: true
        });

        绘画fonticon
        var text = new Kinetic.Text({
            text: String.fromCharCode("0xe600"),
            fontFamily: 'ICON',
            fontSize: 60,
            padding: 10,
            fill: 'white',
            width: 360,
            align: 'center',
            draggable: true
        });

        绘画矩形
        var text = new Kinetic.Rect({
            x : 400,
            y : 150,
            width : 100,
            height : 100,
            fill : "red"
        });

        绘画星星
        var star = new Kinetic.Star({
          x: 100,
          y: 200,
          numPoints: 80,
          innerRadius: 60,
          outerRadius: 70,
          fill: 'red',
          stroke: 'red',
          strokeWidth: 4
        });

        绘画多边形
        var hexagon = new Kinetic.RegularPolygon({
            x: 100,
            y: 200,
            sides: 6,
            radius: 70,
            fill: 'red',
            stroke: 'black',
            strokeWidth: 4
        });

        虚线圆
        var circle = new Kinetic.Circle({
            x: 124 + 26,
            y: 124 + 26,
            radius: 124,
            stroke: "#fff",
            strokeWidth: 4
        });

        自定义路径
        var shape = new Kinetic.Shape({
            drawFunc: function(context) {
              context.beginPath();
              context.moveTo(0, 140);
              context.lineTo(150,180);
              context.lineTo(135,230);
              context.lineTo(0, 280);
              context.closePath();
              context.fillStrokeShape(this);
            },
            fill: '#35395c',
        });

        文字路径【data值请参考svg】
        var textpath = new Kinetic.TextPath({
            fill: '#fff',
            fontSize: 55,
            fontFamily: 'FZCHJT',
            text: config.desc1,
            data: 'M30,110 L110,30',
            shadowColor: '#666',
            shadowBlur: 2,
            shadowOffset: {x:1, y:1},
        });

        嵌入图形
        var imageObj = new Image();
        imageObj.src = 'data:image/png;base64,xxxxxx'
        var image = new Kinetic.Image({
            x: 200,
            y: 50,
            image: imageObj,
            width: 100,
            height: 100
        });

        #半圆&饼
        var wedge = new Kinetic.Wedge({
            radius: 40,
            fill: 'red',
            stroke: 'black',
            strokeWidth: 5,
            angleDeg: 60,
            rotationDeg: -120
        });

        #扇形
        var arc = new Kinetic.Arc({
            innerRadius: 40,
            outerRadius: 80,
            fill: 'red',
            stroke: 'black',
            strokeWidth: 5,
            angle: 60,
            rotationDeg: -120
        });

        #利用svg中贝塞尔曲线模拟角度不超过90度的圆（item_25的虚线可用）
        var path = new Kinetic.Path({
            x: 0,
            y: 0,
            data: 'M10,0 L10 160 C10,225,75,225,75,225 C140,225,140,160,140,160 L140,0',
            stroke: '#fff',
            strokeWidth: 4
        });
        path.dash([10, 8]);

        #很屌的一个例子
        scale=(400/800)*0.5;
        scale1=(370/800)*0.5;
        scale2=(320/800)*0.5;
        var path = new Kinetic.Path({
            x: 0,
            y: 800*scale,
            data: 'M591.272 791.040c0 0-300.56 21.105-506.692-157.31-108.838-94.204-72.254-203.041-72.254-204.871 0 0 25.826-92.905 183.836-151.824 107.924-40.245 82.374-96.243 82.374-96.243s-16.978-41.404-37.102-64.27c-5.488-31.553 18.751-48.931 43.441-39.787 13.565 5.022 120.729 62.192 154.57 160.972 489.314 21.951 560.654 244.199 568.886 289.014 0 0 11.585 53.659 0 58.534-22.978 11.338-417.060 205.786-417.060 205.786z',
            stroke: '#bcbcbc',
            strokeWidth: 1,
            fillLinearGradientStartPoint: {x:0, y:0},
            fillLinearGradientEndPoint: {x:500,y:800},
            fillLinearGradientColorStops: [0.9, '#fff', 1, '#bcbcbc'],
            scale:{x:scale,y:-scale}
        });

        var path1 = new Kinetic.Path({
            x: 40*scale1,
            y: (800+40)*scale1,
            data: 'M562.208 793.683c0 0-286.064 11.53-479.575-155.97-102.177-88.437-67.83-190.615-67.83-192.331 0 0 24.25-87.221 172.586-142.533 101.319-37.78 107.189-78.461 107.189-78.461s11.086-58.533-7.804-79.998c-5.152-29.626-54.634-64.387-26.341-47.804 12.731 4.716 130.73 66.338 150.24 172.679 536.565 19.511 590.301 246.701 598.031 288.773 0 0 5.021 38.346-5.854 42.928-18.518 9.137-185.36 93.893-372.67 191.45-0.001 0-0.326 1.44-67.965 1.277z',
            fill:config.color1,
            scale:{x:scale1,y:-scale1}
        });

        var path2 = new Kinetic.Path({
            x: (800-50)*scale2,
            y: (800+5)*scale2,
            data: 'M2.042 797.182c0 0 185.488-256.343 367.827-282.579 109.718-15.787 149.972 0.788 172.071 11.841z',
            stroke: '#bdbdbd',
            strokeWidth: 1,
            fillLinearGradientStartPoint: {x:422, y:624},
            fillLinearGradientEndPoint: {x:378,y:538},
            fillLinearGradientColorStops: [0.3,'#bcbcbc', 0.8,'#f6f6f6', 1, '#d5d5d5'],
            shadowColor: '#666',
            shadowBlur: 2,
            shadowOffset: {
                x: -2,
                y: 2
            },
            scale:{x:scale2,y:-scale2}
        });

        #渐变文字
        var shape = new Kinetic.Shape({
            drawFunc: function(context) {
                var ctx = context._context;
                var grad = ctx.createLinearGradient(100, 100, 200, 200);
                grad.addColorStop(0, 'orange');
                grad.addColorStop(0.4, 'red');
                grad.addColorStop(1, 'blue');
                ctx.fillStyle = grad;
                ctx.font = "69px verdana";
                ctx.fillText("createLinearGradient", 0, 70);
                context.fillStrokeShape(this);
            }
        });

    */
