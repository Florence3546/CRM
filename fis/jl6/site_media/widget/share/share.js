define(["template"],
    function( template ){
        var generate_share_link = function(content){
            var tpl = __inline("share.html");
            return template.compile(tpl)({'content':content}) ;
        };
        
        return {
            show : generate_share_link
        }
    }
);