from django.db import transaction
from apps.account.models import User
from apps.geography.models import Region
from apps.day_tours.models import DayTour
from apps.itinerary_templates.models import ItineraryTemplate, ItineraryTemplateDay


def run():
    user = User.objects.filter(is_superuser=True).first() or User.objects.first()
    if not user:
        print('ERROR: No users found; cannot create templates without created_by.')
        return

    created = 0
    updated = 0
    attached_days = 0
    skipped_regions = []

    regions = Region.objects.filter(deleted_at__isnull=True, is_active=True).select_related('country').order_by('id')

    for region in regions:
        tours = list(
            DayTour.objects.filter(region=region, deleted_at__isnull=True, is_active=True)
            .order_by('-is_default', 'display_order', 'id')
        )
        if not tours:
            tours = list(
                DayTour.objects.filter(
                    region__country_id=region.country_id,
                    deleted_at__isnull=True,
                    is_active=True,
                ).order_by('-is_default', 'display_order', 'id')
            )
        if not tours:
            skipped_regions.append((region.id, region.name))
            continue

        specs = [
            {
                'key': 'DEF',
                'name': f'{region.name} Default',
                'travel_type': None,
                'is_default': True,
                'includes_night': False,
                'tour': tours[0],
            },
            {
                'key': 'COUPLE',
                'name': f'{region.name} Couple',
                'travel_type': 'COUPLE',
                'is_default': False,
                'includes_night': False,
                'tour': tours[min(1, len(tours) - 1)],
            },
            {
                'key': 'GROUPN',
                'name': f'{region.name} Group Night',
                'travel_type': 'GROUP',
                'is_default': False,
                'includes_night': True,
                'tour': tours[min(2, len(tours) - 1)],
            },
            {
                'key': 'SOLO',
                'name': f'{region.name} Solo',
                'travel_type': 'SOLO',
                'is_default': False,
                'includes_night': False,
                'tour': tours[min(3, len(tours) - 1)],
            },
        ]

        with transaction.atomic():
            ItineraryTemplate.objects.filter(region=region, is_default=True).update(is_default=False)

            for spec in specs:
                code = f'IT-{region.id}-{spec["key"]}'
                obj, was_created = ItineraryTemplate.objects.get_or_create(
                    code=code,
                    defaults={
                        'country': region.country,
                        'region': region,
                        'name': spec['name'],
                        'travel_type': spec['travel_type'],
                        'description': f'Auto-seeded template for {region.name} ({spec["key"]})',
                        'is_default': spec['is_default'],
                        'is_active': True,
                        'includes_night': spec['includes_night'],
                        'created_by': user,
                    },
                )

                if was_created:
                    created += 1
                else:
                    changed = False
                    if obj.country_id != region.country_id:
                        obj.country = region.country
                        changed = True
                    if obj.region_id != region.id:
                        obj.region = region
                        changed = True
                    if obj.name != spec['name']:
                        obj.name = spec['name']
                        changed = True
                    if obj.travel_type != spec['travel_type']:
                        obj.travel_type = spec['travel_type']
                        changed = True
                    if obj.includes_night != spec['includes_night']:
                        obj.includes_night = spec['includes_night']
                        changed = True
                    if obj.is_default != spec['is_default']:
                        obj.is_default = spec['is_default']
                        changed = True
                    if not obj.is_active:
                        obj.is_active = True
                        changed = True
                    if changed:
                        obj.save()
                        updated += 1

                day_obj, day_created = ItineraryTemplateDay.objects.get_or_create(
                    template=obj,
                    day_number=1,
                    defaults={'day_tour': spec['tour'], 'display_order': 1},
                )
                if day_created:
                    attached_days += 1
                elif day_obj.day_tour_id != spec['tour'].id or day_obj.display_order != 1:
                    day_obj.day_tour = spec['tour']
                    day_obj.display_order = 1
                    day_obj.save(update_fields=['day_tour', 'display_order'])
                    attached_days += 1

    print('Template seed completed')
    print('created_templates', created)
    print('updated_templates', updated)
    print('template_day_links_created_or_updated', attached_days)
    print('skipped_regions_no_day_tours', skipped_regions)


run()
