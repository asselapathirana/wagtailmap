from  datetime import date
from django.db import models
from django.db.models import Q
from wagtail.wagtailcore.fields import RichTextField

from wagtail.wagtailcore.models import Page, Orderable
from wagtail.wagtailadmin.edit_handlers import FieldPanel, MultiFieldPanel, \
    InlinePanel, PageChooserPanel

from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtailimages.models import Image
from wagtail.wagtaildocs.edit_handlers import DocumentChooserPanel
from wagtail.wagtailsearch import index

from modelcluster.fields import ParentalKey

import geopy
from geopy.distance import VincentyDistance
from geopy.distance import vincenty
from geopy.geocoders import get_geocoder_for_service
from geopy.exc import GeocoderUnavailable




GEOCODING_SERVICE = 'google'
GOOGLE_MAPS_KEY = 'AIzaSyA3GpN-eFyREu8PkuNSC1y9J2g8MXtLldk'

EVENT_AUDIENCE_CHOICES = (
    ('public', "Public"),
    ('private', "Private"),
)



class Location(models.Model):
    class CouldNotGeocode(Exception):
        pass

    SEARCH_RADIUS = 10
    COMPASS_BEARING = {
        'NORTH': 0,
        'EAST': 90,
        'SOUTH': 180,
        'WEST': 270,
    }

    name = models.CharField(max_length=255,
                            blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
 
    def __str__(self):
        return self.name

    def translate_point(self, bearing):
        origin = geopy.Point(self.latitude, self.longitude)
        destination = VincentyDistance(
            kilometers=self.SEARCH_RADIUS
        ).destination(origin, bearing)
        return destination

    def make_bounding_box(self, radius):
        max_lat = self.translate_point(
            self.COMPASS_BEARING['NORTH']
        ).latitude
        min_lat = self.translate_point(
            self.COMPASS_BEARING['SOUTH']
        ).latitude
        max_long = self.translate_point(
            self.COMPASS_BEARING['EAST']
        ).longitude
        min_long = self.translate_point(
            self.COMPASS_BEARING['WEST']
        ).longitude
        # Fetch locations within the bounding box
        locations = Location.objects.filter(
            latitude__gte=min_lat,
            latitude__lte=max_lat,
            longitude__gte=min_long,
            longitude__lte=max_long
        )
        return locations

    def vincenty_filter(self, locations, radius):
        nearby_locations = []
        for location in locations:
            distance = vincenty(
                (self.latitude, self.longitude),
                (location.latitude, location.longitude)
            ).kilometers
            if distance <= self.SEARCH_RADIUS:
                nearby_locations.append(location)
        return nearby_locations

    def find_nearby_locations(self):
        bb_locations = self.make_bounding_box(self.SEARCH_RADIUS)
        return self.vincenty_filter(bb_locations, self.SEARCH_RADIUS)

    def geocode(self):
        geocoder_for_service = get_geocoder_for_service(GEOCODING_SERVICE)
        geocoder = geocoder_for_service(api_key=GOOGLE_MAPS_KEY)
        geocoded_location = geocoder.geocode(self.name)
        if geocoded_location:
            self.latitude = geocoded_location.latitude
            self.longitude = geocoded_location.longitude
        else:
            raise self.CouldNotGeocode("Location: "+self.name)

    def save(self, *args, **kwargs):
        try:
            self.geocode()
            super(Location, self).save(*args, **kwargs)
        except (GeocoderUnavailable, self.CouldNotGeocode) as e:
            pass


class Locatable(models.Model):
    location_name = models.CharField(
        max_length=255,
        blank=True)
    location = models.ForeignKey(
        'home.Location',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        editable=False
    )

    def save_location(self):
        if self.location_name:
            self.location = Location.objects.get_or_create(
                # iexact doesn't work with get_or_create :(
                name=self.location_name.upper()
            )[0]
            self.location.save()
        if not self.location_name and self.location:
            # If self.location_name has been set to None,
            # make sure to set self.location to None
            self.location = None

    @staticmethod
    def search_locations(q):
        location = Location()
        location.name = q
        try:
            location.geocode()
        except (GeocoderUnavailable, Location.CouldNotGeocode) as e:
            return Location.objects.all()
	
        return location.find_nearby_locations()

    def search_children_locations(self, q, model):
        return model.objects.filter(
            location__in=self.search_locations(q)
        ).child_of(self).live()

    def search_sibling_locations(self, q):
        return self.__class__.objects.filter(
            location__in=self.search_locations(q)
        ).sibling_of(self).live()

    panels = [
        FieldPanel('location_name')
    ]

    class Meta:
        abstract = True


#class HomePage(Page):
#    pass

class DummyHomePage(Page):
    pass



# A couple of abstract classes that contain commonly used fields

class LinkFields(models.Model):
    link_external = models.URLField("External link", blank=True)
    link_page = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        related_name='+'
    )
    link_document = models.ForeignKey(
        'wagtaildocs.Document',
        null=True,
        blank=True,
        related_name='+'
    )

    @property
    def link(self):
        if self.link_page:
            return self.link_page.url
        elif self.link_document:
            return self.link_document.url
        else:
            return self.link_external

    panels = [
        FieldPanel('link_external'),
        PageChooserPanel('link_page'),
        DocumentChooserPanel('link_document'),
    ]

    class Meta:
        abstract = True



# Related links

class RelatedLink(LinkFields):
    title = models.CharField(max_length=255, help_text="Link title")

    panels = [
        FieldPanel('title'),
        MultiFieldPanel(LinkFields.panels, "Link"),
    ]

    class Meta:
        abstract = True

# Event index page

class EventIndexPageRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('home.EventIndexPageGeo', related_name='related_links')


class EventIndexPageRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('home.EventIndexPageGeo', related_name='related_links')



class EventIndexPageGeo(Page, Locatable):
    intro = RichTextField(blank=True)

    search_fields = Page.search_fields + (
        index.SearchField('intro',partial_match=True),
    )

    @property
    def events(self):
        # Get list of live event pages that are descendants of this page
        events = EventPageGeo.objects.live().descendant_of(self)

        # Filter events list to get ones that are either
        # running now ohttps://search.yahoo.com/yhs/searchh?hspart=ddc&hsimp=yhs-linuxmint&type=__alt__ddc_linuxmint_com&p=filtering+a+pagequery+setr start in the future
        events=events.filter(Q(date_from__gte=date.today()) | Q(date_to__gte=date.today()))
        print(events)
        # Order by date
        events = events.order_by('date_from')
        print (events)
        return events

    def get_context(self, request, *args, **kwargs):
        q = request.GET.get('q', '')
        location=Location()
        location.name=q
        if q:
            try:
               location.geocode()
            except (GeocoderUnavailable, location.CouldNotGeocode) as e:
              pages = EventPageGeo.objects.child_of(self).live()
            
            pages = self.search_children_locations(q, EventPageGeo)
	    
        else:
            pages = EventPageGeo.objects.child_of(self).live()
        return {
            'self': self,
            'request': request,
            'GOOGLE_MAPS_KEY': GOOGLE_MAPS_KEY,
            'pages': pages,
	    'query': location
        }

    def save(self, *args, **kwargs):
        self.save_location()
        super(EventIndexPageGeo, self).save(*args, **kwargs)



EventIndexPageGeo.content_panels = [ FieldPanel('title', classname="full title") ] + Locatable.panels \
    + [ FieldPanel('intro', classname="full"),
       InlinePanel(EventIndexPageGeo, 'related_links', label="Related links"), ]


class EventPageGeoRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('home.EventPageGeo', related_name='related_links')


class EventPageGeoSpeaker(Orderable, LinkFields):
    page = ParentalKey('home.EventPageGeo', related_name='speakers')
    first_name = models.CharField("Name", max_length=255, blank=True)
    last_name = models.CharField("Surname", max_length=255, blank=True)
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    @property
    def name_display(self):
        return self.first_name + " " + self.last_name

    panels = [
        FieldPanel('first_name'),
        FieldPanel('last_name'),
        ImageChooserPanel('image'),
        MultiFieldPanel(LinkFields.panels, "Link"),
    ]
    
    



class EventPageGeo(Page, Locatable):
    date_from = models.DateField("Start date",default=date.today())
    date_to = models.DateField(
        "End date",
        null=True,
        blank=True,
        help_text="Not required if event is on a single day"
    )

    time_from = models.TimeField("Start time", null=True, blank=True)
    time_to = models.TimeField("End time", null=True, blank=True)
    audience = models.CharField(max_length=255, choices=EVENT_AUDIENCE_CHOICES, default='public')
    text = RichTextField(blank=True)
    cost = models.CharField(max_length=255,default="Free")
    signup_link = models.URLField(blank=True)
    feed_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    def get_context(self, request, *args, **kwargs):
        return {
            'self': self,
            'request': request,
            'GOOGLE_MAPS_KEY': GOOGLE_MAPS_KEY,
            'pages': self.search_sibling_locations(
                request.GET.get('q', self.location_name)
            )
        }

    def save(self, *args, **kwargs):
        self.save_location()
        super(EventPageGeo, self).save(*args, **kwargs)


EventPageGeo.content_panels = [
    FieldPanel('title', classname="full title"),
] +Locatable.panels + [
    FieldPanel('date_from'),
    FieldPanel('date_to'),
    FieldPanel('time_from'),
    FieldPanel('time_to'),
    FieldPanel('audience'),
    FieldPanel('cost'),
    FieldPanel('signup_link'),
   # InlinePanel(EventPageGeo, 'carousel_items', label="Carousel items"),
    FieldPanel('text', classname="full"),
    InlinePanel(EventPageGeo, 'speakers', label="Speakers"),
    InlinePanel(EventPageGeo, 'related_links', label="Related links"),
]

EventPageGeo.promote_panels = Page.promote_panels + [
    ImageChooserPanel('feed_image'),
]
