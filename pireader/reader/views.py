from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.db.models import F
from models import Feed, Category
from forms import ImportForm
import feedprocessor


def index(request):
    context = {
        'categories': Category.objects.select_related('feeds').all(),
        'uncategorized': Feed.objects.filter(categories__isnull=True)
    }
    print context['uncategorized']
    return render(request, 'reader/index.html', context)


def import_subscription(request):
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