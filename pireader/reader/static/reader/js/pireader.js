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

function load_subscription(subscription){
    var feeds = $('#feeds').empty();
    var categoriesElem = $('<ul id="categories"></ul>').appendTo(feeds);
    var uncategorizedElem = $('<ul id="uncategorized"></ul>').appendTo(feeds);
    if (subscription.categories.length > 0) {
        $.each(subscription.categories, function(category){
            var categoryElem = $('<li><div>' + category.fields.tag + '</div></li>');
            var categoryFeedsElem = $('<ul></ul>');
            $.each(category.feeds, function(ix, feed){
               __append_feed_element(categoryFeedsElem, feed);
            });
            categoryElem.append(categoryFeedsElem).appendTo(categoryElem);
        });
        feeds.append()
    }
    $.each(subscription.uncategorized, function(ix, feed){
        __append_feed_element(uncategorizedElem, feed);
    });

}

function __append_feed_element(parent, feed){
    console.log(feed);
    if (!feed.is_deleted){
        feed_link = $('<a href="#">' + feed.fields.title + '</a>').click(function(){
            load_feed(feed.pk, feed.fields.title);
        });
        $('<li/>').append(feed_link).appendTo(parent);
    }
}

function load_feed(feed_id, feed_title){
    console.log('Loading feed ' + feed_title);
    $.get('subscriptions/' + feed_id, callback = function(data, textStatus, xhr){
        console.log(data);
    })
}

