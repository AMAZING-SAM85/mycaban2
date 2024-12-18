from django_filters import rest_framework as filters
from .models import Property

class PropertyFilter(filters.FilterSet):
    min_price = filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = filters.NumberFilter(field_name='price', lookup_expr='lte')
    property_type = filters.CharFilter(field_name='property_type')
    listing_type = filters.CharFilter(field_name='listing_type')
    location = filters.CharFilter(field_name='location', lookup_expr='icontains')
    amenities = filters.CharFilter(method='filter_amenities')
    
    class Meta:
        model = Property
        fields = ['min_price', 'max_price', 'property_type', 'listing_type', 'location']
    
    def filter_amenities(self, queryset, name, value):
        amenities = value.split(',')
        return queryset.filter(amenities__name__in=amenities).distinct()