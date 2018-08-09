var config = {};

var idm_host = (process.env.IDM_HOST) ? process.env.IDM_HOST : 'localhost'
var idm_port = (process.env.IDM_PORT) ? process.env.IDM_PORT : 'localhost'

config.host = 'http://'+ idm_host +':' + idm_port;
config.port = idm_port

var idm_https = (process.env.IDM_HTTPS == 'true' || process.env.IDM_HTTPS == 'True' || process.env.IDM_HTTPS == 'TRUE') ? true : false

// HTTPS enable
config.https = {
    enabled: idm_https,
    cert_file: '/certs/fullchain.pem',
    key_file: '/certs/privkey.pem',
    port: 443
};

// Config email list type to use domain filtering
config.email_list_type = null   // whitelist or blacklist

// Secret for user sessions in web
config.session = {
    secret: 'mso4sc_idm',       // Must be changed
    expires: 60 * 60 * 1000     // 1 hour
}

// Key to encrypt user passwords
config.password_encryption = {
        key: 'mso4sc_idm'       // Must be changed
}

// Config oauth2 parameters
config.oauth2 = {
    authorization_code_lifetime: 5 * 60,            // Five minutes
    access_token_lifetime: 60 * 60,                 // One hour
    refresh_token_lifetime: 60 * 60 * 24 * 14       // Two weeks
}

// Config api parameters
config.api = {
    token_lifetime: 60 * 60     // One hour
}

// Enable authzforce
config.authzforce = {
        enabled: false,
        host: '',
        port: 8080
}

var database_host = (process.env.DATABASE_HOST) ? process.env.DATABASE_HOST : 'localhost'
var mysql_root_pass = (process.env.MYSQL_ROOT_PASSWORD) ? process.env.MYSQL_ROOT_PASSWORD: 'idm'

// Database info
config.database = {
    host: database_host,         // default: 'localhost'
    password: mysql_root_pass,   // default: 'idm'
    username: 'root',            // default: 'root'
    database: 'idm',             // default: 'idm'
    dialect: 'mysql'             // default: 'mysql'
};

// External user authentication
config.external_auth = {
    enabled: false,
    authentication_driver: 'custom_authentication_driver',
    database: {
        host: 'localhost',
        database: 'db_name',
        username: 'db_user',
        password: 'db_pass',
        user_table: 'user',
        dialect: 'mysql'
    }
}

var smtp_host = (process.env.SMTP_HOST) ? process.env.SMTP_HOST: 'localhost'
var smtp_port = (process.env.SMTP_PORT) ? parseInt(process.env.SMTP_PORT): 25
var smtp_secure = (process.env.SMTP_SECURE) ? (process.env.SMTP_SECURE == 'true'): false
var smtp_user = (process.env.SMTP_USER) ? process.env.SMTP_USER: ''
var smtp_pass = (process.env.SMTP_PASS) ? process.env.SMTP_PASS: ''
var smtp_from = (process.env.SMTP_FROM) ? process.env.SMTP_FROM: ''

// Email configuration
config.mail = {
    host: smtp_host,
    port: smtp_port,
    secure: smtp_secure,
    from: smtp_from,
    auth: {
        user: smtp_user,
        pass: smtp_pass
    }
}


// Config themes
config.site = {
    title: 'Identity Manager',
    theme: 'default'
};

module.exports = config;
