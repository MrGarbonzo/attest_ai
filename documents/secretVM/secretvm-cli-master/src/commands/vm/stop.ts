import { getApiClient } from "../../services/apiClient";
import { StopVmApiResponse, GlobalOptions } from "../../types";
import { API_ENDPOINTS } from "../../constants";
import { AxiosResponse } from "axios";
import { handleCommandExecution, successResponse } from "../../utils";

export async function stopVmCommand(
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
            return await apiClient.post<StopVmApiResponse>(
                API_ENDPOINTS.VM.STOP(trimmedVmId),
            );
        },
        (data: AxiosResponse) => {
            if (globalOptions.interactive) {
                if (data.data) {
                    console.log("\nVM stop request processed.");
                    console.log("------------------------------------------");
                    console.log(
                        `Response Status: ${data.data.status || "N/A"}`,
                    );
                    if (data.data.message) {
                        console.log(`Message: ${data.data.message}`);
                    }
                    console.log("------------------------------------------");
                    console.log(
                        `VM ID "${trimmedVmId}" is being stopped. Use "list-vms" to check its status.`,
                    );
                } else {
                    console.log(
                        "VM stop request processed, but the response was empty or in an unexpected format.",
                    );
                }
            } else {
                successResponse(data.data);
            }
        },
    );
}
