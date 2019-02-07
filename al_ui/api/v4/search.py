
from flask import request

from assemblyline.datastore import SearchException
from al_ui.api.base import api_login, make_api_response, make_subapi_blueprint
from al_ui.config import STORAGE

BUCKET_MAP = {
    'alert': STORAGE.alert,
    'file': STORAGE.file,
    'result': STORAGE.result,
    'signature': STORAGE.signature,
    'submission': STORAGE.submission
}


SUB_API = 'search'
search_api = make_subapi_blueprint(SUB_API, api_version=4)
search_api._doc = "Perform search queries"


@search_api.route("/<bucket>/", methods=["GET", "POST"])
@api_login(required_priv=['R'])
def search(bucket, **kwargs):
    """
    Search through specified buckets for a given query.
    Uses lucene search syntax for query.

    Variables:
    bucket  =>   Bucket to search in (alert, submission,...)

    Arguments:
    query   =>   Query to search for

    Optional Arguments:
    filters =>   List of additional filter queries limit the data
    offset  =>   Offset in the results
    rows    =>   Max number of results
    sort    =>   How to sort the results
    fl      =>   List of fields to return
    timeout =>   Maximum execution time (ms)

    Data Block (POST ONLY):
    {"query": "query",     # Query to search for
     "offset": 0,          # Offset in the results
     "rows": 100,          # Max number of results
     "sort": "field asc",  # How to sort the results
     "fl": "id,score",     # List of fields to return
     "timeout": 1000,      # Maximum execution time (ms)
     "filters": ['fq']}    # List of additional filter queries limit the data


    Result example:
    {"total": 201,       # Total results found
     "offset": 0,        # Offset in the result list
     "rows": 100,        # Number of results returned
     "items": []}        # List of results
    """
    if bucket not in BUCKET_MAP:
        return make_api_response("", f"Not a valid bucket to search in: {bucket}", 400)

    user = kwargs['user']
    fields = ["offset", "rows", "sort", "fl", "timeout"]
    multi_fields = ['filters']

    if request.method == "POST":
        req_data = request.json
        params = {k: req_data.get(k, None) for k in fields if req_data.get(k, None) is not None}
        params.update({k: req_data.get(k, None) for k in multi_fields if req_data.get(k, None) is not None})
        query = req_data.get('query', None)

    else:
        req_data = request.args
        params = {k: req_data.get(k, None) for k in fields if req_data.get(k, None) is not None}
        params.update({k: req_data.getlist(k, None) for k in multi_fields if req_data.get(k, None) is not None})
        query = request.args.get('query', None)

    params.update({'access_control': user['access_control'], 'as_obj': False})

    if not query:
        return make_api_response("", "There was no search query.", 400)

    try:
        return make_api_response(BUCKET_MAP[bucket].search(query, **params))
    except SearchException as e:
        return make_api_response("", f"SearchException: {e}", 400)


@search_api.route("/grouped/<bucket>/<group_field>/", methods=["GET", "POST"])
@api_login(required_priv=['R'])
def group_search(bucket, group_field, **kwargs):
    """
    Search through all relevant buckets for a given query and
    groups the data based on a specific field.
    Uses lucene search syntax for query.

    Variables:
    bucket       =>   Bucket to search in (alert, submission,...)
    group_field  =>   Field to group on

    Optional Arguments:
    group_sort   =>   How to sort the results inside the group
    limit        =>   Maximum number of results return for each groups
    query        =>   Query to search for
    filters      =>   List of additional filter queries limit the data
    offset       =>   Offset in the results
    rows         =>   Max number of results
    sort         =>   How to sort the results
    fl           =>   List of fields to return

    Data Block (POST ONLY):
    {"group_sort": "score desc",
     "limit": "10",
     "query": "query",
     "offset": 0,
     "rows": 100,
     "sort": "field asc",
     "fl": "id,score",
     "filters": ['fq']}


    Result example:
    {"total": 201,       # Total results found
     "offset": 0,        # Offset in the result list
     "rows": 100,        # Number of results returned
     "items": []}        # List of results
    """
    if bucket not in BUCKET_MAP:
        return make_api_response("", f"Not a valid bucket to search in: {bucket}", 400)

    user = kwargs['user']
    fields = ["group_sort", "limit", "query", "offset", "rows", "sort", "fl", "timeout"]
    multi_fields = ['filters']

    if request.method == "POST":
        req_data = request.json
        params = {k: req_data.get(k, None) for k in fields if req_data.get(k, None) is not None}
        params.update({k: req_data.get(k, None) for k in multi_fields if req_data.get(k, None) is not None})

    else:
        req_data = request.args
        params = {k: req_data.get(k, None) for k in fields if req_data.get(k, None) is not None}
        params.update({k: req_data.getlist(k, None) for k in multi_fields if req_data.get(k, None) is not None})

    params.update({'access_control': user['access_control'], 'as_obj': False})

    if not group_field:
        return make_api_response("", "The field to group on was not specified.", 400)

    try:
        return make_api_response(BUCKET_MAP[bucket].grouped_search(group_field, **params))
    except SearchException as e:
        return make_api_response("", f"SearchException: {e}", 400)


@search_api.route("/deep/<bucket>/", methods=["GET", "POST"])
@api_login(required_priv=['R'])
def deep_search(bucket, **kwargs):
    """
    Deep Search through given bucket. This will return all items matching
    the query.
    Uses lucene search syntax.
    
    Variables:
    bucket     =>  Buckets to be used to stream the search query from
    
    Arguments: 
    query      => query to search for

    Optional Arguments:
    limit      => Stop gathering result after this many items returned
    fl         => Field list to return
    filters    => Filter queries to be applied after the query
    
    Data Block (POST ONLY):
    {"query": "id:*",
     "limit": "10",
     "fl": "id,score",
     "filters": ['fq']}
     
    Result example:
    { "items": [],      # List of results
      "length": 0 }     # Number of items returned       
    """
    if bucket not in BUCKET_MAP:
        return make_api_response("", f"Not a valid bucket to search in: {bucket}", 400)

    user = kwargs['user']
    fields = ["fl"]
    multi_fields = ['filters']

    if request.method == "POST":
        req_data = request.json
        params = {k: req_data.get(k, None) for k in fields if req_data.get(k, None) is not None}
        params.update({k: req_data.get(k, None) for k in multi_fields if req_data.get(k, None) is not None})
    else:
        req_data = request.args
        params = {k: req_data.get(k, None) for k in fields if req_data.get(k, None) is not None}
        params.update({k: req_data.getlist(k, None) for k in multi_fields if req_data.get(k, None) is not None})

    query = req_data.get('query', None) or req_data.get('q', None)
    limit = req_data.get('limit', None)
    if limit:
        limit = int(limit)

    params.update({'access_control': user['access_control'], 'as_obj': False})

    if not query:
        return make_api_response("", "No query was specified.", 400)

    out = []
    try:
        for item in BUCKET_MAP[bucket].stream_search(query, **params):
            out.append(item)
            if limit and len(out) == limit:
                break

        return make_api_response({"length": len(out), "items": out})
    except SearchException as e:
        return make_api_response("", f"SearchException: {e}", 400)


@search_api.route("/inspect/<bucket>/", methods=["GET", "POST"])
@api_login(required_priv=['R'])
def inspect_search(bucket, **kwargs):
    """
    Inspect a search query to find out how much result items are
    going to be returned.
    Uses lucene search syntax.
    
    Variables:
    bucket    =>  Buckets to be used to stream the search query from
    
    Arguments: 
    query     => Query to search for

    Optional Arguments:
    filters   => Filter queries to be applied after the query
    
    Data Block (POST ONLY):
    {"query": "id:*",
     "filters": ['fq']}
     
    Result example:
    0         # number of items return by the query
    """
    if bucket not in BUCKET_MAP:
        return make_api_response("", f"Not a valid bucket to search in: {bucket}", 400)

    user = kwargs['user']
    multi_fields = ['filters']

    if request.method == "POST":
        req_data = request.json
        params = {k: req_data.get(k, None) for k in multi_fields if req_data.get(k, None) is not None}
    else:
        req_data = request.args
        params = {k: req_data.getlist(k, None) for k in multi_fields if req_data.get(k, None) is not None}

    query = req_data.get('query', None) or req_data.get('q', None)
    params.update({'access_control': user['access_control'], 'as_obj': False, 'rows': 0, "fl": "id"})

    if not query:
        return make_api_response("", "No query was specified.", 400)

    try:
        return make_api_response(BUCKET_MAP[bucket].search(query, **params)['total'])
    except SearchException as e:
        return make_api_response("", f"SearchException: {e}", 400)


# noinspection PyUnusedLocal
@search_api.route("/fields/<bucket>/", methods=["GET"])
@api_login(required_priv=['R'])
def list_bucket_fields(bucket, **_):
    """
    List all available fields for a given bucket

    Variables:
    bucket  =>     Which specific bucket you want to know the fields for


    Arguments:
    None

    Data Block:
    None

    Result example:
    {
        "<<FIELD_NAME>>": {      # For a given field
            indexed: True,        # Is the field indexed
            stored: False,        # Is the field stored
            type: string          # What type of data in the field
            },
        ...

    }
    """
    if bucket not in BUCKET_MAP:
        return make_api_response("", f"Not a valid bucket to search in: {bucket}", 400)

    return make_api_response(BUCKET_MAP[bucket].fields())


@search_api.route("/facet/<bucket>/<field>/", methods=["GET", "POST"])
@api_login(required_priv=['R'])
def facet(bucket, field, **kwargs):
    """
    Perform field analysis on the selected field. (Also known as facetting in lucene)
    This essentially counts the number of instances a field is seen with each specific values
    where the documents matches the specified queries.
    
    Variables:
    bucket       =>   Bucket to search in (alert, submission,...)
    field        =>   Field to analyse
    
    Optional Arguments:
    query        =>   Query to search for
    mincount    =>   Minimum item count for the fieldvalue to be returned
    filters      =>   Additional query to limit to output

    Data Block (POST ONLY):
    {"query": "id:*",
     "mincount": "10",
     "filters": ['fq']}
    
    Result example:
    {                 # Facetting results
     "value_0": 2,
     ...
     "value_N": 19,
    }
    """
    if bucket not in BUCKET_MAP:
        return make_api_response("", f"Not a valid bucket to search in: {bucket}", 400)

    user = kwargs['user']
    fields = ["query", "mincount"]
    multi_fields = ['filters']

    if request.method == "POST":
        req_data = request.json
        params = {k: req_data.get(k, None) for k in fields if req_data.get(k, None) is not None}
        params.update({k: req_data.get(k, None) for k in multi_fields if req_data.get(k, None) is not None})

    else:
        req_data = request.args
        params = {k: req_data.get(k, None) for k in fields if req_data.get(k, None) is not None}
        params.update({k: req_data.getlist(k, None) for k in multi_fields if req_data.get(k, None) is not None})

    params.update({'access_control': user['access_control']})
    
    try:
        return make_api_response(BUCKET_MAP[bucket].facet(field, **params))
    except SearchException as e:
        return make_api_response("", f"SearchException: {e}", 400)


@search_api.route("/histogram/<bucket>/<field>/", methods=["GET", "POST"])
@api_login(required_priv=['R'])
def histogram(bucket, field, **kwargs):
    """
    Generate an histogram based on a time or and int field using a specific gap size
    
    Variables:
    bucket       =>   Bucket to search in (alert, submission,...)
    field        =>   Field to generate the histogram from

    Optional Arguments:
    query        =>   Query to search for
    mincount     =>   Minimum item count for the fieldvalue to be returned
    filters      =>   Additional query to limit to output
    start        =>   Value at which to start creating the histogram
    end          =>   Value at which to end the histogram
    gap          =>   Size of each step in the histogram

    Data Block (POST ONLY):
    {"query": "id:*",
     "mincount": "10",
     "filters": ['fq'],
     "start": 0,
     "end": 100,
     "gap": 10}

    Result example:
    {                 # Histogram results
     "step_0": 2,
     ...
     "step_N": 19,
    }
    """
    # TODO: Detect field type and set default histogram start, end, gap values or create another api
    #       for integer histogram

    if bucket not in BUCKET_MAP:
        return make_api_response("", f"Not a valid bucket to search in: {bucket}", 400)

    user = kwargs['user']
    fields = ["query", "mincount", "start", "end", "gap"]
    multi_fields = ['filters']

    if request.method == "POST":
        req_data = request.json
        params = {k: req_data.get(k, None) for k in fields if req_data.get(k, None) is not None}
        params.update({k: req_data.get(k, None) for k in multi_fields if req_data.get(k, None) is not None})

    else:
        req_data = request.args
        params = {k: req_data.get(k, None) for k in fields if req_data.get(k, None) is not None}
        params.update({k: req_data.getlist(k, None) for k in multi_fields if req_data.get(k, None) is not None})

    params.update({'access_control': user['access_control']})

    try:
        return make_api_response(BUCKET_MAP[bucket].histogram(field, **params))
    except SearchException as e:
        return make_api_response("", f"SearchException: {e}", 400)
