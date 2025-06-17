import { getApiClient } from "../../services/apiClient";
import { VmInstance, GlobalOptions } from "../../types";
import { AxiosResponse } from "axios";
import { handleCommandExecution, successResponse } from "../../utils";
import Table from "cli-table3";
import { API_ENDPOINTS } from "../../constants";

export async function listVmsCommand(
    globalOptions: GlobalOptions,
): Promise<void> {
    await handleCommandExecution(
        globalOptions,
        async (): Promise<AxiosResponse> => {
            const apiClient = await getApiClient();
            return await apiClient.get<VmInstance[]>(
                API_ENDPOINTS.VM.INSTANCES,
            );
        },
        (data: AxiosResponse) => {
            if (globalOptions.interactive) {
                if (data.data && data.data.length > 0) {
                    var table = new Table({
                        head: [
                            "ID",
                            "UUID",
                            "Name",
                            "Status",
                            "Type",
                            "PricePerHour",
                            "IP",
                            "Domain",
                            "Created At",
                        ],
                    });
                    data.data.forEach((vm: VmInstance) => {
                        table.push([
                            vm.vmId,
                            vm.id,
                            vm.nameFromUser,
                            vm.status,
                            vm.vmTypeId,
                            vm.vmType.pricePerHour,
                            vm.ip_address,
                            vm.vmDomain,
                            vm.createdAt,
                        ]);
                    });
                    console.log(table.toString());
                } else if (data.data) {
                    console.log("No VM instances found.");
                } else {
                    console.log("Received an unexpected response for VM list.");
                }
            } else {
                successResponse(data.data);
            }
        },
    );
}
