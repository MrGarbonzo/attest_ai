import inquirer from "inquirer";
import FormData from "form-data";
import fs from "fs";
import path from "path";
import { getApiClient } from "../../services/apiClient";
import {
    CreateVmApiResponse,
    GlobalOptions,
    CreateVmCommandOptions,
    DockerCompose,
} from "../../types";
import { handleCommandExecution, successResponse } from "../../utils";
import Table from "cli-table3";
import { API_ENDPOINTS } from "../../constants";
import { AxiosResponse } from "axios";
import yaml from "js-yaml";

export async function createVmCommand(
    cmdOptions: CreateVmCommandOptions,
    globalOptions: GlobalOptions,
): Promise<void> {
    let name = cmdOptions.name;
    let type = cmdOptions.type;
    let dockerComposePath = cmdOptions.dockerCompose;
    let inviteCode = cmdOptions.inviteCode;
    let enableHttps = cmdOptions.tls ?? false;

    await handleCommandExecution(
        globalOptions,
        async (): Promise<AxiosResponse> => {
            if (globalOptions.interactive) {
                if (!name) {
                    const answers = await inquirer.prompt([
                        {
                            type: "input",
                            name: "name",
                            message: "Enter a name for your VM:",
                            validate: (input: string) =>
                                input.trim() !== "" ||
                                "VM name cannot be empty.",
                        },
                    ]);
                    name = answers.name;
                }
                if (!type) {
                    const answers = await inquirer.prompt([
                        {
                            type: "input",
                            name: "vmTypeId",
                            message:
                                "Enter the VM Type ID (small, medium, large):",
                            validate: (input: string) =>
                                input.trim() !== "" ||
                                "VM Type ID cannot be empty.",
                        },
                    ]);
                    type = answers.vmTypeId;
                }
                if (!dockerComposePath) {
                    const answers = await inquirer.prompt([
                        {
                            type: "input",
                            name: "dockerComposePath",
                            message:
                                "Enter the path to your docker-compose.yml or similar config file:",
                            validate: (input: string) => {
                                const trimmedInput = input.trim();
                                if (trimmedInput === "")
                                    return "Path cannot be empty.";
                                try {
                                    // Check if path is absolute or resolve it
                                    const resolvedPath =
                                        path.resolve(trimmedInput);
                                    fs.accessSync(
                                        resolvedPath,
                                        fs.constants.R_OK,
                                    );
                                    return true;
                                } catch (err) {
                                    return `File "${trimmedInput}" does not exist or is not readable.`;
                                }
                            },
                        },
                    ]);
                    dockerComposePath = answers.dockerComposePath;
                }
                if (!inviteCode) {
                    const answers = await inquirer.prompt([
                        {
                            type: "input",
                            name: "inviteCode",
                            message:
                                "Enter invite code (optional, press Enter if not needed):",
                        },
                    ]);
                    inviteCode = answers.inviteCode;
                }
                if (!enableHttps) {
                    const answers = await inquirer.prompt([
                        {
                            type: "input",
                            name: "https",
                            message: "Enable HTTPS with TLS? (y/N)",
                        },
                    ]);
                    enableHttps = answers.https.toLowerCase().startsWith("y");
                }
            } else {
                if (!name) {
                    throw new Error("Missing required option: -n, --name");
                }
                if (!type) {
                    throw new Error("Missing required option: -t, --type");
                }
                if (!dockerComposePath) {
                    throw new Error(
                        "Missing required option: -d, --docker-compose",
                    );
                }
            }
            const apiClient = await getApiClient();
            const formData = new FormData();

            formData.append("name", name!.trim());
            formData.append("vmTypeId", type!.trim());

            if (inviteCode && inviteCode.trim() !== "") {
                formData.append("inviteCode", inviteCode.trim());
            }

            const absoluteDockerComposePath = path.resolve(
                dockerComposePath!.trim(),
            );
            const fileBuffer = fs.readFileSync(absoluteDockerComposePath);
            let dockerComposeContent = fileBuffer.toString();
            if (enableHttps) {
                const dockerCompose = yaml.load(
                    dockerComposeContent,
                ) as DockerCompose;

                // Create traefik network if it doesn't exist
                if (!dockerCompose.networks) {
                    dockerCompose.networks = {};
                }
                dockerCompose.networks.traefik = {
                    driver: "bridge",
                };

                // Add Traefik service
                dockerCompose.services.traefik = {
                    image: "traefik:v2.10",
                    command: [
                        "--api.insecure=false",
                        "--providers.docker=true",
                        "--providers.docker.exposedbydefault=false",
                        "--entrypoints.web.address=:80",
                        "--entrypoints.websecure.address=:443",
                        "--certificatesresolvers.myresolver.acme.tlschallenge=true",
                        "--certificatesresolvers.myresolver.acme.email=admin@$DOMAIN_NAME",
                        "--certificatesresolvers.myresolver.acme.storage=/letsencrypt/acme.json",
                    ],
                    ports: ["80:80", "443:443"],
                    volumes: [
                        "/var/run/docker.sock:/var/run/docker.sock:ro",
                        "./letsencrypt:/letsencrypt",
                    ],
                    networks: ["traefik"],
                    labels: {
                        "traefik.enable": "true",
                        "traefik.http.routers.traefik.entrypoints": "websecure",
                        "traefik.http.routers.traefik.service": "api@internal",
                        "traefik.http.routers.traefik.tls.certresolver":
                            "myresolver",
                        "traefik.http.routers.traefik.middlewares": "auth",
                        "traefik.http.middlewares.auth.basicauth.users":
                            "admin:$apr1$H6uskkkW$IgXLP6ewTrSuBkTrqE8wj/",
                    },
                };

                // Add Traefik labels to all other services
                Object.keys(dockerCompose.services).forEach((serviceName) => {
                    if (serviceName !== "traefik") {
                        const service = dockerCompose.services[serviceName];

                        if (!service.networks) {
                            service.networks = [];
                        }
                        if (!service.networks.includes("traefik")) {
                            service.networks.push("traefik");
                        }

                        if (!service.labels) {
                            service.labels = {};
                        }

                        service.labels = {
                            ...service.labels,
                            "traefik.enable": "true",
                            [`traefik.http.routers.${serviceName}.rule`]: `Host(\`$DOMAIN_NAME\`)`,
                            [`traefik.http.routers.${serviceName}.entrypoints`]:
                                "websecure",
                            [`traefik.http.routers.${serviceName}.tls.certresolver`]:
                                "myresolver",
                            [`traefik.http.services.${serviceName}.loadbalancer.server.port`]:
                                "80",
                        };
                    }
                });

                dockerComposeContent = yaml.dump(dockerCompose);
            }
            // The server expects the file field to be named 'dockercompose'
            formData.append(
                "dockercompose",
                dockerComposeContent,
                path.basename(absoluteDockerComposePath),
            );
            return await apiClient.post<CreateVmApiResponse>(
                API_ENDPOINTS.VM.CREATE,
                formData,
                {
                    headers: {
                        ...formData.getHeaders(), // Necessary for multipart/form-data with boundary
                    },
                    maxContentLength: Infinity, // Allow large file uploads
                    maxBodyLength: Infinity, // Allow large file uploads
                },
            );
        },
        (data: AxiosResponse) => {
            if (globalOptions.interactive) {
                if (data.data && data.data.id) {
                    console.log(
                        "\nVM creation process initiated successfully!",
                    );
                    var table = new Table({
                        head: [
                            "ID",
                            "Name",
                            "Status",
                            "Type",
                            "IP",
                            "Domain",
                            "Created At",
                        ],
                    });
                    table.push([
                        data.data.vmId,
                        data.data.nameFromUser,
                        data.data.status,
                        data.data.vmTypeId,
                        data.data.ip_address,
                        data.data.vmDomain,
                        data.data.createdAt,
                    ]);
                    console.log(table.toString());
                    console.log(
                        'You can check the VM status using the "list-vms" command shortly.',
                    );
                } else {
                    console.log(
                        "VM creation request may have been processed, but the response format was unexpected:",
                        data.data,
                    );
                }
            } else {
                successResponse(data.data);
            }
        },
    );
}
