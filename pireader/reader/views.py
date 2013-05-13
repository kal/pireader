from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseBadRequest, HttpResponseServerError, Http404
from django.core.urlresolvers import reverse
from django.views.decorators.http import require_http_methods
from django.views.decorators.gzip import gzip_page
from django.core import serializers
import json
import time
from models import Feed, Category
from forms import ImportForm
import feedprocessor
from storage import FeedStore

def index(request):
    """
    Delivers the reader home page
    """
    context = {
        'categories': Category.objects.select_related('feeds').all(),
        'uncategorized': Feed.objects.filter(categories__isnull=True)
    }
    print context['uncategorized']
    return render(request, 'reader/index.html', context)


def import_subscription(request):
    """
    Forms-based interface for OPML import
    """
    import_failed = False
    if request.method == 'POST':
        form = ImportForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['opml_file']
            try:
                feedprocessor.import_opml(uploaded_file.read())
                return HttpResponseRedirect(reverse('reader:index'))
            except:
                import_failed = True
    else:
        form = ImportForm()
    return render(request, 'reader/import.html', {'form':form, 'import_failed':import_failed})


@require_http_methods(["GET", "POST"])
def subscriptions(request):
    """
    AJAX interface for the list of subscriptions
    """
    if request.method == "GET":
        data = '{ "categories" : ' + \
            serializers.serialize('json', Category.objects.select_related('feeds').all()) + \
            ', "uncategorized" : ' + \
            serializers.serialize('json', Feed.objects.filter(categories__isnull=True)) + " }"
        return HttpResponse(data, mimetype="application/json")
    elif request.method == "POST":
        data = request.read()
        json_feed = json.loads(data)
        try:
            url = json_feed['url']
        except KeyError:
            return HttpResponseBadRequest()
        try:
            new_feed = Feed(url=url)
            new_feed.save()
            feedprocessor.initialize(new_feed)
            new_feed = Feed.objects.get(pk=new_feed.pk) # reload feed after initialization
            return HttpResponse(serializers.serialize('json', [new_feed]), mimetype='application/json')
        except:
            return HttpResponseServerError()


def feed(request, feed_id='0'):
    store = FeedStore()
    try:
        feed = Feed.objects.get(id=int(feed_id))
    except Feed.DoesNotExist:
        print "Cannot find the feed"
        return Http404
    if request.method == "GET":
        skip = 0
        take = None
        if request.GET.has_key('skip'):
            skip = int(request.GET['skip'])
        if request.GET.has_key('take'):
            take = int(request.GET['take'])
        entries = store.get_entries(feed_id, skip=skip, take=take)
        return HttpResponse(json.dumps(entries, cls=TimeHandlingEncoder), mimetype='application/json')
    elif request.method == "POST":
        data = request.read()
        feed_update = json.loads(data)
        store = FeedStore()
        if 'flag' in feed_update:
            for read_item in feed_update['flag']:
                store.keep_unread(feed_id, read_item, True)
        if 'unflag' in feed_update:
            for item in feed_update['unflag']:
                store.keep_unread(feed_id, read_item, False)
        if 'read' in feed_update:
            for read_item in feed_update['read']:
                store.mark_read(feed_id, read_item)
        return HttpResponse()
        #if 'tag' in feed_update:
        #    for item_tag in feed_update['tag']:
        #        store.tag_item(item_tag['item'], item_tag['tag'])


def is_valid_feed(deserialized_object):
    return hasattr(deserialized_object, 'url')

class TimeHandlingEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, time.struct_time):
            return time.strftime('%Y-%m-%dT%H:%M:%S', o)
        return json.JSONEncoder.default(self, o)