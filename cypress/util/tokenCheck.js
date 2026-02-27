const tokenGenerator = require('./tokenGeneration.js');


let header = tokenGenerator.generateheader();
let payload = tokenGenerator.generatepayload();

console.log(header);
console.log(payload);

let keypair = tokenGenerator.generatetestpk();

console.log(keypair);

let jwt = tokenGenerator.generateJWT(header, payload, keypair.pik);

console.log(jwt);

let sigsheet = tokenGenerator.generatecasssigsheet(payload, keypair.puk, keypair.pik);

console.log(sigsheet);

console.log(tokenGenerator.generatetestID());