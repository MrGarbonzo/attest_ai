#!/usr/bin/env node

import { Command } from "commander";
import {
    loginCommand,
    logoutCommand,
    statusCommand,
    listVmsCommand,
    createVmCommand,
    vmLogsCommand,
    vmAttestationCommand,
    stopVmCommand,
    startVmCommand,
    removeVmCommand,
    vmStatusCommand,
} from "./commands";
import { GlobalOptions } from "./types";

async function main() {
    const program = new Command();

    program
        .name("secretvm-cli")
        .description("CLI tool for SecretAI devportal")
        .version("0.1.0")
        .option(
            "-i, --interactive",
            "Enable interactive mode with prompts and human-readable output",
            false,
        );

    const authCommands = new Command("auth").description("Auth commands");
    authCommands
        .command("login")
        .description("Login to the service using web browser")
        .action(async () => {
            await loginCommand(program.opts() as GlobalOptions);
        });
    authCommands
        .command("logout")
        .description("Logout from the service and clear session")
        .action(async () => {
            await logoutCommand(program.opts() as GlobalOptions);
        });
    program.addCommand(authCommands);

    program
        .command("status")
        .description("Check current login status")
        .action(async () => {
            await statusCommand(program.opts() as GlobalOptions);
        });

    const vmCommands = new Command("vm").description("VM commands");
    vmCommands
        .command("list")
        .alias("ls")
        .description("List all virtual machine instances")
        .action(async () => {
            await listVmsCommand(program.opts() as GlobalOptions);
        });
    vmCommands
        .command("create")
        .description("Create new virtual machine")
        .option("-n, --name <vmName>", "VM name")
        .option("-t, --type <vmType>", "VM type (small, medium, large)")
        .option(
            "-d, --docker-compose <dockerComposePath>",
            "Path to docker-compose.yaml",
        )
        .option("-s, --tls", "Enable HTTPS with TLS")
        .option("-c, --invite-code <inviteCode>", "Invite code (optional)")
        .action(async (cmdOptions) => {
            await createVmCommand(cmdOptions, program.opts() as GlobalOptions);
        });
    vmCommands
        .command("stop")
        .argument("<vmId>")
        .description("Stop virtual machine")
        .action(async (vmId: string) => {
            await stopVmCommand(vmId, program.opts() as GlobalOptions);
        });
    vmCommands
        .command("start")
        .argument("<vmId>")
        .description("Start virtual machine")
        .action(async (vmId: string) => {
            await startVmCommand(vmId, program.opts() as GlobalOptions);
        });
    vmCommands
        .command("remove")
        .argument("<vmId>")
        .description("Remove virtual machine")
        .action(async (vmId: string) => {
            await removeVmCommand(vmId, program.opts() as GlobalOptions);
        });
    vmCommands
        .command("logs")
        .description("View logs of the specified virtual machine")
        .argument("<vmId>")
        .action(async (vmId: string) => {
            await vmLogsCommand(vmId, program.opts() as GlobalOptions);
        });
    vmCommands
        .command("attestation")
        .description("View CPU attestation of the specified virtual machine")
        .argument("<vmId>")
        .action(async (vmId: string) => {
            await vmAttestationCommand(vmId, program.opts() as GlobalOptions);
        });
    vmCommands
        .command("status")
        .description("View virtual machine status")
        .argument("<vmUUID>")
        .action(async (vmId: string) => {
            await vmStatusCommand(vmId, program.opts() as GlobalOptions);
        });
    program.addCommand(vmCommands);

    await program.parseAsync(process.argv);
}

main().catch((err) => {
    console.error("Unhandled error in main execution:", err);
    process.exit(1);
});
