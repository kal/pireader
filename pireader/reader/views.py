from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseBadRequest, HttpResponseServerError, Http404
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core import serializers
import json
import time
from models import Feed, Category
from forms import ImportForm
import feedprocessor
from storage import FeedStore

@ensure_csrf_cookie
@login_required
def index(request):
    """
    Delivers the reader home page
    """
    return render(request, 'reader/index.html')

@login_required
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
                feedprocessor.import_opml(uploaded_file.read(), request.user)
                return HttpResponseRedirect(reverse('reader:index'))
            except:
                import_failed = True
    else:
        form = ImportForm()
    return render(request, 'reader/import.html', {'form':form, 'import_failed':import_failed})


@require_http_methods(["GET", "POST"])
@login_required
def subscriptions(request):
    """
    AJAX interface for the list of subscriptions
    """
    if request.method == "GET":
        data = '{ "categories" : ' + \
            serializers.serialize('json', Category.objects.select_related('feeds').filter(owner=request.user)) + \
            ', "uncategorized" : ' + \
            serializers.serialize('json', Feed.objects.filter(categories__isnull=True, owner=request.user)) + " }"
        return HttpResponse(data, mimetype="application/json")
    elif request.method == "POST":
        try:
            url = request.REQUEST['url']
        except KeyError:
            return HttpResponseBadRequest()
        try:
            new_feed = Feed(url=url, owner=request.user)
            new_feed.save()
            feedprocessor.initialize(new_feed)
            new_feed = Feed.objects.get(pk=new_feed.pk) # reload feed after initialization
            return HttpResponse(serializers.serialize('json', [new_feed]), mimetype='application/json')
        except:
            return HttpResponseServerError()

@login_required
def feed(request, feed_id='0'):
    store = FeedStore()
    try:
        feed = Feed.objects.get(id=int(feed_id))
    except Feed.DoesNotExist:
        print "Cannot find the feed"
        return Http404
    if not feed.owner_id == request.user.id:
        return HttpResponse('Unauthorized', status=401)
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
        if 'keep' in feed_update:
            for item in feed_update['keep']:
                store.keep(feed_id, item)
        if 'unkeep' in feed_update:
            for item in feed_update['unkeep']:
                store.unkeep(feed_id, item)
        if 'read' in feed_update:
            for item in feed_update['read']:
                store.mark_read(feed_id, item)
        if 'read_all' in feed_update:
            if feed_update['read_all'] < 0:
                store.mark_all_read(feed_id)
        if 'restore_all' in feed_update:
            store.restore_all_items(feed_id)
            entries = store.get_entries(feed_id)
            return HttpResponse(json.dumps(entries, cls=TimeHandlingEncoder), mimetype='application/json')
        if 'refresh' in feed_update:
            feedprocessor.process_feed(feed_id)
            entries = store.get_entries(feed_id)
            return HttpResponse(json.dumps(entries, cls=TimeHandlingEncoder), mimetype='application/json')

        return HttpResponse('OK', status=200)
    elif request.method == "DELETE":
        feed.is_deleted = True
        feed.save()
        #if 'tag' in feed_update:
        #    for item_tag in feed_update['tag']:
        #        store.tag_item(item_tag['item'], item_tag['tag'])
        return HttpResponse()

class TimeHandlingEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, time.struct_time):
            return time.strftime('%Y-%m-%dT%H:%M:%S', o)
        return json.JSONEncoder.default(self, o)