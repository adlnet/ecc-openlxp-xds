from configurations.models import XDSUIConfiguration
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.forms import ValidationError
from django.urls import reverse
from model_utils.models import TimeStampedModel


class SearchFilter(TimeStampedModel):
    """Model to contain fields used for filtering search results"""
    FILTER_TYPE_CHOICES = [
        ('terms', 'Checkbox'),
    ]
    display_name = models.CharField(
        max_length=200,
        help_text='Enter the display name of the field to filter on')
    field_name = models.CharField(
        max_length=200,
        help_text='Enter the metadata field name as displayed in Elasticsearch'
                  ' e.g. course.title'
    )
    xds_ui_configuration = models.ForeignKey(XDSUIConfiguration,
                                             on_delete=models.CASCADE)
    filter_type = models.CharField(
        max_length=200,
        choices=FILTER_TYPE_CHOICES,
        default='terms',
    )

    active = models.BooleanField(default=True)

    def get_absolute_url(self):
        """ URL for displaying individual model records."""
        return reverse('Configuration-detail', args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.id}'


class SearchField(TimeStampedModel):
    """Model to add aditional fields to search by"""
    display_name = models.CharField(
        max_length=200,
        help_text='Enter the display name of the field to search by on')
    field_name = models.CharField(
        max_length=200,
        help_text='Enter the metadata field name as displayed in Elasticsearch'
                  ' e.g. course.title'
    )
    xds_ui_configuration = models.ForeignKey(XDSUIConfiguration,
                                             on_delete=models.CASCADE)

    active = models.BooleanField(default=True)

    def get_absolute_url(self):
        """ URL for displaying individual model records."""
        return reverse('Configuration-detail', args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.id}'


class SearchSortOption(TimeStampedModel):
    """Model to contain options for sorting search results"""

    display_name = models.CharField(
        max_length=200,
        help_text='Enter the display name of the sorting option')
    field_name = models.CharField(
        max_length=200,
        help_text='Enter the metadata field name as displayed in Elasticsearch'
                  ' e.g. course.title'
    )
    xds_ui_configuration = models \
        .ForeignKey(XDSUIConfiguration, on_delete=models.CASCADE,
                    related_name='search_sort_options')
    active = models.BooleanField(default=True)

    def get_absolute_url(self):
        """ URL for displaying individual model records."""
        return reverse('search-sort-option', args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.id}'


class CourseDetailHighlight(TimeStampedModel):
    """Model to contain course detail fields to display on results"""
    HIGHLIGHT_ICON_CHOICES = [
        ('clock', 'clock'),
        ('hourglass', 'hourglass'),
        ('user', 'user'),
        ('multi_users', 'multi_users'),
        ('location', 'location'),
        ('calendar', 'calendar'),
    ]

    display_name = models.CharField(
        max_length=200,
        help_text='Enter the display name of the sorting option')
    field_name = models.CharField(
        max_length=200,
        help_text='Enter the metadata field name as displayed in Elasticsearch'
                  ' e.g. course.title'
    )
    xds_ui_configuration = models \
        .ForeignKey(XDSUIConfiguration, on_delete=models.CASCADE,
                    related_name='course_highlights')
    active = models.BooleanField(default=True)
    highlight_icon = models.CharField(
        max_length=200,
        choices=HIGHLIGHT_ICON_CHOICES,
        default='user',
    )
    rank = \
        models.IntegerField(default=1,
                            help_text="Order in which highlight show on the "
                                      "course detail page (2 items per row)",
                            validators=[MinValueValidator(1,
                                                          "rank should be at "
                                                          "least 1")])

    def get_absolute_url(self):
        """ URL for displaying individual model records."""
        return reverse('course-detail-highlight', args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.id}'

    def save(self, *args, **kwargs):
        num_active_highlights = \
            CourseDetailHighlight.objects.filter(active=True).count()

        # only 8 highlights can be active at any given time
        if num_active_highlights >= 8:
            # if it's a new record and set to active
            if not self.pk:
                raise ValidationError('Max of 8 active highlight fields has '
                                      'been reached.')
            else:
                return super(CourseDetailHighlight, self).save(*args, **kwargs)
        return super(CourseDetailHighlight, self).save(*args, **kwargs)


class CourseSpotlight(TimeStampedModel):
    """Model to define course spotlight objects"""
    course_id = models.CharField(
        max_length=200,
        help_text='Enter the unique Search Engine ID of the course')
    active = models.BooleanField(default=True)

    def get_absolute_url(self):
        """ URL for displaying individual model records."""
        return reverse('course-spotlight', args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.id}'


class Experience(models.Model):
    """Model to store experience instances for interest lists"""

    metadata_key_hash = models.CharField(max_length=200,
                                         primary_key=True)


class InterestList(TimeStampedModel):
    """Model for Interest Lists"""

    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.CASCADE,
                              related_name="interest_lists")
    description = \
        models.TextField(help_text='Enter a description for the list')
    subscribers = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                         related_name="subscriptions")
    experiences = models.ManyToManyField(Experience,
                                         blank=True)
    name = models.CharField(max_length=200,
                            help_text="Enter the name of the list")
    public = models.BooleanField(
        help_text="Make list searchable to other users", default=False)

    def save(self, *args, **kwargs):
        # If item is not public
        if not self.public and self.id is not None:
            # Remove any subscribers
            self.subscribers.clear()
        return super(InterestList, self).save(*args, **kwargs)

    # Custom permission to allow toggling public/private on interest lists
    class Meta:
        permissions = [
            ("can_toggle_public",
             "Can toggle public/private on interest lists"),
        ]


class SavedFilter(TimeStampedModel):
    """Model for Saved Filter"""

    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.CASCADE,
                              related_name="saved_filters")
    name = models.CharField(max_length=200,
                            help_text="Enter the name of the filter")
    query = models.CharField(max_length=200,
                             help_text="queryString for the filter")
