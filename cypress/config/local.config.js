const { defineConfig } = require('cypress');

const tokengeneration = require('../util/tokenGeneration.js');

//admin properties defined here
const adminProperties = {
  "group-full": [
      "/Platform One/Products/Example1/IL2/roles/ADMIN",
      "/Platform One/Products/adl-ousd/ecc/IL2/roles/USER_STAFF",
      "/Platform One/Products/adl-ousd/ecc/IL2/roles/USER_SUPERUSER",
      "/Impact Level 2 Authorized"
  ]
}
//staff properties defined here
const staffProperties = {
  "group-full": [
      "/Platform One/Products/adl-ousd/ecc/IL2/roles/USER_STAFF",
      "/Impact Level 2 Authorized"
  ]
}

// admin token created based on admin properties
// add given name and family name
const dummyAdminJWT = tokengeneration.generateJWTFromEmail("admin@example.com","Admin", "Dummy", adminProperties).jwt;
const dummyStaffJWT = tokengeneration.generateJWTFromEmail("staff@example.com","Staff", "Bob", staffProperties).jwt;

module.exports = defineConfig({
  e2e: {
    specPattern: [
      "cypress/e2e/*.cy.{js,jsx,ts,tsx}", 
      // "cypress/e2e/uitesting/framework.cy.{js,jsx,ts,tsx}", 
      //'cypress/e2e/sdelement/t85.cy.{js,jsx,ts,tsx}'
    ],
    baseUrl: 'http://localhost:8100',
    experimentalStudio: true,
    hideXHRInCommandLog: true
  },
  env: {
    adminJWT: dummyAdminJWT,
    staffJWT: dummyStaffJWT,
  },
  defaultCommandTimeout: 9000,
});


