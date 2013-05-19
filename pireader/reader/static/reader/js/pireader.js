/**
 * PiReader Script
 * Author: kal
 */

function validate_and_add_subscription($){
    var url = $("#feed_url").val();
    try {
        if (validate_feed_url(url)) {
            $.ajax({
                type: "POST",
                url : "./subscriptions",
                data : {'url':url},
                success : function(data, textStatus, jqXHR){
                    $('#categories').append("<li><a href='" + data.html_url + "'>"+ data.title + "</a></li>");
                    $('#feed_url').val('');
                    $('#subscribe_form').toggle();
                },
                dataType : 'json',
            headers : {'X-CSRFToken' : getCookie('csrftoken')}});
        }
    } catch (e){
        return;
    }
}

/**
 * Performs client-side validation of a feed subscription URL
 * @param url - string. The URL to be validated
 * @returns true if the client-side validation is successful, false otherwise.
 */
function validate_feed_url(url){
    return true;
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
    $('#items_title').html(feed_title);
    $('#items_content').empty().html('Loading feed items...')
    $.get('subscriptions/' + feed_id, callback = function(data, textStatus, xhr){
        console.log(data);
        $('#items_content').empty();
        $.each(data, function(id, item) {
           $('#items_content').append(render_item(item));
        });
    })
}

function render_item(item){
    var item_wrapper = $('<div></div>')
        .addClass('item');
    // Date line
    var item_dateline = $('<div/>').addClass('dateline').appendTo(item_wrapper);
    try {
        var published = new Date(item.published_parsed);
        item_dateline.html(published.toLocaleDateString()).appendTo(item_wrapper);
    } catch (e) {
        // Ignore and just don't display a dateline
    }
    // Article Title
    $('<h3/>').append($('<a/>').attr('href', item.link).html(item.title)).appendTo(item_wrapper);
    // Byline
    var item_byline = $('<div/>').addClass('byline');
    if (item.author){
        item_byline.html(item.author);
    }
    item_byline.appendTo(item_wrapper);
    // Article content
    var item_body = $('<div/>').addClass('item-body').html(item.summary).appendTo(item_wrapper);
    return item_wrapper;
}

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