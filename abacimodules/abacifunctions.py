from rest_framework.pagination import PageNumberPagination
from masters.models import Gate, RFIDCard
from users.models import Account
from gtcc.models import VehicleDetail, GTCC, CouponBooklet, Coupon
from django.utils.crypto import get_random_string
from entity.models import EntityGTCC,EntityGreaseTrap,ServiceRequest,ServiceRequestDetail,Entity, EntityFixture
from masters.models import *
import random
from django.conf import settings
import os
import pandas as pd
from faker import Faker
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from .abaci_dicts import search_in_details, greaseTrapTypes
from django.contrib.auth.hashers import make_password
from os import urandom
from Crypto.Cipher import AES
from cryptography.hazmat.primitives import padding
import base64
from django.utils import timezone
import datetime
from django.test import Client
import json
# from rijndael.cipher.crypt import new
# from rijndael.cipher.blockcipher import MODE_CBC, IV, BLOCKSIZE
from masters.models import ModeOfPayment

class CustomPageNumberPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = 'page_size'
    max_page_size = 1000

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

def get_a_user():
    return Account.objects.filter(user_class = 'Envirol', user_status='Activated', user_type = 'Admin').first()


def gates_maker(num_of_gates = 2):
    user = get_a_user()
    for x in range(num_of_gates):
        Gate.objects.create(
                gate_name = f'gate{x}',
                created_by = user
            )

    

def RFIDMaker():
    existing_rfids = RFIDCard.objects.all()
    vehicles = VehicleDetail.objects.all()
    user = get_a_user()

    for vehicle in vehicles:
        rfid_check = existing_rfids.filter(vehicle=vehicle)
        if len(rfid_check) == 0:
            RFIDCard.objects.create(
                    tag_id = get_random_string(64).lower(),
                    friendly_name = f'card_for_{vehicle}',
                    vehicle = vehicle,
                    created_by = user,
                    )
def tempProcessingJobMaker(driver_username):
    driver = Account.objects.get(username = driver_username)
    vehicle = VehicleDetail.objects.get(driver = driver)
    gtcc = vehicle.gtcc
    entity_gtcc = EntityGTCC.objects.filter(gtcc= gtcc).first()

    entity = entity_gtcc.entity
    entity_grease_traps = EntityGreaseTrap.objects.filter(entity = entity)
    grease_trap_count = len(entity_grease_traps)
    if (entity.status == 'Active'):
        service_request = ServiceRequest(
            entity = entity,
            entity_gtcc = entity_gtcc,
            vehicle = vehicle,
            driver = driver,
            grease_trap_count = grease_trap_count,
            status = 'Processing',
            created_by = driver,
        )
        service_request.save()
        # Now lets create some grease trap collected details
        for grease_trap in entity_grease_traps:
            ServiceRequestDetail.objects.create(
                service_request = service_request,
                grease_trap = grease_trap,
            )
    else:
        print('The entity is not active')



def fake_person():
    gender = random.choice(["M", "F"])
    faker = Faker()
    first_name = faker.first_name_male() if "gender"=="M" else faker.first_name_female()
    last_name = faker.last_name_male() if "gender"=="M" else faker.last_name_female()
    company = faker.company()
    email = first_name.lower() +"_"+ last_name.lower() + "@" + company.replace(" ","").replace(",","").replace("-","").lower() + ".com"
    details = {
        "name" : first_name + " " + last_name,
        "first_name":first_name,
        "last_name":last_name,
        "email" : email,
        "company" : company,
        "address" : faker.address(),
        "contact_number" : faker.phone_number()
    } 
    return details

def initiate_zones():
    Zone.objects.all().delete()
    zones_excel = os.path.join(settings.BASE_DIR,'abacimodules','excels','Zones.xlsx')
    xlsx = pd.ExcelFile(zones_excel)
    df = xlsx.parse(0)
    for index, row in df.iterrows():
        created_by = random.choice(Account.objects.filter(user_class='Envirol', user_type='Admin', user_status='Activated'))
        Zone.objects.create(
            zone_no = row['Zone'],
            zone_name = row['Area'],
            created_by = created_by,
            modified_by = created_by,
        )


def initiate_areas():
    Area.objects.all().delete()
    entities_excel = os.path.join(settings.BASE_DIR,'abacimodules','excels','Entities.xlsx')
    xlsx = pd.ExcelFile(entities_excel)
    df = xlsx.parse(0)
    df = df.drop_duplicates(subset=["Area"])
    for index, row in df.iterrows():
        try:
            created_by = random.choice(Account.objects.filter(user_class='Envirol', user_type='Admin', user_status='Activated'))
            zone = Zone.objects.get(zone_no=row['Zone'])
            Area.objects.create(
                zone = zone,
                area_code = row['Area'],
                area = row['Area'],
                created_by = created_by,
                modified_by = created_by,
            )
        except:
            pass

def initiate_subareas():
    SubArea.objects.all().delete()
    entities_excel = os.path.join(settings.BASE_DIR,'abacimodules','excels','Entities.xlsx')
    xlsx = pd.ExcelFile(entities_excel)
    df = xlsx.parse(0)
    df = df.drop_duplicates(subset=["Sub Area"])
    for index, row in df.iterrows():
        try:
            created_by = random.choice(Account.objects.filter(user_class='Envirol', user_type='Admin', user_status='Activated'))
            area = Area.objects.get(area_code=row['Area'])
            SubArea.objects.create(
                zone = area.zone,
                area = area,
                sub_area = row['Sub Area'],
                created_by = created_by,
                modified_by = created_by,
            )
        except:
            pass

def email_creator(entity_name):
  entity_name = str(entity_name)
  domain = "".join(ch.lower() for ch in entity_name if ch.isalnum())
  email = f'admin@{domain}.com'
  return email

def initiate_designations(num_of_designations = 50):
    faker = Faker()
    created_by = random.choice(Account.objects.filter(user_class='Envirol', user_type='Admin', user_status='Activated'))
    known_designations = ['Driver', 'Operator', 'Inspector']
    for designation in known_designations:
        Designation.objects.create(
                designation = designation,
                created_by = created_by,
                modified_by = created_by,
            )
    for x in range(50):
        created_by = random.choice(Account.objects.filter(user_class='Envirol', user_type='Admin', user_status='Activated'))
        try:
            Designation.objects.create(
                designation = faker.job(),
                created_by = created_by,
                modified_by = created_by,
            )
        except:
            pass

def create_operators(num_of_operators = 5):
    faker = Faker()
    operators = Account.objects.filter(user_type="Operator")
    if (len(operators) == 0):
        operator_id_start = 1001
    else:
        last_operator = operators.last()
        last_operator_id = last_operator.id
        operator_id_start = last_operator_id + 1
    operator_id = operator_id_start
    designation = Designation.objects.get(designation="Operator")
    for x in range(num_of_operators):
        operator = Account.objects.create(
                username = f"O{operator_id}",
                email = f'operator{operator_id}@email.com',
                first_name = faker.first_name_male(),
                last_name = faker.last_name_male(),
                emp_id = random.randint(10000,99999),
                designation = designation,
                extension_number = random.randint(100,9999),
                contact_number = f'05{random.randint(10000000,99999999)}',
                address = "NA",
                emirate = 'Dubai',
                user_status = 'Activated',
                user_class = 'Envirol',
                user_type = 'Operator',
                password = make_password('1111')
            )
        operator_id += 1

def create_inspectors(num_of_inspectors = 5):
    faker = Faker()
    inspectors = Account.objects.filter(user_type="Inspector")
    if (len(inspectors) == 0):
        inspector_id_start = 1001
    else:
        last_inspector = inspectors.last()
        last_inspector_id = last_inspector.id
        inspector_id_start = last_inspector_id + 1
    inspector_id = inspector_id_start
    designation = Designation.objects.get(designation="Inspector")
    for x in range(num_of_inspectors):
        inspector = Account.objects.create(
                username = f"I{inspector_id}",
                email = f'inspector{inspector_id}@email.com',
                first_name = faker.first_name_male(),
                last_name = faker.last_name_male(),
                emp_id = random.randint(10000,99999),
                designation = designation,
                extension_number = random.randint(100,9999),
                contact_number = f'05{random.randint(10000000,99999999)}',
                address = "NA",
                emirate = 'Dubai',
                user_status = 'Activated',
                user_class = 'Envirol',
                user_type = 'Inspector',
                password = make_password('1111')
            )
        inspector_id += 1

def initiate_categories():
    MainCategory.objects.all().delete()
    SubCategory.objects.all().delete()
    entities_excel = os.path.join(settings.BASE_DIR,'abacimodules','excels','Entities.xlsx')
    xlsx = pd.ExcelFile(entities_excel)
    df = xlsx.parse(0)
    df = df.drop_duplicates(subset=["Category Name"])
    df = df.dropna(subset=["Category Name"])
    for index, row in df.iterrows():
        try:
            created_by = random.choice(Account.objects.filter(user_class='Envirol', user_type='Admin', user_status='Activated'))
            main_category = MainCategory.objects.create(
                main_category = row['Category Name'],
                created_by = created_by,
            )
            temp_postfix = ['A','B','C','D','E',]
            for x in temp_postfix:
                SubCategory.objects.create(
                main_category = main_category,
                sub_category = str(row['Category Name']) + f' {x}',
                created_by = created_by,
                    )
        except:
            pass

def initiate_entities():
    faker = Faker()
    Entity.objects.all().delete()
    Account.objects.filter(user_class = 'Entity').delete()
    entities_excel = os.path.join(settings.BASE_DIR,'abacimodules','excels','Entities.xlsx')
    xlsx = pd.ExcelFile(entities_excel)
    df = xlsx.parse(0)
    df = df.drop_duplicates(subset=["Name in Trade License"])
    df['Trade License No'] = df['Trade License No'].apply(lambda x: x if not pd.isnull(x) else random.randint(100000,999999))
    df['email'] = df['Name in Trade License'].apply(lambda x: email_creator(x))
    designations = Designation.objects.all()
    num_completed = 0
    num_of_entities = len(df)
    print(len(df))
    for index, row in df.iterrows():
        try:
            created_by = random.choice(Account.objects.filter(user_class='Envirol', user_type='Admin', user_status='Activated'))
            sub_area = SubArea.objects.get(sub_area = row['Sub Area'])
            address = f'{sub_area.sub_area}, {sub_area.area.area}, {sub_area.area.zone.zone_name}, UAE'
            active_contact_person = Account.objects.create(
                username = row['email'],
                email = row['email'],
                first_name = faker.first_name_male(),
                last_name = faker.last_name_male(),
                emp_id = random.randint(10000,99999),
                designation = random.choice(designations),
                extension_number = random.randint(100,9999),
                contact_number = f'05{random.randint(10000000,99999999)}',
                address = address,
                emirate = 'Dubai',
                inviter = created_by,
                user_status = 'Activated',
                user_class = 'Entity',
                user_type = 'Admin',
                password = make_password('Abcd@123')
            )
            sub_category = random.choice(SubCategory.objects.all())
            entity = Entity.objects.create(
                establishment_name = row['Establishment Name '],
                trade_license_no = row['Trade License No'],
                trade_license_name = row['Name in Trade License'],
                env_sap_id = row['Code '],
                active_contact_person = active_contact_person,
                foodwatch_business_id = random.randint(1000000,9999999),
                category = sub_category.main_category,
                sub_category = sub_category,
                zone = sub_area.area.zone,
                area = sub_area.area,
                subarea = sub_area,
                address = address,
                phone_no = f'04 {random.randint(1000000,9999999)}',
                entity_location = 'Dubai',
                po_box = str(random.randint(1000000,9999999)),
                seating_capacity = random.randint(50,500),
                gps_coordinates = faker.coordinate(),
                google_location = faker.coordinate(),
                makhani_no = str(random.randint(1000000,9999999)),
                meals_per_day = str(random.randrange(1000,5000,50)),
                random_key = get_random_string(64).lower(),
                created_by = created_by,
            )
            active_contact_person.link_id = entity.id
            active_contact_person.link_class = "Entity"
            active_contact_person.save()
            num_completed +=1
            if (num_completed % 100 == 0):
                print(f"{num_completed} entities out of {num_of_entities} are created....")
        except:
            pass    

def initiate_gttcs():
    faker = Faker()
    GTCC.objects.all().delete()
    Account.objects.filter(user_class = 'GTCC').delete()
    gtccs_excel = os.path.join(settings.BASE_DIR,'abacimodules','excels','GTCCs.xlsx')
    xlsx = pd.ExcelFile(gtccs_excel)
    df = xlsx.parse(0)
    df = df.drop_duplicates(subset=["Account Name"])
    df['email'] = df['Account Name'].apply(lambda x: email_creator(x))
    designations = Designation.objects.all()
    num_completed = 0
    num_of_gtccs = len(df)
    for index, row in df.iterrows():
        try:
            created_by = random.choice(Account.objects.filter(user_class='Envirol', user_type='Admin', user_status='Activated'))
            # sub_area = SubArea.objects.get(sub_area = row['Sub Area'])
            # address = f'{sub_area.sub_area}, {sub_area.area.area}, {sub_area.area.zone.zone_name}, UAE'
            active_contact_person = Account.objects.create(
                username = row['email'],
                email = row['email'],
                first_name = faker.first_name_male(),
                last_name = faker.last_name_male(),
                emp_id = random.randint(10000,99999),
                designation = random.choice(designations),
                extension_number = random.randint(100,9999),
                contact_number = f'05{random.randint(10000000,99999999)}',
                address = row['Address'],
                emirate = 'Dubai',
                inviter = created_by,
                user_status = 'Activated',
                user_class = 'GTCC',
                user_type = 'Admin',
                password = make_password('Abcd@123')
            )
            # sub_category = random.choice(SubCategory.objects.all())
            gtcc = GTCC.objects.create(
                    establishment_name = row['Account Name'],
                    trade_license_no = row['Trade License Number'],
                    trade_license_name = row['Account Name'],
                    env_sap_id = str(random.randint(10000,99999)),
                    credit_available = 0,
                    active_contact_person = active_contact_person,
                    foodwatch_business_id = random.randint(1000000,9999999),
                    address = row['Address'],
                    phone_no = f'04 {random.randint(1000000,9999999)}',
                    po_box = str(random.randint(1000000,9999999)),
                    website_url = 'www.'+row['email'].split('@')[1],
                    office_email = row['email'],
                    created_by = created_by,
            )
            active_contact_person.link_id = gtcc.id
            active_contact_person.link_class = "GTCC"
            active_contact_person.save()
            num_completed +=1
            if (num_completed % 10 == 0):
                print(f"{num_completed} GTCC out of {num_of_gtccs} are created....")
        except:
            pass    


def initiate_greasetraps():
    grease_traps = greaseTrapTypes
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
            created_by	        = get_a_user()
        )

def add_greasetraps_to_entity_randomly():
    grease_traps = GreaseTrap.objects.all()
    entites = Entity.objects.all()
    num_of_entities = len(entites)
    num_completed = 0
    for entity in entites:
        num_of_traps = random.randint(2,5)
        for x in range(num_of_traps):
            grease_trap = random.choice(grease_traps)
            EntityGreaseTrap.objects.create(
                entity		=	entity,
                grease_trap	=	grease_trap,
                capacity	=	grease_trap.capacity,
                remarks		=	grease_trap.remarks,
                label		=	grease_trap.description,
                created_by	=	get_a_user(),
            )
        num_completed +=1
        if (num_completed % 100 == 0):
            print(f"Grease traps for {num_completed} entities out of {num_of_entities} are created....")


def add_fixtures_to_entity_randomly():
    fixtures = Fixture.objects.all()
    entites = Entity.objects.all()
    num_of_entities = len(entites)
    num_completed = 0
    fake = Faker()
    for entity in entites:
        for fixture in fixtures:
            EntityFixture.objects.create(
                entity		=	entity,
                fixture	    =	fixture,
                qty         =   random.randint(1,5),
                remarks		=	fake.paragraph(nb_sentences=1),
                label		=	fake.word(),
                created_by	=	get_a_user(),
            )
        num_completed +=1
        if (num_completed % 100 == 0):
            print(f"Fixtures for {num_completed} entities out of {num_of_entities} are created....")


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
    # df.columns = ["Waste Main Category ID", "Weight (KG)"]
    # command_waste_main_category = 'SELECT id, category_name FROM public.mywaste_wastetypemaincategory ORDER BY id'
    # named_ids_main_category = id_name_dict_maker(get_data_from_db(command_waste_main_category))
    # df["Waste Main Category Name"] = df["Waste Main Category ID"].map(named_ids_main_category)
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

def create_and_assign_drivers_for_gtcc():
    faker = Faker()
    gtccs = GTCC.objects.all()
    num_of_gtccs = len(gtccs)
    drivers = Account.objects.filter(user_type="Driver")
    if (len(drivers) == 0):
        driver_id_start = 1001
    else:
        last_driver = drivers.last()
        last_driver_id = last_driver.id
        driver_id_start = last_driver_id + 1
    driver_id = driver_id_start
    num_completed = 0
    designation = Designation.objects.get(designation="Driver")
    for gtcc in gtccs:
        number_of_drivers = random.randint(1,5)
        for x in range(number_of_drivers):
            driver = Account.objects.create(
                    username = f"D{driver_id}",
                    email = f'driver{driver_id}@email.com',
                    first_name = faker.first_name_male(),
                    last_name = faker.last_name_male(),
                    emp_id = random.randint(10000,99999),
                    link_id = gtcc.id,
                    link_class = 'GTCC',
                    designation = designation,
                    extension_number = random.randint(100,9999),
                    contact_number = f'05{random.randint(10000000,99999999)}',
                    license_no = f'TC{random.randint(10000000,99999999)}',
                    address = "NA",
                    emirate = 'Dubai',
                    inviter = get_a_user(),
                    user_status = 'Activated',
                    user_class = 'GTCC',
                    user_type = 'Driver',
                    password = make_password('1111')
                )
            driver_id += 1
        num_completed +=1
        if (num_completed % 10 == 0):
            print(f"Drivers for {num_completed} gtcc out of {num_of_gtccs} are created....")

def vehicle_creator_and_assign_to_gtcc():
    gtccs = GTCC.objects.all()
    num_of_gtccs = len(gtccs)
    drivers = Account.objects.filter(user_type="Driver")
    vehicle_num_type = ['AUH','DXB','SHJ','FUJ','RAK']
    num_completed = 0
    vehicle_types = [
                'Box truck',
                'Cab over',
                'Chassis cab'
                'Conversion van',
                'Dump truck',
                'Flatbed truck',
                'Fire truck',
                ]
    for gtcc in gtccs:
        number_of_vehicles = random.randint(1,5)
        for x in range(number_of_vehicles):
            VehicleDetail.objects.create(
                gtcc = gtcc,
                vehicle_no = f'{random.choice(vehicle_num_type)}{random.randint(10000,99999)}',
                chassis_no = get_random_string(17).capitalize(),
                vehicle_type = random.choice(vehicle_types),
                vehicle_tank_capacity = random.randrange(500,5000,500),
                random_key = get_random_string(64),
                created_by = get_a_user(),
            )
        num_completed +=1
        if (num_completed % 10 == 0):
            print(f"Vehicles for {num_completed} gtcc out of {num_of_gtccs} are created....")            

def create_entity_gtcc_contract_randomly():
    gtccs = GTCC.objects.all()
    entites = Entity.objects.all()
    num_of_entities = len(entites)
    entity_gtcc_choices = ['Active', 'Approval Pending', 'Rejected' , 'Expired' ]
    num_completed = 0
    for entity in entites:
        created_date = timezone.now() - datetime.timedelta(random.randint(5,360))
        contract = EntityGTCC.objects.create(
            entity = entity,
            gtcc = random.choice(gtccs),
            contract_start = created_date,
            created_by = get_a_user(),
            created_date = created_date,
            status = random.choice(entity_gtcc_choices)
        )
        entity.active_gtcc_detail = contract
        entity.save()
        num_completed +=1
        if (num_completed % 100 == 0):
            print(f"Entity GTCC Contract for {num_completed} entities out of {num_of_entities} are created....")

def create_temp_coupons_for_all_gtccs():
    last_booklet_id = CouponBooklet.objects.last()
    if (last_booklet_id == None):
        last_booklet_id = 0
        last_coupon_end_no = 0
    else:
        last_booklet_id = last_booklet_id.id
        last_coupon_end_no = last_booklet_id.coupon_end_no
    next_booklet_id = last_booklet_id + 1
    gtccs = GTCC.objects.all()
    num_completed = 0
    num_of_gtccs = len(gtccs)
    for gtcc in gtccs:

        booklet = CouponBooklet.objects.create(
            booklet_no = f"COUPON{next_booklet_id}",
            coupon_start_no = last_coupon_end_no + 1,
            coupon_end_no = last_coupon_end_no + 100,
            total_coupons = 100,
            used_coupons = 0,
            gtcc = gtcc,
            created_by = get_a_user()
        )
        next_booklet_id += 1
        last_coupon_end_no += 100
        for x in range(100):
            Coupon.objects.create(
                booklet = booklet,
                coupon_no = last_coupon_end_no + 1
            )
            last_coupon_end_no += 1
        num_completed +=1
        if (num_completed % 10 == 0):
            print(f"{num_completed} no. of GTCCs outof {num_of_gtccs} has been assigned with coupon booklets")



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

def test_encryption():
    # For Generating cipher text
    secret_key = 'C9TWNGIDPJU72DI4'
    iv = 'C9TWNGIDPJU72DI4'
    obj = AES.new(secret_key, AES.MODE_CBC, iv)

    # Encrypt the message
    redirect_url = 'https://fogwatch.envirol.ae/payment/test'
    amount = 1000
    message = f"<BankInformation><ClientID>{'cbd100'}</ClientID><ReturnPage>{redirect_url}</ReturnPage><CreateToken>false</CreateToken><locale>{'en-us'}</locale><PaymentInformation><OrderID>{'666467'}</OrderID><TotalAmount>{amount}</TotalAmount><TransactionType>{'sale'}</TransactionType><OrderDescription>{'TEST Description'}</OrderDescription><Currency>{'AED'}</Currency></PaymentInformation><BankInformation>"
    print('Original message is: ', message)
    encrypted_text = obj.encrypt(message)
    print('The encrypted text', encrypted_text)

    # Decrypt the message
    rev_obj = AES.new(secret_key, AES.MODE_CBC, iv)
    decrypted_text = rev_obj.decrypt(encrypted_text)
    print('The decrypted text', decrypted_text.decode('utf-8'))


def encrypt(data):
    cipher = create_cipher()
    padder = padding.PKCS7(128).padder()
    padded = padder.update(data.encode())
    ciphertext = cipher.encrypt(padded)
    return ciphertext

def decrypt(ciphertext):
    cipher = create_cipher()
    padded = cipher.decrypt(ciphertext)
    unpadder = padding.PKCS7(128).unpadder()
    data = unpadder.update(padded)
    return data

def create_cipher():
    encryption_key = "C9TWNGIDPJU72DI4"
    return AES.new(encryption_key, AES.MODE_CBC, encryption_key)
    
# class MakePayment(APIView):
#     def post(self, request):
#         url = "https://test.cbdonline.ae/Cybersource/Payment/InitiateCreditCardPayment"
#         redirect_url = "http://localhost/CBD.PSP.PGTesting/PaymentTesting//CheckoutStatus"

#         payload = "<BankInformation><ClientID>cbd100</ClientID><ReturnPage>"+redirect_url+"</ReturnPage><CreateToken>false</CreateToken><locale>en-us</locale><PaymentInformation><OrderID>666467</OrderID><TotalAmount>100</TotalAmount><TransactionType>sale</TransactionType><OrderDescription>TEST Description</OrderDescription><Currency>AED</Currency></PaymentInformation></BankInformation>"

#         encrypted_payload = encrypt(payload)

#         response = post_url(url, encrypted_payload)
#         return Response(response, status=status.HTTP_200_OK)

# def test2():
#     amount  = 1000
#     redirect_url = "https://fogwatch.envirol.ae/payment/test"

#     payload = f"<BankInformation><ClientID>cbd100</ClientID><ReturnPage>{redirect_url}</ReturnPage><CreateToken>false</CreateToken><locale>en-us</locale><PaymentInformation><OrderID>666467</OrderID><TotalAmount>{amount}</TotalAmount><TransactionType>sale</TransactionType><OrderDescription>TEST Description</OrderDescription><Currency>AED</Currency></PaymentInformation></BankInformation>"
#     encrypted_payload = encrypt(payload)
#     encoded = base64.b64encode(encrypted_payload)
#     decoded = encoded.decode()
#     return(encrypted_payload)

def initiate_all():
    initiate_zones()
    initiate_areas()
    initiate_subareas()
    initiate_designations()
    create_operators()
    create_inspectors()
    initiate_categories()
    initiate_entities()
    initiate_gttcs()
    initiate_greasetraps()
    add_greasetraps_to_entity_randomly()
    add_fixtures_to_entity_randomly()
    create_and_assign_drivers_for_gtcc()
    vehicle_creator_and_assign_to_gtcc()
    create_entity_gtcc_contract_randomly()
    create_temp_coupons_for_all_gtccs()


def get_user_token(username, password):
    client = Client()
    url = '/users_api/login'
    data = {
        'username' : username,
        'password' : password,
    }
    response = client.post(url, data)
    if (response.status_code == 200):
        json_data = json.loads(response.content.decode("utf-8"))
        token = json_data['token']
        return token
    return None


def temp_job_creator_for_driver(driver_username = 'd1001', password = '1111'):
    # This function is to create temperory jobs and assign to the selected driver for testing purpose
    driver = Account.objects.get(username = driver_username)
    vehicle_id = driver.assigned_vehicle.id
    gtcc = GTCC.objects.get(id=driver.link_id)
    gtcc_user = Account.objects.filter(link_id = gtcc.id, user_status = 'Activated', user_type = 'Admin').first()
    gtcc_user_username = gtcc_user.username
    password = 'Abcd@123'
    gtcc_user_token = get_user_token(gtcc_user_username, password)
    if (gtcc_user_token == None):
        print(f'Error in getting user token for {gtcc_user_username}!')
        return
    entities_having_contract_with_this_gtcc = EntityGTCC.objects.filter(gtcc=gtcc, status = 'Active')
    client = Client()
    url_service_request = '/entity_api/service_request'
    url_ssign_vehicle_for_service_request = '/gtcc_api/assign_vehicle_for_service_request'
    for entity_contract in entities_having_contract_with_this_gtcc:
        entity = entity_contract.entity
        this_entity_user = Account.objects.filter(link_id = entity.id, user_status = 'Activated', user_type = 'Admin').first()
        if (this_entity_user == None):
            print(f'No user found for {entity.establishment_name}!')
            continue
        username = this_entity_user.username
        password = 'Abcd@123'
        token = get_user_token(username, password)
        if (token == None):
            print(f'Error in getting user token for {entity.establishment_name}!')
            continue
        greese_traps = EntityGreaseTrap.objects.filter(entity=entity).values_list('id', flat=True, named=False)
        if (len(greese_traps) == 0):
            print(f'No greese traps found for {entity.establishment_name}!')
            continue
        data = {
                    "entity":entity.id,
                    "gtcc":gtcc.id,
                    "grease_traps":list(greese_traps)
                }
        response = client.post(url_service_request, data = data, format = 'json', **{'HTTP_AUTHORIZATION': f'Bearer {token}'},follow = True)
        print(f'Response status for job creation for entity {entity.establishment_name} is {response.status_code}')
        if (response.status_code == 200):
            json_data = json.loads(response.content.decode("utf-8"))
            service_request = json_data['id']
            data = {
                'service_request':service_request,
                'vehicle':vehicle_id,
            }
            response = client.post(url_ssign_vehicle_for_service_request, data = data, format = 'json', **{'HTTP_AUTHORIZATION': f'Bearer {gtcc_user_token}'},follow = True)
            print(f'Response status for job assign to driver is {response.status_code}')


def initiate_mode_of_payments():
    m1 = ModeOfPayment.objects.create(
        mop_id = '1001',
        mode_of_payment = "Online Payment",
        is_editable = False,
        created_by_id = 1,
    )
    m2 = ModeOfPayment.objects.create(
        mop_id = '1002',
        mode_of_payment = "DO Adjustment",
        is_editable = False,
        created_by_id = 1,
    )
    m3 = ModeOfPayment.objects.create(
        mop_id = '1003',
        mode_of_payment = "Credit Refund",
        is_editable = False,
        created_by_id = 1,
    )

def initiate_foodwatch_subcategories():
    # SubCategory.objects.all().delete()
    entities_excel  = os.path.join(settings.BASE_DIR,'abacimodules','excels','Sub-Categories.xlsx')
    xlsx            = pd.ExcelFile(entities_excel)
    df              = xlsx.parse(0)
    for index, row in df.iterrows():
        try:
            main_category, created = MainCategory.objects.get_or_create(
                main_category = row['Category'],
                created_by_id = 1,
            )
            SubCategory.objects.create(
                main_category       = main_category,
                sub_category        = row['Sub Category'],
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
    # SubArea.objects.all().delete()
    entities_excel = os.path.join(settings.BASE_DIR,'abacimodules','excels','Sub-Areas.xlsx')
    xlsx = pd.ExcelFile(entities_excel)
    df = xlsx.parse(0)
    for index, row in df.iterrows():
        try:
            zone, zone_created = Zone.objects.get_or_create(
                zone_no         = row['Zone'],
                zone_name       = row['Zone'],
                created_by_id   = 1,
            )
            area, area_created = Area.objects.get_or_create(
                zone            = zone, 
                area_code       = row['Area'],
                area            = row['Area'],
                created_by_id   = 1,
            )
            SubArea.objects.get_or_create(
                zone            = zone,
                area            = area,
                sub_area        = row['Sub Area'],
                foodwatch_id    = row['Foodwatch Id'],
                foodwatch_name  = row['Foodwatch Name'],
                created_by_id   = 1,
            )
        except:
            pass
    print("sub areas uploaded successfully")
