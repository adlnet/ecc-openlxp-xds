const { defineConfig } = require('cypress')

const adminProperties = {
  "group-full": [
    "/Platform One/Products/adl-ousd/LDSS/IL2/roles/USER_SUPERUSER"
  ]
}

const testtoken = require("../util/tokenGeneration");
const dummyAdminJWT = testtoken.generateJWTFromEmail("admin@dummy.mil", adminProperties).jwt;

module.exports = defineConfig({

  e2e: {
    setupNodeEvents(on, config) {
      config.defaultCommandTimeout = 10000;
      config.baseUrl = "http://localhost:8000";

      config.hideXHRInCommandLog = true;

      return config
    },
    env: {
      jwt: dummyAdminJWT, 
    }
  },
});

