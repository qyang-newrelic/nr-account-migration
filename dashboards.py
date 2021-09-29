import os
import argparse
import library.utils as utils
import library.migrationlogger as m_logger
import library.localstore as store
import library.clients.entityclient as ec
import library.status.dashboard_status as ds


log = m_logger.get_logger(os.path.basename(__file__))


def print_args(args):
    #log.info("Using fromFile : " + args.fromFile[0])
    log.info("Using sourceAccount : " + str(args.sourceAccount[0]))

    
    #log.info("Using sourceApiKey : " + len(src_api_key[:-4])*"*"+src_api_key[-4:])


def configure_parser():
    parser = argparse.ArgumentParser(description='Migrate Dashboards')
    parser.add_argument('--sourceDashboard', nargs=1, type=str, required=True,
                        help='Path to file with dashboard names(newline separated)')
    parser.add_argument('--sourceAccount', nargs=1, type=int, required=True, help='Source accountId')
    parser.add_argument('--sourceApiKey', nargs=1, type=str, required=True, help='Source account API Key or \
                                                                        set environment variable ENV_SOURCE_API_KEY')
    parser.add_argument('--targetStore', nargs=1, type=str,  required=True, help='Target Store')
    parser.add_argument('--sourceStore', nargs=1, type=str, required=True, help='Store name in Source')
    return parser

def dump_dashboard(per_api_key, name, acct_id, *, get_widgets=True, region='us'):
    result = ec.get_dashboard_definition(per_api_key, name, acct_id, region)
    if not result:
        return None
    if not get_widgets:
        return result
    widgets_result = ec.get_dashboard_widgets(per_api_key, result['guid'], region)
    if not widgets_result['entityFound']:
        return None
    return widgets_result['entity']


def update_store(src_store, tgt_store, entity):
    if 'guid' in entity:
        del entity['guid']

    if 'name' in entity:
        entity['name'] = entity['name'].replace(src_store,tgt_store)

    if not 'pages' in entity:
        return
    for page in entity['pages']:
        if not 'widgets' in page:
            continue
        for widget in page['widgets']:
            if not 'rawConfiguration' in widget:
                continue
            if not 'nrqlQueries' in widget['rawConfiguration']:
                continue
            for query in widget['rawConfiguration']['nrqlQueries']:
                if ('query' in query and query['query'].find(src_store) != -1):
                    query['query'] = query['query'].replace(src_store,tgt_store)



def main():
    
    parser = configure_parser()
    args = parser.parse_args()
    src_api_key = utils.ensure_source_api_key(args)
    src_dashboard = args.sourceDashboard[0]
    src_store = args.sourceStore[0]
    nrAccount = args.sourceAccount[0]
    tgt_store = args.targetStore[0]
    #tgt_api_key = utils.ensure_target_api_key(args)
    
    #src_region = utils.ensure_source_region(args)

    

    print_args(args)
    
    dbJson = dump_dashboard(src_api_key, src_dashboard, nrAccount)
    update_store(src_store,tgt_store, dbJson)
    log.info('db: ')
    log.info(dbJson)
    
    result = ec.post_dashboard(src_api_key, dbJson,  nrAccount, 'US')

    log.info(result)


if __name__ == '__main__':
    main()
