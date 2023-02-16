fields = 'id, active_contact_person_id, active_gtcc_detail_id, area_id, category_id, entity_location, env_sap_id, establishment_name, foodwatch_business_id, location_remark, makhani_no, meals_per_day, phone_no, po_box, seating_capacity, status, sub_category_id, subarea_id, trade_license_name, trade_license_no, zone_id'
search_in_details = {
        'establishment_name' : {
            'table_name' : 'public.entity_entity',
            'cell_name' : 'establishment_name',
            'fields': fields
        },
        'trade_license_no' : {
            'table_name' : 'public.entity_entity',
            'cell_name' : 'trade_license_no',
            'fields': fields
        },
        'env_sap_id' : {
            'table_name' : 'public.entity_entity',
            'cell_name' : 'env_sap_id',
            'fields': fields
        },
        'foodwatch_business_id' : {
            'table_name' : 'public.entity_entity',
            'cell_name' : 'foodwatch_business_id',
            'fields': fields
        },
        'phone_no' : {
            'table_name' : 'public.entity_entity',
            'cell_name' : 'phone_no',
            'fields': fields
        },
        'entity_location' : {
            'table_name' : 'public.entity_entity',
            'cell_name' : 'entity_location',
            'fields': fields
        },
        'location_remark' : {
            'table_name' : 'public.entity_entity',
            'cell_name' : 'location_remark',
            'fields': fields
        },
        'po_box' : {
            'table_name' : 'public.entity_entity',
            'cell_name' : 'po_box',
            'fields': fields
        },
        'seating_capacity' : {
            'table_name' : 'public.entity_entity',
            'cell_name' : 'seating_capacity',
            'fields': fields
        },
        'makhani_no' : {
            'table_name' : 'public.entity_entity',
            'cell_name' : 'makhani_no',
            'fields': fields
        },
        'meals_per_day' : {
            'table_name' : 'public.entity_entity',
            'cell_name' : 'meals_per_day',
            'fields': fields
        },
        'status' : {
            'table_name' : 'public.entity_entity',
            'cell_name' : 'status',
            'fields': fields
        },
    }