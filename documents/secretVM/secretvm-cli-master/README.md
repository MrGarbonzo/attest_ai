# SecretAI devportal CLI tool

A command-line interface to manage Secret Virtual Machines (SecretVMs) and interact with SecretAI devportal.

## Prerequisites

- Node.js: Version 16.x or higher.
- npm or yarn.

## Installation

1. Clone the Repository
```bash
git clone https://github.com/scrtlabs/secretvm-cli.git
cd secretvm-cli
```

2. Install Dependencies
```bash
npm install
# or
yarn install
```

3. Build the Project
```bash
npm run build
```
This will create a `/dist` directory with the compiled code.

4. Make the CLI Globally Available (Optional)
To use the CLI command from anywhere on your system, you can link it:
```
npm link
```
This will make the command `secretvm-cli` available globally. Alternatively, you can run it directly using `node dist/cli.js`
