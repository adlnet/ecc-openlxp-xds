// staff user must be created on the application side, STAFF_FLAG must be group-full in settings.py
// staff user Bob Staff, email staff@example.com
// more about user properties can be seen in local.config.js
// staff should log in with valid credentials and display
//REQUIRE_JWT can also be turned on or off in settings.py
 
describe('Login functionality for Staff User', () => {

   it('Successfully Logs in with valid Staff JWT', () => {
    cy.wait(2000)
    //loading staffJWT to be used
    const jwt = Cypress.env('staffJWT')
    //check staffJWT gets created
    if (!jwt) {
      throw new Error('JWT is missing in CI environment')
    }
    //cy.log(jwt);
    cy.visitWithJWT("/admin", jwt);
    cy.wait(2000);
    cy.reload();
    // should be logged in as staff now
    //checkstaff tags
    cy.get('title').contains('Site administration | XDS Configuration Portal');
    cy.checkMetaTagsStaff();
  });

   it('Should not log in Staff without JWT', () => {
    cy.denyStaff();
    cy.contains('Please enter the correct email and password for a staff account. Note that both fields may be case-sensitive.').should('be.visible');
    });
});