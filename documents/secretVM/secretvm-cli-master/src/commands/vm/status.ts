import { getApiClient } from "../../services/apiClient";
import { VmDetailsApiResponse, GlobalOptions } from "../../types";
import { AxiosResponse } from "axios";
import { handleCommandExecution, successResponse } from "../../utils";
import { API_ENDPOINTS } from "../../constants";

export async function vmStatusCommand(
    vmId: string,
    globalOptions: GlobalOptions,
): Promise<void> {
    if (!vmId || vmId.trim() === "") {
        throw new Error("VM ID is required.");
    }
    const trimmedVmId = vmId.trim();

    await handleCommandExecution(
        globalOptions,
        async (): Promise<AxiosResponse> => {
            const apiClient = await getApiClient();
            return await apiClient.get<VmDetailsApiResponse>(
                API_ENDPOINTS.VM.DETAILS(trimmedVmId),
            );
        },
        (data: AxiosResponse) => {
            if (globalOptions.interactive) {
                if (data.data) {
                    const vm = data.data;
                    console.log("\n✅ --- VM Details ---");
                    console.log(`  VM UUID:        ${vm.id}`);
                    console.log(`  VM ID:          ${vm.vmId}`);
                    console.log(
                        `  Name (User):    ${vm.nameFromUser || "N/A"}`,
                    );
                    console.log(`  Name (System):  ${vm.name}`);
                    console.log(
                        `  Status:         ${vm.status} (State: ${vm.state})`,
                    );
                    console.log(`  User Sub:       ${vm.user}`);
                    console.log(`  IP Address:     ${vm.ip_address || "N/A"}`);
                    console.log(`  Domain:         ${vm.vmDomain || "N/A"}`);
                    console.log(
                        `  Created At:     ${new Date(vm.created_at).toLocaleString()}`,
                    );
                    console.log(
                        `  Updated At:     ${new Date(vm.updated_at).toLocaleString()}`,
                    );

                    console.log("\n  ⚙️ --- VM Configuration ---");
                    console.log(`    Memory:       ${vm.memory} GB`);
                    console.log(`    VCPUs:        ${vm.vcpus}`);
                    console.log(`    Disk Size:    ${vm.disk_size} GB`);

                    console.log("\n  📦 --- VM Type ---");
                    console.log(`    Type Name:    ${vm.vmType.type}`);
                    console.log(`    CPU:          ${vm.vmType.cpu} cores`);
                    console.log(`    RAM:          ${vm.vmType.ram} GB`);
                    console.log(`    Disk:         ${vm.vmType.disk} GB`);
                    console.log(
                        `    Price/Hour:   $${Number(vm.vmType.pricePerHour).toFixed(2)}`,
                    );

                    console.log("\n  🖥️ --- Host ---");
                    console.log(
                        `    Host Name:    ${vm.host.name} (${vm.host.host}:${vm.host.port})`,
                    );

                    console.log("\n  🌐 --- Network ---");
                    console.log(`    Gateway:      ${vm.gateway || "N/A"}`);
                    console.log(
                        `    Bridge:       ${vm.network_bridge || "N/A"}`,
                    );
                    console.log(
                        `    TAP Device:   ${vm.network_is_tap ? "Yes" : "No"}`,
                    );
                    console.log(
                        `    Ports:        ${vm.network_ports ? JSON.stringify(vm.network_ports) : "N/A"}`,
                    );

                    if (vm.docker_file && vm.docker_file.trim() !== "") {
                        console.log("\n  📄 --- Docker Config (Snippet) ---");
                        const snippet = vm.docker_file.substring(0, 250);
                        console.log(
                            snippet +
                                (vm.docker_file.length > 250 ? "..." : ""),
                        );
                    }
                    console.log("--------------------");
                } else {
                    console.log(
                        "VM details request processed, but the response was empty or in an unexpected format.",
                    );
                }
            } else {
                successResponse(data.data);
            }
        },
    );
}
