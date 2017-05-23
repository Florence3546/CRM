/**
 * Created by Administrator on 2015/9/24.
 */
define(['jquery','tag_editor','caret'],function() {
    "use strict"



    var tagEditor = function(obj,options){

        if(!options||!options.animateDelete){
            options.animateDelete=0;
        }

        obj.tagEditor(options);

        if(options&&options.close=='show'){
            $('.tag-editor-delete').find('i').css('visibility','visible');
        }

        //获取标签
        var getTags = function(){
            return obj.tagEditor('getTags')[0].tags;
        }

        //添加标签
        var addTag = function(tag){
            if(getTags().indexOf(tag)>-1){
                return false;
            }
            obj.tagEditor('addTag',tag);
        }

        //移除指定标签
        var removeTag = function(tag){
            obj.tagEditor('removeTag', tag);
        }

        //移除所有标签
        var removeAll = function(){
            obj.text('');
            var tags = obj.tagEditor('getTags')[0].tags;
            for (var i = 0; i < tags.length; i++) {
                obj.tagEditor('removeTag', tags[i]);
            }
        };

        //聚焦事件
        var focus = function(callback){
            if(callback){
                options.callback = callback;
            }else{
                obj.next('ul').click();
            }
        };

        //聚焦事件实际上是tageditor的点击事件
        obj.next('ul').click(function(){
            if(options&&options.callback){
                options.callback();
            }
        });

        var getValue = function(){
            var value = '';
            var tags = this.getTags();
            for(var i in tags){
                value+=tags[i];
            }
            return value;
        };

        var destroy = function(){
             obj.tagEditor('destroy');
        }

        return {
            getTags:getTags,
            addTag:addTag,
            removeTag:removeTag,
            removeAll:removeAll,
            focus:focus,
            getValue:getValue,
            destroy:destroy
        }
    };



    return {
        tagEditor:function(obj,options){
            return new tagEditor(obj,options);
        }
    }
});