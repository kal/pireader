/**
 * PiReader Script
 * Author: kal
 */
var PiReader = (function () {

    var FeedUpdates = (function(feed_id, read, keep, unkeep) {
        var my = {
            feed_id: feed_id
        };

        var is_dirty = false;
        var operations = {
            read : read || [],
            keep : keep || [],
            unkeep : unkeep || []
        };

        my.isDirty = function() {
            return is_dirty;
        };

        my.mark_read = function(ref) {
            if (operations.keep.indexOf(ref) >= 0) {
                // Item is in our keep list
                return;
            }
            if (operations.read.indexOf(ref) < 0){
                operations.read.push(ref);
                is_dirty = true;
            }
        };

        my.keep = function(ref) {
            var ix = operations.read.indexOf(ref);
            if (ix >= 0) {
                operations.read.splice(ix, 1);
            }
            if (operations.keep.indexOf(ref) < 0){
                operations.keep.push(ref);
                is_dirty = true;
            }
        };

        my.unkeep = function(ref) {
            if (operations.unkeep.indexOf(ref) < 0){
                operations.unkeep.push(ref);
                is_dirty = true;
            }
        };

        my.clone = function() {
            return  {
                read : operations.read.slice(),
                keep : operations.keep.slice(),
                unkeep : operations.unkeep.slice()
            };
        };

        my.completed = function(completed){
            my.__removeAll(completed.read, operations.read);
            my.__removeAll(completed.keep, operations.keep);
            my.__removeAll(completed.unkeep, operations.unkeep);
            is_dirty = ((operations.read.length + operations.keep.length + operations.unkeep.length) > 0);
        };

        my.__removeAll = function(items, from){
            if (items.length == 0 || from.length == 0) return;
            for(var i = 0; i < items.length; i++){
                var ix = from.indexOf(items[i]);
                if (ix >= 0){
                    from.splice(ix, 1);
                }
            }
        };

        // Merges items in from into to, avoiding duplicates
        my.__merge = function(from, to){
            // Simple case: if from is empty there is nothing to do
            if (from.length == 0){
                return;
            }
            // Simple case: if to is empty, then make it a copy of from
            if (to.length == 0){
                to = from.slice(0);
            }
            for(var i = 0; i < from.length; i++){
                if (to.indexOf(from[i]) < 0) {
                    to.push(from[i]);
                }
            }
        };

        return my;
    });

    var my = {
    };

    var _private = {
        last_notified : 0,
        current_feed_id: -0,
        current_item : null,
        local_items : [],
        local_read : [],
        feed_updates : {}
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
            $.each(subscription.categories, function(ix, category){
                var categoryElem = $('<li class="folder"><div class="folder-name">' + category.fields.tag + '</div></li>');
                var categoryFeedsElem = $('<ul></ul>');
                $.each(category.fields.feeds, function(ix, feed){
                    _private.__append_feed_element(categoryFeedsElem, feed);
                    _private.register_feed(feed);
                });
                categoryElem.append(categoryFeedsElem).appendTo(categoriesElem);
            });
        }
        $.each(subscription.uncategorized, function(ix, feed){
            _private.__append_feed_element(uncategorizedElem, feed);
            _private.register_feed(feed);
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
        $('#items_loading').show();
        $.get('subscriptions/' + feed_id, callback = function(data, textStatus, xhr){
            $('#items_loading').hide();
            my._refresh_feed_widget(data, 0);
        })
    };

    my.refresh = function(){
        $('#items_loading').show();
        $.get('subscriptions/' + _private.current_feed_id, callback = function(data, textStatus, xhr){
            $('#items_loading').hide();
            my._refresh_feed_widget(data, 0);
        });
    };

    /**
     * Sends an update to the server requesting that all items on the current feed be marked as read
     * On a success status from the server, the local cache of items is cleared and the display refreshed
     */
    my.mark_all_read = function(){
        if (_private.current_feed_id > 0){
            var feed_id = _private.current_feed_id;
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
                        my._refresh_feed_widget([], 0);
                        _private.update_feed_count(feed_id, 0);
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
            var feed_id = _private.current_feed_id;
            var subscriptionUri = './subscriptions/' + feed_id;
            var postData = {'restore_all' : 1};
            $.ajax({
                url : subscriptionUri,
                method : 'POST',
                processData : false,
                data : JSON.stringify(postData),
                dataType : 'json',
                success : function(data, textStatus, jqXHR) {
                    my._refresh_feed_widget(data, 0);
                    _private.update_feed_count(feed_id, data.length);
                },
                headers : {'X-CSRFToken' : _private.getCookie('csrftoken')}
            });
        }
    };

    my.render_item = function (item){
        var item_wrapper = $('<div></div>')
            .addClass('item')
            .data('ref', item['ref'])
            .click(function(){
                my.set_current_item(item_wrapper);
            });
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

    my._refresh_feed_widget = function(data, currentIx) {
        data = data || [];
        currentIx = currentIx || 0;
        my.feedWidget.singleItemFeedWidget("option", {items:data, currentIx:currentIx});
    };

    _private.__append_feed_element = function(parent, feed){
        console.log(feed);
        if (!feed.is_deleted){
            feed_link = $('<a href="#"><div class="name-text">' + feed.fields.title + '</div></a>').click(function(){
                my.load_feed(feed.pk, feed.fields.title);
            });
            var total = feed.fields.keep_count + feed.fields.unread_count;
            $('<div class="count"/>').html('(' + total.toString() + ')').appendTo(feed_link);
            var feed_element = $('<li/>')
                .attr('id', 'feed_' + feed.pk)
                .addClass('feed')
                .append(feed_link)
                .appendTo(parent)
                .attr("title", feed.fields.title);

            if (feed.fields.unread_count > 0) {
                feed_element.addClass('unread-items');
            }
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

    _private.register_feed = function(feed){
        var feed_id = feed.pk.toString();
        _private.feed_updates[feed_id] = FeedUpdates(feed_id);
    };

    _private.reset = function(feed_id, feed_title) {
        _private.current_feed_id = feed_id;
        _private.feed_title = feed_title;
        _private.local_items = [];
        _private.local_read = [];
    };

    _private.set_current_item = function(ref) {
        if (_private.current_item == ref) {
            return;
        }
        if (_private.local_read.indexOf(ref) < 0) {
            _private.local_read.push(ref);
            _private.read_item(ref);
        }
    };

    _private.read_item = function(ref){
        _private.feed_updates[_private.current_feed_id].mark_read(ref);
        _private.notify_changes();
    };

    _private.keep_item = function(ref){
        _private.feed_updates[_private.current_feed_id].keep(ref);
        _private.notify_changes();
    };

    _private.unkeep_item = function(ref){
        _private.feed_updates[_private.current_feed_id].unkeep(ref);
        _private.notify_changes();
    };

    _private.notify_changes = function(force) {
        var now = new Date().valueOf();
        if (!force && (now - _private.last_notified < 2000)) {
            console.log("Notification is queued")
            return;
        }
        _private.last_notified = now;
        for (var k in _private.feed_updates) {
            if (_private.feed_updates.hasOwnProperty(k) && _private.feed_updates[k].isDirty()){
                try {
                    console.log("Sending read notification for feed " + k );
                    var subscriptionUri = "./subscriptions/" + k;
                    var postData =  _private.feed_updates[k].clone();
                    $.ajax({
                        url : subscriptionUri,
                        method : 'POST',
                        processData : false,
                        data : JSON.stringify(postData),
                        dataType : 'json',
                        success : function(data, textStatus, jqXHR) {
                            _private.feed_updates[k].completed(postData);
                            if (data.hasOwnProperty('unread_count')){
                                _private.update_feed_count(k, data['unread_count']);
                            }
                        },
                        headers : {'X-CSRFToken' : _private.getCookie('csrftoken')}
                    });
                    break;
                } catch (e){
                    console.log("Notifier caught exception: " + e);
                }
            }
        }
    };

    _private.update_feed_count = function (feed_id, count){
        $('#feed_' + feed_id + ' div.count').html('(' + count.toString() + ')');
        var feed = $('#feed_' + feed_id);
        if (count == 0) {
            feed.removeClass('unread-items');
        } else {
            feed.addClass('unread-items');
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

    my.init = function(feedWidget) {
        var self = this;
        var that = _private;
        this.feedWidget = feedWidget;
        this.feedWidget
            .bind('fwdisplayitem', function(event, data){
                _private.set_current_item(data.item['ref']);
            }).bind('fwreload', function(event) {
                self.restore();
            }).bind('fwkeepchange', function(event, data){
                if (data.item['keep_unread']){
                    _private.keep_item(data.item['ref']);
                } else {
                    _private.unkeep_item(data.item['ref']);
                }
            }).bind('fwfeedend', function(event){
                _private.notify_changes(true);
            })
    };

    return my;
}());