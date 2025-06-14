# GitHub Secrets Setup Guide

Complete guide for configuring secure credential management for attest_ai CI/CD pipeline.

## Required GitHub Secrets

### 1. SecretVM Authentication

#### `SECRETVM_WALLET_ADDRESS`
**Description**: Your SecretVM wallet address for CLI authentication  
**Format**: Wallet address string  
**Example**: `secret1abc123def456...`  

**How to obtain**:
1. Get your Secret Network wallet address
2. Ensure wallet has sufficient SCRT for VM operations
3. Verify wallet can create and manage VMs

**Setting up**:
```bash
# Verify your wallet works with SecretVM CLI
secretvm-cli auth login -w YOUR_WALLET_ADDRESS
secretvm-cli auth status
```

---

### 2. Secret AI Integration

#### `SECRET_AI_API_KEY`
**Description**: Master API key for Secret AI SDK  
**Format**: Base64-encoded string  
**Example**: `bWFzdGVyQHNjcnRsYWJzLmNvbTpTZWNyZXROZXR3b3JrTWFzdGVyS2V5X18yMDI1`  

**How to obtain**:
1. Visit [Secret Network Developer Documentation](https://docs.scrt.network/)
2. Navigate to Secret AI SDK section
3. Generate master API key
4. Copy the base64-encoded key

**Validation**:
```bash
# Test key format (should be valid base64)
echo "YOUR_API_KEY" | base64 -d
```

---

### 3. Arweave Configuration

#### `ARWEAVE_WALLET_JWK`
**Description**: Arweave wallet in JSON Web Key (JWK) format  
**Format**: JSON string with JWK structure  
**Example**: 
```json
{
  "kty": "RSA",
  "e": "AQAB",
  "n": "your_n_value...",
  "d": "your_d_value...",
  "p": "your_p_value...",
  "q": "your_q_value...",
  "dp": "your_dp_value...",
  "dq": "your_dq_value...",
  "qi": "your_qi_value..."
}
```

**How to obtain**:
1. **Option A - Generate new wallet**:
   - Visit [https://arweave.app/wallet](https://arweave.app/wallet)
   - Generate new wallet
   - Download JWK file
   - Copy JSON content

2. **Option B - Export existing wallet**:
   - Use Arweave wallet tools to export JWK
   - Ensure format matches JWK specification

**Validation**:
```bash
# Test JWK format
echo 'YOUR_JWK_JSON' | jq '.'

# Check required fields
echo 'YOUR_JWK_JSON' | jq 'has("kty") and has("e") and has("n") and has("d")'
```

**Security Note**: 
- JWK contains private key material
- Never commit to version control
- Store only in GitHub Secrets

---

## GitHub Secrets Configuration

### Setting Up Secrets in GitHub

1. **Navigate to Repository Settings**:
   - Go to your GitHub repository
   - Click "Settings" tab
   - Select "Secrets and variables" → "Actions"

2. **Add Repository Secrets**:
   ```
   Name: SECRETVM_WALLET_ADDRESS
   Value: secret1abc123def456...
   
   Name: SECRET_AI_API_KEY  
   Value: bWFzdGVyQHNjcnRsYWJzLmNvbTpTZWNyZXROZXR3b3JrTWFzdGVyS2V5X18yMDI1
   
   Name: ARWEAVE_WALLET_JWK
   Value: {"kty":"RSA","e":"AQAB",...}
   ```

3. **Verify Secret Configuration**:
   - All three secrets should be listed
   - Check for typos in secret names
   - Ensure values are properly formatted

### Environment-Specific Secrets (Optional)

For staging/production environments:

#### Staging Environment
```
SECRETVM_WALLET_ADDRESS_STAGING
SECRET_AI_API_KEY_STAGING  
ARWEAVE_WALLET_JWK_STAGING
```

#### Production Environment
```
SECRETVM_WALLET_ADDRESS_PRODUCTION
SECRET_AI_API_KEY_PRODUCTION
ARWEAVE_WALLET_JWK_PRODUCTION
```

---

## Security Best Practices

### 1. Credential Management

#### Secret Rotation
- **Regular Rotation**: Rotate secrets every 90 days
- **Incident Response**: Rotate immediately if compromise suspected
- **Documentation**: Track rotation dates and procedures

#### Access Control
- **Least Privilege**: Only grant access to necessary team members
- **Environment Separation**: Use different credentials for staging/production
- **Audit Trail**: Monitor secret access and usage

### 2. GitHub Security Settings

#### Branch Protection
```yaml
# Recommended .github/branch-protection.yml
protection_rules:
  main:
    required_status_checks:
      - build-and-validate
    enforce_admins: true
    required_pull_request_reviews:
      required_approving_review_count: 1
    restrictions:
      users: []
      teams: []
```

#### Environment Protection
- **Production Environment**: Require manual approval for production deployments
- **Staging Environment**: Allow automatic deployments for testing
- **Review Requirements**: Require code review before secret access

### 3. Monitoring and Alerting

#### Secret Usage Monitoring
- Monitor GitHub Actions logs for secret access
- Set up alerts for failed authentication attempts
- Track deployment frequency and patterns

#### Security Incidents
```bash
# In case of suspected compromise:
1. Immediately rotate all affected secrets
2. Review GitHub Actions logs for unauthorized access
3. Check SecretVM for unauthorized VM creation
4. Verify Arweave wallet for unexpected transactions
5. Update team about security incident
```

---

## Validation and Testing

### 1. Secret Validation Script

Create a test workflow to validate secrets:

```yaml
# .github/workflows/validate-secrets.yml
name: Validate Secrets
on:
  workflow_dispatch:

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Validate SecretVM Authentication
        run: |
          if [[ -z "${{ secrets.SECRETVM_WALLET_ADDRESS }}" ]]; then
            echo "❌ SECRETVM_WALLET_ADDRESS not set"
            exit 1
          fi
          echo "✅ SECRETVM_WALLET_ADDRESS configured"
          
      - name: Validate Secret AI Key
        run: |
          if [[ -z "${{ secrets.SECRET_AI_API_KEY }}" ]]; then
            echo "❌ SECRET_AI_API_KEY not set"
            exit 1
          fi
          # Test base64 format
          if echo "${{ secrets.SECRET_AI_API_KEY }}" | base64 -d > /dev/null 2>&1; then
            echo "✅ SECRET_AI_API_KEY format valid"
          else
            echo "❌ SECRET_AI_API_KEY invalid base64 format"
            exit 1
          fi
          
      - name: Validate Arweave Wallet
        run: |
          if [[ -z "${{ secrets.ARWEAVE_WALLET_JWK }}" ]]; then
            echo "❌ ARWEAVE_WALLET_JWK not set"
            exit 1
          fi
          # Test JSON format
          if echo '${{ secrets.ARWEAVE_WALLET_JWK }}' | jq '.' > /dev/null; then
            echo "✅ ARWEAVE_WALLET_JWK JSON format valid"
          else
            echo "❌ ARWEAVE_WALLET_JWK invalid JSON format"
            exit 1
          fi
```

### 2. Local Testing

Test secret format locally before setting in GitHub:

```bash
# Test Secret AI API Key
echo "YOUR_SECRET_AI_KEY" | base64 -d

# Test Arweave JWK
echo 'YOUR_JWK_JSON' | jq '.kty, .e, .n, .d'

# Test SecretVM wallet format
echo "YOUR_WALLET_ADDRESS" | grep -E '^secret1[a-z0-9]{38}$'
```

---

## Troubleshooting

### Common Issues

#### 1. Invalid Secret AI API Key
**Symptoms**: Authentication errors in Secret AI client
**Solutions**:
- Verify key is valid base64
- Check key hasn't expired
- Regenerate key from Secret Network docs

#### 2. Malformed Arweave JWK
**Symptoms**: JSON parsing errors in Arweave client
**Solutions**:
- Validate JSON syntax: `echo 'JWK' | jq '.'`
- Check all required JWK fields present
- Re-export from wallet if needed

#### 3. SecretVM Authentication Failure
**Symptoms**: `secretvm-cli auth` commands fail
**Solutions**:
- Verify wallet address format
- Check wallet has sufficient SCRT balance
- Ensure wallet permissions for VM operations

### Debug Commands

```bash
# Check secret format in GitHub Actions
- name: Debug Secrets (Development Only)
  run: |
    echo "Wallet length: ${#SECRETVM_WALLET_ADDRESS}"
    echo "API key length: ${#SECRET_AI_API_KEY}"
    echo "JWK contains kty: $(echo "$ARWEAVE_WALLET_JWK" | jq 'has("kty")')"
  env:
    SECRETVM_WALLET_ADDRESS: ${{ secrets.SECRETVM_WALLET_ADDRESS }}
    SECRET_AI_API_KEY: ${{ secrets.SECRET_AI_API_KEY }}
    ARWEAVE_WALLET_JWK: ${{ secrets.ARWEAVE_WALLET_JWK }}
```

**Warning**: Never log actual secret values, only validate format/length.

---

## Compliance and Audit

### Documentation Requirements

1. **Secret Inventory**: Maintain list of all secrets and their purposes
2. **Access Log**: Track who has access to secrets and when
3. **Rotation Schedule**: Document when secrets were last rotated
4. **Incident Response**: Procedures for secret compromise

### Audit Checklist

- [ ] All required secrets configured in GitHub
- [ ] Secret format validation passes
- [ ] Environment-specific secrets separated
- [ ] Branch protection rules enabled
- [ ] Team access properly configured
- [ ] Rotation schedule documented
- [ ] Monitoring and alerting in place
- [ ] Incident response procedures ready

---

## Support and Resources

### Documentation Links
- [GitHub Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Secret Network Documentation](https://docs.scrt.network/)
- [Arweave Developer Docs](https://docs.arweave.org/)
- [SecretVM CLI Documentation](https://docs.scrt.network/secret-network-documentation/development/tools-and-libraries/secret-vm-cli)

### Quick Reference

```bash
# Verify all secrets are working
curl -H "Authorization: Bearer $SECRET_AI_API_KEY" <secret_ai_endpoint>
secretvm-cli auth login -w $SECRETVM_WALLET_ADDRESS
echo "$ARWEAVE_WALLET_JWK" | jq '.kty'
```

---

**Security Note**: This document contains guidance for handling sensitive credentials. Follow your organization's security policies and never expose actual secret values in documentation or logs.