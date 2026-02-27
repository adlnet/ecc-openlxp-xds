//const crypto = require('crypto');
const crypto = require("./fakeCrypto");

function generateUUID() {
    return [4, 2, 2, 2, 6].map(size => 
        crypto.randomBytes(size).toString('hex')
    ).join('-');
}

function generateSessionId() {
    return crypto.randomBytes(16).toString('hex');
}

function generateJTI() {
    let randomNumber1 = Math.floor(Math.random() * Math.floor(254));
    let randomText = Math.random().toString(36).substr(2, 12);
    let randomNumber2 = Math.floor(Math.random() * Math.floor(81458));

    let jti = null;
    jti = (randomNumber1 + "-" + randomText + "-" + randomNumber2);
    return jti;
}
function generateHeader(){
    const header = {
        alg: 'HS256', // HMAC SHA-256 algorithim used
        typ: 'JWT',   // JWT token type
        kid: crypto.randomBytes(44).toString('hex'), // Key ID
    }
    return header;
}
function generatePayload(email, family_name, given_name){
    const payload = {
        exp: Math.floor(Date.now() / 1000) + 60 * 60, // Expiration time
        iat: Math.floor(Date.now() / 1000), // Issued at time
        auth_time: Math.floor(Date.now() / 1000) + 700, // Auth time
        jti: generateJTI(),
        iss: "https://login.dso.mil/auth/realms/baby-yoda",
        aud: "il4_191f836b-ec50-4819-ba10-1afaa5b99600_mission-window",
        sub: generateUUID(),
        azp: "il4_191f836b-ec50-4819-ba10-1afaa5b99600_mission-window",
        nonce: crypto.randomBytes(16).toString('base64'),
        session_state: generateSessionId(),
        acr: "1",
        email: email,
        last_name: family_name,
        first_name: given_name,
        preferred_username: email
    }
    return payload;
}

function generateJWT(header, payload) {

    // Base64Url encode the header and payload
    const encodedHeader = Buffer.from(JSON.stringify(header)).toString('base64').replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
    const encodedPayload = Buffer.from(JSON.stringify(payload)).toString('base64').replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');

    // Create the signature
    const sk = crypto.randomBytes(32).toString('hex');
    const signature = crypto.createHmac('sha256', sk).update(encodedHeader + '.' + encodedPayload).digest('base64').replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
    const jwt = encodedHeader + '.' + encodedPayload + '.' + signature;
    return jwt;
}

function generateTestPK(){
    const { privateKey: pik, publicKey: puk } = crypto.generateKeyPairSync('rsa', { modulusLength: 2048 });
    return { pik, puk };
}

function generateTestID(email){
    const header = generateHeader();
    const payload = generatePayload(email);
    const jwt = generateJWT(header, payload);
    return {jwt};

}

function generateJWTFromEmail(email, family_name, given_name, body_properties={}) {
    const header = generateHeader();
    const payload = generatePayload(email, family_name, given_name, body_properties);
    const jwt = generateJWT(header, payload);
    return {jwt};

}

module.exports = {
    generateJWT,
    generateJWTFromEmail,
    generateTestpk: generateTestPK,
    generateHeader: generateHeader,
    generatePayload: generatePayload,
    generateTestID: generateTestID
};
