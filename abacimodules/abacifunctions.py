import pandas as pd
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from .abaci_dicts import search_in_details

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def name_maker(contact_person_temp):
    splitted_name = contact_person_temp.split(' ')    
    if(len(splitted_name)>=2):
        firstNameTemp = splitted_name[0]
        del splitted_name[0]
        lastNameTemp = splitted_name[0]
        del splitted_name[0]
        for name in splitted_name:
            lastNameTemp += ' ' + name
    elif(len(splitted_name) == 1):
        firstNameTemp = contact_person_temp
        lastNameTemp = None
    return (firstNameTemp, lastNameTemp)

def get_data_from_db(command):
    cursor = connection.cursor()
    cursor.execute(command)
    data = cursor.fetchall()
    cursor.close()
    return data

def df_maker(data):
    df = pd.DataFrame(data=data)
    count = df.iloc[:,-1][0]
    df = df.iloc[: , :-1]
    return count, df

def smart_search_response_creator(**kwargs):
    # This function returns the search results and count, or count only
    search_in = kwargs.get('search_in', None)
    if (search_in == None):
        response = {'error' : 'search_in needs to be provided !'}
        return Response(response, status=status.HTTP_404_NOT_FOUND)
    search_text = kwargs.get('search_text', None)   
    if (search_text == None):
        response = {'error' : 'search_text needs to be provided !'}
        return Response(response, status=status.HTTP_404_NOT_FOUND)
    search_type = kwargs.get('search_type', None)   
    if (search_type == None):
        response = {'error' : 'search_type needs to be provided !'}
        return Response(response, status=status.HTTP_404_NOT_FOUND)
    search_type = search_type[0]
    search_text = '%' + str(search_text[0]).lower() + '%'
    
    search_table_details = search_in_details.get(search_in[0],None)
    if (search_table_details == None):
        response = {'error' : 'invalid search_in details !'}
        return Response(response, status=status.HTTP_404_NOT_FOUND)
    if (search_type not in ['results', 'count', 'filter']):
        response = {'error' : 'invalid search_type details !'}
        return Response(response, status=status.HTTP_404_NOT_FOUND)
    filters = filter_creator(kwargs)
    limit = int(kwargs.get('limit', [10])[0])
    page = int(kwargs.get('page', [1])[0])
    order_by = kwargs.get('ordering', ['ASC'])[0]
    print(order_by)
    if (search_type == 'results'):
        search_fields = search_table_details['fields']
        command =   f"SELECT {search_fields}, count(*) OVER() AS count"\
            f" FROM {search_table_details['table_name']}"\
            f" WHERE LOWER({search_table_details['cell_name']})"\
            f" LIKE '{search_text}'"\
            f" {filters}"\
            f" ORDER  BY establishment_name {order_by}"\
            f" OFFSET {(page - 1)*limit}"\
            f" LIMIT {limit}"

        data = get_data_from_db(command)
        if (len(data) == 0):
            response = {'error' : "No records are available !"}
            return Response(response, status=status.HTTP_404_NOT_FOUND)
        count, df = df_maker(data)
        df.columns = search_table_details['fields'].split(', ')
        response = {
            "data": df.to_dict(orient="records"),
            "count" : count
        }
        return Response(response, status=status.HTTP_200_OK)
    elif (search_type == 'count'):
        command =   f"SELECT count(*)"\
            f" FROM {search_table_details['table_name']}"\
            f" WHERE LOWER({search_table_details['cell_name']})"\
            f" LIKE '{search_text}'"\
            f" {filters}"
        print(command)
        response = {
            'count' : get_data_from_db(command)[0][0]
        }
        return Response(response, status=status.HTTP_200_OK)
    elif (search_type == 'filter'):
        filter_on = kwargs.get('filter_on',None)
        if (filter_on == None):
            response = {'error' : "filter_on is required !"}
            return Response(response, status=status.HTTP_404_NOT_FOUND)
        filter_on = filter_on[0]
        # breakpoint()
        command_dic = {
            'zone' : f"SELECT zone_id, zone_name, count(*)"\
                        f" FROM {search_table_details['table_name']}"\
                        f" JOIN public.masters_zone ON zone_id=public.masters_zone.id"\
                        f" WHERE LOWER({search_table_details['cell_name']})"\
                        f" LIKE '{search_text}'"\
                        f" {filters}"\
                        f'GROUP BY zone_id,zone_name',
            'area' : f"SELECT area_id, area, count(*)"\
                        f" FROM {search_table_details['table_name']}"\
                        f" JOIN public.masters_area ON area_id=public.masters_area.id"\
                        f" WHERE LOWER({search_table_details['cell_name']})"\
                        f" LIKE '{search_text}'"\
                        f" {filters}"\
                        f'GROUP BY area_id,area',
            'subarea' : f"SELECT subarea_id, sub_area, count(*)"\
                        f" FROM {search_table_details['table_name']}"\
                        f" JOIN public.masters_subarea ON subarea_id=public.masters_subarea.id"\
                        f" WHERE LOWER({search_table_details['cell_name']})"\
                        f" LIKE '{search_text}'"\
                        f" {filters}"\
                        f'GROUP BY subarea_id,sub_area',
                        }
        # breakpoint()
        data = get_data_from_db(command_dic[filter_on])
        if (len(data) == 0):
            response = {'error' : "No records are available !"}
            return Response(response, status=status.HTTP_404_NOT_FOUND)
        df = pd.DataFrame(data=data)
        df.columns = ['id','name','count']
        response = {
            "data": df.to_dict(orient="records"),
        }
        # return Response(command_dic[filter_on], status=status.HTTP_200_OK) 
        return Response(response, status=status.HTTP_200_OK) 
    
def filter_creator(kwargs):
    joining_in_tables = False
    if (kwargs.get('search_type') == ['filter']):
        joining_in_tables = True
    # breakpoint()
    keysList = list(kwargs.keys())
    filters = ''
    dic_with_joining = {
        'zone_id' : 'public.entity_entity.zone_id',
        'area_id' : 'public.entity_entity.area_id',
        'subarea_id' : 'public.entity_entity.subarea_id',
    }
    for item in keysList:
        if '_isfilter' in item:
            key = item.split('_isfilter')[0]
            value = kwargs[item][0]
            if joining_in_tables:
                filters += f"and {dic_with_joining[key]}={value} "
            else:
                filters += f"and {key}={value} "
    return filters         


def get_locations_for_smart_search(type_of_loc):
    command = ''
    if (type_of_loc == 'zone'):
        required_fields = 'id, zone_name'
        command = f'SELECT {required_fields}, count(*) OVER() AS full_count FROM public.masters_zone'
    elif (type_of_loc == 'area'):
        required_fields = 'id, area'
        command = f'SELECT {required_fields}, count(*) OVER() AS full_count FROM public.masters_area'
    elif (type_of_loc == 'subarea'):
        required_fields = 'id, sub_area'
        command = f'SELECT {required_fields}, count(*) OVER() AS full_count FROM public.masters_subarea'

    data = get_data_from_db(command)
    if (len(data) == 0):
        response = {'error' : "No records are available !"}
        return Response(response, status=status.HTTP_404_NOT_FOUND)
    count, df = df_maker(data)
    # breakpoint()
    df.columns = ['id','name']
    response = {
        "data": df.to_dict(orient="records"),
        "count" : count
    }
    return Response(response, status=status.HTTP_200_OK)


