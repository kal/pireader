/**
 * PiReader Script
 * Author: kal
 */
var PiReader = (function () {

    var my = {};
    var _private = {
        current_feed_id: -0,
        current_item : null,
        local_items : [],
        local_read : []
    };

    my.validate_and_add_subscription = function() {
        var url = $("#feed_url").val();
        try {
            if (_private.validate_feed_url(url)) {
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
                headers : {'X-CSRFToken' : _private.getCookie('csrftoken')}});
            }
        } catch (e){
        }
    };

    /**
     * Performs client-side validation of a feed subscription URL
     * @param url - string. The URL to be validated
     * @returns true if the client-side validation is successful, false otherwise.
     */
    _private.validate_feed_url = function (url){
        return true;
    };

    my.load_subscription = function(subscription) {
        var feeds = $('#feeds').empty();
        var categoriesElem = $('<ul id="categories"></ul>').appendTo(feeds);
        var uncategorizedElem = $('<ul id="uncategorized"></ul>').appendTo(feeds);
        if (subscription.categories.length > 0) {
            $.each(subscription.categories, function(category){
                var categoryElem = $('<li><div>' + category.fields.tag + '</div></li>');
                var categoryFeedsElem = $('<ul></ul>');
                $.each(category.feeds, function(ix, feed){
                   _private.__append_feed_element(categoryFeedsElem, feed);
                });
                categoryElem.append(categoryFeedsElem).appendTo(categoryElem);
            });
            feeds.append()
        }
        $.each(subscription.uncategorized, function(ix, feed){
            _private.__append_feed_element(uncategorizedElem, feed);
        });
    };

    _private.__append_feed_element = function(parent, feed){
        console.log(feed);
        if (!feed.is_deleted){
            feed_link = $('<a href="#">' + feed.fields.title + '</a>').click(function(){
                my.load_feed(feed.pk, feed.fields.title);
            });
            var total = feed.fields.keep_count + feed.fields.unread_count;
            feed_count = $('<span class="count"/>').html('(' + total.toString() + ')');
            $('<li/>').append(feed_link).append(feed_count).appendTo(parent);
        }
    };

    my.load_feed = function (feed_id, feed_title){
        console.log('Loading feed ' + feed_title);
        _private.reset(feed_id, feed_title);
        $('#feed_actions').show();
        $('#items_title').html(feed_title);
        $('#items_content').empty().html('Loading feed items...');
        $.get('subscriptions/' + feed_id, callback = function(data, textStatus, xhr){
            _private.local_items = data;
            _private.refresh();
        })
    };

    _private.__render_item = function (item){
        var item_wrapper = $('<div></div>')
            .addClass('item').
            data('ref', item['ref']);
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
    };

    my.mark_all_read = function(){
        if (_private.current_feed_id > 0){
            var subscriptionUri = './subscriptions/' + _private.current_feed_id;
            var postData = {'read_all' : -1};
            $.ajax({
                url : subscriptionUri,
                method : 'POST',
                processData : false,
                data : JSON.stringify(postData),
                dataType : 'json',
                statusCode : {
                    200 : function(data, textStatus, jqXHR) {
                        _private.local_items = [];
                        _private.refresh();
                        }
                },
                headers : {'X-CSRFToken' : _private.getCookie('csrftoken')}
            });
        }
    };

    my.restore = function() {
        if (_private.current_feed_id > 0){
            var subscriptionUri = './subscriptions/' + _private.current_feed_id;
            var postData = {'restore_all' : 1};
            $.ajax({
                url : subscriptionUri,
                method : 'POST',
                processData : false,
                data : JSON.stringify(postData),
                dataType : 'json',
                success : function(data, textStatus, jqXHR) {
                    _private.local_items = data;
                    _private.refresh();
                },
                headers : {'X-CSRFToken' : _private.getCookie('csrftoken')}
            });
        }
    };

    _private.getCookie = function(name) {
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
    };

    _private.refresh = function() {
        $('#items_content').empty();
        console.log('Refresh. Current item count ' + _private.local_items.length)
        if (_private.local_items.length) {
            $('#no_items').hide();
            $.each(_private.local_items, function(id, item) {
               $('#items_content').append(_private.__render_item(item));
            });
        } else {
            $('#no_items').show();
        }
    };

    _private.reset = function(feed_id, feed_title) {
        _private.current_feed_id = feed_id;
        _private.feed_title = feed_title;
        _private.local_items = [];
        _private.local_read = [];
    };

    my.set_current_item = function(item) {
        $('.current').removeClass('current');
        item.addClass('current');
        _private.set_current_item(item.data('ref'));
    };

    _private.set_current_item = function(ref) {
        if (_private.current_item == ref) {
            return;
        }
        if (_private.local_read.indexOf(ref) < 0){
            _private.local_read.push(ref);
            console.log(_private.local_read);
        }
    }

    my.cmd_next_item = function(ref) {
        var cur = $('.current').first();
        if (cur.length > 0) {
            var nxt = cur.next('.item');
            if (nxt.length > 0) {
                my.set_current_item(nxt);
            }
        } else {
            my.set_current_item($('.item').first());
        }
    };

    return my;
}());