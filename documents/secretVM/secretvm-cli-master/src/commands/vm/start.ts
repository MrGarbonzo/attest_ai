import { getApiClient } from "../../services/apiClient";
import { StartVmApiResponse, GlobalOptions } from "../../types";
import { API_ENDPOINTS } from "../../constants";
import { AxiosResponse } from "axios";
import { handleCommandExecution, successResponse } from "../../utils";

export async function startVmCommand(
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
            return await apiClient.post<StartVmApiResponse>(
                API_ENDPOINTS.VM.START(trimmedVmId),
            );
        },
        (data: AxiosResponse) => {
            if (globalOptions.interactive) {
                if (data.data) {
                    console.log("\nVM start request processed.");
                    console.log("------------------------------------------");
                    console.log(
                        `Response Status: ${data.data.status || "N/A"}`,
                    );
                    if (data.data.message) {
                        console.log(`Message: ${data.data.message}`);
                    }
                    if (data.data.data) {
                        console.log(
                            "Details:",
                            JSON.stringify(data.data.data, null, 2),
                        );
                    }
                    console.log("------------------------------------------");
                    console.log(
                        `VM ID "${trimmedVmId}" is being started. Use "list-vms" to check its status shortly.`,
                    );
                } else {
                    console.log(
                        "VM start request processed, but the response was empty or in an unexpected format.",
                    );
                }
            } else {
                successResponse(data.data);
            }
        },
    );
}
