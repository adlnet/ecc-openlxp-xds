// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************
//
//
// -- This is a parent command --
// Cypress.Commands.add('login', (email, password) => { ... })
//
//
// -- This is a child command --
// Cypress.Commands.add('drag', { prevSubject: 'element'}, (subject, options) => { ... })
//
//
// -- This is a dual command --
// Cypress.Commands.add('dismiss', { prevSubject: 'optional'}, (subject, options) => { ... })
//
//
// -- This will overwrite an existing command --
// Cypress.Commands.overwrite('visit', (originalFn, url, options) => { ... })

// reusable commands -> can be reused on different webpages

  //check tags on admin page
    Cypress.Commands.add('checkMetaTagsAdmin', () => {
    cy.get('head meta[name="robots"]').should('exist');
    cy.get('head meta[name="viewport"]').should('exist');
    cy.get('link[href="/static/admin/css/responsive.css"]').should('exist');
    cy.get('a[href="/admin/"]').should('exist');
    cy.contains('h1', 'Site administration').should('be.visible');
    cy.get('head link[rel="stylesheet"]').
    should('have.attr', 'href', '/static/admin/css/base.css');
    cy.get('div.app-admin_interface.module').find('a[href="/admin/admin_interface/"]').should('exist');
    cy.get('div.app-admin_interface.module').find('a[title="Models in the Admin Interface application"]').should('exist')
    cy.contains('Welcome, admin@example.com.').should('be.visible');
  });
  
// deny admin access without JWT
    Cypress.Commands.add('denyAdmin', () => {
    cy.visit('/admin');
    cy.get('#id_username').type(Cypress.env('adminUsername'));
    cy.get('#id_password').type(Cypress.env('adminPassword'));
    cy.contains('input', 'Log in').click();
    cy.get('p.errornote').should('be.visible');
  });

  //check staff access
   Cypress.Commands.add('checkMetaTagsStaff', () => {
    cy.get('head meta[name="robots"]').should('exist');
    cy.get('head meta[name="viewport"]').should('exist');
    cy.get('link[href="/static/admin/css/responsive.css"]').should('exist');
    cy.get('a[href="/admin/"]').should('exist');
    cy.contains('h1', 'Site administration').should('be.visible');
    cy.get('head link[rel="stylesheet"]').
    should('have.attr', 'href', '/static/admin/css/base.css');
    cy.contains('You don’t have permission to view or edit anything.').should('be.visible');
    cy.contains('Welcome, staff@example.com.').should('be.visible');
    cy.get('h3').next('p').should('have.text', 'None available');
  });

  //deny staff access without JWT
    Cypress.Commands.add('denyStaff', () => {
    cy.visit('/admin');
    cy.get('#id_username').type(Cypress.env('staffUsername'));
    cy.get('#id_password').type(Cypress.env('staffPassword'));
    cy.contains('input', 'Log in').click();
    cy.get('p.errornote').should('be.visible');
  });

// visit webpage with JWT
  Cypress.Commands.add('visitWithJWT', (url, jwtToken) => {
  cy.intercept('GET', '**/*', (req) => {
    req.headers['authorization'] = `Bearer ${jwtToken}`
  }).as('getRequest')
  cy.intercept('POST', '**/*', (req) => {
    req.headers['authorization'] = `Bearer ${jwtToken}`
  }).as('postRequest')
  cy.intercept('HEAD', '**/*', (req) => {
    req.headers['authorization'] = `Bearer ${jwtToken}`
  }).as('newHead')
  cy.intercept('DELETE', '**/*', (req) => {
    req.headers['authorization'] = `Bearer ${jwtToken}`
  }).as('delete')
  cy.intercept('PUT', '**/*', (req) => {
    req.headers['authorization'] = `Bearer ${jwtToken}`
  }).as('putRequest')
  return cy.visit({
    url: url,
     headers: {
      Authorization: `Bearer ${jwtToken}`
    },
    failOnStatusCode: false,
  })
});

//reduced to check regular GET request and 200 response
 Cypress.Commands.add('visitWithJWT2', (url, jwtToken) => {
  cy.request({
    method: 'GET',
    url: url,
    headers: {
      Authorization: `Bearer ${jwtToken}`
    }
  }).then((response) => {
    expect(response.status).to.eq(200);
      // Assuming your API returns the token in response.body.token
    //const jwtToken = response.body.token;
    cy.log(response.body)
    //cy.log(jwtToken)
  });
  
  // After setting the token, visit the main page.
  // The app should now be authenticated.
  cy.visit('/admin'); 
});
