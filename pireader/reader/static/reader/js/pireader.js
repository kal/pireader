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
        local_read : [],
        queued_notifications : {}
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
     * Renders the list of categories and feeds retrieved for a subscription
     * @param subscription
     */
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

    /**
     * Makes the specified feed the new selected feed and retrieves
     * items from the server
     * @param feed_id
     * @param feed_title
     */
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

    /**
     * Sends an update to the server requesting that all items on the current feed be marked as read
     * On a success status from the server, the local cache of items is cleared and the display refreshed
     */
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

    /**
     * Sends an update request to the server asking for all items previously marked as read
     * to be returned to an unread status.
     * On a success, the server will respond with the first page of unread items and this will
     * be locally cached and the display updated
     */
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

    /**
     * Updates the view to render the specified item as current
     * and then invokes _private.set_current_item to ensure that
     * the previous item is marked as read.
     * @param item
     */
    my.set_current_item = function(item) {
        $('.current').removeClass('current');
        item.addClass('current');
        _private.set_current_item(item.data('ref'));
    };

    /**
     * Handles the keyboard command to advance to the next unread item
     * If there is no current item, then the first item in the list becomes
     * the current item.
     */
    my.cmd_next_item = function() {
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

    /**
     * Performs client-side validation of a feed subscription URL
     * @param url - string. The URL to be validated
     * @returns true if the client-side validation is successful, false otherwise.
     */
    _private.validate_feed_url = function (url){
        return true;
    };

    _private.__append_feed_element = function(parent, feed){
        console.log(feed);
        if (!feed.is_deleted){
            feed_link = $('<a href="#">' + feed.fields.title + '</a>').click(function(){
                my.load_feed(feed.pk, feed.fields.title);
            });
            var total = feed.fields.keep_count + feed.fields.unread_count;
            feed_count = $('<span class="count"/>').html('(' + total.toString() + ')');
            $('<li/>').attr('id', 'feed_' + feed.pk).append(feed_link).append(feed_count).appendTo(parent);
        }
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

        // Article actions
        var actions = $('<div/>').addClass('actions')
            .append('<label>Keep Unread: </label>')
            .append($('<input type="checkbox" />').val(item.hasOwnProperty('keep_unread') && item['keep_unread']))
            .appendTo(item_wrapper);

        return item_wrapper;
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
        _private.queued_notifications[feed_id] = [];
    };

    _private.set_current_item = function(ref) {
        if (_private.current_item == ref) {
            return;
        }
        if (_private.local_read.indexOf(ref) < 0){
            _private.local_read.push(ref);
            _private.queued_notifications[_private.current_feed_id].push(ref);
        }
    };

    _private.notifier = function() {
        for (var k in _private.queued_notifications) {
            if (_private.queued_notifications.hasOwnProperty(k)){
            if (_private.queued_notifications[k].length > 0){
                console.log("Sending read notification for feed " + k );
                var subscriptionUri = "./subscriptions/" + k;
                var read_items = _private.queued_notifications[k].slice(0);
                var postData = {read : read_items };
                $.ajax({
                    url : subscriptionUri,
                    method : 'POST',
                    processData : false,
                    data : JSON.stringify(postData),
                    dataType : 'json',
                    statusCode : {
                        200 : function(data, textStatus, jqXHR) {
                            read_items.map(function(item) {
                                var ix = _private.queued_notifications[k].indexOf(item);
                                if (ix >= 0){
                                    _private.queued_notifications[k].splice(ix, 1);
                                }
                            });
                            if (data.hasOwnProperty('unread_count')){
                                _private.update_feed_count(k, data['unread_count']);
                            }
                        }
                    },
                    headers : {'X-CSRFToken' : _private.getCookie('csrftoken')}
                });
                break;
            }
            }
        }
        setTimeout(_private.notifier, 10000);
    };

    _private.update_feed_count = function (feed_id, count){
        $('#feed_' + feed_id + ' > .count').html('(' + count.toString() + ')');
    };

    _private.notifier();

    return my;
}());