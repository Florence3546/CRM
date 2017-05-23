// scales the image by (float) scale < 1
// returns a canvas containing the scaled image.
function downScaleImage(img, scale) {
    var imgCV = document.createElement('canvas');
    imgCV.width = img.width;
    imgCV.height = img.height;
    var imgCtx = imgCV.getContext('2d');
    imgCtx.drawImage(img, 0, 0);
    return downScaleCanvas(imgCV, scale,img);
}

// scales the canvas by (float) scale < 1
// returns a new canvas containing the scaled image.
function downScaleCanvas(cv, scale,img) {
    if (!(scale < 1) || !(scale > 0)){
        return img;
    };
    scale = normaliseScale(scale);
    var sqScale = scale * scale; // square scale =  area of a source pixel within target
    var sw = cv.width; // source image width
    var sh = cv.height; // source image height
    var tw = Math.floor(sw * scale); // target image width
    var th = Math.floor(sh * scale); // target image height
    var sx = 0,
        sy = 0,
        sIndex = 0; // source x,y, index within source array
    var tx = 0,
        ty = 0,
        yIndex = 0,
        tIndex = 0; // target x,y, x,y index within target array
    var tX = 0,
        tY = 0; // rounded tx, ty
    var w = 0,
        nw = 0,
        wx = 0,
        nwx = 0,
        wy = 0,
        nwy = 0; // weight / next weight x / y
    // weight is weight of current source point within target.
    // next weight is weight of current source point within next target's point.
    var crossX = false; // does scaled px cross its current px right border ?
    var crossY = false; // does scaled px cross its current px bottom border ?
    var sBuffer = cv.getContext('2d').
    getImageData(0, 0, sw, sh).data; // source buffer 8 bit rgba
    var tBuffer = new Float32Array(3 * tw * th); // target buffer Float32 rgb
    var sR = 0,
        sG = 0,
        sB = 0; // source's current point r,g,b

    for (sy = 0; sy < sh; sy++) {
        ty = sy * scale; // y src position within target
        tY = 0 | ty; // rounded : target pixel's y
        yIndex = 3 * tY * tw; // line index within target array
        crossY = (tY !== (0 | (ty + scale)));
        if (crossY) { // if pixel is crossing botton target pixel
            wy = (tY + 1 - ty); // weight of point within target pixel
            nwy = (ty + scale - tY - 1); // ... within y+1 target pixel
        }
        for (sx = 0; sx < sw; sx++, sIndex += 4) {
            tx = sx * scale; // x src position within target
            tX = 0 |  tx; // rounded : target pixel's x
            tIndex = yIndex + tX * 3; // target pixel index within target array
            crossX = (tX !== (0 | (tx + scale)));
            if (crossX) { // if pixel is crossing target pixel's right
                wx = (tX + 1 - tx); // weight of point within target pixel
                nwx = (tx + scale - tX - 1); // ... within x+1 target pixel
            }
            sR = sBuffer[sIndex]; // retrieving r,g,b for curr src px.
            sG = sBuffer[sIndex + 1];
            sB = sBuffer[sIndex + 2];
            if (!crossX && !crossY) { // pixel does not cross
                // just add components weighted by squared scale.
                tBuffer[tIndex] += sR * sqScale;
                tBuffer[tIndex + 1] += sG * sqScale;
                tBuffer[tIndex + 2] += sB * sqScale;
            } else if (crossX && !crossY) { // cross on X only
                w = wx * scale;
                // add weighted component for current px
                tBuffer[tIndex] += sR * w;
                tBuffer[tIndex + 1] += sG * w;
                tBuffer[tIndex + 2] += sB * w;
                // add weighted component for next (tX+1) px
                nw = nwx * scale
                tBuffer[tIndex + 3] += sR * nw;
                tBuffer[tIndex + 4] += sG * nw;
                tBuffer[tIndex + 5] += sB * nw;
            } else if (!crossX && crossY) { // cross on Y only
                w = wy * scale;
                // add weighted component for current px
                tBuffer[tIndex] += sR * w;
                tBuffer[tIndex + 1] += sG * w;
                tBuffer[tIndex + 2] += sB * w;
                // add weighted component for next (tY+1) px
                nw = nwy * scale
                tBuffer[tIndex + 3 * tw] += sR * nw;
                tBuffer[tIndex + 3 * tw + 1] += sG * nw;
                tBuffer[tIndex + 3 * tw + 2] += sB * nw;
            } else { // crosses both x and y : four target points involved
                // add weighted component for current px
                w = wx * wy;
                tBuffer[tIndex] += sR * w;
                tBuffer[tIndex + 1] += sG * w;
                tBuffer[tIndex + 2] += sB * w;
                // for tX + 1; tY px
                nw = nwx * wy;
                tBuffer[tIndex + 3] += sR * nw;
                tBuffer[tIndex + 4] += sG * nw;
                tBuffer[tIndex + 5] += sB * nw;
                // for tX ; tY + 1 px
                nw = wx * nwy;
                tBuffer[tIndex + 3 * tw] += sR * nw;
                tBuffer[tIndex + 3 * tw + 1] += sG * nw;
                tBuffer[tIndex + 3 * tw + 2] += sB * nw;
                // for tX + 1 ; tY +1 px
                nw = nwx * nwy;
                tBuffer[tIndex + 3 * tw + 3] += sR * nw;
                tBuffer[tIndex + 3 * tw + 4] += sG * nw;
                tBuffer[tIndex + 3 * tw + 5] += sB * nw;
            }
        } // end for sx
    } // end for sy

    // create result canvas
    var resCV = document.createElement('canvas');
    resCV.width = tw;
    resCV.height = th;
    var resCtx = resCV.getContext('2d');
    var imgRes = resCtx.getImageData(0, 0, tw, th);
    var tByteBuffer = imgRes.data;
    // convert float32 array into a UInt8Clamped Array
    var pxIndex = 0; //
    for (sIndex = 0, tIndex = 0; pxIndex < tw * th; sIndex += 3, tIndex += 4, pxIndex++) {
        tByteBuffer[tIndex] = 0 | (tBuffer[sIndex]);
        tByteBuffer[tIndex + 1] = 0 | (tBuffer[sIndex + 1]);
        tByteBuffer[tIndex + 2] = 0 | (tBuffer[sIndex + 2]);
        tByteBuffer[tIndex + 3] = 255;
    }
    // writing result to canvas.
    resCtx.putImageData(imgRes, 0, 0);
    return resCV;
}

function log2(v) {
    // taken from http://graphics.stanford.edu/~seander/bithacks.html
    var b = [0x2, 0xC, 0xF0, 0xFF00, 0xFFFF0000];
    var S = [1, 2, 4, 8, 16];
    var i = 0,
        r = 0;

    for (i = 4; i >= 0; i--) {
        if (v & b[i]) {
            v >>= S[i];
            r |= S[i];
        }
    }
    return r;
}
// normalize a scale <1 to avoid some rounding issue with js numbers
function normaliseScale(s) {
    if (s > 1) throw ('s must be <1');
    s = 0 | (1 / s);
    var l = log2(s);
    var mask = 1 << l;
    var accuracy = 4;
    while (accuracy && l) {
        l--;
        mask |= 1 << l;
        accuracy--;
    }
    return 1 / (s & mask);
}

//图像绘画类
var ImageDrawManager = function(options) {
    var defaults = {
        width: 800,
        twidth: 270,
        height: 800,
        theight: 270,
        scale: 270 / 800
    }
    this.options = $.extend({}, defaults, options);
    this.__init_stage();
    this.__add_single_mark();
}

/**
  创建一个舞台 this.stage
  创建一个层   this.layer
  创建三个可拖动的组 this.group[n]
*/
ImageDrawManager.prototype.__init_stage = function() {
    this.stage = new Kinetic.Stage({
        container: this.options.id,
        width: this.options.twidth,
        height: this.options.theight,
        scale: {
            x: this.options.scale,
            y: this.options.scale
        }
    });

    this.layer = new Kinetic.Layer();

    this.group1 = new Kinetic.Group({
        draggable: true
    });
    this.group2 = new Kinetic.Group({
        draggable: true
    });
    this.group3 = new Kinetic.Group({
        draggable: true
    });
}

//添加所有单个标签
ImageDrawManager.prototype.__add_single_mark=function(){
    var i=1;
    for(var t in this.template){
        this.style_config['9_'+i]=[{
            x: 0,
            y: 0,
            index: t,
            group: 1
        }];

        i++;
    }

    //设置单个标签的位置
    for(var s in this.single_tag_config){
        this.style_config['9_'+s][0]['x']=this.single_tag_config[s]['x'];
        this.style_config['9_'+s][0]['y']=this.single_tag_config[s]['y'];
    }
    // console.log(this.style_config);
}

// 清空所有组
ImageDrawManager.prototype.clear_group = function() {
    var group_list=this.stage.find("Group");

    if(!group_list.length){
        return false;
    }

    //记录当前group的位置，避免用户重新输入文字后goup位置重置导致用户移动位置丢失
    this._group_config={};
    for (var g=0;g < group_list.length;g++){
        var obj=group_list[g];
        this._group_config[obj.getId()]={x:obj.getX(),y:obj.getY()}
    }

    this.stage.find("Group").destroy();
}

// 清空所有层
ImageDrawManager.prototype.clear_layer = function() {
    this.stage.find("Layer").destroy();
}

// 绘制组中的效果
ImageDrawManager.prototype.draw_group = function(index,config_id, group, callBack) {

    var func = this['group_item_' + index];

    if (!group) {
        group = this.group1;
    }

    if (typeof func == "function") {
        if(this.custom_template){
            var is_active=false;
            //当所有输入为空时，就不绘制
            for(var i in this.custom_template[index]){
                if (i.indexOf('color')!=-1||i.indexOf('fontsize')!=-1){
                    continue;
                }
                if(this.custom_template[index][i]!=""){
                    is_active=true;
                    break;
                }
            }

            is_active&&func.apply(this, [group, (this.custom_template[index])]);

        }else{
            func.apply(this, [group, (this.template[config_id])]);
        }
    }

    callBack && callBack.apply(this);
}

//绘制风格
ImageDrawManager.prototype.draw_style = function(temp_id, callBack) {
    var taht=this;
    this.clear_group();

    this.temp_id = temp_id;

    var config = this.style_config[temp_id];

    for (var c in config) {
        var group = this['group' + config[c].group];
        var index = config[c].index;
        var config_id = config[c].config_id;
        var group_id;
        //设置每个组的属性，主要设置位置

        // group.id('group_' + index);

        if(config_id==undefined){
            config_id=index;
        }

        group_id='group_' + config_id+temp_id;
        group.id(group_id);

        this.draw_group(index,config_id, group);

        if(this._group_config && this._group_config[group_id]){ //恢复用户移动的坐标
            group.x(this._group_config[group_id].x);
            group.y(this._group_config[group_id].y);
        }else{
            group.x(config[c].x);
            group.y(config[c].y);
        }



        this.layer.add(group);
    }

    this.stage.add(this.layer);

    //绑定鼠标经过事件
    this.stage.find('Group').on('mouseover',function(){
        taht.group_mouseover && taht.group_mouseover.apply(taht);
    });

    //绑定鼠标移开事件
    this.stage.find('Group').on('mouseleave',function(){
        taht.group_mouseleave && taht.group_mouseleave.apply(taht);
    });

    callBack && callBack.apply(this);
}

//初始化绘制
ImageDrawManager.prototype.init_draw=function(temp_id,callBack){
    this.custom_template=null;
    this.draw_style(temp_id,callBack);
}

//根据用户输入绘制
ImageDrawManager.prototype.draw_by_custom=function(temp_id,template,callBack){
    this.custom_template=template;
    this.draw_style(temp_id,callBack);
}

// 绘画层的图片，主要是背景图
ImageDrawManager.prototype.draw_layer = function(callBack) {
    var that = this;

    // this.clear_layer();

    this.load_img(this.src, function() {
        var width,
            height,
            scale,
            scaled_img;

        that.imgObj =this;

        if (that.imgObj.height <= that.imgObj.width) {
            height = that.options.height;
            width = that.options.height * that.imgObj.width / that.imgObj.height;
            scale=270/that.imgObj.height;
        } else {
            width = that.options.width;
            height = that.options.width * that.imgObj.height / that.imgObj.width;
            scale=270/that.imgObj.width;
        }

        scaled_img= downScaleImage(this,scale);

        var backgroundImg = new Kinetic.Image({
            x: 0,
            y: 0,
            image: scaled_img,
            width: width,
            height: height,
            draggable: false
        });

        that.backgroundImg = backgroundImg;

        that.layer.add(that.backgroundImg);
        callBack && callBack.apply(that);
    });

}

//绘制
ImageDrawManager.prototype.draw = function(src, callBack) {

    this.src = src;

    this.draw_layer(function() {
        this.stage.add(this.layer);
        callBack && callBack(this.stage);
    });
}

//重绘绘制层
ImageDrawManager.prototype.redraw_layer = function(src, callBack) {
    this.stage.add(this.layer);
}

//加载图片主要用来获取图片的真实宽度和高度
ImageDrawManager.prototype.load_img = function(src, callBack) {
    var imgObj = new Image();

    imgObj.crossOrigin = "anonymous"; //允许convas导出图像数据

    imgObj.onload = function() {
        callBack && callBack.apply(this);
    }
    imgObj.src = src;

}

//获取问上传文件的沙盒URL
ImageDrawManager.prototype.create_object_url = function(file) {
    return (window.URL || window.webkitURL).createObjectURL(file);
}

/*
    根据坐标剪裁图像
    left:   左边距
    top:    上边距
    width:  截取宽度
    height: 截取高度
    zoom:   缩放比例
*/
ImageDrawManager.prototype.cut_img = function(left, top, width, height, zoom, callBack) {
    this.backgroundImg.x((this.options.width * left) / width);
    this.backgroundImg.y((this.options.width * top) / height);
    this.backgroundImg.width(this.imgObj.width * this.options.width / (width * zoom));
    this.backgroundImg.height(this.imgObj.height * this.options.height / (height * zoom));
    this.redraw_layer();
}

//恢复背景图
ImageDrawManager.prototype.recover_cut_img = function(callBack) {
    this.draw_layer(function() {
        this.layer.add(this.group1);
        this.layer.add(this.group2);
        this.layer.add(this.group3);
        this.stage.add(this.layer);
        callBack && callBack(this.stage);
    });
}

//获取图片base64的数据
ImageDrawManager.prototype.get_base64 = function(callBack) {
    this.stage.toDataURL({
        mimeType: 'image/jpeg',
        quality: 1,
        callback: function(data) {
            callBack && callBack(data);
        }
    });
}

//修复文字宽度
ImageDrawManager.prototype.fix_font_size = function(size,original,current) {
    if(current.length<=original.length){
        return size;
    }
    return Math.floor((size*original.length)/current.length);
}

//修复文字y轴,使得文字始终保持在中间
ImageDrawManager.prototype.fix_y = function(y,size,original,current) {
    if(current.length<=original.length){
        return y;
    }
    return y+Math.floor((size-this.fix_font_size(size,original,current)));
}



//图像剪裁类
var ImageCutManager = function(options) {
    var defaults = {
        width: 500,
        minwidth: 270
    }
    this.options = $.extend({}, defaults, options);
}

ImageCutManager.prototype.cut = function(id, img, changeCallBack, callBack) {
    //计算图片最小可选去区域
    if (img.width > this.options.width) {
        zoom_w = zoom_h = this.options.minwidth * (this.options.width / img.width);
    } else {
        zoom_w = zoom_h = Math.min(this.options.width, img.height * (this.options.width / img.width));
    }

    $('#' + id).Jcrop({
        aspectRatio: 1,
        minSize: [zoom_w, zoom_h],
        setSelect: [0, 0, this.options.width, this.options.width],
        onChange: changeCallBack
    }, function() {
        callBack && callBack.apply(this);
    });
}
