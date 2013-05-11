/**
 * PiReader Script
 * Author: kal
 */

function validate_and_add_subscription($){
    var url = $("#feed_url").value();
    try {
        url = validate_feed_url(url);
        $.post("./subscriptions", {'url':url}, function(data, textStatus, jqXHR){
            $('#categories').append("<li><a href='" + data.html_url + "'>"+ data.title + "</a></li>");
        }, 'json' )
    } catch (e){
        return;
    }
}