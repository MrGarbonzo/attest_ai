import { getApiClient } from "../../services/apiClient";
import { AxiosResponse } from "axios";
import { GlobalOptions } from "../../types";
import { handleCommandExecution, successResponse } from "../../utils";
import { API_ENDPOINTS } from "../../constants";

export async function vmLogsCommand(
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
            return await apiClient.get<string>(
                API_ENDPOINTS.VM.LOGS(trimmedVmId),
            );
        },
        (data: AxiosResponse) => {
            if (globalOptions.interactive) {
                if (data.data) {
                    console.log(data.data);
                } else {
                    console.log("Received an unexpected response for VM logs.");
                }
            } else {
                successResponse(data.data);
            }
        },
    );
}
