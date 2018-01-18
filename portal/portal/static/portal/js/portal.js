$(document).ready(function () {
    //    $("#marketplace").on('load', function () {
    /*
    //$(this).height($(this).contents().find("body").height());
    var valueSize = $(this).offset();
    console.log("offset: " + $(this).offset());
    var totalsize = (valueSize.top * 2) + valueSize.left;
    //style="min-height: 400px"
    $(this).height(totalsize);
    */
    //$(this).css('height', $(this).contents().find('body').height() + 'px')
    //$(this).height($(this).contents().find("body").height());
    //console.log("height: " + $(this).contents().find("body").height());
    //    });
});


function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

$.ajaxSetup({
    beforeSend: function (xhr, settings) {
        if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
            // Only send the token to relative URLs i.e. locally.
            xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
        }
    }
});