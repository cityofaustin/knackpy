#  todo:
#  test csv, page limit, no app key
import csv
import json
import logging

import arrow
import requests

import pdb

class Knack(object):
        
    def __init__(
            self, obj=None, scene=None, view=None, field_obj=None, filters=None, app_id=None,
            api_key=None, timeout=10, include_ids=True, id_outfield='id',
            localize=True, tzinfo='US/Central', raw_connections=False,
            rows_per_page=1000, page_limit=10
        ):
        '''  
        Class to interact with Knack application via the API as
        documented at https://www.knack.com/developer-documentation/
        
        Parameters
        ----------
        app_id : string (required)
            Knack application ID string
        api_key : string (optional)
            Knack application key. Required for accessing private views.
        filters : dict (optional)
            Search and limit the records returned by object query. Ignored for
            view-based requests. Does not currently support range queries.
            Filters dict must be formatted as described in API docs:
            See: https://www.knack.com/developer-documentation/#filters
        timeout : numeric (optional | default : 10)
            Number of seconds before http request timeout
        obj : string (required if scene + view are not specified)
            A Knack object idenfiter in format "object_xx". If specified, the
            instance will retrieve data from an object endpoint.
        scene : string (required with view if obj not specified)
            A Knack scene identifier in format "scene_xx"
        view : string (required with scene if obj not specified)
            A Knack view identifier in format "view_xx"
        field_obj : list (optional)
            An array of Knack object identifiers which specify the Knck objects
            that are referenced by a Knack view. Required to retrieve
            field metadata for view-based requests.
        include_ids : bool (optional | default : True)
            When true, Knack record IDs will be included in the parsed data.
        id_outfield : string (optional | default : 'id')
            The name that should be assigned to the the Knack record ID field.
            Make sure this field name does not match any existing
            field names in your application.
        tzinfo : string (optional | default : 'US/Central')
            This value should match the timezone setting of your Knack
            application, formatted as a timezone string compliant to the tz database
            (https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).
            When specified, datetime fields will be localized
            accordingly.
        raw_connections : bool (option | default : False)
            When true, connection fields will be parsed as "raw" connection fields,
            i.e., the connection field will be assigned
            an array of Knack record of format:
                {'id': 'abc_record_id', 'identifier': 'record identifier'}
            will be returned. When false, connection fields are (if one
            connection) returned as the field's display name, or (if many
            connetions) an array of the connection field's display name
        rows_per_page : int (optional | default: 1000)
            The number of rows to return per page requested. The maximum
            supported amount is 1000.
        page_limit : int (optional | default: 10)
            The maximum number of pages to request when retrieving data from
             an object or view.  
        '''
        self.obj = obj
        self.scene = scene
        self.view = view
        self.field_obj = field_obj
        self.filters = filters
        self.app_id = app_id
        self.api_key = api_key
        self.timeout = float(timeout)
        self.include_ids = include_ids
        self.id_outfield = id_outfield
        self.tzinfo = tzinfo
        self.raw_connections = raw_connections
        self.rows_per_page = rows_per_page
        self.page_limit = page_limit
        self.fields = None
        self.field_map = None
        self.endpoint = None
        self.data_raw = None
        self.data = None

        if not app_id:
            raise Exception('app_id is required.')

        if not api_key:
            logging.warning(
                '''
                API key is required to access private views and objects.
                '''
            )

        if not (self.view and self.scene) and not self.obj:
            raise Exception(
                '''
                Knack instance must specify an object or a view/scene
                '''
            )
        
        if self.obj and (self.view or self.scene):
            raise Exception(
                ''''
                Knack instance must specify an object or view/scene,
                but not both.
                '''
            )

        if (self.view and self.scene) and not (self.field_obj and self.api_key) :
            logging.warning(
                '''
                Field_obj and api_key are required for retrieving fieldnames.
                Raw field names will be used.
                '''
            )
          
        #  get data from view or object
        self.endpoint = self.get_endpoint()
        self.data_raw = self.get_data(self.endpoint, 'records', self.filters)
        
        if not self.data_raw:
            logging.warning('No data found at {}'.format(self.endpoint))

        if self.view and self.scene and self.field_obj and self.api_key:
            #  get field metadata for views with field objects and api key
            self.get_fields(self.field_obj)
            #  create fieldmap from metadata
            self.create_field_map()

        elif self.obj:
            #  get field mdetadata for object
            self.get_fields([self.obj])
            #  create fieldmap from metadata
            self.create_field_map()

        elif self.view and self.scene:
            #  extract knack fieldnames from data
            #  if api_key and/or field_obj unavailable
            self.extract_fields()

        if self.data_raw and self.field_map:
            #  parse data and send to self.data_parsed
            self.parse_data()
        else:
            self.data = self.data_raw


    def get_data(self, endpoint, record_type, filters=None):
        '''
        Get data from Knack view or object.

        Parameters
        ----------
        endpoint : string (required)
            URL of the api endpoint from which data will be retrieved
        record_type : string (required)
            Identifies the type of records to be retrieved from the Knack API.
            Must be specified as either 'fields' or 'records'.
        filters :
            A filter dict that should be included in the request. Only
            applicable for object-based record requests.

        Returns
        -------
        data (list or dict)
            If record_type is 'fields', a dictionary of field metatdata.
            If record type is 'records', a list of dictionaries of database
            records.
        '''
        print("Get data from {}".format(endpoint))
        
        headers = {
            'x-knack-application-id': self.app_id,
            'x-knack-rest-api-key' : self.api_key
        }
        
        if not self.api_key:
            #  use 'knack' as api key for public views
            headers['x-knack-rest-api-key'] = 'knack'

        current_page = 1
        data = []
        
        while current_page:
            
            params = {'page':current_page}

            if filters:
                params['filters'] = json.dumps(filters)

            req = requests.get(
                endpoint, headers=headers, params=params, timeout=self.timeout
            )

            if req.status_code == 200:
                data = data + req.json()[record_type]
            else:
                raise Exception(req.text)
            
            try:
                total_pages = req.json()['total_pages']
            except KeyError:
                total_pages = 1

            if self.page_limit < total_pages:
                total_pages = self.page_limit

            if current_page >= total_pages:
                current_page = None
            else:
                current_page = current_page + 1

        print("Retrieved {} {}".format( len(data), record_type))
        
        return data

    def get_fields(self, objects):
        '''
        Get field data from Knack objects
        
        Returns self.fields : A dictionary of field metadata where each entry

        '''
        fields = []
        raw_fields = {}

        for obj in objects:  
            print('Get field data for {}'.format(obj))

            fields_endpoint = 'https://api.knack.com/v1/objects/{}/fields?rows_per_page={}'.format(obj, self.rows_per_page)

            field_data = self.get_data(fields_endpoint, 'fields')

            fields = fields + field_data

        for field in fields:
            if field['key'] + '_raw' not in raw_fields:
                '''
                not all Knack fields have a 'raw' object
                so create one here
                '''
                raw_fields[field['key'] + '_raw'] = field  # 
        
        self.fields = raw_fields
        return self.fields
    
    def extract_fields(self):
        '''
        Extract field names from list of knack records.
        Assign list of fieldnames to self.fields.
        '''
        keys = [key for row in self.data_raw for key in row]
        self.fields = list( set(keys) )
        return self.fields

    def create_field_map(self): 
        field_map = {}
        
        for field in self.fields:
            new_field = field.replace('_raw', '')
            field_map[self.fields[field]['label']] = new_field

        if self.include_ids:
            #  update field map with map to record id field
            field_map[self.id_outfield] = 'id'

        self.field_map = field_map
        return self.field_map

    def parse_data(self):
        print('parse knack data')
        '''
        Parse Knack record objects and replace "raw" field names with field labels

        returns self.data (list of record dictionaries)
        '''
        parsed_data = []
        count = 0

        for record in self.data_raw:
            count += 1
            new_record = {}  #  parsed record goes here
            
            for key in record:  

                try:
                    record[key] = record[key].strip()
                except AttributeError:
                    pass

                if key in self.fields:
                    field_label = self.fields[key]['label']
                    field_type = self.fields[key]['type']

                else:
                    continue

                if field_type == 'address':
                    #  convert location field to lat/lon  
                    new_record['LATITUDE'] = record[key]['latitude']
                    new_record['LONGITUDE'] = record[key]['longitude']

                elif field_type in ['date', 'date_time']:
                    if record[key]:
                        d = int( record[key]['unix_timestamp'] )  #  this "unix" timestamp has milliseconds

                        if self.tzinfo:
                            #  convert from mills and replace timezone
                            d = arrow.get(d / 1000).replace(tzinfo=self.tzinfo)
                            #  convert back to mills
                            d = d.timestamp * 1000
                    else:
                        d = ''

                    new_record[field_label] = d

                elif field_type == 'connection':
                    if self.raw_connections:
                        #  assign entire connection dict to field
                        new_record[field_label] = record[key]
                    
                    elif record[key]:
                        #  assign only connection identifier
                        #  (aka display field) to label
                        new_record[field_label] = record[key][0]['identifier']
                    else:
                        #  connection is empty
                        new_record[field_label] = ''

                else:
                    new_record[field_label] = record[key]

            if self.include_ids:
                new_record[self.id_outfield] = record['id']

            parsed_data.append(new_record)

        self.data = parsed_data

        return self.data


    def get_endpoint(self):
        '''
        Get endpoint for object or view-based request

        return self.endpoint (string)
        '''
        if self.scene and self.view:
            self.endpoint = 'https://api.knack.com/v1/pages/{}/views/{}/records?rows_per_page={}'.format( self.scene, self.view, self.rows_per_page)

            return self.endpoint
        
        if self.obj:
            self.endpoint = 'https://api.knack.com/v1/objects/{}/records?rows_per_page={}'.format( self.obj, self.rows_per_page ) 
            return self.endpoint

    def to_csv(self, filename, delimiter=","):
        '''
        Write data from Knack instance to csv
        
        Parameters
        ----------
        filename : string (required)
            Name of the output file that will be created
        delimiter : string (optional | default : ",")
            The column separation character that will be used when
            writing data to file.

        Returns
        _______
        None
        '''
        with open(filename, 'w', newline='\n') as fout:
            
            if self.field_map:
                fieldnames = self.field_map.keys()
            else:
                fieldnames = self.fields

            writer = csv.DictWriter(fout, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()
            for row in self.data:
                writer.writerow(row)

        return None

def update_record(record_dict, knack_object, id_key, app_id, api_key, timeout=10):
    print('update knack record')

    knack_id = record_dict[id_key]  #  extract knack ID and remove from update object

    del record_dict[id_key]

    update_endpoint = 'https://api.knack.com/v1/objects/{}/records/{}'.format(knack_object, knack_id)

    headers = { 
        'x-knack-application-id': app_id,
        'x-knack-rest-api-key': api_key,
        'Content-type': 'application/json'
    }
    
    req = requests.put(
            update_endpoint, 
            headers=headers,
            json=record_dict,
            timeout=timeout
    )

    return req.json()
    

def insert_record(record_dict, knack_object, app_id, api_key, timeout=10):
    print('update knack record')
    
    insert_endpoint = 'https://api.knack.com/v1/objects/{}/records'.format(knack_object)
    
    headers = {
        'x-knack-application-id': app_id,
        'x-knack-rest-api-key': api_key,
        'Content-type': 'application/json'
    }

    req = requests.post(
        insert_endpoint,
        headers=headers,
        json=record_dict,
        timeout=timeout
    )

    return req.json()


