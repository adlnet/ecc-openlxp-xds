function generatetestJWT(username, email, firstName, lastName) {

    const crypto = require('crypto')
    
    const header = {
        alg: 'HS256', // HMAC SHA-256 algorithim used
        typ: 'JWT',   // JWT token type
    }
    
    const payload = {
        "exp": 1613756062,
        "iat": 1613755162,
        "auth_time": 1613755162,
        "jti": "abcd1234-ab12-cd34-ef56-abcdef123456",
        "iss": 'https://login.dso.mil/auth/realms/baby-yoda',
        "aud": "client_id_here",
        "sub": "abcd1234-ab12-cd34-ef56-abcdef123456",
        "typ": "ID",
        "azp": "client_id_here",
        "session_state": "abcd1234-ab12-cd34-ef56-abcdef123456",
        "at_hash": "0ff7a609-55f9-4d6e-844c-9c120d7b3a9d",
        "acr": "1",
        "email_verified": true,
        "group-simple": [
          "ADMIN",
          "USER",
          "ADMIN",
          "USER_STAFF",
          "USER_SUPERUSER",
          "Impact Level 2 Authorized",
          "Impact Level 4 Authorized",
          "Impact Level 5 Authorized"
        ],
        "preferred_username": username,
        "given_name": firstName,
        "family_name": lastName,
        "activecac": "DOE.JOHN.P.1234567890",
        "affiliation": "Contractor",
        "group-full": [
          "/Platform One/Products/Example1/IL2/roles/ADMIN",
          "/Platform One/Products/Example1/IL4/roles/USER",
          "/Platform One/Products/Example2/IL4/roles/ADMIN",
          "/Platform One/Products/adl-ousd/LDSS/IL2/roles/USER_STAFF",
          "/Platform One/Products/adl-ousd/LDSS/IL2/roles/USER_SUPERUSER",
          "/Impact Level 2 Authorized",
          "/Impact Level 4 Authorized",
          "/Impact Level 5 Authorized"
        ],
        "organization": "Example Company LLC",
        "name": firstName +" User",
        "usercertificate": "DOE.JOHN.P.1234567890",
        "rank": "N/A",
        "family_name": "User",
        "email": email
    }
    
    // Base64Url encode the header and payload
    const encodedHeader = Buffer.from(JSON.stringify(header)).toString('base64').replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_')
    const encodedPayload = Buffer.from(JSON.stringify(payload)).toString('base64').replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_')
    
    // Create the signature
    const secretkey = crypto.randomBytes(256).toString('base64')
    
    const signature = crypto.createHmac('sha256', secretkey).update(encodedHeader + '.' + encodedPayload).digest('base64').replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_')
    const jwt = encodedHeader + '.' + encodedPayload + '.' + signature
    return jwt
}

function generateBadJWT() {
    const crypto = require('crypto')
    
    const header = {
        alg: 'HS256', // HMAC SHA-256 algorithim used
        typ: 'JWT',   // JWT token type
    }
    
    const now = Math.floor(Date.now() / 1000);
    const payload = {
        "exp": now + 3600,
        "iat": now,
        "auth_time": 1613755162,
        "iss": 'https://login.dso.mil/auth/realms/baby-yoda',
        "aud": "client_id_here",
        "sub": "unauthorized-user-id",
        "preferred_username": "unauthorized-user",
        "group-full": [
          "/Unauthorized/Product/IL2/roles/NONE",
          "/Completely/Fake/Role"
        ],
        "email": "unauthorized@example.com"
    }
    
    // Base64Url encode the header and payload
    const encodedHeader = Buffer.from(JSON.stringify(header)).toString('base64').replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_')
    const encodedPayload = Buffer.from(JSON.stringify(payload)).toString('base64').replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_')
    
    // Create the signature
    var secretkey = crypto.randomBytes(256).toString('base64')
    
    const signature = crypto.createHmac('sha256', secretkey).update(encodedHeader + '.' + encodedPayload).digest('base64').replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_')
    const jwt = encodedHeader + '.' + encodedPayload + '.' + signature
    return jwt
}
    
    module.exports = {
        generatetestJWT,
        generateBadJWT
    }
