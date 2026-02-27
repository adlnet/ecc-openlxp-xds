/**
 * Copilot-generated stub version of crypto for use in Cypress tests,
 * as Cypress 15+ no longer supports Node's crypto module directly.
 * 
 * This stub provides basic functionality needed for tests,
 * but does not implement full cryptographic security.
 */

// Write a function similar to crypto.randomBytes that returns a semi-random value for testing
function fakeRandomBytes(size) {
    // Create a buffer with a fixed pattern for testing purposes
    // Make the fill value random enough to avoid collisions in tests
    const fillValue = 'a'.charCodeAt(0) + Math.floor(Math.random() * 256);
    const buffer = Buffer.alloc(size, fillValue);
    return buffer;
}

// Write a similar function for createHmac that returns a fixed value for testing
function fakeCreateHmac(algorithm, key) {
    return {
        update: function(data) {
            // Do nothing with data, just return this for chaining
            return this;
        },
        digest: function(encoding) {
            // Return a fixed string for testing purposes
            const fixedString = 'fixed-hmac-signature';
            if (encoding === 'base64') {
                return Buffer.from(fixedString).toString('base64');
            } else if (encoding === 'hex') {
                return Buffer.from(fixedString).toString('hex');
            } else {
                return fixedString; // Default to raw string
            }
        }
    };
}

function fakeGenerateKeyPairSync() {
    // Use simple strings for testing that will not flag security tools
    return {
        publicKey: 'pk_test_1234567890abcdef',
        privateKey: 'sk_test_1234567890abcdef'
    };
}

module.exports = {
    randomBytes: fakeRandomBytes,
    createHmac: fakeCreateHmac,
    generateKeyPairSync: fakeGenerateKeyPairSync
};