from typing import Optional
from typing import Dict, List, Optional
from beacon.db.filters import apply_filters
from beacon.db.schemas import DefaultSchemas
from beacon.db.utils import query_id, get_count, get_documents, get_cross_query
from beacon.request.model import RequestParams
from beacon.db import client

import logging
import yaml

LOG = logging.getLogger(__name__)

def include_resultset_responses(query: Dict[str, List[dict]], qparams: RequestParams):
    LOG.debug("Include Resultset Responses = {}".format(qparams.query.include_resultset_responses))
    return query

def apply_request_parameters(query: Dict[str, List[dict]], qparams: RequestParams):
    LOG.debug("Request parameters len = {}".format(len(qparams.query.request_parameters)))
    for k, v in qparams.query.request_parameters.items():
        if ',' in v:
            query["$text"] = {}
            v_list = v.split(',')
            v_string=''
            for val in v_list:
                v_string += f'"{val}"'
            query["$text"]["$search"]=v_string
        elif k == 'datasets':
            if v == '*******':
                query = {}
            else:
                query["$text"] = {}
                string = ''
                for word in v:
                    string = word + ' '
                dict_search={}
                dict_search['$search']=string
                query["$text"]=dict_search
                
        else:
            query["$text"] = {}
            dict_search={}
            dict_search['$search']=v
            query["$text"]=dict_search
    LOG.debug(query)
    return query

def get_datasets(entry_id: Optional[str], qparams: RequestParams):
    collection = 'datasets'
    limit = qparams.query.pagination.limit
    query = apply_request_parameters({}, qparams)
    #query = apply_filters({}, qparams.query.filters, collection)
    schema = DefaultSchemas.DATASETS
    count = get_count(client.beacon.datasets, query)
    docs = get_documents(
        client.beacon.datasets,
        query,
        0,
        qparams.query.pagination.skip*limit
    )
    return schema, count, docs


def get_dataset_with_id(entry_id: Optional[str], qparams: RequestParams):
    collection = 'datasets'
    limit = qparams.query.pagination.limit
    query = apply_request_parameters({}, qparams)
    #query = apply_filters({}, qparams.query.filters, collection)
    query = query_id(query, entry_id)
    schema = DefaultSchemas.DATASETS
    count = get_count(client.beacon.datasets, query)
    docs = get_documents(
        client.beacon.datasets,
        query,
        qparams.query.pagination.skip,
        qparams.query.pagination.skip*limit
    )
    return schema, count, docs


def get_variants_of_dataset(entry_id: Optional[str], qparams: RequestParams, dataset: str):
    collection = 'datasets'
    dataset_count=0
    limit = qparams.query.pagination.limit
    query = apply_filters({}, qparams.query.filters, collection)
    query = query_id(query, entry_id)
    count = get_count(client.beacon.datasets, query)
    with open("/beacon/beacon/request/datasets.yml", 'r') as datasets_file:
        datasets_dict = yaml.safe_load(datasets_file)
    
    individual_ids=get_cross_query(datasets_dict[entry_id],'individualIds','caseLevelData.biosampleId')
    query = apply_filters(individual_ids, qparams.query.filters, collection)
    schema = DefaultSchemas.GENOMICVARIATIONS
    with open("/beacon/beacon/request/datasets.yml", 'r') as datasets_file:
        datasets_dict = yaml.safe_load(datasets_file)
    include = qparams.query.include_resultset_responses
    limit = qparams.query.pagination.limit
    if limit > 100 or limit == 0:
        limit = 100
    if include == 'MISS':
        count = get_count(client.beacon.genomicVariations, query)
        query_count=query
        i=1
        for k, v in datasets_dict.items():
            query_count["$or"]=[]
            if k == dataset:
                for id in v:
                    if i < len(v):
                        queryid={}
                        queryid["caseLevelData.biosampleId"]=id
                        query_count["$or"].append(queryid)
                        i+=1
                    else:
                        queryid={}
                        queryid["caseLevelData.biosampleId"]=id
                        query_count["$or"].append(queryid)
                        i=1
                if query_count["$or"]!=[]:
                    dataset_count = get_count(client.beacon.genomicVariations, query_count)
                    if dataset_count!=0:
                        return schema, count, -1, None
                    LOG.debug(dataset_count)
                    docs = get_documents(
                        client.beacon.genomicVariations,
                        query_count,
                        qparams.query.pagination.skip*limit,
                        limit
                    )
                else:
                    dataset_count=0

    elif include == 'NONE':
            count = get_count(client.beacon.genomicVariations, query)
            dataset_count=0
            docs = get_documents(
            client.beacon.genomicVariations,
            query,
            qparams.query.pagination.skip*limit,
            limit
        )
    elif include == 'HIT':
        count = get_count(client.beacon.genomicVariations, query)
        query_count=query
        i=1
        query_count["$or"]=[]
        for k, v in datasets_dict.items():
            if k == dataset:
                for id in v:
                    
                    if i < len(v):
                        queryid={}
                        queryid["caseLevelData.biosampleId"]=id
                        query_count["$or"].append(queryid)
                        i+=1
                    else:
                        queryid={}
                        queryid["caseLevelData.biosampleId"]=id
                        query_count["$or"].append(queryid)
                        i=1
                if query_count["$or"]!=[]:
                    dataset_count = get_count(client.beacon.genomicVariations, query_count)
                    LOG.debug(dataset_count)
                    docs = get_documents(
                        client.beacon.genomicVariations,
                        query_count,
                        qparams.query.pagination.skip*limit,
                        limit
                    )
                else:
                    dataset_count=0
        if dataset_count==0:
            return schema, count, -1, None
    elif include == 'ALL':
        count = get_count(client.beacon.genomicVariations, query)
        query_count=query
        i=1
        for k, v in datasets_dict.items():
            query_count["$or"]=[]
            if k == dataset:
                for id in v:
                    if i < len(v):
                        queryid={}
                        queryid["caseLevelData.biosampleId"]=id
                        query_count["$or"].append(queryid)
                        i+=1
                    else:
                        queryid={}
                        queryid["caseLevelData.biosampleId"]=id
                        query_count["$or"].append(queryid)
                        i=1
                if query_count["$or"]!=[]:
                    dataset_count = get_count(client.beacon.genomicVariations, query_count)
                    LOG.debug(dataset_count)
                    docs = get_documents(
                        client.beacon.genomicVariations,
                        query_count,
                        qparams.query.pagination.skip*limit,
                        limit
                    )
                else:
                    dataset_count=0
    return schema, count, dataset_count, docs


def get_biosamples_of_dataset(entry_id: Optional[str], qparams: RequestParams, dataset: str):
    collection = 'datasets'
    dataset_count=0
    limit = qparams.query.pagination.limit
    query = apply_filters({}, qparams.query.filters, collection)
    query = query_id(query, entry_id)
    count = get_count(client.beacon.datasets, query)
    with open("/beacon/beacon/request/datasets.yml", 'r') as datasets_file:
        datasets_dict = yaml.safe_load(datasets_file)
    biosample_ids=get_cross_query(datasets_dict[entry_id],'biosampleIds','id')
    query = apply_filters(biosample_ids, qparams.query.filters, collection)
    LOG.debug(query)
    schema = DefaultSchemas.BIOSAMPLES
    with open("/beacon/beacon/request/datasets.yml", 'r') as datasets_file:
        datasets_dict = yaml.safe_load(datasets_file)
    include = qparams.query.include_resultset_responses
    limit = qparams.query.pagination.limit
    if limit > 100 or limit == 0:
        limit = 100
    if include == 'MISS':
        count = get_count(client.beacon.biosamples, query)
        query_count=query
        i=1
        for k, v in datasets_dict.items():
            query_count["$or"]=[]
            if k == dataset:
                for id in v:
                    if i < len(v):
                        queryid={}
                        queryid["id"]=id
                        query_count["$or"].append(queryid)
                        i+=1
                    else:
                        queryid={}
                        queryid["id"]=id
                        query_count["$or"].append(queryid)
                        i=1
                if query_count["$or"]!=[]:
                    dataset_count = get_count(client.beacon.biosamples, query_count)
                    if dataset_count!=0:
                        return schema, count, -1, None
                    LOG.debug(dataset_count)
                    docs = get_documents(
                        client.beacon.biosamples,
                        query_count,
                        qparams.query.pagination.skip*limit,
                        limit
                    )
                else:
                    dataset_count=0

    elif include == 'NONE':
            count = get_count(client.beacon.biosamples, query)
            dataset_count=0
            docs = get_documents(
            client.beacon.biosamples,
            query,
            qparams.query.pagination.skip*limit,
            limit
        )
    elif include == 'HIT':
        count = get_count(client.beacon.biosamples, query)
        query_count=query
        i=1
        query_count["$or"]=[]
        for k, v in datasets_dict.items():
            if k == dataset:
                for id in v:
                    
                    if i < len(v):
                        queryid={}
                        queryid["id"]=id
                        query_count["$or"].append(queryid)
                        i+=1
                    else:
                        queryid={}
                        queryid["id"]=id
                        query_count["$or"].append(queryid)
                        i=1
                if query_count["$or"]!=[]:
                    dataset_count = get_count(client.beacon.biosamples, query_count)
                    LOG.debug(dataset_count)
                    docs = get_documents(
                        client.beacon.biosamples,
                        query_count,
                        qparams.query.pagination.skip*limit,
                        limit
                    )
                else:
                    dataset_count=0
        if dataset_count==0:
            return schema, count, -1, None
    elif include == 'ALL':
        count = get_count(client.beacon.biosamples, query)
        query_count=query
        i=1
        for k, v in datasets_dict.items():
            query_count["$or"]=[]
            if k == dataset:
                for id in v:
                    if i < len(v):
                        queryid={}
                        queryid["id"]=id
                        query_count["$or"].append(queryid)
                        i+=1
                    else:
                        queryid={}
                        queryid["id"]=id
                        query_count["$or"].append(queryid)
                        i=1
                if query_count["$or"]!=[]:
                    dataset_count = get_count(client.beacon.biosamples, query_count)
                    LOG.debug(dataset_count)
                    docs = get_documents(
                        client.beacon.biosamples,
                        query_count,
                        qparams.query.pagination.skip*limit,
                        limit
                    )
                else:
                    dataset_count=0
    return schema, count, dataset_count, docs


def get_individuals_of_dataset(entry_id: Optional[str], qparams: RequestParams, dataset: str):
    collection = 'datasets'
    dataset_count=0
    limit = qparams.query.pagination.limit
    query = apply_filters({}, qparams.query.filters, collection)
    query = query_id(query, entry_id)
    count = get_count(client.beacon.datasets, query)
    with open("/beacon/beacon/request/datasets.yml", 'r') as datasets_file:
        datasets_dict = yaml.safe_load(datasets_file)
    individual_ids=get_cross_query(datasets_dict[entry_id],'individualIds','id')
    query = apply_filters(individual_ids, qparams.query.filters, collection)
    schema = DefaultSchemas.INDIVIDUALS
    with open("/beacon/beacon/request/datasets.yml", 'r') as datasets_file:
        datasets_dict = yaml.safe_load(datasets_file)
    include = qparams.query.include_resultset_responses
    limit = qparams.query.pagination.limit
    if limit > 100 or limit == 0:
        limit = 100
    if include == 'MISS':
        count = get_count(client.beacon.individuals, query)
        query_count=query
        i=1
        for k, v in datasets_dict.items():
            query_count["$or"]=[]
            if k == dataset:
                for id in v:
                    if i < len(v):
                        queryid={}
                        queryid["id"]=id
                        query_count["$or"].append(queryid)
                        i+=1
                    else:
                        queryid={}
                        queryid["id"]=id
                        query_count["$or"].append(queryid)
                        i=1
                if query_count["$or"]!=[]:
                    dataset_count = get_count(client.beacon.individuals, query_count)
                    LOG.debug(dataset_count)
                    if dataset_count!=0:
                        return schema, count, -1, None
                    docs = get_documents(
                        client.beacon.individuals,
                        query_count,
                        qparams.query.pagination.skip*limit,
                        limit
                    )
                else:
                    dataset_count=0
    elif include == 'NONE':
            count = get_count(client.beacon.individuals, query)
            dataset_count=0
            docs = get_documents(
            client.beacon.analyses,
            query,
            qparams.query.pagination.skip*limit,
            limit
        )
    elif include == 'HIT':
        count = get_count(client.beacon.individuals, query)
        query_count=query
        i=1
        query_count["$or"]=[]
        for k, v in datasets_dict.items():
            if k == dataset:
                for id in v:
                    
                    if i < len(v):
                        queryid={}
                        queryid["id"]=id
                        query_count["$or"].append(queryid)
                        i+=1
                    else:
                        queryid={}
                        queryid["id"]=id
                        query_count["$or"].append(queryid)
                        i=1
                if query_count["$or"]!=[]:
                    dataset_count = get_count(client.beacon.individuals, query_count)
                    LOG.debug(dataset_count)
                    docs = get_documents(
                        client.beacon.individuals,
                        query_count,
                        qparams.query.pagination.skip*limit,
                        limit
                    )
                else:
                    dataset_count=0
        if dataset_count==0:
            return schema, count, -1, None
    elif include == 'ALL':
        count = get_count(client.beacon.individuals, query)
        query_count=query
        i=1
        for k, v in datasets_dict.items():
            query_count["$or"]=[]
            if k == dataset:
                for id in v:
                    if i < len(v):
                        queryid={}
                        queryid["id"]=id
                        query_count["$or"].append(queryid)
                        i+=1
                    else:
                        queryid={}
                        queryid["id"]=id
                        query_count["$or"].append(queryid)
                        i=1
                if query_count["$or"]!=[]:
                    dataset_count = get_count(client.beacon.individuals, query_count)
                    LOG.debug(dataset_count)
                    docs = get_documents(
                        client.beacon.individuals,
                        query_count,
                        qparams.query.pagination.skip*limit,
                        limit
                    )
                else:
                    dataset_count=0
    return schema, count, dataset_count, docs


def filter_public_datasets(requested_datasets_ids):
    query = {"dataUseConditions.duoDataUse.modifiers.id": "DUO:0000004"}
    return client.beacon.datasets \
        .find(query)


def get_filtering_terms_of_dataset(entry_id: Optional[str], qparams: RequestParams):
    query = {'scope': 'datasets'}
    schema = DefaultSchemas.FILTERINGTERMS
    count = get_count(client.beacon.filtering_terms, query)
    docs = get_documents(
        client.beacon.filtering_terms,
        query,
        qparams.query.pagination.skip,
        0
    )
    return schema, count, docs


def get_runs_of_dataset(entry_id: Optional[str], qparams: RequestParams, dataset: str):
    collection = 'datasets'
    dataset_count=0
    limit = qparams.query.pagination.limit
    query = apply_filters({}, qparams.query.filters, collection)
    query = query_id(query, entry_id)
    count = get_count(client.beacon.datasets, query)
    with open("/beacon/beacon/request/datasets.yml", 'r') as datasets_file:
        datasets_dict = yaml.safe_load(datasets_file)
    biosample_ids=get_cross_query(datasets_dict[entry_id],'biosampleIds','id')
    query = apply_filters(biosample_ids, qparams.query.filters, collection)
    schema = DefaultSchemas.RUNS
    with open("/beacon/beacon/request/datasets.yml", 'r') as datasets_file:
        datasets_dict = yaml.safe_load(datasets_file)
    include = qparams.query.include_resultset_responses
    limit = qparams.query.pagination.limit
    if limit > 100 or limit == 0:
        limit = 100
    if include == 'MISS':
        count = get_count(client.beacon.runs, query)
        query_count=query
        i=1
        for k, v in datasets_dict.items():
            query_count["$or"]=[]
            if k == dataset:
                for id in v:
                    if i < len(v):
                        queryid={}
                        queryid["biosampleId"]=id
                        query_count["$or"].append(queryid)
                        i+=1
                    else:
                        queryid={}
                        queryid["biosampleId"]=id
                        query_count["$or"].append(queryid)
                        i=1
                if query_count["$or"]!=[]:
                    dataset_count = get_count(client.beacon.runs, query_count)
                    if dataset_count!=0:
                        return schema, count, -1, None
                    LOG.debug(dataset_count)
                    docs = get_documents(
                        client.beacon.runs,
                        query_count,
                        qparams.query.pagination.skip*limit,
                        limit
                    )
                else:
                    dataset_count=0

    elif include == 'NONE':
            count = get_count(client.beacon.runs, query)
            dataset_count=0
            docs = get_documents(
            client.beacon.runs,
            query,
            qparams.query.pagination.skip*limit,
            limit
        )
    elif include == 'HIT':
        count = get_count(client.beacon.runs, query)
        query_count=query
        i=1
        query_count["$or"]=[]
        for k, v in datasets_dict.items():
            if k == dataset:
                for id in v:
                    
                    if i < len(v):
                        queryid={}
                        queryid["biosampleId"]=id
                        query_count["$or"].append(queryid)
                        i+=1
                    else:
                        queryid={}
                        queryid["biosampleId"]=id
                        query_count["$or"].append(queryid)
                        i=1
                if query_count["$or"]!=[]:
                    dataset_count = get_count(client.beacon.runs, query_count)
                    LOG.debug(dataset_count)
                    docs = get_documents(
                        client.beacon.runs,
                        query_count,
                        qparams.query.pagination.skip*limit,
                        limit
                    )
                else:
                    dataset_count=0
        if dataset_count==0:
            return schema, count, -1, None
    elif include == 'ALL':
        count = get_count(client.beacon.runs, query)
        query_count=query
        i=1
        for k, v in datasets_dict.items():
            query_count["$or"]=[]
            if k == dataset:
                for id in v:
                    if i < len(v):
                        queryid={}
                        queryid["biosampleId"]=id
                        query_count["$or"].append(queryid)
                        i+=1
                    else:
                        queryid={}
                        queryid["biosampleId"]=id
                        query_count["$or"].append(queryid)
                        i=1
                if query_count["$or"]!=[]:
                    dataset_count = get_count(client.beacon.runs, query_count)
                    LOG.debug(dataset_count)
                    docs = get_documents(
                        client.beacon.runs,
                        query_count,
                        qparams.query.pagination.skip*limit,
                        limit
                    )
                else:
                    dataset_count=0
    return schema, count, dataset_count, docs


def get_analyses_of_dataset(entry_id: Optional[str], qparams: RequestParams, dataset: str):
    collection = 'datasets'
    dataset_count=0
    limit = qparams.query.pagination.limit
    query = apply_filters({}, qparams.query.filters, collection)
    query = query_id(query, entry_id)
    count = get_count(client.beacon.datasets, query)
    with open("/beacon/beacon/request/datasets.yml", 'r') as datasets_file:
        datasets_dict = yaml.safe_load(datasets_file)
    biosample_ids=get_cross_query(datasets_dict[entry_id],'biosampleIds','id')
    query = apply_filters(biosample_ids, qparams.query.filters, collection)
    schema = DefaultSchemas.ANALYSES
    with open("/beacon/beacon/request/datasets.yml", 'r') as datasets_file:
        datasets_dict = yaml.safe_load(datasets_file)
    include = qparams.query.include_resultset_responses
    limit = qparams.query.pagination.limit
    if limit > 100 or limit == 0:
        limit = 100
    if include == 'MISS':
        count = get_count(client.beacon.analyses, query)
        query_count=query
        i=1
        for k, v in datasets_dict.items():
            query_count["$or"]=[]
            if k == dataset:
                for id in v:
                    if i < len(v):
                        queryid={}
                        queryid["biosampleId"]=id
                        query_count["$or"].append(queryid)
                        i+=1
                    else:
                        queryid={}
                        queryid["biosampleId"]=id
                        query_count["$or"].append(queryid)
                        i=1
                if query_count["$or"]!=[]:
                    dataset_count = get_count(client.beacon.analyses, query_count)
                    if dataset_count!=0:
                        return schema, count, -1, None
                    LOG.debug(dataset_count)
                    docs = get_documents(
                        client.beacon.analyses,
                        query_count,
                        qparams.query.pagination.skip*limit,
                        limit
                    )
                else:
                    dataset_count=0

    elif include == 'NONE':
            count = get_count(client.beacon.analyses, query)
            dataset_count=0
            docs = get_documents(
            client.beacon.analyses,
            query,
            qparams.query.pagination.skip*limit,
            limit
        )
    elif include == 'HIT':
        count = get_count(client.beacon.analyses, query)
        query_count=query
        i=1
        query_count["$or"]=[]
        for k, v in datasets_dict.items():
            if k == dataset:
                for id in v:
                    
                    if i < len(v):
                        queryid={}
                        queryid["biosampleId"]=id
                        query_count["$or"].append(queryid)
                        i+=1
                    else:
                        queryid={}
                        queryid["biosampleId"]=id
                        query_count["$or"].append(queryid)
                        i=1
                if query_count["$or"]!=[]:
                    dataset_count = get_count(client.beacon.analyses, query_count)
                    LOG.debug(dataset_count)
                    docs = get_documents(
                        client.beacon.analyses,
                        query_count,
                        qparams.query.pagination.skip*limit,
                        limit
                    )
                else:
                    dataset_count=0
        if dataset_count==0:
            return schema, count, -1, None
    elif include == 'ALL':
        count = get_count(client.beacon.analyses, query)
        query_count=query
        i=1
        for k, v in datasets_dict.items():
            query_count["$or"]=[]
            if k == dataset:
                for id in v:
                    if i < len(v):
                        queryid={}
                        queryid["biosampleId"]=id
                        query_count["$or"].append(queryid)
                        i+=1
                    else:
                        queryid={}
                        queryid["biosampleId"]=id
                        query_count["$or"].append(queryid)
                        i=1
                if query_count["$or"]!=[]:
                    dataset_count = get_count(client.beacon.analyses, query_count)
                    LOG.debug(dataset_count)
                    docs = get_documents(
                        client.beacon.analyses,
                        query_count,
                        qparams.query.pagination.skip*limit,
                        limit
                    )
                else:
                    dataset_count=0
    return schema, count, dataset_count, docs
