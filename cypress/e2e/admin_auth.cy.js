// super user must be created on the application side, SU_FLAG must be group-full in settings.py
// super user Dummy Admin, email admin@example.com
// more details of the user and permissions can be seen in local.config.js
//REQUIRE_JWT can also be turned on or off in settings.py

describe('Login Functionality for SuperUser', () => {

  // Test for standard encoding format for all HTML content https://sdelements.il2.dso.mil/bunits/platform1/ecc/openlxp-xds/tasks/phase/testing/395-T132/
   it('Successfully Logs in with valid SuperUser JWT', () => {
    cy.wait(2000)
    //loading adminJWT to be used
    const jwt = Cypress.env('adminJWT')
    //check adminJWT gets created
    if (!jwt) {
      throw new Error('JWT is missing in CI environment')
    }
      //cy.log(jwt);
    cy.visitWithJWT("/admin", jwt);
    cy.wait(2000);
    cy.reload();

    cy.get('title').contains('Site administration | XDS Configuration Portal');
     // Assertions for successful login, title and username
    cy.checkMetaTagsAdmin();
  });

  // admin should log in with valid credentials and display 
  it('Should not log in SuperUser without JWT', () => {
    cy.denyAdmin();
    cy.contains('Please enter the correct email and password for a staff account. Note that both fields may be case-sensitive.').should('be.visible');
    });
  });
