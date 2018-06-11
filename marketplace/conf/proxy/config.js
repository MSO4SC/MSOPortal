var config = {};

// Version of the software
config.version = {
    version: '6.4.0',
    releaseDate: '',
    gitHash: '',
    doc: 'https://fiware-tmforum.github.io/Business-API-Ecosystem/',
    userDoc: 'http://business-api-ecosystem.readthedocs.io/en/develop'
};

// The PORT used by
config.port = 80;
config.host = 'proxy.docker';

var biz_host = (process.env.BIZ_HOST) ? process.env.BIZ_HOST : 'proxy.docker'

config.proxy = {
    enabled: true,
    host: biz_host,
    secured: false,
    port: 80
};

// Set this var to undefined if you don't want the server to listen on HTTPS
config.https = {
    enabled: false,
    certFile: 'cert/cert.crt',
    keyFile: 'cert/key.key',
    caFile: 'cert/ca.crt',
    port: 443
};

// Express configuration
config.proxyPrefix = '';
config.portalPrefix = '';
config.logInPath = '/login';
config.logOutPath = '/logOut';
config.sessionSecret = 'keyboard cat';
config.theme = '';

var idm_entrypoint = (process.env.IDM_ENTRYPOINT) ? process.env.IDM_ENTRYPOINT : 'http://idm.docker:3000'
var idm_biz_id = (process.env.IDM_BIZ_ID) ? process.env.IDM_BIZ_ID : ''
var idm_biz_secret = (process.env.IDM_BIZ_SECRET) ? process.env.IDM_BIZ_SECRET : ''

// OAuth2 configuration
config.oauth2 = {
    'server': idm_entrypoint,
    'clientID': idm_biz_id,
    'clientSecret': idm_biz_secret,
    'callbackURL': 'http://'+biz_host+':8004/auth/fiware/callback',
    'roles': {
        'admin': 'provider',
        'customer': 'customer',
        'seller': 'seller',
        'orgAdmin': 'orgAdmin'
    }
};

// Customer Role Required to buy items
config.customerRoleRequired = false;

// MongoDB
config.mongoDb = {
    server: 'mongo',
    port: 27017,
    user: '',
    password: '',
    db: 'belp'
};

// Configure endpoints
config.endpoints = {
    'management': {
        'path': 'management',
        'host': 'localhost',
        'port': config.port,
        'appSsl': config.https.enabled
    },
    'catalog': {
        'path': 'DSProductCatalog',
        'host': 'apis.docker',
        'port': '8080',
        'appSsl': false
    },
    'ordering': {
        'path': 'DSProductOrdering',
        'host': 'apis.docker',
        'port': '8080',
        'appSsl': false
    },
    'inventory': {
        'path': 'DSProductInventory',
        'host': 'apis.docker',
        'port': '8080',
        'appSsl': false
    },
    'charging': {
        'path': 'charging',
        'host': 'charging.docker',
        'port': '8006',
        'appSsl': false
    },
    'rss': {
        'path': 'DSRevenueSharing',
        'host': 'rss.docker',
        'port': '8080',
        'appSsl': false
    },
    'party': {
        'path': 'DSPartyManagement',
        'host': 'apis.docker',
        'port': '8080',
        'appSsl': false
    },
    'billing':{
        'path': 'DSBillingManagement',
        'host': 'apis.docker',
        'port': '8080',
        'appSsl': false
    },
    'customer': {
        'path': 'DSCustomerManagement',
        'host': 'apis.docker',
        'port': '8080',
        'appSsl': false
    },
    'usage':  {
        'path': 'DSUsageManagement',
        'host': 'apis.docker',
        'port': '8080',
        'appSsl': false
    }
};

// Percentage of the generated revenues that belongs to the system
config.revenueModel = 30;

// Tax rate
config.taxRate = 20;

// Billing Account owner role
config.billingAccountOwnerRole = 'bill receiver';

// list of paths that will not check authentication/authorization
// example: ['/public/*', '/static/css/']
config.publicPaths = [];

config.magicKey = undefined;

config.usageChartURL = 'https://mashup.lab.fiware.org/fdelavega/UsageChart?mode=embedded&theme=wirecloud.fiwarelabtheme';

module.exports = config;
