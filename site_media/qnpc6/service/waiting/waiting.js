define("site_media/service/waiting/waiting",["site_media/plugins/jquery/jquery.min","site_media/widget/ajax/ajax","site_media/plugins/owlcarousel/owl.carousel.min"],function(e,i){function a(i){"undefined"!=typeof i.redicrect&&(window.location.href=i.redicrect),"undefined"!=typeof i.finished&&(i.finished?e("#download_progress").animate({width:"100%"},100,function(){e("#download_progress").text("100%"),window.location.href="/qnpc/qnpc_home"}):(e("#download_progress").animate({width:i.progress+"%"},100),e("#download_progress").text(i.progress+"%")))}var n=function(){e("#owl-carousel").owlCarousel({items:1,autoPlay:!0,itemsDesktop:!1}),setInterval(function(){i.ajax("is_data_ready",{},a)},5e3),i.ajax("is_data_ready",{},a)};return{init:n}});