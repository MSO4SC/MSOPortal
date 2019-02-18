import requests
import urllib
from urlparse import urlparse

from bson import ObjectId
from pymongo import MongoClient


CATALOG = 'http://apis.docker:8080/DSProductCatalog/api/catalogManagement/v2/productOffering'
PRODUCTS = 'http://apis.docker:8080/DSProductCatalog/api/catalogManagement/v2/productSpecification'
ORDERING = 'http://apis.docker:8080/DSProductOrdering/api/productOrdering/v2/productOrder'
PARTY = 'http://apis.docker:8080/DSPartyManagement/api/partyManagement/v2/individual'

MONGO = 'mongo'
DATABASE = 'wstore_db'

processed_offerings = []
bundles = []
db = None


def create_organization(owner_href):
    # Get parties
    site = urlparse(PARTY)
    p = urlparse(owner_href)

    party_url = '{}://{}{}'.format(site.scheme, site.netloc, p.path)
    party = requests.get(party_url).json()

    # Create userprofile object
    organization = {
        "managers" : [],
	    "name" : party['id'],
	    "correlation_number" : 0,
	    "notification_url" : None,
	    "private" : True,
	    "tax_address" : {},
	    "expenditure_limits" : {},
	    "actor_id" : None,
        "acquired_offerings" : []
 
    }

    # Create organization object
    return db.wstore_organization.save(organization)


def get_product_owner_obj(product):
    owner_id = None
    owner_href = None
    for party in product['relatedParty']:
        if party['role'].lower() == 'owner':
            owner_id = party['id']
            owner_href = party['href']
            break

    owner_obj = db.wstore_organization.find_one({
        'name': owner_id
    })

    owner_obj_id = None
    if owner_obj is None:
        owner_obj_id = create_organization(owner_href)
    else:
        owner_obj_id = owner_obj['_id']

    return owner_obj_id


def get_product_owner(product_href):
    site = urlparse(CATALOG)
    prod = urlparse(product_href)

    product_url = '{}://{}{}'.format(site.scheme, site.netloc, prod.path)
    product = requests.get(product_url).json()
    return get_product_owner_obj(product)


def save_offering(offering, internal_id=None):

    assets = db.wstore_resource.find({
        'product_id': offering['productSpecification']['id']
    })

    asset = None
    owner = None
    if assets.count() > 0:
        asset = assets[0]['_id']
        owner = assets[0]['provider_id']
    else:
        # Owner must be retrieved from product specification
        owner = get_product_owner(offering['productSpecification']['href'])

    is_digital = asset is not None

    description = ''
    if 'description' in offering:
        description = offering['description']

    offering_object = {
        'off_id': offering['id'],
        'href': offering['href'],
        'owner_organization_id': owner,
        'name': offering['name'],
        'version': offering['version'],
        'description': description,
        'is_digital': is_digital,
        'asset_id': asset,
        'bundled_offerings': []
    }

    # When the offering to be restored in the database is used in an order,
    # the internal id must be the same it had
    if internal_id is not None:
        offering_object['_id'] = internal_id

    db.ordering_offering.save(offering_object)


def process_orders():
    orders = db.wstore_order.find()
    for order_obj in orders:
        if len(order_obj['contracts']) > 0:
            order_resp = requests.get(ORDERING + '/' + order_obj['order_id'])
            api_order = order_resp.json()

            # Each contract is created using a particular offering
            i = 0
            while i < len(api_order['orderItem']):
                site = urlparse(CATALOG)
                off = urlparse(api_order['orderItem'][i]['productOffering']['href'])

                offering_url = '{}://{}{}'.format(site.scheme, site.netloc, off.path)
                offering = requests.get(offering_url).json()

                if offering['id'] not in processed_offerings:
                    internal_id = order_obj['contracts'][i]['offering_id']
                    if not is_bundle(offering):
                        save_offering(offering, internal_id)
                        processed_offerings.append(offering['id'])

                    else:
                        bundles.append((offering, internal_id))
                i += 1


def save_bundle(bundle):
    # Check if the bundle is digital
    bundle_offering = bundle[0]
    bundled_offerings = []

    for bundled in bundle_offering['bundledProductOffering']:
        bundled_offerings.append(db.ordering_offering.find_one({
            'off_id': bundled['id']
        }))

    digital = len([offering for offering in bundled_offerings if offering['is_digital']])
    is_digital = digital > 0

    owner = None
    if is_digital:
        asset = db.wstore_resource.find_one({
            '_id': bundled_offerings[0]['asset_id']
        })
        owner = asset['provider_id']
    else:
        raw_bundled = requests.get(CATALOG + '/' + bundled_offerings[0]['off_id']).json()
        owner = get_product_owner(raw_bundled['productSpecification']['href'])

    bundle_ids = [unicode(offering['_id']) for offering in bundled_offerings]

    description = ''
    if 'description' in bundle_offering:
        description = bundle_offering['description']

    offering_object = {
        'off_id': bundle_offering['id'],
        'href': bundle_offering['href'],
        'owner_organization_id': owner,
        'name': bundle_offering['name'],
        'version': bundle_offering['version'],
        'description': description,
        'is_digital': is_digital,
        'asset_id': None,
        'bundled_offerings': bundle_ids
    }

    # When the offering to be restored in the database is used in an order,
    # the internal id must be the same it had
    if bundle[1] is not None:
        offering_object['_id'] = bundle[1]

    db.ordering_offering.save(offering_object)


def is_bundle(offering):
    return 'isBundle' in offering and offering['isBundle'] == True


def load_offerings():

    process_orders()

    # Get offerings from catalog API
    response = requests.get(CATALOG)
    response.raise_for_status()

    for offering in response.json():
        if offering['id'] not in processed_offerings:
            if not is_bundle(offering):
                save_offering(offering)
            else:
                # Bundles cannot be processes until all single offerings are saved
                bundles.append((offering, None))

    for bundle in bundles:
        save_bundle(bundle)


def _get_characteristic_value(characteristic):
    return characteristic['productSpecCharacteristicValue'][0]['value']


def parse_characteristics(product_spec):
        expected_chars = {
            'asset type': [],
            'media type': [],
            'location': []
        }

        asset_type = None
        media_type = None
        location = None
        has_terms = False

        if 'productSpecCharacteristic' in product_spec:
            terms = []

            # Extract the needed characteristics for processing digital assets
            is_digital = False
            for char in product_spec['productSpecCharacteristic']:
                if char['name'].lower() in expected_chars:
                    is_digital = True
                    expected_chars[char['name'].lower()].append(_get_characteristic_value(char))

                if char['name'].lower() == 'license':
                    terms.append(_get_characteristic_value(char))

            has_terms = len(terms) > 0

            if is_digital:
                asset_type = expected_chars['asset type'][0]
                media_type = expected_chars['media type'][0]
                location = expected_chars['location'][0]

        return asset_type, media_type, location, has_terms


def load_assets():
    # Save basic service asset
    plugins = db.wstore_resourceplugin.find()
    if plugins.count() == 0:
        db.wstore_resourceplugin.save({
             "media_types" : [],
             "name" : "Basic Service",
             "form" : {},
             "author" : "fdelavega",
             "overrides" : [],
             "pull_accounting" : False,
             "module" : "wstore.asset_manager.resource_plugins.plugins.basic-service.basic_url.BasicPlugin",
             "version" : "1.0",
             "formats" : [ "URL" ],
             "plugin_id" : "basic-service",
             "options" : {}
        })

    # Get products
    products = requests.get(PRODUCTS).json()

    for product in products:
        owner = get_product_owner_obj(product)
        # Build asset object if the product is digital
        asset_type, media_type, location, has_terms = parse_characteristics(product)

        if asset_type is not None:
            asset = {
                "provider_id" : owner,
	            "meta_info" : {},
	            "content_type" : media_type,
	            "resource_path" : "",
	            "bundled_assets" : [ ],
	            "old_versions" : [ ],
	            "has_terms" : has_terms,
	            "state" : "attached",
	            "version" : "0.1",
	            "download_link" : location,
	            "is_public" : False,
	            "resource_type" : asset_type,
	            "product_id" : product['id']
            }
            db.wstore_resource.save(asset)


if __name__ == "__main__":
    import ipdb; ipdb.set_trace()
    global db
    # Initialize databse connection
    client = MongoClient(MONGO)
    db = client[DATABASE]
    #load_organizations()
    load_assets()
    load_offerings()
