from django.urls import include, path
from rest_framework.routers import DefaultRouter
from xds_api import views

router = DefaultRouter()
router.register(r'experiences/most-saved',
                views.CourseMostSavedViewSet,
                'most-saved-courses')

app_name = 'xds_api'
urlpatterns = [
    path('', include(router.urls)),
    path('spotlight-courses', views.GetSpotlightCoursesView.as_view(),
         name='spotlight-courses'),
    path('experiences/<str:exp_hash>/', views.GetExperiencesView.as_view(),
         name='get_courses'),
    path('interest-lists/', views.InterestListsView.as_view(),
         name='interest-lists'),
    path('interest-lists/<int:list_id>', views.InterestListView.as_view(),
         name='interest-list'),
    path('experiences/<str:exp_hash>/interest-lists',
         views.AddCourseToListsView.as_view(),
         name='add_course_to_lists'),
    path('interest-lists/owned',
         views.InterestListsOwnedView.as_view(),
         name='owned-lists'),
    path('interest-lists/subscriptions',
         views.InterestListsSubscriptionsView.as_view(),
         name='interest-list-subscriptions'),
    path('interest-lists/<int:list_id>/subscribe',
         views.InterestListSubscribeView.as_view(),
         name='interest-list-subscribe'),
    path('interest-lists/<int:list_id>/unsubscribe',
         views.InterestListUnsubscribeView.as_view(),
         name='interest-list-unsubscribe'),
    path('saved-filters/<int:filter_id>', views.SavedFilterView.as_view(),
         name='saved-filter'),
    path('saved-filters/owned',
         views.SavedFiltersOwnedView.as_view(),
         name='owned-filters'),
    path('saved-filters',
         views.SavedFiltersView.as_view(),
         name='saved-filters'),
    path('statements',
         views.StatementForwardView.as_view(),
         name='forward_statements'),
    path('interest-lists/most-subscribed',
         views.InterestListMostSubscribedView.as_view(),
         name='most-subscribed-lists')
]
