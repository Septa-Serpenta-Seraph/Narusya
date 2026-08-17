#!/usr/bin/env node
// BountyBook auth helper — signs a nonce with the daemon's wallet key.
// Reads the key from the secrets file; NEVER prints the key itself.
// Usage: node sign_nonce.js <nonce>
// Output: the signature hex on stdout.
const { ethers } = require('ethers');
const fs = require('fs');
const path = require('path');

const nonce = process.argv[2];
if (!nonce) {
  console.error('Usage: node sign_nonce.js <nonce>');
  process.exit(1);
}

const secretFile = path.join(process.env.HOME, '.hermes/secrets/sunburst_wallet.txt');
if (!fs.existsSync(secretFile)) {
  console.error('ERROR: secrets file not found');
  process.exit(1);
}

const content = fs.readFileSync(secretFile, 'utf8');
const keyLine = content.split('\n').find(l => l.startsWith('key: '));
if (!keyLine) {
  console.error('ERROR: key not found in secrets file');
  process.exit(1);
}
const key = keyLine.replace('key: ', '').trim();
const wallet = new ethers.Wallet(key);

wallet.signMessage(nonce).then(sig => {
  console.log(sig);
}).catch(e => {
  console.error('ERROR signing:', e.message);
  process.exit(1);
});
