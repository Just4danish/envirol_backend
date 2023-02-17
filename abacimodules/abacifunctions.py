import pandas as pd
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from .abaci_dicts import search_in_details
from masters.models import SubArea, Area, Zone, MainCategory, SubCategory, GreaseTrap
from entity.models import EntityGTCC
from django.conf import settings
from datetime import datetime
import os

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

def initiate_greasetraps():
    grease_traps = [
                {
                "grease_trap_id": "TP0001",
                "foodwatch_id": None,
                "trap_label": "A",
                "capacity": 40,
                "part_no": "A",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 10,
                "length": 10,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0002",
                "foodwatch_id": None,
                "trap_label": "ACO NS 1 SEPARATOR (OVAL)",
                "capacity": 85,
                "part_no": "ACO NS 1 SEPARATOR (OVAL)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 11,
                "length": 11,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0003",
                "foodwatch_id": None,
                "trap_label": "ACO NS 10 SEPARATOR (OVAL)",
                "capacity": 528,
                "part_no": "ACO NS 10 SEPARATOR (OVAL)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 12,
                "length": 12,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0004",
                "foodwatch_id": None,
                "trap_label": "ACO NS 10 SEPARATOR (ROUND)",
                "capacity": 647,
                "part_no": "ACO NS 10 SEPARATOR (ROUND)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 13,
                "length": 13,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0005",
                "foodwatch_id": None,
                "trap_label": "ACO NS 15 SEPARATOR  ( ROUND)",
                "capacity": 954,
                "part_no": "ACO NS 15 SEPARATOR  ( ROUND)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 14,
                "length": 14,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0006",
                "foodwatch_id": None,
                "trap_label": "ACO NS 2 SEPARATOR (OVAL)",
                "capacity": 116,
                "part_no": "ACO NS 2 SEPARATOR (OVAL)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 15,
                "length": 15,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0007",
                "foodwatch_id": None,
                "trap_label": "ACO NS 2 SEPARATOR (ROUND)",
                "capacity": 180,
                "part_no": "ACO NS 2 SEPARATOR (ROUND)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 16,
                "length": 16,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0008",
                "foodwatch_id": None,
                "trap_label": "ACO NS 20 SEPARATOR ( ROUND)",
                "capacity": 1075,
                "part_no": "ACO NS 20 SEPARATOR ( ROUND)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 17,
                "length": 17,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0009",
                "foodwatch_id": None,
                "trap_label": "ACO NS 3 SEPARATOR (OVAL)",
                "capacity": 166,
                "part_no": "ACO NS 3 SEPARATOR (OVAL)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 18,
                "length": 18,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0010",
                "foodwatch_id": None,
                "trap_label": "ACO NS 30 SEPARATOR (OVAL)",
                "capacity": 1466,
                "part_no": "ACO NS 30 SEPARATOR (OVAL)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 19,
                "length": 19,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0011",
                "foodwatch_id": None,
                "trap_label": "ACO NS 4 SEPARATOR (OVAL)",
                "capacity": 219,
                "part_no": "ACO NS 4 SEPARATOR (OVAL)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 20,
                "length": 20,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0012",
                "foodwatch_id": None,
                "trap_label": "ACO NS 4 SEPARATOR (ROUND)",
                "capacity": 235,
                "part_no": "ACO NS 4 SEPARATOR (ROUND)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 21,
                "length": 21,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0013",
                "foodwatch_id": None,
                "trap_label": "ACO NS 5.5 SEPARATOR (OVAL)",
                "capacity": 378,
                "part_no": "ACO NS 5.5 SEPARATOR (OVAL)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 22,
                "length": 22,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0014",
                "foodwatch_id": None,
                "trap_label": "ACO NS 7 SEPARATOR ( ROUND)",
                "capacity": 560,
                "part_no": "ACO NS 7 SEPARATOR ( ROUND)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 23,
                "length": 23,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0015",
                "foodwatch_id": None,
                "trap_label": "ACO NS 7 SEPARATOR (OVAL)",
                "capacity": 423,
                "part_no": "ACO NS 7 SEPARATOR (OVAL)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 24,
                "length": 24,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0016",
                "foodwatch_id": None,
                "trap_label": "ACO NS 8.5 SEPARATOR (OVAL)",
                "capacity": 502,
                "part_no": "ACO NS 8.5 SEPARATOR (OVAL)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 25,
                "length": 25,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0017",
                "foodwatch_id": None,
                "trap_label": "ACO NS 25 SEPARATOR ",
                "capacity": 1585,
                "part_no": "ACO NS 25 SEPARATOR ",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 26,
                "length": 26,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0018",
                "foodwatch_id": None,
                "trap_label": "AG1",
                "capacity": 15,
                "part_no": "AG1",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 27,
                "length": 27,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0019",
                "foodwatch_id": None,
                "trap_label": "AG2",
                "capacity": 25,
                "part_no": "AG2",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 28,
                "length": 28,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0020",
                "foodwatch_id": None,
                "trap_label": "AG3",
                "capacity": 40,
                "part_no": "AG3",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 29,
                "length": 29,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0021",
                "foodwatch_id": None,
                "trap_label": "AG5",
                "capacity": 250,
                "part_no": "AG5",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 30,
                "length": 30,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0022",
                "foodwatch_id": None,
                "trap_label": "B",
                "capacity": 100,
                "part_no": "B",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 31,
                "length": 31,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0023",
                "foodwatch_id": None,
                "trap_label": "C",
                "capacity": 135,
                "part_no": "C",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 32,
                "length": 32,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0024",
                "foodwatch_id": None,
                "trap_label": "Coffee Cater",
                "capacity": 11,
                "part_no": "Coffee Cater",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 33,
                "length": 33,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0025",
                "foodwatch_id": None,
                "trap_label": "D",
                "capacity": 15,
                "part_no": "D",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 34,
                "length": 34,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0026",
                "foodwatch_id": None,
                "trap_label": "E",
                "capacity": 700,
                "part_no": "E",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 35,
                "length": 35,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0027",
                "foodwatch_id": None,
                "trap_label": "KESSEL NG 10 SEPARATOR",
                "capacity": 586,
                "part_no": "KESSEL NG 10 SEPARATOR",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 36,
                "length": 36,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0028",
                "foodwatch_id": None,
                "trap_label": "KESSEL NG 15 SEPARATOR",
                "capacity": 983,
                "part_no": "KESSEL NG 15 SEPARATOR",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 37,
                "length": 37,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0029",
                "foodwatch_id": None,
                "trap_label": "KESSEL NG 2 SEPARATOR",
                "capacity": 137,
                "part_no": "KESSEL NG 2 SEPARATOR",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 38,
                "length": 38,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0030",
                "foodwatch_id": None,
                "trap_label": "KESSEL NG 4 SEPARATOR",
                "capacity": 246,
                "part_no": "KESSEL NG 4 SEPARATOR",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 39,
                "length": 39,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0031",
                "foodwatch_id": None,
                "trap_label": "KESSEL NG 7 SEPARATOR",
                "capacity": 415,
                "part_no": "KESSEL NG 7 SEPARATOR",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 40,
                "length": 40,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0032",
                "foodwatch_id": None,
                "trap_label": "KESSEL NS 10 SEPARATOR",
                "capacity": 502,
                "part_no": "KESSEL NS 10 SEPARATOR",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 41,
                "length": 41,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0033",
                "foodwatch_id": None,
                "trap_label": "KESSEL NS 15 SEPARATOR",
                "capacity": 687,
                "part_no": "KESSEL NS 15 SEPARATOR",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 42,
                "length": 42,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0034",
                "foodwatch_id": None,
                "trap_label": "KESSEL NS 2 SEPARATOR",
                "capacity": 159,
                "part_no": "KESSEL NS 2 SEPARATOR",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 43,
                "length": 43,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0035",
                "foodwatch_id": None,
                "trap_label": "KESSEL NS 20 SEPARATOR",
                "capacity": 890,
                "part_no": "KESSEL NS 20 SEPARATOR",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 44,
                "length": 44,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0036",
                "foodwatch_id": None,
                "trap_label": "KESSEL NS 25 SEPARATOR",
                "capacity": 978,
                "part_no": "KESSEL NS 25 SEPARATOR",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 45,
                "length": 45,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0037",
                "foodwatch_id": None,
                "trap_label": "KESSEL NS 3 SEPARATOR",
                "capacity": 179,
                "part_no": "KESSEL NS 3 SEPARATOR",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 46,
                "length": 46,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0038",
                "foodwatch_id": None,
                "trap_label": "KESSEL NS 30 SEPARATOR",
                "capacity": 1155,
                "part_no": "KESSEL NS 30 SEPARATOR",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 47,
                "length": 47,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0039",
                "foodwatch_id": None,
                "trap_label": "KESSEL NS 4 SEPARATOR",
                "capacity": 211,
                "part_no": "KESSEL NS 4 SEPARATOR",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 48,
                "length": 48,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0040",
                "foodwatch_id": None,
                "trap_label": "KESSEL NS 7 SEPARATOR",
                "capacity": 357,
                "part_no": "KESSEL NS 7 SEPARATOR",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 49,
                "length": 49,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0041",
                "foodwatch_id": None,
                "trap_label": "Septic Tank AG",
                "capacity": 100,
                "part_no": "Septic Tank AG",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 50,
                "length": 50,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0042",
                "foodwatch_id": None,
                "trap_label": "SPT-100-5000(1)",
                "capacity": 100,
                "part_no": "SPT-100-5000(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 51,
                "length": 51,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0043",
                "foodwatch_id": None,
                "trap_label": "SPT-100-5000(2)",
                "capacity": 100,
                "part_no": "SPT-100-5000(2)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 52,
                "length": 52,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0044",
                "foodwatch_id": None,
                "trap_label": "SPT-150-250(2)",
                "capacity": 150,
                "part_no": "SPT-150-250(2)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 53,
                "length": 53,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0045",
                "foodwatch_id": None,
                "trap_label": "SPT-225-300(1)",
                "capacity": 225,
                "part_no": "SPT-225-300(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 54,
                "length": 54,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0046",
                "foodwatch_id": None,
                "trap_label": "SPT-40-50(2)",
                "capacity": 40,
                "part_no": "SPT-40-50(2)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 55,
                "length": 55,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0047",
                "foodwatch_id": None,
                "trap_label": "SPT-900-1200(0.166)",
                "capacity": 900,
                "part_no": "SPT-900-1200(0.166)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 56,
                "length": 56,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0048",
                "foodwatch_id": None,
                "trap_label": "Tank 40-60",
                "capacity": 40,
                "part_no": "Tank 40-60",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 57,
                "length": 57,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0049",
                "foodwatch_id": None,
                "trap_label": "Tank EKFC 1",
                "capacity": 1600,
                "part_no": "Tank EKFC 1",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 58,
                "length": 58,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0050",
                "foodwatch_id": None,
                "trap_label": "Tank EKFC2",
                "capacity": 3200,
                "part_no": "Tank EKFC2",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 59,
                "length": 59,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0051",
                "foodwatch_id": None,
                "trap_label": "Tank EKFC3",
                "capacity": 3500,
                "part_no": "Tank EKFC3",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 60,
                "length": 60,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0052",
                "foodwatch_id": None,
                "trap_label": "Tank Marsa",
                "capacity": 150,
                "part_no": "Tank Marsa",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 61,
                "length": 61,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0053",
                "foodwatch_id": None,
                "trap_label": "TNK-1000-1200(1)",
                "capacity": 1000,
                "part_no": "TNK-1000-1200(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 62,
                "length": 62,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0054",
                "foodwatch_id": None,
                "trap_label": "TNK-1000-1300(1)",
                "capacity": 1000,
                "part_no": "TNK-1000-1300(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 63,
                "length": 63,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0055",
                "foodwatch_id": None,
                "trap_label": "TNK-100-200(1)",
                "capacity": 100,
                "part_no": "TNK-100-200(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 64,
                "length": 64,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0056",
                "foodwatch_id": None,
                "trap_label": "TNK-100-5000(2)",
                "capacity": 100,
                "part_no": "TNK-100-5000(2)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 65,
                "length": 65,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0057",
                "foodwatch_id": None,
                "trap_label": "TNK-125-150(0.5)",
                "capacity": 125,
                "part_no": "TNK-125-150(0.5)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 66,
                "length": 66,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0058",
                "foodwatch_id": None,
                "trap_label": "TNK-125-200(1)",
                "capacity": 125,
                "part_no": "TNK-125-200(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 67,
                "length": 67,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0059",
                "foodwatch_id": None,
                "trap_label": "TNK-135-150(1)",
                "capacity": 135,
                "part_no": "TNK-135-150(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 68,
                "length": 68,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0060",
                "foodwatch_id": None,
                "trap_label": "TNK-135-150(2)",
                "capacity": 135,
                "part_no": "TNK-135-150(2)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 69,
                "length": 69,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0061",
                "foodwatch_id": None,
                "trap_label": "TNK-150-200(0.5)",
                "capacity": 150,
                "part_no": "TNK-150-200(0.5)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 70,
                "length": 70,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0062",
                "foodwatch_id": None,
                "trap_label": "TNK-150-200(1)",
                "capacity": 150,
                "part_no": "TNK-150-200(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 71,
                "length": 71,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0063",
                "foodwatch_id": None,
                "trap_label": "TNK-150-250(1)",
                "capacity": 150,
                "part_no": "TNK-150-250(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 72,
                "length": 72,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0064",
                "foodwatch_id": None,
                "trap_label": "TNK-150-300(1)",
                "capacity": 150,
                "part_no": "TNK-150-300(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 73,
                "length": 73,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0065",
                "foodwatch_id": None,
                "trap_label": "TNK-180-250(1)",
                "capacity": 180,
                "part_no": "TNK-180-250(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 74,
                "length": 74,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0066",
                "foodwatch_id": None,
                "trap_label": "TNK-20000-25000(0.33)",
                "capacity": 20000,
                "part_no": "TNK-20000-25000(0.33)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 75,
                "length": 75,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0067",
                "foodwatch_id": None,
                "trap_label": "TNK-200-250(1)",
                "capacity": 200,
                "part_no": "TNK-200-250(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 76,
                "length": 76,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0068",
                "foodwatch_id": None,
                "trap_label": "TNK-200-250(1.5)",
                "capacity": 200,
                "part_no": "TNK-200-250(1.5)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 77,
                "length": 77,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0069",
                "foodwatch_id": None,
                "trap_label": "TNK-200-250(2)",
                "capacity": 200,
                "part_no": "TNK-200-250(2)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 78,
                "length": 78,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0070",
                "foodwatch_id": None,
                "trap_label": "TNK-200-300(1)",
                "capacity": 200,
                "part_no": "TNK-200-300(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 79,
                "length": 79,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0071",
                "foodwatch_id": None,
                "trap_label": "TNK-200-300(2)",
                "capacity": 200,
                "part_no": "TNK-200-300(2)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 80,
                "length": 80,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0072",
                "foodwatch_id": None,
                "trap_label": "TNK-200-400(1)",
                "capacity": 200,
                "part_no": "TNK-200-400(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 81,
                "length": 81,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0073",
                "foodwatch_id": None,
                "trap_label": "TNK-250-300(1)",
                "capacity": 250,
                "part_no": "TNK-250-300(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 82,
                "length": 82,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0074",
                "foodwatch_id": None,
                "trap_label": "TNK-250-300(2)",
                "capacity": 250,
                "part_no": "TNK-250-300(2)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 83,
                "length": 83,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0075",
                "foodwatch_id": None,
                "trap_label": "TNK-250-350(1)",
                "capacity": 250,
                "part_no": "TNK-250-350(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 84,
                "length": 84,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0076",
                "foodwatch_id": None,
                "trap_label": "TNK-250-400(2)",
                "capacity": 250,
                "part_no": "TNK-250-400(2)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 85,
                "length": 85,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0077",
                "foodwatch_id": None,
                "trap_label": "TNK-300-400(0.5)",
                "capacity": 300,
                "part_no": "TNK-300-400(0.5)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 86,
                "length": 86,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0078",
                "foodwatch_id": None,
                "trap_label": "TNK-300-400(1)",
                "capacity": 300,
                "part_no": "TNK-300-400(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 87,
                "length": 87,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0079",
                "foodwatch_id": None,
                "trap_label": "TNK-300-400(2)",
                "capacity": 300,
                "part_no": "TNK-300-400(2)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 88,
                "length": 88,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0080",
                "foodwatch_id": None,
                "trap_label": "TNK-300-500(0.5)",
                "capacity": 300,
                "part_no": "TNK-300-500(0.5)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 89,
                "length": 89,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0081",
                "foodwatch_id": None,
                "trap_label": "TNK-300-500(1)",
                "capacity": 300,
                "part_no": "TNK-300-500(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 90,
                "length": 90,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0082",
                "foodwatch_id": None,
                "trap_label": "TNK-300-500(2)",
                "capacity": 300,
                "part_no": "TNK-300-500(2)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 91,
                "length": 91,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0083",
                "foodwatch_id": None,
                "trap_label": "TNK-300-600(1)",
                "capacity": 300,
                "part_no": "TNK-300-600(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 92,
                "length": 92,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0084",
                "foodwatch_id": None,
                "trap_label": "TNK-350-500(1)",
                "capacity": 350,
                "part_no": "TNK-350-500(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 93,
                "length": 93,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0085",
                "foodwatch_id": None,
                "trap_label": "TNK-400-500(0.5)",
                "capacity": 400,
                "part_no": "TNK-400-500(0.5)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 94,
                "length": 94,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0086",
                "foodwatch_id": None,
                "trap_label": "TNK-400-500(1)",
                "capacity": 400,
                "part_no": "TNK-400-500(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 95,
                "length": 95,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0087",
                "foodwatch_id": None,
                "trap_label": "TNK-400-500(2)",
                "capacity": 400,
                "part_no": "TNK-400-500(2)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 96,
                "length": 96,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0088",
                "foodwatch_id": None,
                "trap_label": "TNK-400-600(1)",
                "capacity": 400,
                "part_no": "TNK-400-600(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 97,
                "length": 97,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0089",
                "foodwatch_id": None,
                "trap_label": "TNK-400-700(1)",
                "capacity": 400,
                "part_no": "TNK-400-700(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 98,
                "length": 98,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0090",
                "foodwatch_id": None,
                "trap_label": "TNK-450-500(1)",
                "capacity": 450,
                "part_no": "TNK-450-500(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 99,
                "length": 99,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0091",
                "foodwatch_id": None,
                "trap_label": "TNK-450-550(1)",
                "capacity": 450,
                "part_no": "TNK-450-550(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 100,
                "length": 100,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0092",
                "foodwatch_id": None,
                "trap_label": "TNK-500-1000(1)",
                "capacity": 500,
                "part_no": "TNK-500-1000(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 101,
                "length": 101,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0093",
                "foodwatch_id": None,
                "trap_label": "TNK-500-600(1)",
                "capacity": 500,
                "part_no": "TNK-500-600(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 102,
                "length": 102,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0094",
                "foodwatch_id": None,
                "trap_label": "TNK-500-700(0.5)",
                "capacity": 500,
                "part_no": "TNK-500-700(0.5)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 103,
                "length": 103,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0095",
                "foodwatch_id": None,
                "trap_label": "TNK-500-700(1)",
                "capacity": 500,
                "part_no": "TNK-500-700(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 104,
                "length": 104,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0096",
                "foodwatch_id": None,
                "trap_label": "TNK-500-700(2)",
                "capacity": 500,
                "part_no": "TNK-500-700(2)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 105,
                "length": 105,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0097",
                "foodwatch_id": None,
                "trap_label": "TNK-500-800(1)",
                "capacity": 500,
                "part_no": "TNK-500-800(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 106,
                "length": 106,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0098",
                "foodwatch_id": None,
                "trap_label": "TNK-600-1000(2)",
                "capacity": 600,
                "part_no": "TNK-600-1000(2)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 107,
                "length": 107,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0099",
                "foodwatch_id": None,
                "trap_label": "TNK-600-700(1)",
                "capacity": 600,
                "part_no": "TNK-600-700(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 108,
                "length": 108,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0100",
                "foodwatch_id": None,
                "trap_label": "TNK-600-800(0.5)",
                "capacity": 600,
                "part_no": "TNK-600-800(0.5)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 109,
                "length": 109,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0101",
                "foodwatch_id": None,
                "trap_label": "TNK-650-750(2)",
                "capacity": 650,
                "part_no": "TNK-650-750(2)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 110,
                "length": 110,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0102",
                "foodwatch_id": None,
                "trap_label": "TNK-700-1000(1)",
                "capacity": 700,
                "part_no": "TNK-700-1000(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 111,
                "length": 111,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0103",
                "foodwatch_id": None,
                "trap_label": "TNK-700-900(1)",
                "capacity": 700,
                "part_no": "TNK-700-900(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 112,
                "length": 112,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0104",
                "foodwatch_id": None,
                "trap_label": "TNK-750-850(1)",
                "capacity": 750,
                "part_no": "TNK-750-850(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 113,
                "length": 113,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0105",
                "foodwatch_id": None,
                "trap_label": "TNK-800-1000(1)",
                "capacity": 800,
                "part_no": "TNK-800-1000(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 114,
                "length": 114,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0106",
                "foodwatch_id": None,
                "trap_label": "TNK-800-1500(0.5)",
                "capacity": 800,
                "part_no": "TNK-800-1500(0.5)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 115,
                "length": 115,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0107",
                "foodwatch_id": None,
                "trap_label": "TNK-900-1000(1)",
                "capacity": 900,
                "part_no": "TNK-900-1000(1)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 116,
                "length": 116,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0108",
                "foodwatch_id": None,
                "trap_label": "TNK-900-1200(0.33)",
                "capacity": 900,
                "part_no": "TNK-900-1200(0.33)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 117,
                "length": 117,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0109",
                "foodwatch_id": None,
                "trap_label": "TNK-900-1200(2)",
                "capacity": 900,
                "part_no": "TNK-900-1200(2)",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 118,
                "length": 118,
                "remarks": "NA",
                "image": None
                },
                {
                "grease_trap_id": "TP0110",
                "foodwatch_id": None,
                "trap_label": "UG3",
                "capacity": 40,
                "part_no": "UG3",
                "material": "NA",
                "shape": "NA",
                "manufacturer": "NA",
                "width": 119,
                "length": 119,
                "remarks": "NA",
                "image": None
                }
                ]
    for item in grease_traps:
        GreaseTrap.objects.create(
            grease_trap_id	    =	item['grease_trap_id'],
            foodwatch_id	    =	item['foodwatch_id'],
            part_no	            =	item['part_no'],
            description	        =	item['trap_label'],
            capacity	        =	item['capacity'],
            material	        =	item['material'],
            shape	            =	item['shape'],
            manufacturer	    =	item['manufacturer'],
            width	            =	item['width'],
            length	            =	item['length'],
            height	            =	item['length']*2,
            height_to_outlet_pipe	=	item['length']*2 - 2,
            image	            =	item['image'],
            remarks	            =	item['remarks'],
            created_by_id	    = 1
        )
    print("grease traps uploaded successfully")

def initiate_foodwatch_subcategories():
    entities_excel  = os.path.join(settings.BASE_DIR,'abacimodules','excels','Sub-Categories.xlsx')
    xlsx            = pd.ExcelFile(entities_excel)
    df              = xlsx.parse(0)
    for index, row in df.iterrows():
        try:
            main_category, created = MainCategory.objects.get_or_create(
                main_category = row['Category'].strip(),
                created_by_id = 1,
            )
            SubCategory.objects.create(
                main_category       = main_category,
                sub_category        = row['Sub Category'].strip(),
                foodwatch_id        = row['Foodwatch Id'],
                foodwatch_name      = row['Foodwatch Name'],
                foodwatch_sub_id    = row['Foodwatch Sub Id'],
                foodwatch_sub_name  = row['Foodwatch Sub Name'],
                created_by_id       = 1,
            )
        except:
            pass
    print("sub categories uploaded successfully")

def initiate_foodwatch_subareas():
    entities_excel = os.path.join(settings.BASE_DIR,'abacimodules','excels','Sub-Areas.xlsx')
    xlsx = pd.ExcelFile(entities_excel)
    df = xlsx.parse(0)
    for index, row in df.iterrows():
        try:
            zone, zone_created = Zone.objects.get_or_create(
                zone_no         = row['Zone'].strip(),
                zone_name       = row['Zone'].strip(),
                created_by_id   = 1,
            )
            area, area_created = Area.objects.get_or_create(
                zone            = zone, 
                area_code       = row['Area'].strip(),
                area            = row['Area'].strip(),
                created_by_id   = 1,
            )
            SubArea.objects.get_or_create(
                zone            = zone,
                area            = area,
                sub_area        = row['Sub Area'].strip(),
                foodwatch_id    = row['Foodwatch Id'],
                foodwatch_name  = row['Foodwatch Name'],
                created_by_id   = 1,
            )
        except:
            pass
    print("sub areas uploaded successfully")

def entity_gtcc(entity, gtcc):
        check_active_gtcc = EntityGTCC.objects.filter(entity=entity).exclude(status='Rejected').exclude(status='Expired').first()
        if check_active_gtcc:
            if check_active_gtcc.status == 'Approval Pending':
                print("You have one approval pending contract")
            check_active_gtcc.status = 'Expired'
            check_active_gtcc.contract_end = datetime.date.today()
            check_active_gtcc.save()
        active_gtcc_detail = EntityGTCC.objects.create(
            entity = entity,
            gtcc = gtcc,
            created_by_id = 1
        )
        entity.active_gtcc_detail = active_gtcc_detail
        entity.modified_by_id = 1
        entity.save()


