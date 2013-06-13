/**
 * Created with PyCharm.
 * User: kal
 * Date: 03/06/13
 * Time: 21:22
 * To change this template use File | Settings | File Templates.
 */

$.widget( "pireader.singleItemFeedWidget" , {
    widgetEventPrefix : 'fw',
    options: {
        items: [],
        currentIx : 0,
        noItemsMessage : "No items left in this feed.",
        noItemsReload : "Show All Items",
        endOfItemsMessage : "You have reached the end of the items available in this feed. Click below or press N to refresh the feed.",
        endOfItemsRefresh : "Refresh Feed"
    },

    _create : function() {
        var self = this;
        this.baseId = this.element.attr('id');
        this.element.addClass('fw-container');
        this.noItems = $('<div/>').addClass('fw-noitems')
            .attr('id', this.baseId + '-noitems')
            .append($('<div/>').addClass('fw-noitems-message').html(this.options.noItemsMessage))
            .append($('<div/>').addClass('fw-noitems-button')
                            .html(this.options.noItemsReload)
                            .button()
                            .bind('click', function(event){
                                self._trigger("reload");
                            }))
            .hide()
            .appendTo(this.element);
        this.itemPane = $('<div/>').addClass('fw-itempane').attr('id', this.baseId + '-item').appendTo(this.element);
        this.content = $('<div/>').addClass('fw-content')
            .attr('id', this.baseId + '-content')
            .appendTo(this.itemPane);

        // Bind keyboard commands
        $('body').keydown(function(event){
            console.log(event.which);
            if (event.which == 78){
                // n
                self.nextItem();
            } else if (event.which == 80) {
                // p
                self.previousItem();
            } else if (event.which == 75){
                // k
                self.toggleKeep();
            }
        });
        this.refresh();
    },

    _setOption: function( key, val ){
        this._super( key, val );
    },

    _setOptions : function ( options ) {
        this._super( options );
        this.refresh();
    },

    refresh : function() {
        var items = this.options.items;
        var ix = this.options.currentIx;

        this.element.height($(document).height() - this.element.offset().top);
        if (items.length > 0) {
            this.noItems.hide();
            this.itemPane.show();
            // Ensure currentIx is in range
            if (ix < 0 || ix > items.length){
                ix = this.options.currentIx = 0;
            }
            // Display current item
            this.refreshItem();
        } else {
            this.noItems.show();
            this.itemPane.hide();
        }
    },

    _renderItem: function(item){
        var self = this;
        var item_wrapper = $('<div></div>')
            .addClass('item')
            .data('ref', item['ref']);
        // Date line
        var item_dateline = $('<div/>').addClass('dateline').appendTo(item_wrapper);
        try {
            var published = new Date(item.published_parsed);
            item_dateline.html(published.toLocaleDateString()).appendTo(item_wrapper);
        } catch (e) {
            // Ignore and just don't display a dateline
        }
        // Article Title
        $('<h3/>').append($('<a/>')
            .attr('href', item.link)
            .attr('target', '_new')
            .html(item.title))
            .appendTo(item_wrapper);
        // Byline
        var item_byline = $('<div/>').addClass('byline');
        if (item.author){
            item_byline.html(item.author);
        }
        item_byline.appendTo(item_wrapper);

        // Article content
        var item_body = $('<div/>').addClass('item-body').html(item.summary).appendTo(item_wrapper);

        // Article actions
        var keep_unread = $('<input type="checkbox"/>')
                        .attr('id', this.baseId + '-keep')
                        .change(function(event){
                                item['keep_unread'] = this.checked;
                                self._trigger('keepchange', null, {item: item});
                        });
        if (item['keep_unread']){
            keep_unread.attr('checked', 'true');
        }

        $('<div/>').addClass('fw-actions')
            .attr('id', this.baseId + '-actions')
            .append($('<label>Keep Unread</label>').attr('for', this.baseId + '-keep'))
            .append(keep_unread)
            .appendTo(item_wrapper);

        return item_wrapper;
    },

    nextItem : function() {
        console.log("Next");
        this.options.currentIx = this.options.currentIx + 1;
        if (this.options.currentIx >= this.options.items.length){
            // -1 =  Display "End of Feed" Message
            this.options.currentIx = -1;
            this._trigger('feedend');
        }
        this.refreshItem();
    },

    previousItem : function() {
        console.log("Previous");
        if (this.options.currentIx > 0){
            this.options.currentIx = this.options.currentIx - 1;
        }
        this.refreshItem();
    },

    toggleKeep : function() {
        console.log("Toggle Keep");
        var item = this.options.items[this.options.currentIx];
        item['keep_unread'] = !item['keep_unread'];
        $('#' + this.baseId + '-keep').attr('checked', item['keep_unread']);
        this._trigger('keepchange', null, {item: item});
    },

    refreshItem : function() {
        if (this.options.currentIx < 0){
            // You are at the end of all items
            var self = this;
            this.content.empty().append(
                $('<div />').addClass('notice').html(this.options.endOfItemsMessage)
            ).append($('<div />').html(this.options.endOfItemsRefresh).button().click(function(){
                    self.nextItem()
                }));
            return;
        }
        var item= this.options.items[this.options.currentIx];
        this.content.empty().append(this._renderItem(item));
        this.content.scrollTop(0);
        this.content.scrollLeft(0);
        this._trigger('displayitem', null, {item : item});
    }

});