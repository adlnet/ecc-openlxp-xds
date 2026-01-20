//Login for local development environment

export function localLogin(username, password) {
    cy.visit('/admin');

    cy.wait(200);
    // cy.get('input[name="username"]').clear();
    // cy.wait(200);
    // cy.get('input[name="password"]').clear();
    // cy.wait(200);

    cy.get('input[name="username"]').type(username);
    cy.get('input[name="password"]').type(password);

    return cy.contains('Log in').click();
    // cy.url().should('include', '/admin');
}
